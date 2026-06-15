# 各数据源查询策略

## 通用原则

- 窄查询 → 精确结果；宽查询 → 多但噪声大
- 始终运行 2 种以上查询变体：精确概念 + 更宽泛的同义词
- 中文课题加中文翻译作为单独查询

---

## multi-search.py / multi-search.ps1（推荐起点）

`-d` 参数自动选择最佳数据源组合：

| Domain 值 | 激活的数据源 |
|-----------|------------|
| `cs` | OpenAlex + arXiv |
| `engineering` | OpenAlex + CrossRef |
| `biomedicine` | PubMed + OpenAlex + CrossRef |
| `biology` | PubMed + OpenAlex |
| `physics` | arXiv + OpenAlex + CrossRef |
| `chemistry` | OpenAlex + CrossRef + PubMed |
| `social` | OpenAlex + CrossRef |
| `humanities` | CrossRef |
| `general` | OpenAlex + CrossRef + PubMed |

```bash
# 手动指定数据源（跳过 domain 路由）
python scripts/multi-search.py -q "..." -s openalex,pubmed
```

---

## Google Scholar（ai4scholar MCP / google-scholar.py）

```
"exact phrase search"              # 引号精确匹配
allintitle: styrene shape memory   # 全部关键词出现在标题中
author:Vaswani attention           # 按作者检索
```

用 `--since` / `--until`（`google-scholar.py`）或 `year_from` / `year_to`（ai4scholar MCP 参数）过滤年份，比在查询字符串中写年份更可靠。

`google-scholar.py` 输出 JSON 到 stdout，Claude 可直接解析。

---

## Semantic Scholar（ai4scholar MCP / 直连 API）

自然语言查询效果好。年份过滤参数：
```
year = "2020-2024"   # 范围
year = "2020-"        # 2020 年至今
```

---

## PubMed（E-utilities / ai4scholar MCP）

| 字段限定符 | 示例 |
|-----------|------|
| `[Title/Abstract]` | `"styrene"[Title/Abstract]` |
| `[MeSH Terms]` | `"Polymers"[MeSH]` |
| `[Author]` | `Smith J[Author]` |
| `[Journal]` | `"Nature"[Journal]` |
| 日期范围 | `2020/01/01[PDAT]:2025/12/31[PDAT]` |
| 文献类型 | `"Review"[PT]`、`"Clinical Trial"[PT]` |

布尔运算符（必须大写）：
```
styrene AND polymer NOT "case report"[PT]
("shape memory" OR "stimuli responsive") AND styrene[Title/Abstract]
```

---

## arXiv（直连 API）

务必加分类限定，否则泛泛的关键词会匹配大量无关领域的论文：

```
# 好：限定到材料科学
search_query=all:styrene+polymer+AND+(cat:cond-mat.mtrl-sci)

# 差：无分类限定（"smart" 会匹配 smart grid / smart wheelchair 等）
search_query=all:smart+polymer
```

常用分类（`multi-search.py` 按 domain 自动添加）：

| 分类 | 用途 |
|------|------|
| `cond-mat.mtrl-sci` | 材料 / 化学 / 高分子 |
| `physics.chem-ph` | 化学物理 |
| `physics.app-ph` | 应用物理 |
| `cs.LG` / `cs.AI` / `cs.CL` | 机器学习 / AI / NLP |
| `cs.CV` | 计算机视觉 |
| `q-bio` | 生物学 |

---

## OpenAlex（免费，2.5 亿篇）— 精确关键词策略

OpenAlex 按引用数排序而非语义相关性。宽泛查询返回泛泛的高引用综述，而非你想要的专项论文。

```
# 差 — 返回 Nature Materials 通用综述
search=styrene smart polymer

# 好 — 具体材料 + 功能
search=styrene-butadiene-styrene strain sensor carbon nanotube

# 加年份 + 文献类型过滤
search=SEBS dielectric elastomer&filter=publication_year:>2020,primary_location.source.type:journal
```

**PowerShell 特别注意：** 必须加 `&select=` 排除 `abstract_inverted_index` 字段，否则 PS5.1 的 `ConvertFrom-Json` 报 JSON 解析错误：
```powershell
&select=id,doi,title,publication_year,cited_by_count,authorships,primary_location,open_access
```

---

## CrossRef（免费，1.5 亿篇）— 降噪过滤

始终组合类型 + 摘要过滤，否则可能混入会议摘要、补充材料和书籍章节：

```
filter=type:journal-article,has-abstract:true
```

CrossRef 相关性排序通常比 OpenAlex 更准确，适合"找某个具体结果"的场景。

---

## CNKI / 知网（Chrome DevTools MCP）

直接在你已登录的 Chrome 中操作知网，无需配置 WebVPN URL。知网布尔检索语法：

```
SU=形状记忆 AND SU=苯乙烯        # 主题（广）
TI=大语言模型                     # 仅标题（精确）
AU=张三 AND SU=量子计算           # 作者 + 主题
KY=强化学习                       # 关键词
```

- `SU=`（主题）= 标题 + 关键词 + 摘要，覆盖面广
- `TI=` 只匹配标题，结果少但精确

**使用方式：** 告诉 Claude "帮我在知网搜索「大语言模型」"，Claude 通过 Chrome DevTools MCP 在你的浏览器中操作，自动复用机构登录态。

无 Chrome DevTools MCP 时回退：`cnki-search.ps1`（生成浏览器 URL，需手动打开）。

---

## 多数据源组合策略

```bash
# 快速上手 — 一条命令，按领域选源，自动去重 + 等级标注
python scripts/multi-search.py -q "styrene smart material" -d chemistry

# 精细控制 — 手动并行搜索不同源再合并
python scripts/multi-search.py -q "..." -s openalex -n 20
python scripts/multi-search.py -q "..." -s pubmed -n 20
python scripts/multi-search.py -q "..." -s arxiv -n 20
```

---

## 查询扩展技巧

**结果太少：** 同义词 → 更广泛的上位概念 → 相关领域 → 引文链追踪（`get_semantic_citations` / `get_semantic_references`）。

**结果太多：** 加年份过滤 → 加领域限定词 → 最小引用数过滤（OpenAlex `cited_by_count:>50`）→ 切换到更精准的数据源。
