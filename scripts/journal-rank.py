#!/usr/bin/env python3
"""Journal ranking via OneScholar API + offline database. Cross-platform.

Usage:
    python journal-rank.py -j "Nature" "Science" "Cell"
    python journal-rank.py -j "Advanced Materials" --quiet
    python journal-rank.py -i "0028-0836" "0036-8075"
"""

import argparse, json, os, sys, time, urllib.request
from pathlib import Path

if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

CONFIG_DIR = Path.home() / ".lit-search-cite"
CONFIG_FILE = CONFIG_DIR / "config.json"
CACHE_FILE = CONFIG_DIR / "cache" / "journal-ranks.json"

def load_config():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except:
            pass
    return {}

def load_cache():
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except:
            pass
    return {}

def save_cache(cache):
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")

def query_offline_db(journals: list, issns: list) -> list:
    """Look up journals in the bundled offline references/journal-ranks.json."""
    db_path = Path(__file__).parent.parent / "references" / "journal-ranks.json"
    if not db_path.exists():
        return []
    try:
        db = json.loads(db_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    jdb = db.get("journals", {})
    aliases = db.get("_aliases", {})

    results = []
    for name in journals:
        key = name.strip().lower().lstrip("the ").strip()
        entry = jdb.get(key) or jdb.get(aliases.get(key, ""))
        if entry:
            results.append({
                "query": name, "type": "journal", "source": "offline",
                "if": str(entry.get("if", "")), "if5": "",
                "jcr": "", "cas": f"{entry.get('tier','')} {entry.get('level','')}".strip(),
                "cas_top": "", "cas_upgrade": "", "citescore": "",
                "nature_index": "", "risk": "",
            })
        else:
            results.append({
                "query": name, "type": "journal", "source": "not_found",
                "if": "", "if5": "", "jcr": "", "cas": "", "cas_top": "",
                "cas_upgrade": "", "citescore": "", "nature_index": "", "risk": "",
            })
    for issn in issns:
        key = issn.strip().lower()
        journal_key = aliases.get(key, "")
        entry = jdb.get(journal_key) if journal_key else None
        if entry:
            results.append({
                "query": issn, "type": "issn", "source": "offline",
                "if": str(entry.get("if", "")), "if5": "",
                "jcr": "", "cas": f"{entry.get('tier','')} {entry.get('level','')}".strip(),
                "cas_top": "", "cas_upgrade": "", "citescore": "",
                "nature_index": "", "risk": "",
            })
        else:
            results.append({
                "query": issn, "type": "issn", "source": "not_found",
                "if": "", "if5": "", "jcr": "", "cas": "", "cas_top": "",
                "cas_upgrade": "", "citescore": "", "nature_index": "", "risk": "",
            })
    return results


def query_onescholar(journals: list, issns: list, api_key: str, quiet: bool) -> list:
    """Batch query OneScholar API (max 5 per call). Falls back to curl if urllib fails."""
    items = []
    for j in journals:
        items.append(("journal", j))
    for i in issns:
        items.append(("issn", i))

    results = []
    batch_size = 5
    cache = load_cache()
    api_ok = False

    for start in range(0, len(items), batch_size):
        if start > 0:
            time.sleep(1.5)
        batch = items[start:start+batch_size]
        body = [dict([(typ, [val])]) for typ, val in batch]
        body_str = json.dumps(body)

        resp_data = None
        try:
            req = urllib.request.Request(
                "https://api.scigreat.com/info/getrank",
                data=body_str.encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "lit-search-cite/1.0"
                },
                method="POST"
            )
            resp = urllib.request.urlopen(req, timeout=15)
            resp_data = json.loads(resp.read())
        except Exception:
            import subprocess, tempfile
            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
                    f.write(body_str)
                    tmp = f.name
                result = subprocess.run(
                    ["curl", "-s", "-X", "POST",
                     "https://api.scigreat.com/info/getrank",
                     "-H", f"Authorization: Bearer {api_key}",
                     "-H", "Content-Type: application/json",
                     "-d", f"@{tmp}"],
                    capture_output=True, text=True, timeout=20
                )
                os.unlink(tmp)
                if result.returncode == 0 and result.stdout.strip():
                    resp_data = json.loads(result.stdout)
            except Exception:
                pass

        if resp_data and resp_data.get("status") == "success":
            api_ok = True
            for item in resp_data.get("results", []):
                d = item.get("data", {})
                q = item.get("query", {})
                name = (q.get("journal", [""]) + q.get("issn", [""]))[0]
                cache[f"journal:{name}"] = {
                    "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "data": d
                }
                results.append({
                    "query": name, "type": "journal" if q.get("journal") else "issn",
                    "source": "api",
                    "if": d.get("imf", ""), "if5": d.get("if5", ""),
                    "jcr": d.get("jcr", ""), "cas": d.get("cas", ""),
                    "cas_top": d.get("cas_top", ""), "cas_upgrade": d.get("xr", ""),
                    "citescore": d.get("citescore", ""), "nature_index": d.get("nij", ""),
                    "risk": d.get("jcar_risk", ""),
                })
                if not quiet:
                    print(f"[{name}] IF={d.get('imf')} JCR={d.get('jcr')} CAS={d.get('cas')}",
                          file=sys.stderr)
            save_cache(cache)

    if not api_ok and not quiet:
        print("[OneScholar] API unavailable -- trying offline journal DB", file=sys.stderr)
    return results

def main():
    parser = argparse.ArgumentParser(description="Journal ranking via OneScholar API")
    parser.add_argument("--journal", "-j", nargs="+", default=[], help="Journal names")
    parser.add_argument("--issn", "-i", nargs="+", default=[], help="ISSNs")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress verbose output")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if not args.journal and not args.issn:
        parser.error("Provide at least one --journal or --issn")

    cfg = load_config()
    api_key = (cfg.get("api_keys", {}).get("onescholar", "") or
               os.environ.get("ONESCHOLAR_API_KEY", ""))

    if not api_key or not api_key.startswith("sk_"):
        print("Error: OneScholar API key not configured", file=sys.stderr)
        print("Set api_keys.onescholar in ~/.lit-search-cite/config.json or ONESCHOLAR_API_KEY env var",
              file=sys.stderr)
        sys.exit(1)

    results = query_onescholar(args.journal, args.issn, api_key, args.quiet)

    # Offline fallback for any journal not returned by the API
    found = {r["query"].lower() for r in results}
    missing_j = [j for j in args.journal if j.lower() not in found]
    missing_i = [i for i in args.issn if i.lower() not in found]
    if missing_j or missing_i:
        results.extend(query_offline_db(missing_j, missing_i))

    if not results:
        print("No results found.", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    if len(results) == 1:
        r = results[0]
        src = f"  [{r.get('source','api')}]" if r.get("source") != "api" else ""
        print(f"\n=== {r['query']} ==={src}")
        if_str = r['if'] + (f" (5yr: {r['if5']})" if r['if5'] else "")
        cas_str = r['cas'] + (f" ({r['cas_top']})" if r['cas_top'] else "")
        if r['cas_upgrade']: cas_str += f"  |  Upgrade: {r['cas_upgrade']}"
        print(f"  Impact Factor : {if_str or '--'}")
        print(f"  JCR           : {r['jcr'] or '--'}")
        print(f"  CAS           : {cas_str or '--'}")
        if r['citescore']: print(f"  CiteScore     : {r['citescore']}")
        if r['risk']:      print(f"  Risk          : {r['risk']}")
    else:
        print(f"\n{'Journal':<35}  {'IF':>6}  {'JCR':<6}  {'CAS':<14}  Source")
        print("-" * 75)
        for r in results:
            src = r.get("source", "api")
            not_found = (src == "not_found")
            cas_str = r["cas"] if r["cas"] else ("--" if not_found else "")
            if_str  = r["if"]  if r["if"]  else ("--" if not_found else "")
            jcr_str = r["jcr"] if r["jcr"] else ("--" if not_found else "")
            print(f"  {r['query']:<33}  {if_str:>6}  {jcr_str:<6}  {cas_str:<14}  {src}")

if __name__ == "__main__":
    main()
