# API 配置指南

各搜索和下载路径的 API 端点与调用示例。所有 PowerShell 示例在 Windows 上经过验证。

---

## 速查表 — 各路径所需配置

| 路径 | 数据源 | 需要 Key？ | 最适合 |
|------|--------|-----------|--------|
| A1 | ai4scholar MCP（Google Scholar + S2 + PubMed） | `AI4SCHOLAR_API_KEY` | 多源，最快，推荐 |
| A2 | ai4scholar REST API（Semantic Scholar） | `AI4SCHOLAR_API_KEY` | 无 MCP 时的 REST 备选 |
| B | Semantic Scholar 直连 | `SEMANTIC_SCHOLAR_API_KEY` | S2 直连备选 |
| C | PubMed E-utilities | 免费，无需 Key | 生物医学 |
| D | arXiv API | 免费，无需 Key | CS / 物理 / 数学 |
| E | scansci-pdf MCP | 免费，无需 Key | PDF 下载 |
| F | OpenAlex | 免费，无需 Key | 通用（2.5 亿篇） |
| G | CrossRef | 免费，无需 Key | DOI 注册论文 |
| H | Wanfang Data API | `WANFANG_API_KEY` | 万方中文结构化检索 |
| I | `multi-search.py` / `multi-search.ps1` | 免费（C+D+F+G 组合） | 一键多源零配置 |

---

## Path A1/A2 — ai4scholar（Google Scholar + Semantic Scholar + PubMed）

一个 Key，多个数据库。MCP 模式（A1）用于 Claude 工具调用；REST 模式（A2）用于直接 HTTP。

获取 Key：`https://ai4scholar.net` → Dashboard → Open Platform → Create Key

### REST API（Path A2，不依赖 MCP）

```
GET https://ai4scholar.net/graph/v1/paper/search
  ?query=<关键词>
  &limit=10
  &fields=paperId,title,year,citationCount,authors,abstract,venue
Authorization: Bearer <AI4SCHOLAR_API_KEY>
```

**PowerShell：**
```powershell
$headers = @{ "Authorization" = "Bearer $env:AI4SCHOLAR_API_KEY" }
$r = Invoke-RestMethod "https://ai4scholar.net/graph/v1/paper/search?query=styrene+polymer&limit=10&fields=paperId,title,year,citationCount,venue" -Headers $headers
$r.data  # papers array
```

**Python：**
```python
import urllib.request, json, os
headers = {"Authorization": f"Bearer {os.environ['AI4SCHOLAR_API_KEY']}"}
req = urllib.request.Request(
    "https://ai4scholar.net/graph/v1/paper/search?query=styrene+polymer&limit=10",
    headers=headers
)
data = json.loads(urllib.request.urlopen(req).read())
```

其他端点：`/paper/{id}/citations`、`/paper/{id}/references`、`/author/search`。

---

## Path B — Semantic Scholar 直连 API

免费 Key（1–2 个工作日审批）：`https://www.semanticscholar.org/product/api`

> 匿名模式理论上支持，实测几乎每次返回 429，必须申请 Key。

```
GET https://api.semanticscholar.org/graph/v1/paper/search
  ?query=<关键词>
  &limit=10
  &fields=title,year,citationCount,venue
x-api-key: <SEMANTIC_SCHOLAR_API_KEY>
```

**PowerShell：**
```powershell
$r = Invoke-RestMethod "https://api.semanticscholar.org/graph/v1/paper/search?query=styrene+block+copolymer&limit=10&fields=title,year,citationCount,venue" `
    -Headers @{ "x-api-key" = $env:SEMANTIC_SCHOLAR_API_KEY }
$r.data
```

---

## Path C — PubMed E-utilities（免费）

两步：搜索获取 ID → 批量获取摘要。无需 Key。

```powershell
# 1. 搜索（返回 PMID 列表）
$s = Invoke-RestMethod "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=styrene+smart+material&retmax=10&retmode=json&sort=relevance"
$ids = $s.esearchresult.idlist -join ","

# 2. 获取摘要
$sum = Invoke-RestMethod "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=$ids&retmode=json"
$sum.result.$($s.esearchresult.idlist[0]).title
```

MeSH 字段限定符：`[Title/Abstract]`、`[MeSH Terms]`、`[Author]`、`[Journal]`。
完整查询语法见 `search-strategies.md`。

---

## Path D — arXiv API（免费）

返回 Atom XML。务必加分类过滤，否则泛泛的关键词（如 "smart"）会匹配大量无关论文。

```
GET https://export.arxiv.org/api/query
  ?search_query=all:styrene+polymer+AND+(cat:cond-mat.mtrl-sci)
  &max_results=10
  &sortBy=relevance
```

**PowerShell：**
```powershell
$r = Invoke-WebRequest "https://export.arxiv.org/api/query?search_query=all:styrene+polymer+AND+(cat:cond-mat.mtrl-sci)&max_results=10&sortBy=relevance" -UseBasicParsing
# 解析标题：
[regex]::Matches($r.Content, '<title>(.*?)</title>', 'Singleline') | Select-Object -Skip 1 | ForEach-Object { $_.Groups[1].Value }
```

| arXiv 分类 | 用途 |
|-----------|------|
| `cond-mat.mtrl-sci` | 材料 / 化学 / 高分子 |
| `physics.chem-ph` | 化学物理 |
| `cs.LG` / `cs.AI` / `cs.CL` | 机器学习 / AI / NLP |
| `cs.CV` | 计算机视觉 |
| `q-bio` | 生物学 |
| `physics.app-ph` | 应用物理 |

---

## Path F — OpenAlex（免费，2.5 亿篇）

无需 Key。按引用数排序。用精确关键词效果更好。

```
GET https://api.openalex.org/works
  ?search=<关键词>
  &per-page=10
  &sort=cited_by_count:desc
  &select=id,doi,title,publication_year,cited_by_count,authorships,primary_location,open_access
```

**PowerShell（PS5.1 必须指定 `select=` 排除 `abstract_inverted_index`，否则 `ConvertFrom-Json` 报错）：**
```powershell
$q = [uri]::EscapeDataString("styrene-butadiene-styrene strain sensor")
$r = Invoke-RestMethod "https://api.openalex.org/works?search=$q&per-page=10&sort=cited_by_count:desc&select=id,doi,title,publication_year,cited_by_count,authorships,primary_location,open_access"
$r.results | ForEach-Object { "$($_.title) ($($_.publication_year))" }
```

年份过滤：`&filter=publication_year:>2022`
类型过滤：`&filter=primary_location.source.type:journal`

---

## Path G — CrossRef（免费，1.5 亿篇）

相关性排序比 OpenAlex 好。始终组合 `type:journal-article,has-abstract:true` 过滤噪声。

```
GET https://api.crossref.org/works
  ?query=<关键词>
  &rows=10
  &sort=relevance
  &filter=type:journal-article,has-abstract:true
```

**PowerShell：**
```powershell
$q = [uri]::EscapeDataString("styrene block copolymer self-healing")
$r = Invoke-RestMethod "https://api.crossref.org/works?query=$q&rows=10&sort=relevance&filter=type:journal-article,has-abstract:true"
$r.message.items | ForEach-Object { "$($_.title[0]) — DOI: $($_.DOI)" }
```

---

## Path H — Wanfang Data API（万方，需 Key）

注册：`https://open.wanfangdata.com.cn/`

```
GET https://openapiquery.wanfangdata.com.cn/periodical/search
  ?apikey=<WANFANG_API_KEY>
  &query=<关键词>
  &pageSize=10
  &pageNum=1
  &lang=zh
```

**PowerShell（通过 `cnki-search.ps1` 封装，推荐）：**
```powershell
.\scripts\cnki-search.ps1 -Query "大语言模型 代码生成" -Source wanfang -Limit 20
```

**直接调用：**
```powershell
$q = [uri]::EscapeDataString("大语言模型")
$r = Invoke-RestMethod "https://openapiquery.wanfangdata.com.cn/periodical/search?apikey=$env:WANFANG_API_KEY&query=$q&pageSize=10&pageNum=1&lang=zh"
$r.Records | ForEach-Object { "$($_.Title) — $($_.PeriodicalName) ($($_.Year))" }
```

---

## Path I — multi-search.py / multi-search.ps1（一条命令，全部免费 API）

封装 Path C/D/F/G，自动去重、期刊等级标注、格式化输出。

```bash
# Python（全平台）
python scripts/multi-search.py -q "styrene smart polymer" -d chemistry -t 20
python scripts/multi-search.py -q "..." --online-rank           # + OneScholar 在线等级
python scripts/multi-search.py -q "..." --year-from 2022 --year-to 2025
python scripts/multi-search.py -q "..." -s openalex,pubmed      # 手动指定数据源
python scripts/multi-search.py -q "..." --json                  # JSON 输出
```

```powershell
# PowerShell（Windows）
.\scripts\multi-search.ps1 -Query "..." -Domain biomedicine -YearFrom 2022 -OnlineRank
.\scripts\multi-search.ps1 -Query "..." -Sources "openalex,crossref" -TotalLimit 50
```

---

## 期刊等级 — OneScholar API

```
POST https://api.scigreat.com/info/getrank
Authorization: Bearer <ONESCHOLAR_API_KEY>
Content-Type: application/json

[{"journal": ["Nature"]}, {"journal": ["Science"]}]
```

免费：1,000 次/天，1 次/秒，每次最多 5 个期刊。推荐使用脚本封装：

```bash
python scripts/journal-rank.py -j "Nature" "Adv. Mater." "JACS"
python scripts/journal-rank.py -i "0028-0836" "0036-8075"   # 按 ISSN 查询
```

```powershell
.\scripts\journal-rank.ps1 -Journal "Nature","Science"
.\scripts\journal-rank.ps1 -Issn "0028-0836" -Quiet
```

脚本处理了批量查询（每批 ≤5）、30 天本地缓存、错误处理。

---

## PDF 下载

**主方案（scansci-pdf MCP，零配置）：**
```
# MCP 工具调用（Claude 内）：
scansci_pdf_smart_download(identifier="10.xxxx/..." 或 "arXiv:2401.12345")
```

**备选（无 MCP，仅支持 DOI）：**
```bash
python scripts/pdf-fetch.py --doi "10.xxxx/..." --output ./Papers
```
```powershell
.\scripts\pdf-fetch.ps1 -DOI "10.xxxx/..." -OutputPath ".\Papers"
```

回退链：Unpaywall → OpenAlex → EuropePMC → Sci-Hub URL（仅生成链接，需在浏览器打开）。

付费论文（优先级顺序）：
1. `scansci_pdf_smart_download` — 自动尝试 Springer Direct / ElsevierAPI / Sci-Hub / OA 库
2. 仍失败 → Chrome DevTools MCP — 在已登录的 Chrome 中直接下载（零配置，复用机构 cookies）
3. 一次性浏览器登录（`scansci_pdf_carsi_login` / `ezproxy_login`）→ Cookie 保存至 `~/.scansci-pdf/` → 之后永久无头下载

---

## CNKI / 知网（中文）

无公开 REST API。通过 Chrome DevTools MCP 在你已登录的浏览器中访问：

```
告诉 Claude："帮我在知网搜索「形状记忆 聚合物」"
```

Claude 通过 Chrome DevTools MCP 自动操作知网，复用你浏览器中的机构登录状态，无需配置 VPN URL。详见 `references/chrome-devtools.md`。

无 Chrome DevTools MCP 时，生成浏览器 URL（需手动打开）：
```powershell
.\scripts\cnki-search.ps1 -Query "形状记忆 聚合物"
```

万方 API（结构化中文结果）：Path H 上方。

---

## 配置文件

`~/.lit-search-cite/config.json`（由 `setup.ps1` 创建和管理）：

```json
{
  "vpn_url": "https://vpn.your-school.edu.cn",
  "cnki_vpn_base": "https://kns-cnki-net-s.vpn.your-school.edu.cn",
  "vpn_username": "",
  "api_keys": {
    "ai4scholar": "sk-user-...",
    "semantic_scholar": "s2k-...",
    "onescholar": "sk_...",
    "unpaywall_email": "you@email.com",
    "wanfang": "",
    "elsevier": "",
    "springer": "",
    "wos": ""
  }
}
```

所有 Python 和 PowerShell 脚本优先读取此文件，环境变量作为回退。
