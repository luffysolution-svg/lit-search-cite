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

## 发布前检查清单

```
[ ] allowlist 只包含运行时必要文件
[ ] 安装器有 pre-clean (removeDir) 步骤
[ ] 每个新平台的路径已对照已知可用 skill 确认
[ ] 所有文档示例使用 npx pkg@latest
[ ] package.json files 字段与 allowlist 一致（目录级）
[ ] 本地跑一次安装，检查目标目录内容是否干净
[ ] npm publish 后用 npx pkg@latest 验证版本号正确
```

---

## 版本发布流程

```bash
# 1. 改 package.json version + CHANGELOG.md
# 2. 提交
git add . && git commit -m "v1.0.x: ..."
# 3. 打 tag
git tag v1.0.x
# 4. 推送代码和 tag
git push origin master && git push origin v1.0.x
# 5. 发布到 npm
npm publish
# 6. 创建 GitHub Release
gh release create v1.0.x --title "..." --notes "..."
# 7. 验证
npx lit-search-cite@latest
```
