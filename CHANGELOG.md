# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.0.10] — 2026-06-15

### Fixed
- Windows GBK console encoding crash (`UnicodeEncodeError`) in `multi-search.py`, `journal-rank.py`, `pdf-fetch.py` when printing non-ASCII characters (e.g., author names with diacritics) — added `sys.stdout.reconfigure(encoding='utf-8', errors='replace')` on win32 (note: `google-scholar.py` and `cnki-playwright.py` already had this fix)

---

## [1.0.9] — 2026-06-15

### Added
- `cli.js` replaces `install.js`: fixes `--all` flag bug (previously installed 0 locations), adds `--help` / `-h`, `--version` / `-v`, proper exit codes
- `package.json`: added `bin` field (`lit-search-cite` → `cli.js`) to fix `npx` "could not determine executable" warning; added `files`, `author`, `repository` object fields
- `google-scholar.py`: Google Scholar via Playwright; one-time setup, headless after; supports `--query`, `--limit`, `--since`, `--until`, `--status`, `--login-only`
- `cnki-playwright.py`: built-in VPN URL lookup for ~100 Chinese universities; `--db` flag for database selection; PDF download via browser `fetch()` (VPN cookie-aware); debug screenshot on failure
- `check-deps.ps1`: 12-item dependency and config checker
- `scripts/setup.ps1`: API key wizard with `-Show` and `-Reset` flags; stores 8 keys including `wos`
- `references/mcp-template.json`: copy-paste MCP config template

### Changed
- `SKILL.md`: updated description to eval-optimized version; corrected Mode 5 PDF download (scansci-pdf primary, pdf-fetch fallback for DOI only); added `google-scholar.py` usage examples; fixed journal-rank.py note (requires OneScholar key, no silent offline fallback)
- `README.md`: rewritten based on actual source code; corrected script list and capabilities
- `AGENTS.md`: rewritten; fixed undefined `$SKILL_DIR` in manual installation; corrected Hermes note; accurate feature table
- `references/setup-guide.md`: rewritten; added Google Scholar step; corrected school count (~100); accurate config file schema
- `references/api-setup.md`: added missing Path H (Wanfang API); fixed api table ordering; corrected PowerShell examples
- `references/search-strategies.md`: added `multi-search.py` domain routing table; corrected arXiv category list; added CNKI `--db` note
- `references/optional-apis.md`: added Wanfang section; clarified journal-rank offline DB scope; corrected OneScholar note

### Fixed
- `--all` flag in `cli.js` now correctly installs to all 3 platforms
- `npx lit-search-cite` no longer shows "could not determine executable" warning
- CHANGELOG was stuck at v1.0.0 while package was at v1.0.9

---

## [1.0.0] — 2026-06-15

### Added
- Multi-source literature search: OpenAlex, CrossRef, PubMed, arXiv (zero-config); Semantic Scholar, Google Scholar (ai4scholar MCP); CNKI (Playwright); Wanfang (API)
- Journal ranking: OneScholar API (IF / JCR / CAS / CiteScore) + 300+ journal offline DB
- PDF download: scansci-pdf MCP (13+ sources) + pdf-fetch fallback chain (Unpaywall → OpenAlex → EuropePMC → Sci-Hub URL)
- Auto-citation: manual workflow supporting APA, GB/T 7714, IEEE, MLA, Chicago, Nature, Vancouver
- Literature review: multi-round search, paper clustering, structured draft generation
- SKILL.md: 5 modes (search, citation, review, relevance, PDF); platform-agnostic
- `multi-search.py` / `multi-search.ps1`: domain-routed multi-source search, DOI dedup, journal ranking
- `journal-rank.py` / `journal-rank.ps1`: OneScholar API with local cache
- `pdf-fetch.py` / `pdf-fetch.ps1`: PDF download chain (DOI input)
- `cnki-search.ps1`: Wanfang API + browser URLs for CNKI / Baidu Scholar / Weipu
- Platform support: Claude Code, Claude Desktop, OpenCode, Codex, Hermes
- `npx lit-search-cite` installer
