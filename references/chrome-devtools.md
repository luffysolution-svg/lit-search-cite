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
{
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-chrome-devtools"],
      "env": {
        "CDP_URL": "http://localhost:9222"
      }
    }
  }
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
1. 导航到 cnki.net（自动携带你的登录 cookie）
2. 填入搜索词，提取结果列表
3. 返回结构化元数据

### 场景 B — Wiley / 付费出版商 PDF 下载

当 `scansci_pdf_smart_download` 失败（非 OA，Sci-Hub 无法访问）时：

```
告诉 Claude："这篇 DOI 10.1002/adma.xxx scansci-pdf 下不了，用浏览器帮我下"
```

Claude 会：
1. 在 Chrome 中打开该 DOI 页面（机构 cookies 自动生效，Wiley 识别为校园用户）
2. 点击 PDF 下载按钮
3. 文件保存到浏览器默认下载目录

### 场景 C — 谷歌学术（无验证码）

Chrome 已有正常使用历史，不会被当作爬虫：

```python
# Claude 内部调用
navigate_page(url="https://scholar.google.com/scholar?q=large+language+model+survey")
evaluate_script("() => [...document.querySelectorAll('.gs_rt a')].map(a => ({title: a.innerText, href: a.href}))")
```

---

## Cookies 说明

| 问题 | 答案 |
|------|------|
| 需要手动导出 cookies 吗？ | **不需要**，Chrome 自动管理所有 cookies |
| 机构登录会过期吗？ | 会，和普通浏览器一样过期，但你日常使用时会自动续期 |
| 需要配置 WebVPN URL 吗？ | **不需要**，只要你的 Chrome 里 WebVPN 插件是开着的，Chrome DevTools MCP 就能用 |
| 能下载 CNKI PDF 吗？ | 能，前提是你的机构账号有下载权限 |

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

---

## 注意事项

- Chrome 必须在运行中，且以 `--remote-debugging-port=9222` 启动
- 同一时间只支持连接一个 Chrome 实例
- Wiley 的 Cloudflare 检测会在批量操作时触发，单篇文章 URL 直接访问通常正常
