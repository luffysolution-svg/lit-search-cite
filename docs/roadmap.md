# Roadmap — lit-search-cite

> 待实现的功能改进，按优先级排序。
> 完成一项后在对应条目打勾并记录版本号。

---

## P0 — 高价值、改动小（优先做）

### [ ] CAS + Springer：OpenCLI vs scansci-pdf 实测对比

**背景**：Wiley 和 Elsevier 已测完（见 `references/opencli.md`）。CAS（中国科学院文献情报中心，cas.cn）和 Springer Nature 是下两个最常用的付费来源，尚未实测 OpenCLI 的机构访问表现和文件下载成功率。

**计划测试项目**：
- **Springer**：`/content/pdf/<doi>.pdf` 是否触发直接文件下载（类 Wiley `pdfdirect` 模式）；机构 token 是否从 cookies 自动生效
- **CAS（中科院期刊）**：cas.cn / webofscience 机构入口识别；全文访问 + PDF 下载路径
- **scansci-pdf Springer Direct 通道**：与 OpenCLI 实测速度和成功率对比
- 更新 `references/opencli.md` 的优先级表

**预计工作量**：小（测试 + 文档更新，无代码改动）

---

### [ ] BibTeX / RIS 导出 + Zotero 推送

**背景**：搜索完只输出格式化文本，研究者实际需要把引用导入 Zotero / Endnote / Obsidian。`scansci_pdf_zotero_push` MCP 工具已在系统内，基础设施已就位。

**实现思路**：
- 所有搜索结果支持"导出为 .bib 文件"选项（新增 Mode 6 或作为 Mode 1 的后续步骤）
- `scansci_pdf_smart_download` 已返回 BibTeX，把这个能力推广到全部搜索结果
- 调用 `scansci_pdf_zotero_push` 直接推送到 Zotero 本地库

**预计工作量**：小（主要是 SKILL.md 补充说明，MCP 工具已有）

---

### [ ] 撤稿检测（Retraction Check）

**背景**：引用被撤稿论文是严重学术风险，现在完全无提示。

**实现思路**：
- 搜索结果展示时，对每篇论文调用 Crossref `/works/{doi}` 接口检查 `update-policy` 或 `relation.is-retracted-by` 字段
- 如检测到撤稿，在输出中标注 `⚠️ RETRACTED`，并附撤稿原因链接
- Crossref API 免费，无需额外 Key

**预计工作量**：中（需要在 multi-search.py 里加一个检查步骤）

---

## P1 — 中等价值，有一定工作量

### [ ] 预印本 → 正式发表版本匹配

**背景**：用户拿到 arXiv 链接时，应自动查有没有对应的正式 DOI 版本，避免引用预印本。

**实现思路**：
- 通过 Semantic Scholar `externalIds` 字段：`GET /paper/arXiv:{id}` 返回 `externalIds.DOI`
- 如有正式版，在输出中提示"已发表版本：DOI xxx"并优先展示正式版信息

**预计工作量**：小（单次 API 调用，逻辑简单）

---

### [ ] 批量 DOI 处理

**背景**：研究生整理文献时，常需要处理一个列表（从 PDF 参考文献提取的多个 DOI）。现在每次只能处理一篇。

**实现思路**：
- 支持用户粘贴多行 DOI 或标题列表
- 批量调用 `scansci_pdf_smart_download` 或批量生成引用格式
- 输出合并的 .bib 文件或引用列表

**预计工作量**：中（循环逻辑 + 进度提示）

---

### [ ] 多语言查询自动扩展

**背景**：中英文是完全分开的两条搜索路径，但很多领域核心文献中英都有。

**实现思路**：
- 中文查询时，自动用 AI 生成对应英文关键词组，两路并行搜索
- 英文查询时，若用户是中文研究方向，补充中文关键词搜 CNKI
- 结果合并去重后展示

**预计工作量**：中（需要 AI 辅助翻译关键词 + 去重逻辑）

---

### [ ] 研究空白识别（Research Gap Detection）

**背景**：综述写完后自动分析"哪些角度很少有人研究"，是目前 AI 助手 skill 里基本没人做的差异化功能。

**实现思路**：
- 基于搜索结果的关键词频率 + citation 分布，识别高引用但研究相对稀少的交叉领域
- 分析近 3 年论文数量趋势，标记"新兴方向"（论文数量快速增长但绝对量仍少）
- 作为 Mode 3 综述的可选后续步骤输出

**预计工作量**：大（需要设计分析逻辑，结果质量依赖搜索覆盖度）

---

## P2 — 锦上添花（用户反馈驱动）

- [ ] **引用速度分析**：不只看总引用数，看近 1-3 年的引用增长趋势（识别"正在爆发"的论文）
- [ ] **会议等级扩展**：在 CCF 基础上补充 CORE / ERA ranking（覆盖更多非 CS 领域）
- [ ] **系统综述 / PRISMA 支持**：为医学/公卫方向提供 PRISMA 流程图模板和 PICO 框架搜索
- [ ] **摘要自动翻译**：英文摘要一键翻译为中文（调用现有 AI 能力，无需额外 API）
- [ ] **作者主页聚合**：给出作者在 Google Scholar / ORCID / Semantic Scholar 的主页链接

---

## 已完成

| 版本 | 功能 |
|------|------|
| v1.0.0 | 基础文献搜索（OpenAlex / CrossRef / PubMed / arXiv） |
| v1.0.11 | MCP-first 工作流（ai4scholar + scansci-pdf 为主路径） |
| v1.0.19 | 移除 Playwright / VPN；改用 Chrome DevTools MCP |
| v1.0.21 | journal-rank 离线兜底 + 多期刊并行查询 |
| v1.0.22 | 安装器 allowlist；新增 Codex 平台；安装前清空旧目录 |
| — | 新增 `references/opencli.md`；将 SKILL.md / AGENTS.md 的 Chrome DevTools MCP 替换为 OpenCLI browser；Wiley/Elsevier/CNKI 实测验证（2026-06-15）|
