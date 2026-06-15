---
name: lit-search-cite
description: "Use when a user needs to find or work with academic papers: searching databases (知网/CNKI, arXiv, PubMed, Google Scholar, 万方) for literature on a topic; downloading a paper PDF by DOI, arXiv ID, or title; looking up journal rankings (影响因子, 中科院分区, JCR quartile, CCF tier); judging whether a specific paper is relevant to their research direction; adding formatted citations (GB/T 7714, APA, IEEE) to existing text; or drafting a literature review or related-work section. Covers Chinese (知网/万方/维普) and English research workflows."
compatibility: opencode, claude-code, codex, hermes, claude-desktop
---

# Lit-Search-Cite: Academic Literature & Citation Skill

Multi-source literature search, journal ranking, auto-citation, and PDF download. English & Chinese.

> **First run:** `.\scripts\check-deps.ps1` → `references/setup-guide.md`
> **Windows:** Use `Invoke-RestMethod` / `Invoke-WebRequest` — never Bash `curl` (returns exit 49 on Windows).
> **Configure keys:** Say "帮我配置 API key" — the AI reads current config and writes missing keys directly.

---

## Mode 0 — Configure API Keys

**Triggers:** "帮我配置key", "set up my API keys", "configure lit-search-cite", "我的key是..."

Two config files. The AI reads both, fills in only the fields the user provides, and saves.

### File 1 — `~/.lit-search-cite/config.json` (Python scripts)

```json
{
  "api_keys": {
    "semantic_scholar": "",   // s2k-... — free at semanticscholar.org/product/api
    "onescholar":       "",   // sk_...  — journal ranking, scigreat.com
    "unpaywall_email":  "",   // any email — PDF OA lookup
    "elsevier":         "",   // Scopus/ScienceDirect API key
    "springer":         "",   // Springer Nature API key
    "wanfang":          "",   // 万方 API key
    "wos":              ""    // Web of Science key
  }
}
```

### File 2 — `~/.claude/mcp.json` (MCP servers, requires Claude Code restart)

Update only the `env` block inside the `ai4scholar` server entry:
```json
"AI4SCHOLAR_API_KEY": "sk-user-..."
```

**AI workflow:**
1. Read `~/.lit-search-cite/config.json` (create with empty keys if missing).
2. Read `~/.claude/mcp.json` — locate the `ai4scholar.env.AI4SCHOLAR_API_KEY` field.
3. Ask the user only for keys that are currently empty/missing.
4. Write both files. Remind user to **restart Claude Code** after mcp.json changes.
5. Never overwrite a key that is already set unless the user explicitly provides a new value.

> **Note for AI:** You CAN write these files directly with the Write/Edit tool — no interactive terminal needed. Do NOT touch any other fields in mcp.json.

---

## Primary Workflow (MCP-first)

**Search → Download → Cite. All headless after MCP setup.**

```
Search:   ai4scholar MCP  →  multi-search.py (fallback)
Download: scansci-pdf MCP  →  OpenCLI browser (paywall fallback)  →  pdf-fetch.py (OA only)
Chinese:  ai4scholar Google Scholar MCP (Chinese keywords)  →  OpenCLI browser (CNKI with existing login)
```

**Download priority:** `scansci_pdf_smart_download` first (Springer Direct / ElsevierAPI / OA repos / Sci-Hub). Only fall back to OpenCLI browser when all scansci-pdf channels fail — it reuses your existing browser login state, no `--remote-debugging-port` required.

---

## Source Selection (Quick Reference)

| Domain | MCP path (primary) | Script fallback |
|--------|--------------------|-----------------|
| CS / AI | `search_semantic` + `search_google_scholar` | `multi-search.py -d cs` |
| Engineering | `search_semantic` | `multi-search.py -d engineering` |
| Chemistry / Materials | `search_semantic` + `search_google_scholar` | `multi-search.py -d chemistry` |
| Biomedicine | `search_pubmed` + `search_semantic` | `multi-search.py -d biomedicine` |
| Physics / Math | `search_arxiv` + `search_semantic` | `multi-search.py -d physics` |
| Social / Humanities | `search_google_scholar` | `multi-search.py -d social` |
| **Chinese** | `search_google_scholar` (Chinese keywords) + OpenCLI browser (CNKI) | `cnki-search.ps1` browser URLs |
| General | `search_semantic` + `search_google_scholar` | `multi-search.py -d general` |

**PDF download:** Always try `scansci_pdf_smart_download` first — covers OA, Sci-Hub, CARSI, ElsevierAPI, CORE, LibGen. If all channels fail, fall back to OpenCLI browser (reuses existing browser institutional login; Wiley `pdfdirect` works fully, Elsevier falls back to ElsevierAPI channel). `pdf-fetch.py` is last resort for OA-only papers.

**Journal ranking:** Use offline DB via `multi-search.py` (300+ journals, zero-config). `journal-rank.py` requires OneScholar API key.

---

## Mode 1 — Literature Search

**Triggers:** "find papers on X", "搜索关于X的文献", "state of the art", "related work"

**Step 1 — Clarify:** topic, domain (→ table above), year range, language, how many results.

**Step 2 — Search (MCP-first):**

```python
# Primary: Semantic Scholar (best relevance, 214M papers)
search_semantic(query="ethylbenzene dehydrogenation styrene catalyst", max_results=12)

# Deep text match (finds specific methods, data, claims)
search_semantic_snippets(query="oxidative dehydrogenation ethylbenzene SMART process", limit=8)

# Google Scholar (covers Chinese literature too)
search_google_scholar(query="乙苯脱氢 苯乙烯工艺 催化剂", max_results=10, year_from=2018)

# PubMed for biomedical
search_pubmed(query="CRISPR gene editing therapy", max_results=15)

# arXiv for CS/physics preprints
search_arxiv(query="transformer attention mechanism", max_results=10)
```

**Step 2 (fallback — no MCP):**
```bash
# Zero-config: OpenAlex + CrossRef + PubMed
python scripts/multi-search.py -q "styrene shape memory polymer" -d chemistry

# Year filter + JSON output
python scripts/multi-search.py -q "cancer immunotherapy" -d biomedicine --year-from 2022 -t 20

# Chinese literature browser URLs (no setup needed)
.\scripts\cnki-search.ps1 -Query "大语言模型 代码生成"
```

**Step 3 — Output format:**
```
[N] Title (Year)
    Authors  : Lead Author et al.
    Venue    : Journal Name  |  Tier: IF=X.X JCR-Q1 CAS-1区
    Citations: N  |  Source: SemanticScholar
    DOI      : https://doi.org/10.xxxx/...
    Relevance: why it matches (1–2 sentences)
```

**Step 4 — Follow-up:** "Download PDFs? Find citing papers? Add citations to your text?"

---

## Mode 2 — Auto-Citation

**Triggers:** "add citations to this text", "加引用", "annotate with references", "标注参考文献"

**Citation styles:** `gbt7714` (Chinese default) | `apa` | `ieee` | `nature` | `vancouver` | `mla` | `chicago`

**Workflow:**
1. Read user's text. Identify each claim that needs a citation. Mark as `[1]`, `[2]`, etc.
2. For each claim, run one targeted `search_semantic` or `search_semantic_snippets`. Pick best match by relevance + citation count.
3. Produce output:

```
--- Annotated Text ---
[Original sentence with inline [1] markers]...

--- References ---
[1] Author A, Author B. "Title." Journal, Year. DOI: 10.xxxx/...
    Relevance: directly supports claim about X
    (⚠ verify) ← add this flag when match confidence < 80%
```

4. If no strong match found, insert `[?]` and note "No strong match found — manual search recommended."

---

## Mode 3 — Literature Review

**Triggers:** "write a literature review", "综述", "survey", "related work section"

1. Clarify: topic, 3–5 sub-themes, year range, target length, citation style, language.
2. **Round 1 (broad):** `search_semantic` × 2–3 queries per sub-theme; collect 20–30 papers.
3. **Round 2 (fill gaps):** `get_semantic_citations` on key papers; `get_semantic_recommendations` for related work.
4. **Cluster** by sub-theme. Draft structure:

```
1. Overview → 2. Background → 3. Theme A → 4. Theme B → 5. Recent Advances → 6. Research Gaps → References
```

5. Each paragraph cites specific papers with `[Author, Year]` inline markers. Append full reference list.

---

## Mode 4 — Relevance Assessment

**Triggers:** "is this paper relevant?", "评价这篇文献", "rate this paper"

Score **1–10** using: topic fit (40%) + methodology (20%) + recency (20%) + venue quality (20%).

For venue quality: check offline tier via `multi-search.py` output, or `journal-rank.py` (requires OneScholar key).
Run `get_semantic_recommendations_for_paper` to surface related work the user may have missed.

---

## Mode 5 — PDF Download

**Triggers:** "download this paper", "get the PDF", user says yes after Mode 1

### Primary — scansci-pdf MCP (zero-config, 13+ sources)

```python
# Works for DOI and arXiv IDs, also returns BibTeX
scansci_pdf_smart_download(identifier="10.1016/j.apcatb.2022.121070", bibtex=True)
scansci_pdf_smart_download(identifier="2301.12345")   # arXiv

# For paywalled papers via institutional access (one-time browser login, then headless):
scansci_pdf_carsi_login(publisher="sciencedirect")  # or springer, wiley, ieee, nature
# After login, scansci_pdf_smart_download works headlessly for all future downloads
```

### Fallback — pdf-fetch scripts (OA papers, DOI only)

```bash
python scripts/pdf-fetch.py --doi "10.1038/s41586-021-03819-2" --output ./Papers
.\scripts\pdf-fetch.ps1 -DOI "10.1038/s41586-021-03819-2" -OutputPath ".\Papers"
```

### Chinese papers (CNKI)

CNKI PDF download via CARSI (one-time browser login):
```python
scansci_pdf_carsi_login()          # opens browser → log in with your university account
scansci_pdf_smart_download(identifier="10.xxxx/...")  # headless after first login
```

For CNKI search + PDF download via institutional login (OpenCLI browser, no extra setup):
```
Tell Claude: "帮我在知网搜索「大语言模型」" — Claude navigates CNKI in your existing
Chrome session (institutional cookies auto-applied, no VPN URL configuration needed).
```

See `references/opencli.md` for verified selectors and download patterns.
See `references/chrome-devtools.md` for the older Chrome DevTools MCP approach (requires `--remote-debugging-port=9222`).

---

## Reference Files

| File | When to read |
|------|-------------|
| `references/setup-guide.md` | First-time setup: Node.js, Python, MCP config |
| `references/api-setup.md` | All API endpoints with PowerShell + Python examples |
| `references/search-strategies.md` | Query syntax: PubMed MeSH, arXiv categories, CNKI Boolean |
| `references/optional-apis.md` | OneScholar, Elsevier, Springer, Web of Science setup |
| `references/opencli.md` | OpenCLI browser automation — CNKI search, Wiley download, Elsevier access (verified 2026-06-15) |
| `references/chrome-devtools.md` | Chrome DevTools MCP — legacy approach, requires `--remote-debugging-port=9222` |
| `references/journal-ranks.json` | 300+ journal tier offline DB (built into multi-search scripts) |
| `references/mcp-template.md` | MCP server config template (copy to `%USERPROFILE%\.claude\mcp.json`) |

---

> **Note for AI:** Do NOT run `setup.ps1` or any scansci-pdf login tool (`carsi_login`, `ezproxy_login`, `import_browser_cookies`) via shell tools — these require an interactive terminal and a visible browser. Tell the user the exact command to run themselves. OpenCLI browser commands (`opencli browser <session> open/fill/click/eval/wait`) can be called directly by the AI via the Bash tool — they operate on the user's already-running Chrome session.
