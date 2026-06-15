# 安装指南

完整的一次性配置。完成后所有搜索和下载均可无头运行，无需打开浏览器。

---

## 第一步 — 安装系统依赖

| 组件 | 用途 | 安装命令（Windows） |
|------|------|-------------------|
| Node.js 18+ | ai4scholar MCP 运行时 | `winget install OpenJS.NodeJS` |
| Python 3.10+ | 所有 Python 脚本 | `winget install Python.Python.3.11` |
| Playwright + Chromium | CNKI、Google Scholar 浏览器引擎 | `pip install playwright && playwright install chromium` |
| uv | scansci-pdf MCP 运行时 | `winget install astral-sh.uv` 或 `pip install uv` |

**验证安装：**
```powershell
node --version          # 应显示 v18.x 或更高
python --version        # 应显示 3.10.x 或更高
python -c "from playwright.sync_api import sync_playwright; print('OK')"
uvx --version
```

---

## 第二步 — 配置 MCP 服务器

编辑 `%USERPROFILE%\.claude\mcp.json`（不存在则新建），加入以下内容：

```json
{
  "mcpServers": {
    "ai4scholar": {
      "command": "npx",
      "args": ["-y", "@ai4scholar/mcp-server"],
      "env": {
        "AI4SCHOLAR_API_KEY": "sk-user-你的密钥"
      }
    },
    "scansci-pdf": {
      "command": "uvx",
      "args": ["scansci-pdf"]
    }
  }
}
```

直接复制粘贴模板：`references/mcp-template.json`。

**重启 Claude Code** 后生效。

---

## 第三步 — API 密钥

```powershell
.\scripts\setup.ps1
```

交互式配置向导，按提示逐项输入。密钥保存到 `~/.lit-search-cite/config.json`，所有脚本自动读取。

| 密钥 | 用途 | 必要性 |
|------|------|--------|
| `ai4scholar` | Google Scholar + Semantic Scholar（2.14 亿篇）| 推荐 |
| `unpaywall_email` | OA PDF 发现（Unpaywall ToS 要求填写邮箱）| 推荐，任意邮箱 |
| `onescholar` | 在线期刊等级（IF / JCR / CAS）| 可选 |
| `semantic_scholar` | S2 API 直连备选 | 可选 |
| `wanfang` | 万方结构化中文检索 | 可选 |
| `elsevier` | Scopus 7800 万篇 | 机构授权 |
| `springer` | Springer OA 全文元数据 | 可选 |
| `wos` | Web of Science 引用指标 | 付费，可选 |

查看当前配置：`.\scripts\setup.ps1 -Show`

---

## 第四步 — Google Scholar Playwright（可选）

一次性浏览器配置，之后永久无头运行：
```bash
python scripts/google-scholar.py --setup
# 浏览器打开 → 解决 CAPTCHA（如出现）→ 在终端按 Enter
```

之后的搜索：
```bash
python scripts/google-scholar.py --query "attention mechanism" --limit 15 --since 2022
python scripts/google-scholar.py --status   # 查看 Cookie 有效期
```

Cookie 约 7 天过期，刷新：`python scripts/google-scholar.py --login-only`

---

## 第五步 — CNKI WebVPN（中文文献）

内置约 100 所中国高校 VPN 地址，一次配置，永久无头搜索：

```bash
# 用学校缩写自动检测 VPN 地址
python scripts/cnki-playwright.py --setup --school scau
python scripts/cnki-playwright.py --setup --school "清华大学"

# 不确定学校缩写时不带 --school，向导会提示手动输入 VPN 地址
python scripts/cnki-playwright.py --setup
```

浏览器打开 → 登录 VPN → 导航至知网页面 → 在终端按 Enter。

之后无头搜索：
```bash
python scripts/cnki-playwright.py --query "形状记忆 聚合物" --limit 20
```

Session 约 7 天过期，刷新：
```bash
python scripts/cnki-playwright.py --login-only --no-headless
```

---

## 第六步 — 出版商 PDF 访问（付费论文）

通过 scansci-pdf 的一次性浏览器登录，之后永久无头下载付费 PDF：

- **通用（ScienceDirect 等）：** 告诉 Claude "帮我配置 scansci-pdf 的 ScienceDirect cookie 访问"
- **国内高校 CARSI：** 告诉 Claude "帮我配置 scansci-pdf CARSI 登录"
- **图书馆 EZProxy：** 告诉 Claude "帮我配置 scansci-pdf EZProxy 登录"

Claude 会调用相应的 scansci-pdf MCP 工具打开浏览器，你登录一次后 cookie 保存至 `~/.scansci-pdf/`，之后所有下载无头进行。

> **注意：** 以上登录操作需要可见浏览器，不能由 AI 自动运行 — AI 会告诉你确切的命令，由你在终端执行。

---

## 第七步 — 验证

```powershell
.\scripts\check-deps.ps1
```

预期输出（12 项全通过）：`Status: READY — all critical components configured.`

---

## 最低可用配置

| 级别 | 需要配置 | 可用功能 |
|------|---------|---------|
| 零配置 | 无 | OpenAlex、CrossRef、PubMed、arXiv、OA PDF 下载 |
| 推荐 | 第二步 + 第三步 | + Google Scholar（MCP）、Semantic Scholar、期刊等级 |
| 完整英文 | + 第六步 | + 任意出版商付费 PDF |
| 完整中文 | + 第五步 | + CNKI 无头搜索 |
| 全功能 | 全部步骤 | + 万方 API 结构化结果 + Google Scholar Playwright |

---

## 配置文件

`~/.lit-search-cite/config.json`（仅本地存储，切勿分享）：

```json
{
  "vpn_url": "https://vpn.your-school.edu.cn",
  "cnki_vpn_base": "https://kns-cnki-net-s.vpn.your-school.edu.cn",
  "vpn_username": "",
  "api_keys": {
    "ai4scholar": "sk-user-...",
    "onescholar": "sk_...",
    "semantic_scholar": "s2k-...",
    "unpaywall_email": "you@email.com",
    "wanfang": "",
    "elsevier": "",
    "springer": "",
    "wos": ""
  }
}
```

> **给 AI 的提示：** 不要通过 shell 工具运行 `setup.ps1`、`cnki-playwright.py --setup/--login-only`、`google-scholar.py --setup/--login-only` 或任何 scansci-pdf 登录工具 —— 它们需要交互式终端和可见浏览器。告诉用户确切命令让其自己运行。
