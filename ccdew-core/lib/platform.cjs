'use strict';
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const IS_WIN = process.platform === 'win32';

function findExecutable(name, extraCandidates = []) {
  const home = process.env.HOME || process.env.USERPROFILE || '';
  const candidates = [
    ...extraCandidates,
    path.join(home, '.npm-global', 'bin', name),
    path.join(home, '.local', 'bin', name),
    '/usr/local/bin/' + name,
    '/usr/bin/' + name,
  ];
  if (IS_WIN) {
    candidates.push(path.join(home, 'AppData', 'Roaming', 'npm', name + '.cmd'));
  }
  for (const c of candidates) {
    if (fs.existsSync(c)) return c;
  }
  try {
    const finder = IS_WIN ? 'where' : 'which';
    const lines = execSync(`${finder} ${name}`, {
      encoding: 'utf-8', timeout: 2000, stdio: ['ignore', 'pipe', 'ignore'],
    }).trim().split(/\r?\n/).filter(Boolean);
    if (IS_WIN) {
      const winExe = lines.find(l => /\.(cmd|exe|bat)$/i.test(l));
      if (winExe) return winExe;
    }
    return lines[0] || null;
  } catch { return null; }
}

function findPython() {
  if (process.env.PYTHON_BIN) return process.env.PYTHON_BIN;
  const { spawnSync } = require('child_process');
  for (const cand of ['python3', 'python', 'py']) {
    const p = findExecutable(cand);
    if (!p) continue;
    try {
      const r = spawnSync(p, ['-V'], {
        encoding: 'utf-8', timeout: 3000,
        stdio: ['ignore', 'pipe', 'pipe'],
        shell: IS_WIN && /\.(cmd|bat)$/i.test(p),
      });
      const out = (r.stdout || '') + (r.stderr || '');
      if (r.status === 0 && /^Python\s+\d+\./i.test(out.trim())) return p;
    } catch { /* try next */ }
  }
  return null;
}

module.exports = { IS_WIN, findExecutable, findPython };
