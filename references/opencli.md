# OpenCLI 浏览器自动化 — 付费墙兜底 + CNKI 搜索

OpenCLI 通过**浏览器扩展**连接正在运行的 Chrome，继承其全部登录状态和机构 cookies。  
与 Chrome DevTools MCP 的根本区别：**无需** `--remote-debugging-port=9222`，正常启动 Chrome 即可使用。

---

## 安装与配置（一次性）

### 第一步 — 安装 CLI

需要 Node.js >= 20：

```bash
node --version   # 确认 >= 20，否则先升级
npm install -g @jackwener/opencli
```

### 第二步 — 安装浏览器扩展

**推荐方式（Chrome 应用商店）：**  
打开 [Chrome Web Store — OpenCLI](https://chromewebstore.google.com/detail/opencli/ildkmabpimmkaediidaifkhjpohdnifk) 点击"添加到 Chrome"。

**手动方式（离线或无法访问商店时）：**
1. 从 [GitHub Releases](https://github.com/jackwener/opencli/releases) 下载最新 `opencli-extension-v{version}.zip`
2. 解压后打开 `chrome://extensions`
3. 开启右上角**开发者模式**
4. 点击"加载已解压的扩展程序"，选择解压目录

### 第三步 — 验证

```bash
opencli doctor
```

输出全绿（Daemon running + Extension connected）即可使用。Daemon 自动在端口 19825 启动，无需手动管理。

**常见问题：**
- `Extension not connected`：扩展未安装，或安装后未刷新页面
- `attach failed: chrome-extension://...`：1Password / 其他扩展占用了 CDP 端口，临时禁用后重试
- `Daemon not running`：运行任意 `opencli browser` 命令会自动拉起 Daemon

### 可选：环境变量

| 变量 | 默认值 | 用途 |
|------|--------|------|
| `OPENCLI_DAEMON_PORT` | `19825` | Daemon 端口（多实例时修改） |
| `OPENCLI_WINDOW` | 命令默认 | `foreground` 或 `background` 控制窗口模式 |
| `OPENCLI_BROWSER_CONNECT_TIMEOUT` | `30` | 浏览器连接超时（秒） |
| `OPENCLI_BROWSER_COMMAND_TIMEOUT` | `60` | 单条命令超时（秒） |
| `OPENCLI_VERBOSE` | `false` | 详细日志（或 `-v` flag） |

---

## 前置条件（每次使用前确认）

```bash
opencli doctor
```

输出全绿后才能使用。

---

## 场景一 — 知网搜索（已验证 2026-06-15）

机构登录（华南农业大学）自动生效，270 条以上结果正常返回，无验证码。

```bash
# 1. 打开首页并等待搜索框
opencli browser cnki open "https://www.cnki.net"
opencli browser cnki wait selector "#txt_SearchText" --timeout 8000

# 2. 填入关键词（用 fill，不用 type；textarea 会精确写入）
opencli browser cnki fill "#txt_SearchText" "大语言模型 代码生成"

# 3. 找到检索按钮并点击（按钮是 <div class="search-btn">，不是 <button>）
opencli browser cnki find --css ".search-btn"   # 记下 ref 编号
opencli browser cnki click <ref>

# 4. 等待结果加载
opencli browser cnki wait selector ".result-table-list" --timeout 12000

# 5. 提取前 10 条结果
opencli browser cnki eval "(() => {
  const rows = document.querySelectorAll('.result-table-list tbody tr');
  return Array.from(rows).slice(0, 10).map(row => ({
    title:     row.querySelector('.name a')?.innerText?.trim(),
    authors:   row.querySelector('.author')?.innerText?.trim(),
    source:    row.querySelector('.source a')?.innerText?.trim(),
    date:      row.querySelector('.date')?.innerText?.trim(),
    citations: row.querySelector('.quote')?.innerText?.trim(),
  }));
})()"

# 6. 释放 session
opencli browser cnki close
```

**关键坑：**
- 搜索框是 `<textarea id="txt_SearchText">`，`find --css "input[type=text]"` 查不到
- `.btn-search` 选择器无效；实际按钮是 `.search-btn`（`<div>`，非 `<button>`）
- 不能直接 URL 导航到搜索结果页（会返回"暂无数据"），必须从首页走搜索流程

---

## 场景二 — Wiley 付费墙论文下载（已验证 2026-06-15）

机构识别显示 `Access By South China Agricultural University`，非 OA 论文的 PDF 链接解锁，无购买按钮。

```bash
# 一行命令：导航到 pdfdirect URL → Chrome 自动触发文件下载 → 捕获
opencli browser wiley open "https://onlinelibrary.wiley.com/doi/pdfdirect/<doi>"
opencli browser wiley wait download --timeout 30000
opencli browser wiley close
```

**实测结果：** `New Phytologist - 2023 - ...SliP4.pdf`，**6,271,607 字节，真实 PDF**（DOI: 10.1111/nph.18987）

**关键：** 必须用 `/doi/pdfdirect/<doi>` URL，而非 `/doi/epdf/<doi>`（epdf 是在线阅读器，不触发文件下载）。

---

## 场景三 — Elsevier/ScienceDirect 机构访问（已验证 2026-06-15）

机构识别正常（`Brought to you by: South China Agricultural University`），全文可读，但**文件下载被 session fingerprint 拦截**。

### 访问全文（正确 URL）

```bash
# 必须用 /pii/ 路径，不能用 /abs/pii/（摘要页只有 Purchase PDF）
opencli browser elsevier open "https://www.sciencedirect.com/science/article/pii/<PII>"
opencli browser elsevier wait selector "a[href*='pdfft']" --timeout 8000
# → 显示 "View PDF" 按钮 + "Brought to you by: South China Agricultural University"
```

### 为什么文件下载失败

Elsevier 的 `pdfft` URL 只对浏览器 navigation 请求返回 S3 跳转，S3 签名 URL 绑定了浏览器的 session fingerprint（`ua=` + `tsoh=` + `rh=` 参数），满足以下任一条件时均被重定向回主页：
- 通过 JS `fetch()` 请求（CORS 跨域）
- 通过 `<a download>` 属性（不跟 server-side 重定向）
- 通过 PowerShell `Invoke-WebRequest`（UA/Referer 不匹配）

### 替代方案

Elsevier 论文优先走 `scansci_pdf_smart_download`（ElsevierAPI 通道已验证有效，见 chrome-devtools.md 优先级表）。OpenCLI 仅用于阅读全文和提取结构化数据。

---

## 与 Chrome DevTools MCP 的对比

| 维度 | Chrome DevTools MCP | OpenCLI |
|------|--------------------|---------| 
| Chrome 启动要求 | 需要 `--remote-debugging-port=9222` | 普通启动，通过扩展连接 |
| 配置成本 | 需修改 Chrome 快捷方式 + 加 mcp.json 条目 | 安装扩展即可 |
| CNKI 搜索 | ✅ 已验证 | ✅ 已验证 |
| Wiley 下载 | ✅ 点击下载按钮 | ✅ `pdfdirect` URL，自动捕获 |
| Elsevier 访问 | ✅ 全文 + 可点击 View PDF | ✅ 全文，下载受 fingerprint 拦截 |
| Elsevier 文件下载 | ✅（依赖 navigate_page 打开 PDF 页） | ⚠️ 需 scansci ElsevierAPI 通道兜底 |
| 调用方式 | MCP 工具调用（在 Claude 里直接用） | Bash 命令行（通过 Bash 工具） |

---

## 已知限制

| 限制 | 说明 |
|------|------|
| PDF viewer 无 DOM | Chrome 内置 PDF 查看器无可操作 DOM，`state --source ax` 返回 0 交互元素 |
| Elsevier 下载 | S3 签名 URL 5 分钟有效期 + session fingerprint，外部工具无法复现 |
| wait download 是全局监听 | `wait download` 监听 Chrome 全局下载队列，与 session 无关——可能捕获到其他 session 的下载 |
| CNKI 不能 URL 直跳 | 直接导航到搜索结果 URL 返回"暂无数据"，必须从首页触发搜索流程 |

---

## 与 scansci-pdf 的优先级

```
scansci_pdf_smart_download             ← 首选（无需浏览器交互，自动多源）
  ├─ ElsevierAPI                        ← Elsevier 机构访问（已验证）
  ├─ Springer Direct                    ← 待测试
  ├─ OA 开放库 / Sci-Hub
  └─ CARSI/EZProxy/VPNSci
           ↓ 失败
OpenCLI browser                        ← 兜底（复用浏览器登录态）
  ├─ Wiley:     /doi/pdfdirect/<doi> → wait download    ✅ 完整替代
  ├─ CNKI:      fill + click + eval 提取               ✅ 完整替代
  └─ Elsevier:  全文阅读 + 数据提取可用，文件下载回退到 scansci  ⚠️ 部分替代
```

> **CAS（中科院文献情报中心）和 Springer 的测试计划**：见 `docs/roadmap.md`。
