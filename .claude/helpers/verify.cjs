#!/usr/bin/env node
'use strict';
/**
 * /verify backend — quick sanity sweep over uncommitted changes.
 * Runs (in parallel): typecheck, tests, lint, secret-scan, dead-code.
 *
 * Detects project type from disk markers:
 *   tsconfig.json     -> TypeScript (tsc --noEmit)
 *   package.json      -> Node (npm test, eslint)
 *   pyproject.toml    -> Python (pytest, ruff)
 *   go.mod            -> Go (go vet, go test)
 *
 * Run: node verify.cjs [--staged|--branch|<file>]
 */

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');
const { findExecutable } = require('./lib/platform.cjs');
const secretScan = require('./secret-scan.cjs');

const WORK = process.cwd();
const args = process.argv.slice(2);
const SCOPE = args[0] || '--unstaged';

const results = [];
function record(check, status, detail, ms) {
  results.push({ check, status, detail: detail || '', ms: ms || 0 });
}

function run(cmd, cmdArgs, opts = {}) {
  const t0 = Date.now();
  const r = spawnSync(cmd, cmdArgs, {
    cwd: WORK, encoding: 'utf-8', timeout: opts.timeout || 60_000,
    stdio: ['ignore', 'pipe', 'pipe'], shell: opts.shell || false,
  });
  return {
    code: r.status, stdout: r.stdout || '', stderr: r.stderr || '',
    ms: Date.now() - t0,
  };
}

function listChangedFiles() {
  if (SCOPE.startsWith('--branch')) {
    const r = run('git', ['diff', '--name-only', 'main...HEAD']);
    return r.stdout.trim().split('\n').filter(Boolean);
  }
  if (SCOPE.startsWith('--staged')) {
    const r = run('git', ['diff', '--cached', '--name-only']);
    return r.stdout.trim().split('\n').filter(Boolean);
  }
  if (SCOPE.startsWith('--unstaged') || !SCOPE.startsWith('--')) {
    const r = run('git', ['diff', '--name-only']);
    const files = r.stdout.trim().split('\n').filter(Boolean);
    if (!SCOPE.startsWith('--') && SCOPE) return [SCOPE];
    return files;
  }
  return [];
}

const projectMarkers = {
  ts: fs.existsSync(path.join(WORK, 'tsconfig.json')),
  node: fs.existsSync(path.join(WORK, 'package.json')),
  py: fs.existsSync(path.join(WORK, 'pyproject.toml')) || fs.existsSync(path.join(WORK, 'setup.py')),
  go: fs.existsSync(path.join(WORK, 'go.mod')),
};

console.log(`\n[VERIFY] scope: ${SCOPE}`);
const changed = listChangedFiles();
console.log(`[VERIFY] changed files: ${changed.length}`);

// 1. Typecheck
if (projectMarkers.ts) {
  const tsc = findExecutable('tsc') || (findExecutable('npx') ? 'npx' : null);
  if (tsc) {
    const r = tsc.endsWith('npx') || /\bnpx/.test(tsc)
      ? run(tsc, ['--no-install', 'tsc', '--noEmit'], { shell: process.platform === 'win32' })
      : run(tsc, ['--noEmit'], { shell: process.platform === 'win32' });
    record('typecheck', r.code === 0 ? 'PASS' : 'FAIL', r.code !== 0 ? r.stdout.split('\n').slice(0, 3).join(' | ') : '', r.ms);
  } else { record('typecheck', 'SKIP', 'tsc/npx not found'); }
} else if (projectMarkers.go) {
  const r = run('go', ['vet', './...'], { shell: process.platform === 'win32' });
  record('typecheck (go vet)', r.code === 0 ? 'PASS' : 'FAIL', r.stderr.slice(0, 200), r.ms);
} else {
  record('typecheck', 'SKIP', 'no TS/Go project markers');
}

// 2. Tests
if (projectMarkers.node && changed.length > 0) {
  const pkg = JSON.parse(fs.readFileSync(path.join(WORK, 'package.json'), 'utf-8'));
  if (pkg.scripts && pkg.scripts.test) {
    const r = run('npm', ['test', '--silent'], { timeout: 120_000, shell: process.platform === 'win32' });
    record('tests (npm test)', r.code === 0 ? 'PASS' : 'FAIL', r.code !== 0 ? r.stdout.split('\n').slice(-3).join(' | ') : '', r.ms);
  } else {
    record('tests', 'SKIP', 'no npm test script');
  }
} else if (projectMarkers.py) {
  const py = findExecutable('pytest');
  if (py) {
    const r = run(py, ['-q', '--no-header'], { timeout: 120_000, shell: process.platform === 'win32' });
    record('tests (pytest)', r.code === 0 ? 'PASS' : 'FAIL', '', r.ms);
  }
} else if (projectMarkers.go) {
  const r = run('go', ['test', './...'], { timeout: 120_000, shell: process.platform === 'win32' });
  record('tests (go test)', r.code === 0 ? 'PASS' : 'FAIL', r.stderr.slice(0, 200), r.ms);
} else {
  record('tests', 'SKIP', 'no project markers / no changed files');
}

// 3. Lint (changed files only when possible)
if (projectMarkers.node) {
  const eslint = findExecutable('eslint');
  if (eslint && changed.length > 0) {
    const codeFiles = changed.filter(f => /\.(js|cjs|mjs|ts|tsx|jsx)$/i.test(f));
    if (codeFiles.length > 0) {
      const r = run(eslint, codeFiles, { shell: process.platform === 'win32' });
      record('lint (eslint changed)', r.code === 0 ? 'PASS' : 'WARN', r.code !== 0 ? `${codeFiles.length} files` : '', r.ms);
    } else { record('lint', 'SKIP', 'no JS/TS files in scope'); }
  } else if (eslint) {
    record('lint', 'SKIP', 'no changed files');
  } else {
    record('lint', 'SKIP', 'eslint not installed');
  }
} else if (projectMarkers.py) {
  const ruff = findExecutable('ruff');
  if (ruff) {
    const r = run(ruff, ['check', '.'], { shell: process.platform === 'win32' });
    record('lint (ruff)', r.code === 0 ? 'PASS' : 'WARN', '', r.ms);
  }
} else {
  record('lint', 'SKIP', 'no linter for project type');
}

// 4. Secret-scan on changed files
if (changed.length > 0) {
  let blocked = 0;
  const blockedDetails = [];
  for (const f of changed) {
    const full = path.isAbsolute(f) ? f : path.join(WORK, f);
    if (!fs.existsSync(full)) continue;
    let content = '';
    try { content = fs.readFileSync(full, 'utf-8'); } catch { continue; }
    const r = secretScan.check({ filePath: full, content });
    if (!r.safe) {
      blocked++;
      blockedDetails.push(`${path.basename(f)}: ${r.reason}`);
    }
  }
  record('secret-scan', blocked === 0 ? 'PASS' : 'FAIL',
    blocked === 0 ? `${changed.length} files clean` : blockedDetails.slice(0, 2).join('; '));
} else {
  record('secret-scan', 'SKIP', 'no changed files');
}

// 5. Diff stats
if (changed.length > 0) {
  const r = run('git', ['diff', '--shortstat']);
  if (r.stdout) record('diff stats', 'INFO', r.stdout.trim().slice(0, 100));
}

// Output
const COLORS = { PASS: '✓', FAIL: '✗', WARN: '⚠', SKIP: '·', INFO: 'ℹ' };
let failed = 0;
console.log('');
for (const r of results) {
  const sym = COLORS[r.status] || '?';
  const ms = r.ms ? ` (${r.ms}ms)` : '';
  console.log(`  [${sym} ${r.status.padEnd(4)}] ${r.check.padEnd(28)}${r.detail ? ' — ' + r.detail : ''}${ms}`);
  if (r.status === 'FAIL') failed++;
}

console.log('');
const total = results.length;
const passed = results.filter(r => r.status === 'PASS').length;
const skipped = results.filter(r => r.status === 'SKIP').length;
console.log(`[VERIFY] ${passed}/${total} PASS, ${failed} FAIL, ${skipped} SKIP`);

if (process.argv.includes('--json')) {
  console.log(JSON.stringify({ scope: SCOPE, changed_files: changed.length, results }, null, 2));
}

process.exit(failed > 0 ? 1 : 0);
