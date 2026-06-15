# lit-search-cite

> 多源学术文献检索、期刊等级查询、自动引用标注、PDF 下载 —— AI 编程助手的学术 Skill

一键安装：

```bash
npx lit-search-cite
```

自动适配 Claude Code / Claude Desktop / OpenCode / Codex / Hermes。

---

## 功能

- **文献检索** — OpenAlex、CrossRef、PubMed、arXiv（零配置）；Semantic Scholar、Google Scholar（ai4scholar MCP）；CNKI（Chrome DevTools MCP，复用浏览器登录态）；万方（API Key）
- **期刊等级** — OneScholar 在线 API（IF / JCR / CAS / CiteScore）+ 300+ 期刊离线库（无需 Key）
- **PDF 下载** — scansci-pdf MCP（13+ 来源：Springer Direct / ElsevierAPI / OA 库 / Sci-Hub）；付费墙兜底：Chrome DevTools MCP（零配置，复用机构登录）
- **引用标注** — GB/T 7714 / APA / IEEE / MLA / Chicago / Nature / Vancouver
- **综述写作** — 多轮搜索 + 论文聚类 + 结构化草稿

## 快速开始

```bash
# 英文文献（零配置）
python scripts/multi-search.py -q "styrene shape memory polymer" -d chemistry

# 带在线期刊等级
python scripts/multi-search.py -q "transformer attention mechanism" -d cs --online-rank

# 年份过滤
python scripts/multi-search.py -q "cancer immunotherapy" -d biomedicine --year-from 2022 -t 20

# 期刊等级查询（需 OneScholar Key）
python scripts/journal-rank.py -j "Nature" "Science" "Advanced Materials"

# PDF 下载（需 scansci-pdf MCP）
# 告诉 Claude："下载 DOI 10.1038/s41586-021-03819-2 的 PDF"

# 中文文献（需 Chrome DevTools MCP，Chrome 中已登录知网）
# 告诉 Claude："帮我在知网搜索「大语言模型 代码生成」"
```

## 安装

```bash
npx lit-search-cite                           # 自动检测所有平台
npx lit-search-cite --claude                  # 仅 Claude Code / Claude Desktop
npx lit-search-cite --opencode                # 仅 OpenCode / Codex
npx lit-search-cite --target ~/my-skills      # 自定义路径
```

或手动复制到平台对应的 skills 目录：

| 平台 | 目录（全局） | 目录（项目级） |
|------|------------|--------------|
| Claude Code | `~/.claude/skills/lit-search-cite/` | `.claude/skills/lit-search-cite/` |
| OpenCode / Codex | `~/.config/opencode/skills/lit-search-cite/` | `.opencode/skills/lit-search-cite/` |
| 通用 Agent Skills | `~/.agents/skills/lit-search-cite/` | `.agents/skills/lit-search-cite/` |

## 脚本

| 脚本 | 平台 | 说明 |
|------|------|------|
| `multi-search.py` | 全平台 | 一键多源搜索（OpenAlex/CrossRef/PubMed/arXiv）+ DOI 去重 + 期刊等级 |
| `multi-search.ps1` | Windows | 同上，PowerShell 版 |
| `journal-rank.py` | 全平台 | OneScholar API 期刊等级查询（需 Key） |
| `journal-rank.ps1` | Windows | 同上，PowerShell 版，支持 ISSN 查询 |
| `pdf-fetch.py` | 全平台 | PDF 下载回退链（DOI 输入，Unpaywall → OpenAlex → EuropePMC） |
| `pdf-fetch.ps1` | Windows | 同上，PowerShell 版 |
| `cnki-search.ps1` | Windows | 万方 API + CNKI/百度学术/维普 浏览器 URL 生成 |
| `check-deps.ps1` | Windows | 依赖检查 |
| `setup.ps1` | Windows | API Key 配置向导 |

## 支持的文献源

| 数据源 | 规模 | 费用 |
|--------|------|------|
| OpenAlex | 2.5 亿篇 | 免费 |
| CrossRef | 1.5 亿篇 | 免费 |
| PubMed | 3,600 万篇 | 免费 |
| arXiv | 200 万+ 篇 | 免费 |
| Semantic Scholar | 2.14 亿篇 | 免费 Key |
| Google Scholar | — | ai4scholar MCP Key |
| CNKI / 知网 | — | Chrome DevTools MCP（浏览器登录态，零额外配置） |
| 万方 | — | API Key |
| 百度学术 / 维普 | — | 浏览器 URL |
| Elsevier Scopus | 7,800 万篇 | 机构授权 |
| Springer Nature OA | — | 免费 Key |

## MCP 配置

详见 `references/mcp-template.md`，支持三种配置级别：

| 级别 | MCP | 适用场景 |
|------|-----|---------|
| 最小 | scansci-pdf | 仅 OA PDF 下载 |
| 推荐 | ai4scholar + scansci-pdf | 全功能搜索 + 多源下载 |
| 完整 | + Chrome DevTools MCP | + 付费墙兜底（复用浏览器机构登录） |

## 兼容平台

Claude Code · Claude Desktop · OpenCode · Codex · Hermes

---

[English](AGENTS.md) · [Setup Guide](references/setup-guide.md) · [Chrome DevTools MCP](references/chrome-devtools.md)
