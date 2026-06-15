---
name: lit-search-cite
description: Use when a user needs to find or work with academic papers: searching databases (知网/CNKI, arXiv, PubMed, Google Scholar, 万方) for literature on a topic; downloading a paper PDF by DOI, arXiv ID, or title; looking up journal rankings (影响因子, 中科院分区, JCR quartile, CCF tier); judging whether a specific paper is relevant to their research direction; adding formatted citations (GB/T 7714, APA, IEEE) to existing text; or drafting a literature review or related-work section. Covers Chinese (知网/万方/维普) and English research workflows.
compatibility: opencode, claude-code, codex, hermes, claude-desktop
---

# Lit-Search-Cite: Academic Literature & Citation Skill

Multi-source literature search, journal ranking, auto-citation, and PDF download. English & Chinese.

> **First run:** `.\scripts\check-deps.ps1` → `references/setup-guide.md`
> **Windows:** Use `Invoke-RestMethod` / `Invoke-WebRequest` — never Bash `curl` (returns exit 49 on Windows).

---

## Source Selection (Quick Reference)

Pick 1–2 sources per search. More sources ≠ better results — use domain routing.

| Domain | Primary (with key) | Free fallback | Journal ranking |
|--------|--------------------|---------------|-----------------|
| CS / AI | `ai4scholar` MCP → arXiv | `multi-search.py -d cs` | Auto via offline DB |
| Engineering | `ai4scholar` MCP → Semantic Scholar | `multi-search.py -d engineering` | Auto via offline DB |
| Chemistry / Materials | `ai4scholar` MCP → Semantic Scholar | `multi-search.py -d chemistry` | Auto via offline DB |
| Biomedicine | `ai4scholar` MCP → PubMed | `multi-search.py -d biomedicine` | Auto via offline DB |
| Physics / Math | arXiv + Semantic Scholar | `multi-search.py -d physics` | Auto via offline DB |
| Social / Humanities | Google Scholar + Semantic Scholar | `multi-search.py -d social` | `journal-rank.py` |
| **Chinese** | CNKI Playwright + Wanfang API | CNKI browser URLs via `cnki-search.ps1` | `journal-rank.py` |
| General | `multi-search.py -d general` | Same (covers OpenAlex + CrossRef + PubMed) | Auto via offline DB |

**Google Scholar:** `ai4scholar` MCP (fastest) → `google-scholar.py` (one-time Playwright setup) → OpenAlex/CrossRef (zero-config).

**Journal ranking:**
```bash
# OneScholar API (requires key) — returns IF, JCR, CAS, CiteScore, risk
python scripts/journal-rank.py -j "Nature" "Adv. Mater." "JACS"

# Offline fallback (zero-config, 300+ journals) — used automatically by multi-search.py
# journal-rank.py itself requires the key; offline DB is built into multi-search.py only
```

---

## Mode 1 — Literature Search

**Triggers:** "find papers on X", "搜索关于X的文献", "state of the art", "related work"

**Step 1 — Clarify:** topic, domain (→ table above), year range, language, how many results.

**Step 2 — Search:**

```bash
# Zero-config: OpenAlex + CrossRef + PubMed (domain-routed)
python scripts/multi-search.py -q "styrene shape memory polymer" -d chemistry

# With live journal rankings
python scripts/multi-search.py -q "transformer attention" -d cs --online-rank

# Year filter + JSON output
python scripts/multi-search.py -q "cancer immunotherapy" -d biomedicine --year-from 2022 -t 20

# Google Scholar (Playwright, one-time setup required)
python scripts/google-scholar.py --query "attention is all you need" --limit 15 --since 2020

# Chinese literature (CNKI Playwright — requires prior setup)
python scripts/cnki-playwright.py --query "大语言模型 代码生成" --limit 20

# Chinese literature (Wanfang API + browser URLs — no setup needed for URLs)
.\scripts\cnki-search.ps1 -Query "大语言模型 代码生成"
```

**Step 3 — Output format:**
```
[N] Title (Year)
    Authors  : Lead Author et al.
    Venue    : Journal Name  |  Tier: IF=X.X JCR-Q1 CAS-1区
    Citations: N  |  Source: OpenAlex
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
2. For each claim, run one targeted search. Pick best match by relevance + citation count.
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
2. **Round 1 (broad):** 2–3 queries per sub-theme via `multi-search.py`, collect 20–30 papers.
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

For venue quality: `python scripts/journal-rank.py -j "JournalName"` (requires OneScholar key).
Also run `get_semantic_recommendations_for_paper` to surface related work the user may have missed.

---

## Mode 5 — PDF Download

**Triggers:** "download this paper", "get the PDF", user says yes after Mode 1

### English papers

```
# Primary — scansci-pdf MCP (headless, 13+ sources, zero-config):
scansci_pdf_smart_download(identifier="10.xxxx/..." or "arXiv:2401.12345")

# Fallback — pdf-fetch (DOI only, no arXiv):
python scripts/pdf-fetch.py --doi "10.xxxx/..." --output ./Papers
.\scripts\pdf-fetch.ps1 -DOI "10.xxxx/..." -OutputPath ".\Papers"
```

For paywalled papers: one-time browser login (`scansci_pdf_import_browser_cookies` / `scansci_pdf_carsi_login` / `scansci_pdf_ezproxy_login`) → cookies saved permanently → all future downloads headless.

### Chinese papers (CNKI)

Headless search works after VPN setup. PDF download requires a visible browser due to CAPTCHA:
```bash
# Search (headless after setup)
python scripts/cnki-playwright.py --query "形状记忆 聚合物" --limit 20

# Download PDFs (needs visible browser for CAPTCHA)
python scripts/cnki-playwright.py --query "形状记忆 聚合物" --download --output ./Papers --no-headless
```

---

## Reference Files

| File | When to read |
|------|-------------|
| `references/setup-guide.md` | First-time setup: Node.js, Python, Playwright, MCP config, CNKI VPN |
| `references/api-setup.md` | All API endpoints with PowerShell + Python examples |
| `references/search-strategies.md` | Query syntax: PubMed MeSH, arXiv categories, CNKI Boolean |
| `references/optional-apis.md` | OneScholar, Elsevier, Springer, Web of Science setup |
| `references/journal-ranks.json` | 300+ journal tier offline DB (built into multi-search scripts) |
| `references/mcp-template.json` | MCP server config template (copy to `%USERPROFILE%\.claude\mcp.json`) |

---

> **Note for AI:** Do NOT run `setup.ps1`, `cnki-playwright.py --setup/--login-only`, `google-scholar.py --setup/--login-only`, or any scansci-pdf login tool via shell tools — these require an interactive terminal and a visible browser. Tell the user the exact command to run themselves.
