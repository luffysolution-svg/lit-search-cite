#!/usr/bin/env python3
"""PDF download chain: Unpaywall → OpenAlex → EuropePMC → Sci-Hub. Cross-platform.

Usage:
    python pdf-fetch.py --doi "10.1038/s41586-021-03819-2"
    python pdf-fetch.py --doi "10.3390/polym9120668" --output ./Papers
"""

import argparse, json, os, re, sys, urllib.request
from pathlib import Path

if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

CONFIG_DIR = Path.home() / ".lit-search-cite"
CONFIG_FILE = CONFIG_DIR / "config.json"

def load_email():
    if CONFIG_FILE.exists():
        try:
            cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            email = (cfg.get("api_keys", {}) or {}).get("unpaywall_email", "")
            if email: return email
        except:
            pass
    return os.environ.get("UNPAYWALL_EMAIL", "")

def fetch_pdf(doi: str, email: str, output_dir: str = "", quiet: bool = False):
    doi = doi.strip().replace("https://doi.org/", "").replace("http://doi.org/", "")
    pdf_url = None
    source = None
    oa_landing = None

    # 1. Unpaywall
    if email:
        try:
            req = urllib.request.Request(f"https://api.unpaywall.org/v2/{doi}?email={email}")
            resp = urllib.request.urlopen(req, timeout=12)
            data = json.loads(resp.read())
            loc = data.get("best_oa_location") or {}
            if loc.get("url_for_pdf"):
                pdf_url = loc["url_for_pdf"]
                source = f"Unpaywall ({data.get('oa_status', 'unknown')})"
        except Exception:
            pass

    # 2. OpenAlex
    if not pdf_url:
        try:
            req = urllib.request.Request(f"https://api.openalex.org/works/https://doi.org/{doi}")
            resp = urllib.request.urlopen(req, timeout=12)
            data = json.loads(resp.read())
            oa = data.get("open_access") or {}
            url = oa.get("oa_url", "")
            if url and url.endswith(".pdf"):
                pdf_url = url
                source = "OpenAlex"
            elif url:
                oa_landing = url
        except Exception:
            pass

    # 3. EuropePMC
    if not pdf_url:
        try:
            q = f"DOI:{doi}"
            req = urllib.request.Request(
                f"https://www.ebi.ac.uk/europepmc/webservices/rest/search"
                f"?query={urllib.request.quote(q)}&resultType=core&format=json"
            )
            resp = urllib.request.urlopen(req, timeout=12)
            data = json.loads(resp.read())
            for r in data.get("resultList", {}).get("result", []):
                if r.get("isOpenAccess") == "Y" and r.get("pmcid"):
                    pdf_url = f"https://europepmc.org/articles/{r['pmcid']}/pdf"
                    source = f"EuropePMC (PMC:{r['pmcid']})"
                    break
        except Exception:
            pass

    scihub_url = f"https://sci-hub.st/{doi}"

    if not pdf_url:
        if not quiet:
            print(f"Warning: No OA PDF found for DOI: {doi}", file=sys.stderr)
            if oa_landing:
                print(f"OA landing page: {oa_landing}", file=sys.stderr)
            print(f"Sci-Hub (open in browser): {scihub_url}", file=sys.stderr)
            print(f"Publisher page: https://doi.org/{doi}", file=sys.stderr)
        sys.exit(1)

    if not quiet:
        print(f"PDF found via {source}")
        print(f"URL: {pdf_url}")

    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        safe = re.sub(r'[/\\:*?"<>|]', '_', doi)
        fpath = out / f"{safe}.pdf"
        try:
            urllib.request.urlretrieve(pdf_url, str(fpath))
            print(f"Saved: {fpath}")
            return str(fpath)
        except Exception as e:
            print(f"Warning: Download failed — {e}", file=sys.stderr)
            print(f"URL: {pdf_url}", file=sys.stderr)
    else:
        return pdf_url

def main():
    parser = argparse.ArgumentParser(description="PDF download chain for academic papers")
    parser.add_argument("--doi", "-d", required=True, help="Paper DOI")
    parser.add_argument("--output", "-o", default="", help="Output directory")
    parser.add_argument("--quiet", "-q", action="store_true")
    args = parser.parse_args()

    email = load_email()
    fetch_pdf(args.doi, email, args.output, args.quiet)

if __name__ == "__main__":
    main()
