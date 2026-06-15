#!/usr/bin/env node
'use strict';

const fs   = require('fs');
const path = require('path');
const os   = require('os');

const PKG        = require('./package.json');
const SKILL_NAME = 'lit-search-cite';
const SRC        = __dirname;
const SKIP_DIRS  = new Set(['node_modules', '.git']);

const TARGETS = {
  claude: {
    label: 'Claude Code / Claude Desktop',
    dirs: [
      path.join(os.homedir(), '.claude', 'skills', SKILL_NAME),
      path.join(process.cwd(), '.claude', 'skills', SKILL_NAME),
    ],
  },
  opencode: {
    label: 'OpenCode / Codex',
    dirs: [
      path.join(os.homedir(), '.config', 'opencode', 'skills', SKILL_NAME),
      path.join(process.cwd(), '.opencode', 'skills', SKILL_NAME),
    ],
  },
  agents: {
    label: 'Agent Skills',
    dirs: [
      path.join(os.homedir(), '.agents', 'skills', SKILL_NAME),
      path.join(process.cwd(), '.agents', 'skills', SKILL_NAME),
    ],
  },
};

function copyDir(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    if (SKIP_DIRS.has(entry.name)) continue;
    const srcPath  = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDir(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

function installTarget(key) {
  const target = TARGETS[key];
  if (!target) return false;

  const destDir = target.dirs.find(d => {
    try {
      fs.mkdirSync(path.dirname(d), { recursive: true });
      return true;
    } catch {
      return false;
    }
  });

  if (!destDir) {
    console.log(`  ${target.label}: skipped (no writable location)`);
    return false;
  }

  copyDir(SRC, destDir);
  console.log(`  ${target.label}: ${destDir}`);
  return true;
}

const argv = process.argv.slice(2);

if (argv.includes('--version') || argv.includes('-v')) {
  console.log(PKG.version);
  process.exit(0);
}

if (argv.includes('--help') || argv.includes('-h')) {
  console.log(`
lit-search-cite v${PKG.version}
Multi-source academic literature search + citation skill installer.

Usage:
  npx lit-search-cite [options]

Options:
  (no flags)       Install to all detected platforms
  --claude, -c     Install to Claude Code / Claude Desktop only
  --opencode, -o   Install to OpenCode / Codex only
  --agents, -a     Install to Agent Skills only
  --all            Install to all platforms (same as no flags)
  --target <dir>   Install to a custom directory
  --version, -v    Print version and exit
  --help, -h       Show this help
`);
  process.exit(0);
}

// --target <dir>
const tiIdx = argv.indexOf('--target');
if (tiIdx >= 0 && argv[tiIdx + 1]) {
  const dest = argv[tiIdx + 1];
  copyDir(SRC, dest);
  console.log(`\nlit-search-cite v${PKG.version}`);
  console.log(`Installed to: ${dest}\n`);
  process.exit(0);
}

const flags = {
  claude:   argv.includes('--claude')   || argv.includes('-c'),
  opencode: argv.includes('--opencode') || argv.includes('-o'),
  agents:   argv.includes('--agents')  || argv.includes('-a'),
  all:      argv.includes('--all'),
};

const anyFlag = flags.claude || flags.opencode || flags.agents || flags.all;
// When --all or no flags: install everything. When specific flags: only those.
const keys = (!anyFlag || flags.all)
  ? Object.keys(TARGETS)
  : Object.keys(flags).filter(k => k !== 'all' && flags[k]);

console.log(`\nlit-search-cite v${PKG.version}`);
console.log('Installing...\n');

let installed = 0;
for (const key of keys) {
  if (installTarget(key)) installed++;
}

console.log(`\nDone — ${installed} location(s) installed.`);
if (installed === 0) {
  console.error('Warning: nothing was installed. Check write permissions.');
  process.exit(1);
}
