# 可选 API 参考

以下 API 均为可选增强。不配置任何 Key，Skill 仍可通过零配置路径（OpenAlex + CrossRef + PubMed + arXiv）正常工作。

---

## OneScholar API（期刊等级，推荐配置）

**功能：** JCR 分区、中科院分区（含升区信息）、影响因子（IF / IF5）、CiteScore、Nature Index、50+ 中国高校期刊认定等级（中华医学会期刊名单、HUST、SJTU 等）、JCAR 风险评估。

**注册：** `https://www.scigreat.com/s/app/?t=oneapi-info`
免费版：1,000 次/天，1 次/秒，每次最多 5 个期刊。

**调用格式：**
```http
POST https://api.scigreat.com/info/getrank
Authorization: Bearer <ONESCHOLAR_API_KEY>
Content-Type: application/json

[{"journal": ["Nature"]}, {"journal": ["Science"]}]
```

**推荐用法（脚本封装）：**
```bash
# 按期刊名（支持批量）
python scripts/journal-rank.py -j "Nature" "Science" "Advanced Materials"

# 按 ISSN
python scripts/journal-rank.py -i "0028-0836" "0036-8075"
```

```powershell
.\scripts\journal-rank.ps1 -Journal "Nature","Advanced Materials" -Quiet
.\scripts\journal-rank.ps1 -Issn "0028-0836"
```

脚本处理了批量（每批 ≤5）、30 天本地缓存、速率限制、以及 urllib/curl 双重回退。

> **注意：** `journal-rank.py` 和 `journal-rank.ps1` 在无 Key 时会直接报错退出。300+ 期刊的离线 DB 仅内置于 `multi-search.py` / `multi-search.ps1`（`--online-rank` 未启用时自动使用）。

---

## Semantic Scholar API（214M 篇论文，免费 Key）

**注册：** `https://www.semanticscholar.org/product/api`（免费，1–2 个工作日审批）

> 匿名模式实测几乎每次返回 429，强烈建议申请 Key。

**搜索端点：**
```
GET https://api.semanticscholar.org/graph/v1/paper/search
  ?query=styrene+polymer
  &limit=10
  &fields=title,year,citationCount,venue,abstract
x-api-key: <SEMANTIC_SCHOLAR_API_KEY>
```

**PowerShell：**
```powershell
$r = Invoke-RestMethod "https://api.semanticscholar.org/graph/v1/paper/search?query=styrene+polymer&limit=10&fields=title,year,citationCount,venue" `
    -Headers @{ "x-api-key" = $env:SEMANTIC_SCHOLAR_API_KEY }
$r.data
```

通常通过 ai4scholar MCP 使用（封装了 S2 + Google Scholar），直连仅作备选。

---

## Elsevier Scopus（7,800 万篇，需机构授权）

**注册：** `https://dev.elsevier.com/apikey/manage`（需机构购买 Scopus 订阅）

**搜索端点：**
```
GET https://api.elsevier.com/content/search/scopus
  ?query=TITLE-ABS-KEY(styrene+polymer)
  &count=10
X-ELS-APIKey: <ELSEVIER_API_KEY>
```

**PowerShell：**
```powershell
$r = Invoke-RestMethod "https://api.elsevier.com/content/search/scopus?query=TITLE-ABS-KEY(styrene+polymer)&count=10" `
    -Headers @{ "X-ELS-APIKey" = $env:ELSEVIER_API_KEY }
$r.'search-results'.'entry' | ForEach-Object { $_.'dc:title' }
```

---

## Springer Nature OA（免费 Key）

**注册：** `https://dev.springernature.com/`

**搜索端点：**
```
GET https://api.springernature.com/openaccess/json
  ?q=styrene+polymer
  &api_key=<SPRINGER_API_KEY>
  &p=10
```

覆盖 Springer / Nature 旗下 16,000+ 开放获取论文的全文元数据。

---

## Wanfang Data API（万方，结构化中文检索）

**注册：** `https://open.wanfangdata.com.cn/`

**快速调用：**
```powershell
.\scripts\cnki-search.ps1 -Query "大语言模型 代码生成" -Source wanfang -Limit 20
```

详见 `api-setup.md` Path H。

---

## Web of Science（付费机构授权）

**注册：** `https://developer.clarivate.com/apis/wos`（无免费版）

Gold-standard 引用指标，需机构购买 WoS 许可。Key 通过 `setup.ps1` 配置（`wos` 字段）。
