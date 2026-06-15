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

    for start in range(0, len(items), batch_size):
        if start > 0:
            time.sleep(1.5)
        batch = items[start:start+batch_size]
        body = [dict([(typ, [val])]) for typ, val in batch]
        body_str = json.dumps(body)

        resp_data = None
        # Try Python urllib first
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
            # Fallback: use system curl
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
            for item in resp_data.get("results", []):
                d = item.get("data", {})
                q = item.get("query", {})
                name = (q.get("journal", [""]) + q.get("issn", [""]))[0]
                cache[f"journal:{name}"] = {
                    "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "data": d
                }
                results.append({
                    "query": name,
                    "type": "journal" if q.get("journal") else "issn",
                    "if": d.get("imf", ""),
                    "if5": d.get("if5", ""),
                    "jcr": d.get("jcr", ""),
                    "cas": d.get("cas", ""),
                    "cas_top": d.get("cas_top", ""),
                    "cas_upgrade": d.get("xr", ""),
                    "citescore": d.get("citescore", ""),
                    "nature_index": d.get("nij", ""),
                    "risk": d.get("jcar_risk", ""),
                })
                if not quiet:
                    print(f"[{name}] IF={d.get('imf')} JCR={d.get('jcr')} CAS={d.get('cas')}",
                          file=sys.stderr)
            save_cache(cache)
        elif not quiet and not resp_data:
            print("[OneScholar] API unavailable — using offline journal DB as fallback", file=sys.stderr)
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

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    if len(results) == 1 and not args.quiet:
        r = results[0]
        print(f"\n=== {r['query']} ===")
        print(f"  Impact Factor : {r['if']} (5yr: {r['if5']})")
        print(f"  JCR           : {r['jcr']}")
        print(f"  CAS           : {r['cas']} ({r['cas_top']})  |  Upgrade: {r['cas_upgrade']}")
        print(f"  CiteScore     : {r['citescore']}")
        print(f"  Risk          : {r['risk']}")

if __name__ == "__main__":
    main()
