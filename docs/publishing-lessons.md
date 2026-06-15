# Skill 跨平台发布经验

> 来源：lit-search-cite v1.0.22 发布过程（2026-06-15）
> 适用于所有需要跨平台发布的 AI Skill / Plugin 项目

---

## 1. 安装器用 allowlist，不用 blocklist

```js
const ROOT_ALLOWLIST = new Set(['SKILL.md', 'AGENTS.md', 'scripts', 'references']);

function copyDir(src, dest, root) {
  fs.mkdirSync(dest, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    if (root && !ROOT_ALLOWLIST.has(entry.name)) continue; // ← allowlist 过滤
    const srcPath  = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDir(srcPath, destPath, false);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}
```

**为什么**：blocklist（只排除 `node_modules`、`.git`）会持续泄漏新增的开发文件。allowlist 只复制运行时真正需要的内容。

**踩坑**：第一版用 blocklist，把 `cli.js`、`package.json`、`LICENSE`、`CHANGELOG.md`、`README.md`、`.claude/`、`evals/` 全部安装进了用户目录。

---

## 2. 安装前先清空目标目录

```js
function removeDir(dir) {
  try { fs.rmSync(dir, { recursive: true, force: true }); } catch {}
}

// 安装时：
removeDir(destDir);
copyDir(SRC, destDir, true);
```

**为什么**：不清空的话，从源码删掉一个文件，已安装的旧版文件永远留在用户目录里。清空后重装保证幂等性，重复运行结果一致。

---

## 3. 每个平台的 skills 路径必须单独确认

不要猜，不要合并两个平台共用一个 flag。找一个该平台上**已知能显示**的 skill，看它实际在哪个目录，再照着写。

| 平台 | 全局路径 | 项目级路径 |
|------|---------|-----------|
| Claude Code / Desktop | `~/.claude/skills/<name>/` | `.claude/skills/<name>/` |
| OpenCode | `~/.config/opencode/skills/<name>/` | `.opencode/skills/<name>/` |
| Codex | `~/.codex/skills/<name>/` | `.codex/skills/<name>/` |
| Agent Skills | `~/.agents/skills/<name>/` | `.agents/skills/<name>/` |

**踩坑**：Codex 目标完全缺失，`--opencode` 错误地代劳了 Codex 安装，导致 Codex 从未安装过该 skill。

---

## 4. OpenCode 对目录结构很敏感

OpenCode 的 skill 扫描器对目录结构有隐性假设。已知能正常显示的 skill（如 brandkit、minimalist-ui）目录内**只有 `SKILL.md`**。带有额外子目录的 skill 可能被静默跳过。

**验证方法**：安装后对比一个已知可见 skill 的目录结构，确认两者形态一致。

**注意**：如果你的 skill 需要 `scripts/`、`references/` 等辅助文件，目前只能接受 OpenCode 可能无法显示的风险，或等待 OpenCode 的文件式 skill 机制完善。

---

## 5. 文档和示例命令写 `@latest`

```bash
# 正确 ✅
npx lit-search-cite@latest

# 有风险 ❌ — 可能命中 npx 缓存，运行旧版本
npx lit-search-cite
```

**为什么**：npm publish 之后，`npx pkg` 不会立即拉最新版，本地缓存可能持续数小时。用户会以为安装了新版，实际跑的是旧版。

---

## 6. `package.json files` 字段和安装器 allowlist 保持同步

两处应该覆盖同一套文件集合，且都用**目录级**而非逐文件列举：

```json
// package.json
"files": [
  "SKILL.md",
  "AGENTS.md",
  "LICENSE",
  "cli.js",
  "scripts/",       // ← 目录级，不要逐个列文件
  "references/"
]
```

**为什么**：逐文件列举时，`scripts/` 新增文件后容易忘记同步更新 `files` 字段，导致本地安装和 npx 安装结果不一致。

---

## 7. 编码问题

### Python 脚本在 Windows 上的输出编码

Windows PowerShell 5.1 默认控制台编码为 GBK（cp936），Python 默认用系统编码输出，遇到非 ASCII 字符（作者名、特殊符号）会抛 `UnicodeEncodeError`。

**修复**：所有 Python 脚本开头加：

```python
import sys, os
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
```

**为什么用 `errors='replace'` 而非 `errors='ignore'`**：replace 把无法编码的字符替换为 `?`，输出仍可读；ignore 静默丢字，调试时难以发现。

### PowerShell 脚本输出非 ASCII

PowerShell 5.1 的 `Write-Host` / `Write-Output` 遇到非 ASCII 字符也会乱码。解决方案：

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
```

放在脚本开头。

### 文件写入编码

PowerShell 5.1 的 `Out-File` / `Set-Content` 默认 UTF-16 LE（with BOM）。写给其他工具读的文件加 `-Encoding utf8`：

```powershell
$content | Out-File -FilePath $path -Encoding utf8
```

### Git 行尾警告（LF → CRLF）

Windows 上 git 会提示 `LF will be replaced by CRLF`。这是正常现象，不影响功能，但如果脚本在 Linux/Mac 上运行需要 LF，在 `.gitattributes` 中指定：

```
*.py  text eol=lf
*.ps1 text eol=crlf
*.md  text eol=lf
```

---

## 8. 跨平台兼容问题

### Windows 上禁用 `curl`，改用 PowerShell 原生命令

Windows 上的 `curl` 实际是 `Invoke-WebRequest` 的别名，行为与 Linux `curl` 不同，直接调用会返回 exit 49 或解析错误。

```powershell
# ❌ 错误：Windows 上 curl 是别名，参数不兼容
curl -s "https://api.example.com/data"

# ✅ 正确：用 PowerShell 原生
Invoke-RestMethod -Uri "https://api.example.com/data"
# 或
(Invoke-WebRequest -Uri "https://api.example.com/data").Content
```

Python 脚本中用 `requests` 库，不依赖系统 `curl`。

### 路径分隔符

Python 脚本统一用 `pathlib.Path` 或 `os.path.join()`，不要硬编码 `/` 或 `\`：

```python
from pathlib import Path
output = Path.home() / '.lit-search-cite' / 'config.json'
```

PowerShell 脚本用 `Join-Path`：

```powershell
$config = Join-Path $env:USERPROFILE '.lit-search-cite\config.json'
```

### 命令可用性差异

| 操作 | Linux/Mac | Windows |
|------|-----------|---------|
| HTTP 请求 | `curl` | `Invoke-RestMethod` |
| 解压 | `tar` / `unzip` | `Expand-Archive` |
| 环境变量 | `$VAR` | `$env:VAR` |
| 用户目录 | `$HOME` | `$env:USERPROFILE` |
| 后台运行 | `cmd &` | `Start-Job` |

### Node.js 路径（`os.homedir()`）

`os.homedir()` 在 Windows 返回 `C:\Users\xxx`，在 Linux/Mac 返回 `/home/xxx`。`path.join()` 会自动用正确的分隔符，不要手动拼接：

```js
// ✅
path.join(os.homedir(), '.claude', 'skills', SKILL_NAME)

// ❌
os.homedir() + '/.claude/skills/' + SKILL_NAME
```

### 发布前跨平台验证清单

```
[ ] Python 脚本有 win32 编码头
[ ] PowerShell 脚本有 UTF-8 输出编码设置
[ ] 没有硬编码路径分隔符
[ ] 没有在 PowerShell 脚本里调用 curl / grep / sed 等 Unix 命令
[ ] Node.js 路径用 path.join() + os.homedir()
[ ] 文件写入明确指定编码
```

---

## 9. 改动后先给用户确认，再推送 GitHub

本地改完之后，先展示：
- 改了什么（diff 摘要）
- 拟提交的 commit message
- 将推送到哪里（branch、tag、npm、GitHub Release）

**等用户确认后**再执行 `git push` / `npm publish` / `gh release create`。

**为什么**：推送是高风险不可逆操作。已发布的 npm 版本无法删除（只能 deprecate），GitHub Release 回滚也会造成用户困惑。

---

## 10. 版本更新时所有文档必须同步，不能分批

一次版本变更必须在同一个发布会话中完成：

| 步骤 | 内容 |
|------|------|
| 文档 | `package.json` version、`CHANGELOG.md`、`README.md`（安装命令、平台表格）、`references/` 相关文件 |
| 代码仓库 | `git commit` + `git tag` + `git push origin master` + `git push origin vX.Y.Z` |
| 包注册表 | `npm publish`（或 `pypi upload`） |
| GitHub Release | `gh release create vX.Y.Z` |

**为什么**：分批操作容易出现"README 写了新版本但 npm 还是旧版"或"GitHub Release 有 tag 但 npm 没更新"的不一致状态。

---

## 发布前检查清单

```
代码 & 文档
[ ] allowlist 只包含运行时必要文件
[ ] 安装器有 pre-clean (removeDir) 步骤
[ ] 每个新平台的路径已对照已知可用 skill 确认
[ ] package.json version 已更新
[ ] CHANGELOG.md 已更新（版本号 + 日期 + 变更内容）
[ ] README.md 已更新（安装命令、平台表格、选项说明）
[ ] 所有文档示例使用 npx pkg@latest
[ ] package.json files 字段与 allowlist 一致（目录级）

本地验证
[ ] 本地跑一次安装，检查目标目录内容是否干净
[ ] 向用户展示 diff 和 commit message，等待确认

推送（确认后执行）
[ ] git commit + git tag + git push origin master + git push origin vX.Y.Z
[ ] npm publish（或 pypi upload）
[ ] gh release create vX.Y.Z

发布后验证
[ ] npx pkg@latest 拉到正确版本号
[ ] GitHub Release 页面内容正确
```

---

## 版本发布流程

```bash
# ── 准备阶段 ──────────────────────────────────────────
# 1. 更新 package.json version
# 2. 更新 CHANGELOG.md（版本号 + 日期 + 变更说明）
# 3. 更新 README.md（安装选项、平台表格等）
# 4. 展示 diff，等用户确认 ← 不要跳过这步

# ── 推送阶段（用户确认后）─────────────────────────────
# 5. 提交
git add . && git commit -m "v1.0.x: ..."
# 6. 打 tag
git tag v1.0.x
# 7. 推送代码和 tag
git push origin master && git push origin v1.0.x
# 8. 发布到 npm（或 pypi）
npm publish
# 9. 创建 GitHub Release
gh release create v1.0.x --title "v1.0.x: 标题" --notes "变更说明"

# ── 验证阶段 ──────────────────────────────────────────
# 10. 验证 npx 拿到新版
npx lit-search-cite@latest
```
