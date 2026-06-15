# lit-search-cite

> 多源学术文献检索、期刊等级查询、自动引用标注、PDF 下载 —— AI 编程助手的学术 Skill

一键安装：

```bash
npx lit-search-cite
```

自动适配 Claude Code / OpenCode / Codex / Hermes / Claude Desktop。

---

## 功能

- **文献检索** — OpenAlex、CrossRef、PubMed、arXiv、Semantic Scholar、Google Scholar、CNKI、万方
- **期刊等级** — OneScholar 在线 API + 300+ 期刊离线库（CAS/JCR/CCF/IF）
- **PDF 下载** — scansci-pdf（13+ 来源）+ pdf-fetch 回退链
- **引用标注** — GB/T 7714 / APA / IEEE / MLA / Chicago / Nature / Vancouver
- **综述写作** — 多轮搜索 + 论文聚类 + 结构化草稿

## 快速开始

```bash
# 英文文献（零配置）
python scripts/multi-search.py -q "styrene shape memory polymer" -d chemistry

# 带期刊等级
python scripts/multi-search.py -q "transformer attention mechanism" -d cs --online-rank

# 中文文献（需一次性 VPN 配置）
python scripts/cnki-playwright.py --setup --school scau
python scripts/cnki-playwright.py --query "大语言模型 代码生成" --limit 20

# 期刊等级查询
python scripts/journal-rank.py -j "Nature" "Science" "Advanced Materials"
```

## 安装

```bash
npx lit-search-cite                           # 自动检测所有平台
npx lit-search-cite --claude                  # 仅 Claude Code
npx lit-search-cite --opencode                # 仅 OpenCode / Codex
npx lit-search-cite --target ~/my-skills      # 自定义路径
```

或手动复制：

```bash
cp -r lit-search-cite ~/.claude/skills/       # Claude Code
cp -r lit-search-cite ~/.config/opencode/skills/  # OpenCode
cp -r lit-search-cite ~/.agents/skills/       # 通用
```

> npx 安装后提示 "could not determine executable" 可忽略 —— skill 已自动安装到位。

## 支持的文献源

| 数据源 | 规模 | 费用 |
|--------|------|------|
| OpenAlex | 2.5 亿篇 | 免费 |
| CrossRef | 1.5 亿篇 | 免费 |
| PubMed | 3600 万篇 | 免费 |
| arXiv | 200 万篇 | 免费 |
| Semantic Scholar | 2.14 亿篇 | 免费 Key |
| Google Scholar | — | MCP Key 或浏览器 |
| CNKI / 万方 / 维普 | — | VPN 配置 |
| Elsevier Scopus | 7800 万篇 | 机构授权 |
| Springer Nature | — | 免费 Key |

## 兼容平台

Claude Code · Claude Desktop · OpenCode · Codex · Hermes

---

[English](AGENTS.md) · [Changelog](CHANGELOG.md)
