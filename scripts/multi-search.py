#!/usr/bin/env python3
"""Multi-source academic literature search with dedup, journal ranking, and formatted output.

Usage:
    python multi-search.py -q "styrene shape memory polymer" -d chemistry
    python multi-search.py -q "PEDOT PSS sensor" -d engineering --online-rank
    python multi-search.py -q "transformer attention" -s openalex,arxiv -n 20
"""

import argparse, json, os, re, sys, time, urllib.request
from pathlib import Path
from urllib.parse import quote

if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ── Source routing by domain ───────────────────────────────────────────────────
DEFAULT_SOURCES = {
    "cs":          ["openalex", "arxiv"],
    "engineering": ["openalex", "crossref"],
    "biomedicine": ["pubmed", "openalex", "crossref"],
    "biology":     ["pubmed", "openalex"],
    "physics":     ["arxiv", "openalex", "crossref"],
    "chemistry":   ["openalex", "crossref", "pubmed"],
    "social":      ["openalex", "crossref"],
    "humanities":  ["crossref"],
    "general":     ["openalex", "crossref", "pubmed"],
}

ARXIV_CATS = {
    "cs":     "cat:cs.LG+OR+cat:cs.AI+OR+cat:cs.CL+OR+cat:cs.CV",
    "physics": "cat:cond-mat.mtrl-sci+OR+cat:physics.app-ph+OR+cat:physics.chem-ph",
    "chemistry": "cat:cond-mat.mtrl-sci+OR+cat:physics.chem-ph",
    "biology":   "cat:q-bio",
    "engineering": "cat:cond-mat.mtrl-sci",
}

# ── Config ─────────────────────────────────────────────────────────────────────
CONFIG_DIR = Path.home() / ".lit-search-cite"
CONFIG_FILE = CONFIG_DIR / "config.json"

def load_config():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def get_key(cfg, name):
    api = cfg.get("api_keys", {})
    key = api.get(name, "")
    if key and not key.startswith("sk-") and not key.startswith("s2k-"):
        return key
    return key or os.environ.get(name.upper(), "")

# ── Journal ranks (offline, fast) ─────────────────────────────────────────────
def load_ranks_local():
    rank_file = Path(__file__).resolve().parent.parent / "references" / "journal-ranks.json"
    if rank_file.exists():
        try:
            return json.loads(rank_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"journals": {}, "_aliases": {}}

def get_tier_offline(venue: str, ranks: dict) -> str:
    if not venue or not ranks:
        return ""
    key = venue.strip().lower().lstrip("the ")
    j = ranks["journals"].get(key)
    if not j:
        alias = ranks.get("_aliases", {}).get(key, "")
        j = ranks["journals"].get(alias, {})
    if j:
        return f"[{j['tier']}-{j['level']}] IF={j['if']}"
    return ""

# ── OneScholar online ranks ────────────────────────────────────────────────────
def query_onescholar(journals: list, api_key: str) -> dict:
    """Batch query OneScholar API (max 5 per call). Returns {name_lower: display_str}."""
    results = {}
    batch_size = 5
    cache_dir = CONFIG_DIR / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / "journal-ranks.json"
    cache = {}
    if cache_file.exists():
        try:
            cache = json.loads(cache_file.read_text(encoding="utf-8"))
        except:
            pass

    for i in range(0, len(journals), batch_size):
        if i > 0:
            time.sleep(1.5)
        batch = journals[i:i+batch_size]
        body = [{"journal": [j]} for j in batch]
        try:
            req = urllib.request.Request(
                "https://api.scigreat.com/info/getrank",
                data=json.dumps(body).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                method="POST"
            )
            resp = urllib.request.urlopen(req, timeout=15)
            data = json.loads(resp.read())
            if data.get("status") == "success":
                for item in data.get("results", []):
                    d = item.get("data", {})
                    q = item.get("query", {})
                    name = (q.get("journal", [""])[0]).lower()
                    if d:
                        cache_key = f"journal:{name}"
                        cache[cache_key] = {"fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "data": d}
                        parts = []
                        if d.get("imf"): parts.append(f"IF={d['imf']}")
                        if d.get("jcr"): parts.append(f"JCR-{d['jcr']}")
                        if d.get("cas"): parts.append(f"CAS-{d['cas']}")
                        if d.get("cas_top"): parts.append(d['cas_top'])
                        results[name] = " ".join(parts)
        except Exception as e:
            if "429" in str(e):
                break
    # Save cache
    try:
        cache_file.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    except:
        pass
    return results

# ── DOI normalization for dedup ─────────────────────────────────────────────────
def norm_doi(doi: str) -> str:
    if not doi:
        return ""
    d = doi.strip().lower()
    m = re.match(r'(10\.\d{4,}/)', d)
    if m:
        return m.group(1) + d.split(m.group(1), 1)[-1]
    return d

# ═══════════════════════════════════════════════════════════════════════════════
# Search sources
# ═══════════════════════════════════════════════════════════════════════════════

def search_openalex(query: str, limit: int, year_from: int, year_to: int) -> list:
    """Path F — OpenAlex (free, 250M papers)."""
    filters = []
    if year_from > 0: filters.append(f"publication_year:>{year_from-1}")
    if year_to > 0:   filters.append(f"publication_year:<{year_to+1}")
    fstr = f"&filter={','.join(filters)}" if filters else ""
    url = (f"https://api.openalex.org/works?search={quote(query)}"
           f"&per-page={limit}&sort=cited_by_count:desc"
           f"&select=id,doi,title,publication_year,cited_by_count,authorships,primary_location,open_access"
           f"{fstr}&mailto=lit-search-cite@opencode.ai")
    try:
        resp = urllib.request.urlopen(url, timeout=20)
        data = json.loads(resp.read())
        results = []
        for w in data.get("results", []):
            authors = "; ".join(
                a.get("author", {}).get("display_name", "")
                for a in w.get("authorships", [])[:3]
            )
            venue_obj = w.get("primary_location", {}) or {}
            source = venue_obj.get("source") or {}
            venue = source.get("display_name", "N/A") if source else "N/A"
            results.append({
                "title": w.get("title", ""),
                "authors": authors,
                "year": w.get("publication_year", 0),
                "venue": venue,
                "doi": w.get("doi", ""),
                "citations": w.get("cited_by_count", 0),
                "source": "OpenAlex",
                "oa_url": (w.get("open_access") or {}).get("oa_url", ""),
            })
        print(f"[OpenAlex] Found {len(results)} results", file=sys.stderr)
        return results
    except Exception as e:
        print(f"[OpenAlex] Failed: {e}", file=sys.stderr)
        return []

def search_crossref(query: str, limit: int, year_from: int, year_to: int) -> list:
    """Path G — CrossRef (free, 150M DOI-registered papers)."""
    url = (f"https://api.crossref.org/works?query={quote(query)}"
           f"&rows={limit}&sort=relevance"
           f"&filter=type:journal-article,has-abstract:true"
           f"&mailto=lit-search-cite@opencode.ai")
    try:
        resp = urllib.request.urlopen(url, timeout=20)
        data = json.loads(resp.read())
        results = []
        for w in data.get("message", {}).get("items", []):
            title = (w.get("title") or [""])[0]
            if not title:
                continue
            dp = w.get("published", {}).get("date-parts", [[0]])[0]
            year = dp[0] if dp else 0
            if year_from > 0 and year < year_from: continue
            if year_to > 0 and year > year_to: continue
            authors = "; ".join(
                f"{a.get('family','')}, {a.get('given','')[:1]}"
                for a in (w.get("author") or [])[:3]
            )
            container = w.get("container-title") or ["N/A"]
            results.append({
                "title": title,
                "authors": authors,
                "year": year,
                "venue": container[0],
                "doi": w.get("DOI", ""),
                "citations": w.get("is-referenced-by-count", 0),
                "source": "CrossRef",
                "oa_url": "",
            })
        print(f"[CrossRef] Found {len(results)} results", file=sys.stderr)
        return results
    except Exception as e:
        print(f"[CrossRef] Failed: {e}", file=sys.stderr)
        return []

def search_pubmed(query: str, limit: int, year_from: int, year_to: int) -> list:
    """Path C — PubMed E-utilities (free)."""
    date_filter = ""
    if year_from > 0 and year_to > 0:
        date_filter = f"+AND+({year_from}/01/01[PDAT]:{year_to}/12/31[PDAT])"
    elif year_from > 0:
        date_filter = f"+AND+({year_from}/01/01[PDAT]:3000[PDAT])"
    elif year_to > 0:
        date_filter = f"+AND+(0001/01/01[PDAT]:{year_to}/12/31[PDAT])"

    try:
        search_url = (f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
                      f"?db=pubmed&term={quote(query + date_filter)}"
                      f"&retmax={limit}&retmode=json&sort=relevance")
        resp = urllib.request.urlopen(search_url, timeout=15)
        sdata = json.loads(resp.read())
        ids = sdata.get("esearchresult", {}).get("idlist", [])
        if not ids:
            print("[PubMed] No results", file=sys.stderr)
            return []

        sum_url = (f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
                   f"?db=pubmed&id={','.join(ids)}&retmode=json")
        resp = urllib.request.urlopen(sum_url, timeout=15)
        sumdata = json.loads(resp.read())
        results = []
        for pid in ids:
            d = sumdata.get("result", {}).get(pid)
            if not d: continue
            authors = "; ".join(
                a.get("name", "") for a in (d.get("authors") or [])[:3]
            )
            doi = d.get("elocationid", "").replace("doi: ", "")
            year_str = d.get("pubdate", "0")
            year = int(re.sub(r'\D', '', year_str)[:4]) if re.sub(r'\D', '', year_str) else 0
            results.append({
                "title": d.get("title", ""),
                "authors": authors,
                "year": year,
                "venue": d.get("source", "N/A"),
                "doi": doi,
                "citations": 0,
                "source": "PubMed",
                "oa_url": "",
            })
        print(f"[PubMed] Found {len(results)} results", file=sys.stderr)
        return results
    except Exception as e:
        print(f"[PubMed] Failed: {e}", file=sys.stderr)
        return []

def search_arxiv(query: str, limit: int, domain: str, year_from: int, year_to: int) -> list:
    """Path D — arXiv API (free)."""
    cat = ARXIV_CATS.get(domain, "")
    cat_q = f"+AND+({cat})" if cat else ""
    url = (f"https://export.arxiv.org/api/query"
           f"?search_query=all:{quote(query)}{cat_q}"
           f"&max_results={limit}&sortBy=relevance")
    try:
        resp = urllib.request.urlopen(url, timeout=20)
        content = resp.read().decode("utf-8")
        entries = re.findall(r'<entry>(.*?)</entry>', content, re.DOTALL)
        results = []
        for entry in entries:
            title_m = re.search(r'<title>(.*?)</title>', entry)
            if not title_m: continue
            title = re.sub(r'\s+', ' ', title_m.group(1).strip())
            year_m = re.search(r'<published>(\d{4})', entry)
            year = int(year_m.group(1)) if year_m else 0
            if year_from > 0 and year < year_from: continue
            if year_to > 0 and year > year_to: continue
            id_m = re.search(r'<id>.*?arxiv.org/abs/([^<]+)', entry)
            arxiv_id = id_m.group(1).split('v')[0] if id_m else ""
            results.append({
                "title": title,
                "authors": "N/A",
                "year": year,
                "venue": f"arXiv ({arxiv_id})",
                "doi": "",
                "citations": 0,
                "source": "arXiv",
                "oa_url": f"https://arxiv.org/pdf/{arxiv_id}" if arxiv_id else "",
            })
        print(f"[arXiv] Found {len(results)} results", file=sys.stderr)
        return results
    except Exception as e:
        print(f"[arXiv] Failed: {e}", file=sys.stderr)
        return []

# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Multi-source academic literature search")
    parser.add_argument("--query", "-q", required=True, help="Search query")
    parser.add_argument("--domain", "-d", default="general",
                       choices=list(DEFAULT_SOURCES.keys()), help="Research domain")
    parser.add_argument("--sources", "-s", default="", help="Manual sources (comma-separated)")
    parser.add_argument("--year-from", type=int, default=0)
    parser.add_argument("--year-to", type=int, default=0)
    parser.add_argument("--limit", "-n", type=int, default=15, help="Per-source limit")
    parser.add_argument("--total", "-t", type=int, default=30, help="Total output limit")
    parser.add_argument("--online-rank", action="store_true", help="Query OneScholar for live rankings")
    parser.add_argument("--no-dedup", action="store_true", help="Skip DOI dedup")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    active = [s.strip().lower() for s in args.sources.split(",")] if args.sources else DEFAULT_SOURCES[args.domain]

    if not args.json:
        print(f"\n=== Multi-Source Search ===", file=sys.stderr)
        print(f"  Query  : {args.query}", file=sys.stderr)
        print(f"  Domain : {args.domain}", file=sys.stderr)
        print(f"  Sources: {', '.join(active)}", file=sys.stderr)
        print(file=sys.stderr)

    # ── Execute searches ───────────────────────────────────────────────────────
    all_results = []
    for src in active:
        if src == "openalex":
            all_results.extend(search_openalex(args.query, args.limit, args.year_from, args.year_to))
        elif src == "crossref":
            all_results.extend(search_crossref(args.query, args.limit, args.year_from, args.year_to))
        elif src == "pubmed":
            all_results.extend(search_pubmed(args.query, args.limit, args.year_from, args.year_to))
        elif src == "arxiv":
            all_results.extend(search_arxiv(args.query, args.limit, args.domain, args.year_from, args.year_to))

    # ── Dedup by DOI ──────────────────────────────────────────────────────────
    if not args.no_dedup:
        seen = {}
        deduped = []
        for r in all_results:
            nd = norm_doi(r["doi"])
            if nd and nd in seen:
                if r["citations"] > seen[nd].get("citations", 0):
                    deduped[deduped.index(seen[nd])] = r
                    seen[nd] = r
                continue
            if nd:
                seen[nd] = r
            deduped.append(r)
        all_results = deduped
        if not args.json:
            print(f"[Dedup] {len(all_results)} unique papers", file=sys.stderr)

    # ── Sort ──────────────────────────────────────────────────────────────────
    all_results.sort(key=lambda x: (-(x["citations"] or 0), -(x["year"] or 0)))

    # ── Journal ranks ──────────────────────────────────────────────────────────
    ranks_local = load_ranks_local()
    ranks_online = {}
    cfg = load_config()

    if args.online_rank:
        os_key = get_key(cfg, "onescholar")
        if os_key and os_key.startswith("sk_"):
            venues = list(set(r["venue"] for r in all_results if r["venue"] and r["venue"] != "N/A"))
            max_q = min(10, len(venues))
            if not args.json:
                print(f"[OneScholar] Looking up {max_q} journal rankings...", file=sys.stderr)
            ranks_online = query_onescholar(venues[:max_q], os_key)
            if not args.json:
                print(f"[OneScholar] Got {len(ranks_online)} live rankings", file=sys.stderr)

    # ── Output ─────────────────────────────────────────────────────────────────
    output = all_results[:args.total]
    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    print(f"\n=== Results ({len(output)} of {len(all_results)} papers) ===\n")
    for i, r in enumerate(output, 1):
        venue = r["venue"]
        # Tier: prefer online, fallback to offline
        tier = ranks_online.get(venue.lower(), "") or get_tier_offline(venue, ranks_local)

        print(f"[{i}] {r['title']}")
        print(f"    Authors   : {r['authors']}")
        print(f"    Year      : {r['year']}  |  Venue: {venue}  |  Source: {r['source']}  {('|  Tier: ' + tier) if tier else ''}")
        print(f"    Citations : {r['citations']}")
        if r["doi"]:
            doi_str = r["doi"]
            if not doi_str.startswith("http"):
                doi_str = f"https://doi.org/{doi_str}"
            print(f"    DOI       : {doi_str}")
        if r.get("oa_url"):
            print(f"    OA URL    : {r['oa_url']}")
        print()

    print(f"---")
    print(f"Sources: {', '.join(active)}  |  Total: {len(all_results)}  |  Shown: {len(output)}")

if __name__ == "__main__":
    main()
