# 安装指南

完整的一次性配置。完成后所有搜索和下载均可无头运行，无需打开浏览器。

---

## 第一步 — 安装系统依赖

| 组件 | 用途 | 安装命令（Windows） |
|------|------|-------------------|
| Node.js 18+ | ai4scholar MCP 运行时 | `winget install OpenJS.NodeJS` |
| Python 3.10+ | 所有 Python 脚本 | `winget install Python.Python.3.11` |
| uv | scansci-pdf MCP 运行时 | `winget install astral-sh.uv` 或 `pip install uv` |

**验证安装：**
```powershell
node --version          # 应显示 v18.x 或更高
python --version        # 应显示 3.10.x 或更高
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

直接复制粘贴模板：`references/mcp-template.md`（含 OpenCLI 付费墙兜底说明）。

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

## 第四步 — 出版商 PDF 访问（付费论文）

通过 scansci-pdf 的一次性浏览器登录，之后永久无头下载付费 PDF：

- **通用（ScienceDirect 等）：** 告诉 Claude "帮我配置 scansci-pdf 的 ScienceDirect cookie 访问"
- **国内高校 CARSI：** 告诉 Claude "帮我配置 scansci-pdf CARSI 登录"
- **图书馆 EZProxy：** 告诉 Claude "帮我配置 scansci-pdf EZProxy 登录"

Claude 会调用相应的 scansci-pdf MCP 工具打开浏览器，你登录一次后 cookie 保存至 `~/.scansci-pdf/`，之后所有下载无头进行。

> **注意：** 以上登录操作需要可见浏览器，不能由 AI 自动运行 — AI 会告诉你确切的命令，由你在终端执行。

---

## 第五步（可选）— OpenCLI 浏览器（付费墙兜底 + CNKI 搜索）

当 scansci-pdf 所有通道失败时，OpenCLI 可直接通过你已登录的 Chrome 浏览器下载。**不需要配置 WebVPN URL、不需要导出 cookies、不需要 `--remote-debugging-port`**，通过扩展直接复用日常浏览器的登录状态。

**适用场景：** Wiley 非 OA 下载、未被 Sci-Hub 收录的新论文、知网机构搜索。

**安装（一次性）：**

```bash
# 1. 安装 CLI（需 Node.js >= 20）
npm install -g @jackwener/opencli

# 2. 安装浏览器扩展
# Chrome Web Store → 搜索 "OpenCLI" 或直接访问：
# https://chromewebstore.google.com/detail/opencli/ildkmabpimmkaediidaifkhjpohdnifk

# 3. 验证
opencli doctor   # 全绿即可使用
```

详见 `references/opencli.md`（含已验证的 CNKI / Wiley / Elsevier 操作命令）。

---

## 第六步 — 验证

```powershell
.\scripts\check-deps.ps1
```

预期输出：`Status: READY — all critical components configured.`

---

## 最低可用配置

| 级别 | 需要配置 | 可用功能 |
|------|---------|---------|
| 零配置 | 无 | OpenAlex、CrossRef、PubMed、arXiv、OA PDF 下载 |
| 推荐 | 第二步 + 第三步 | + Google Scholar（MCP）、Semantic Scholar、期刊等级 |
| 完整英文 | + 第四步 | + 任意出版商付费 PDF（无头） |
| 完整中文 + 付费墙兜底 | + 第五步 | + 知网机构搜索、Wiley 机构下载（OpenCLI） |

---

## 配置文件

`~/.lit-search-cite/config.json`（仅本地存储，切勿分享）：

```json
{
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

> **给 AI 的提示：** 不要通过 shell 工具运行 `setup.ps1` 或任何 scansci-pdf 登录工具 —— 它们需要交互式终端和可见浏览器。告诉用户确切命令让其自己运行。OpenCLI 命令（`opencli browser <session> open/fill/click/eval/wait`）可由 AI 通过 Bash 工具直接调用，无需用户干预。
