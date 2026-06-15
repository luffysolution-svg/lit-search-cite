# Project Instructions for Claude

## 提交 & 发布规则

**在执行以下任何操作前，必须先向用户展示变更摘要并等待明确确认：**

- `git push`（包括 tag push）
- `npm publish` / `pypi upload`
- `gh release create`

展示格式：
1. 改了什么（文件列表 + 关键变更）
2. 拟提交的 commit message
3. 将推送到哪里

收到用户确认后再执行。唯一例外：用户在同一条消息中明确说"完成后推 master"等指令，可直接执行。

## 版本发布检查清单

每次版本变更必须在同一会话中完成以下全部步骤：

```
[ ] package.json version 已更新
[ ] CHANGELOG.md 已更新（版本号 + 日期 + 变更内容）
[ ] README.md 已更新（安装命令、平台表格、选项说明）
[ ] git commit + git tag + git push origin master + git push origin vX.Y.Z
[ ] npm publish
[ ] gh release create vX.Y.Z
[ ] 验证：npx <pkg>@latest 拉到正确版本号
```

## 编码规范

- Python 脚本开头加 win32 UTF-8 编码头（见 `docs/publishing-lessons.md` 第 7 节）
- PowerShell 脚本开头加 `[Console]::OutputEncoding = [System.Text.Encoding]::UTF8`
- 文件写入用 `-Encoding utf8`
- Node.js 路径用 `path.join(os.homedir(), ...)`，不硬编码分隔符

## 跨平台兼容

- PowerShell 脚本中禁止调用 `curl` / `grep` / `sed` / `awk`
- HTTP 请求：PowerShell 用 `Invoke-RestMethod`，Python 用 `requests`
- 路径：Python 用 `pathlib.Path`，PowerShell 用 `Join-Path`

## 安装命令规范

文档和示例中的 npx 命令统一写 `@latest`：

```bash
npx lit-search-cite@latest   # ✅
npx lit-search-cite           # ❌ 可能命中缓存
```
