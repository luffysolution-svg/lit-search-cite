# Chrome DevTools MCP — 付费墙兜底方案

浏览器原生访问，零额外配置。复用你已登录的 Chrome 会话，无需 WebVPN URL、无需导出/导入 cookies。

---

## 工作原理

Chrome DevTools MCP 连接到**你正在运行的 Chrome 浏览器**，继承其全部状态：

- 所有网站的登录 cookies（知网、Wiley、Elsevier、万方……）
- 机构 IP 识别（学校网络/VPN 已开启时自动生效）
- 浏览器扩展（WebVPN 插件状态）

这与 Playwright 的根本区别：Playwright 每次启动空白浏览器，需要交互式配置。Chrome DevTools MCP 直接使用你日常浏览器的状态，**不需要任何额外操作**。

---

## 配置步骤（一次性）

### 1. 启动 Chrome 时开启远程调试

```powershell
# Windows — 关闭所有 Chrome 窗口后执行
Start-Process "chrome.exe" --args "--remote-debugging-port=9222 --user-data-dir=$env:LOCALAPPDATA\Google\Chrome\User Data"
```

> **提示：** 可以把这行加到 Windows 启动脚本里，这样每次开机自动开启调试端口。

### 2. 在 MCP 配置中添加 chrome-devtools

编辑 `%USERPROFILE%\.claude\mcp.json`，加入：

```json
"chrome-devtools": {
  "command": "cmd",
  "args": ["/c", "npx", "-y", "chrome-devtools-mcp@latest"]
}
```

重启 Claude Code 后生效。完整模板见 `references/mcp-template.md`。

---

## 使用场景

### 场景 A — 知网搜索（复用机构登录）

知网打开过一次并登录后，Claude 可直接操控：

```
告诉 Claude："帮我在知网搜索「大语言模型 代码生成」"
```

Claude 会：
1. 导航到 cnki.net（自动携带登录 cookie，机构身份自动生效）
2. 填入搜索词，按 Enter 触发检索
3. 提取结构化结果列表返回

**已验证（2026-06-15）：** 机构登录自动生效，无验证码，270 条结果正常返回。

### 场景 B — 谷歌学术（无验证码）

Chrome 已有正常使用历史，不会被识别为爬虫：

```
告诉 Claude："帮我在谷歌学术搜索 large language model code generation"
```

**已验证（2026-06-15）：** 全程无验证码，629 万条结果，PDF 链接正常提取。

### 场景 C — Wiley / 付费出版商 PDF 下载

当 `scansci_pdf_smart_download` 失败（非 OA，Sci-Hub 无法访问）时：

```
告诉 Claude："这篇 DOI 10.1002/adma.xxx scansci-pdf 下不了，用浏览器帮我下"
```

Claude 会：
1. 在 Chrome 中打开该 DOI 页面（机构 cookies 自动生效）
2. 点击 PDF 下载按钮
3. 文件保存到浏览器默认下载目录

---

## AI 调用参考（已验证的选择器）

### 知网搜索

```js
// 1. 导航
navigate_page({ type: "url", url: "https://www.cnki.net" })

// 2. 填入关键词（uid 从页面快照获取，通常为搜索框 textbox）
fill({ uid: "<搜索框uid>", value: "大语言模型 代码生成" })

// 3. 提交（注意：用 Enter，不是 Return）
press_key({ key: "Enter" })

// 4. 提取结果（已验证可用）
evaluate_script({
  function: `() => {
    const rows = document.querySelectorAll('.result-table-list tbody tr');
    return Array.from(rows).slice(0, 10).map(row => ({
      title:     row.querySelector('.name a')?.innerText?.trim(),
      authors:   row.querySelector('.author')?.innerText?.trim(),
      source:    row.querySelector('.source a')?.innerText?.trim(),
      date:      row.querySelector('.date')?.innerText?.trim(),
      citations: row.querySelector('.quote')?.innerText?.trim(),
    }));
  }`
})
```

**已验证字段：** `.result-table-list tbody tr` / `.name a` / `.author` / `.source a` / `.date` / `.quote`

### 谷歌学术搜索

```js
// 1. 直接带参数导航（最简单）
navigate_page({
  type: "url",
  url: "https://scholar.google.com/scholar?q=large+language+model&hl=zh-CN"
})

// 2. 提取结果（已验证可用）
evaluate_script({
  function: `() => {
    const items = document.querySelectorAll('.gs_r.gs_or.gs_scl');
    return Array.from(items).slice(0, 10).map(item => ({
      title:     item.querySelector('.gs_rt a')?.innerText?.trim(),
      authors:   item.querySelector('.gs_a')?.innerText?.trim(),
      snippet:   item.querySelector('.gs_rs')?.innerText?.trim().slice(0, 150),
      citations: item.querySelector('.gs_fl a[href*="cites"]')?.innerText?.trim(),
      pdf_link:  item.querySelector('.gs_or_ggsm a')?.href,
    }));
  }`
})
```

**已验证字段：** `.gs_r.gs_or.gs_scl` / `.gs_rt a` / `.gs_a` / `.gs_rs` / `.gs_fl a[href*="cites"]` / `.gs_or_ggsm a`

---

## 注意事项

| 问题 | 说明 |
|------|------|
| `press_key` 按键名 | 用 `Enter`，**不是** `Return`（会报错） |
| CNKI 首页搜索按钮 | `.btn-search` 选择器无效，统一用 `press_key Enter` 提交 |
| `wait_for` 内容过多 | 内容丰富的页面返回超量数据，改用截图 + 短延迟判断页面状态 |
| 需要手动导出 cookies 吗？ | **不需要**，Chrome 自动管理所有 cookies |
| 机构登录会过期吗？ | 会，和普通浏览器一样过期，日常使用时会自动续期 |
| 需要配置 WebVPN URL 吗？ | **不需要**，只要 Chrome 里 WebVPN 插件是开着的即可 |
| 能下载 CNKI PDF 吗？ | 能，前提是机构账号有下载权限 |
| Chrome 必须开着吗？ | 是，且需以 `--remote-debugging-port=9222` 启动 |
| 同时几个 Chrome 实例？ | 只支持一个 |
| Wiley Cloudflare 检测 | 批量操作会触发，单篇 URL 直接访问通常正常 |

---

## 与其他下载方案的优先级

```
scansci_pdf_smart_download         ← 优先（自动多源，最快）
  ├─ Springer Direct / ElsevierAPI ← 机构 IP 级别直接访问
  ├─ Unpaywall / CORE / OpenAlex   ← OA 开放库
  └─ Sci-Hub（如可达）
          ↓ 失败
Chrome DevTools MCP                ← 兜底（浏览器登录态，无额外配置）
```

只有当 scansci-pdf 所有通道都失败时，才回落到 Chrome DevTools MCP。
