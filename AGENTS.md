# lit-search-cite

> Multi-source academic literature search, journal ranking, auto-citation, and PDF download skill.

## Installation

### One command (recommended)

```bash
npx lit-search-cite
```

Auto-detects and installs to Claude Code, OpenCode, and Agent Skills directories. Options:

```bash
npx lit-search-cite --claude       # Claude Code / Claude Desktop only
npx lit-search-cite --opencode     # OpenCode / Codex only
npx lit-search-cite --agents       # Agent Skills only
npx lit-search-cite --all          # All platforms (same as no flags)
npx lit-search-cite --target ~/my-skills   # Custom path
```

### Manual installation

Copy the skill directory to the appropriate location for your platform:

| Platform | Global (all projects) | Project-level |
|----------|-----------------------|---------------|
| Claude Code | `~/.claude/skills/lit-search-cite/` | `.claude/skills/lit-search-cite/` |
| OpenCode / Codex | `~/.config/opencode/skills/lit-search-cite/` | `.opencode/skills/lit-search-cite/` |
| Agent Skills | `~/.agents/skills/lit-search-cite/` | `.agents/skills/lit-search-cite/` |

MCP servers are required for full functionality. Copy the JSON blocks from `references/mcp-template.md` into `~/.claude/mcp.json` (or merge into your existing file) and restart Claude Code.

### Hermes

Copy the directory to the Hermes skills directory. Tool names in SKILL.md are used without the `mcp__<server>__` prefix in some modes — Hermes resolves these automatically via its tool registry.

---

## Quick Start

```bash
# English search — zero-config (OpenAlex + CrossRef + PubMed)
python scripts/multi-search.py -q "transformer attention mechanism" -d cs

# With live journal rankings (requires OneScholar API key)
python scripts/multi-search.py -q "cancer immunotherapy" -d biomedicine --online-rank

# Year filter
python scripts/multi-search.py -q "styrene shape memory polymer" -d chemistry --year-from 2022 -t 20

# Google Scholar (one-time Playwright setup required)
python scripts/google-scholar.py --setup
python scripts/google-scholar.py --query "attention is all you need" --limit 15

# Chinese literature — CNKI via Playwright (one-time VPN setup required)
python scripts/cnki-playwright.py --setup --school scau
python scripts/cnki-playwright.py --query "大语言模型 代码生成" --limit 20

# Chinese literature — Wanfang API + browser URLs (Windows)
.\scripts\cnki-search.ps1 -Query "大语言模型 代码生成"

# Journal ranking (requires OneScholar API key)
python scripts/journal-rank.py -j "Nature" "Science" "Advanced Materials"
```

---

## Features

| Feature | Zero-config | With API key / setup |
|---------|------------|----------------------|
| English search | OpenAlex + CrossRef + PubMed + arXiv | + Semantic Scholar + Google Scholar (ai4scholar MCP) |
| Google Scholar | Browser URLs only | ai4scholar MCP (key) or Playwright (one-time setup) |
| Chinese search | Browser URLs (CNKI/Baidu/Weipu) | + CNKI headless (Playwright) + Wanfang API |
| Journal ranking | 300+ journal offline DB (built into multi-search) | + OneScholar live API (key) |
| PDF download | scansci-pdf (13+ sources) | + publisher access via CARSI / EZProxy / VPNSci |
| Citation | Manual workflow (all 7 styles) | — |

---

## Scripts

| Script | Platform | Description |
|--------|----------|-------------|
| `multi-search.py` | All | Multi-source search (OpenAlex/CrossRef/PubMed/arXiv), DOI dedup, journal ranking |
| `multi-search.ps1` | Windows | Same, PowerShell version |
| `journal-rank.py` | All | OneScholar API journal ranking (requires key) |
| `journal-rank.ps1` | Windows | Same, PowerShell version; supports ISSN lookup |
| `pdf-fetch.py` | All | PDF download chain: Unpaywall → OpenAlex → EuropePMC → Sci-Hub URL (DOI input) |
| `pdf-fetch.ps1` | Windows | Same, PowerShell version |
| `cnki-playwright.py` | All | CNKI search + PDF download via Playwright; ~100 built-in school VPN entries |
| `google-scholar.py` | All | Google Scholar via Playwright; headless after one-time setup |
| `cnki-search.ps1` | Windows | Wanfang API results + browser URLs for CNKI, Baidu Scholar, Weipu |
| `check-deps.ps1` | Windows | Dependency and config checker (12 checks) |
| `setup.ps1` | Windows | Interactive API key setup wizard |

---

## Requirements

- **Python 3.10+** — multi-search, journal-rank, pdf-fetch, cnki-playwright, google-scholar
- **Playwright + Chromium** — cnki-playwright.py, google-scholar.py
- **Node.js 18+** — ai4scholar MCP server (`npx -y @ai4scholar/mcp-server`)
- **uv** — scansci-pdf MCP server (`uvx scansci-pdf`)
- **Windows PowerShell 5.1+** — `.ps1` scripts (optional; Python scripts work cross-platform)

---

## Supported Sources

| Source | Scale | Cost |
|--------|-------|------|
| OpenAlex | 250M papers | Free |
| CrossRef | 150M papers | Free |
| PubMed | 36M papers | Free |
| arXiv | 2M+ papers | Free |
| Semantic Scholar | 214M papers | Free key |
| Google Scholar | — | MCP key or Playwright setup |
| CNKI (知网) | — | Institutional VPN setup |
| Wanfang (万方) | — | API key |
| Baidu Scholar / Weipu | — | Browser URL only |
| Elsevier Scopus | 78M papers | Institutional |
| Springer Nature OA | — | Free key |

---

## Platform Compatibility

| Feature | Claude Code | Claude Desktop | OpenCode | Codex | Hermes |
|---------|------------|----------------|----------|-------|--------|
| MCP tools | `mcp__server__tool` | same | auto-mapped | auto-mapped | generic names |
| Skill auto-load | ✅ | ✅ | ✅ | ✅ | ✅ |
| Python scripts | ✅ | ✅ | ✅ | ✅ | ✅ |
| PowerShell scripts | ✅ (Windows) | ✅ (Windows) | ✅ (Windows) | ✅ (Windows) | — |
