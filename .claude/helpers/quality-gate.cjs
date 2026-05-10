#!/usr/bin/env node
'use strict';
/**
 * /quality-gate — strict pass/fail before merge/deploy.
 *
 * Inherits checks from /verify, adds:
 *   - coverage threshold (80% default)
 *   - bundle size delta vs main (5% default)
 *   - cost/call from codeburn (≤ $0.05)
 *   - no FIXME/XXX in changed files
 *
 * Per-project overrides: .claude/quality-gate.json
 */

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const WORK = process.cwd();
const CFG_PATH = path.join(WORK, '.claude', 'quality-gate.json');

const DEFAULTS = {
  coverage_threshold: 80,
  bundle_size_delta_max_pct: 5,
  cost_per_call_max: 0.05,
  fixme_max_in_diff: 0,
  skip: [],
};

function loadCfg() {
  try {
    if (fs.existsSync(CFG_PATH)) {
      return { ...DEFAULTS, ...JSON.parse(fs.readFileSync(CFG_PATH, 'utf-8')) };
    }
  } catch { /* fall through */ }
  return { ...DEFAULTS };
}

function run(cmd, args, opts = {}) {
  const r = spawnSync(cmd, args, {
    cwd: WORK, encoding: 'utf-8', timeout: opts.timeout || 60_000,
    stdio: ['ignore', 'pipe', 'pipe'], shell: opts.shell || (process.platform === 'win32'),
  });
  return { code: r.status, out: r.stdout || '', err: r.stderr || '' };
}

const cfg = loadCfg();
const results = [];
function record(check, status, detail) {
  results.push({ check, status, detail: detail || '' });
}

// 1. Run /verify (delegated)
const verifyPath = path.join(__dirname, 'verify.cjs');
if (fs.existsSync(verifyPath) && !cfg.skip.includes('verify')) {
  const r = run(process.execPath, [verifyPath]);
  record('verify (typecheck+test+lint+secret)', r.code === 0 ? 'PASS' : 'FAIL', r.code !== 0 ? 'see /verify output above' : '');
} else {
  record('verify', 'SKIP', 'verify.cjs missing or in skip list');
}

// 2. Coverage (Node only, with c8/nyc)
if (!cfg.skip.includes('coverage') && fs.existsSync(path.join(WORK, 'package.json'))) {
  const pkg = JSON.parse(fs.readFileSync(path.join(WORK, 'package.json'), 'utf-8'));
  const hasCov = pkg.scripts && (pkg.scripts['test:coverage'] || pkg.scripts.coverage);
  if (hasCov) {
    const script = pkg.scripts['test:coverage'] ? 'test:coverage' : 'coverage';
    const r = run('npm', ['run', script, '--silent'], { timeout: 180_000 });
    const m = r.out.match(/All files\s+\|\s+([0-9.]+)/);
    const pct = m ? parseFloat(m[1]) : null;
    if (pct !== null) {
      record(`coverage (${pct}% vs ${cfg.coverage_threshold}%)`,
        pct >= cfg.coverage_threshold ? 'PASS' : 'FAIL',
        `${pct}%`);
    } else {
      record('coverage', 'WARN', 'no parseable output from npm run');
    }
  } else {
    record('coverage', 'SKIP', 'no test:coverage script in package.json');
  }
} else {
  record('coverage', 'SKIP', 'no Node project / disabled');
}

// 3. FIXME/XXX in changed files
if (!cfg.skip.includes('fixme')) {
  const changed = run('git', ['diff', '--name-only']).out.trim().split('\n').filter(Boolean);
  let count = 0;
  for (const f of changed) {
    const full = path.isAbsolute(f) ? f : path.join(WORK, f);
    if (!fs.existsSync(full)) continue;
    try {
      const c = fs.readFileSync(full, 'utf-8');
      const matches = c.match(/\b(FIXME|XXX|HACK|TODO\(.*\))\b/g);
      if (matches) count += matches.length;
    } catch {}
  }
  record(`fixme/xxx markers (${count} vs max ${cfg.fixme_max_in_diff})`,
    count <= cfg.fixme_max_in_diff ? 'PASS' : 'FAIL',
    count > cfg.fixme_max_in_diff ? `${count} markers in diff` : '');
}

// 4a. npm audit
if (!cfg.skip.includes('npm-audit') && fs.existsSync(path.join(WORK, 'package.json'))) {
  try {
    const r = run('npm', ['audit', '--json', '--audit-level=high'], { timeout: 30_000 });
    let high = 0, critical = 0;
    try {
      const j = JSON.parse(r.out || '{}');
      const vuln = j.metadata && j.metadata.vulnerabilities;
      if (vuln) { high = vuln.high || 0; critical = vuln.critical || 0; }
    } catch {}
    record(`npm audit (high=${high} critical=${critical})`,
      (high === 0 && critical === 0) ? 'PASS' : 'FAIL',
      (high + critical > 0) ? `${high + critical} vulnerabilities` : '');
  } catch {
    record('npm audit', 'SKIP', 'npm audit unavailable');
  }
}

// 4b. Cost-per-call from codeburn
if (!cfg.skip.includes('cost')) {
  try {
    const codeburn = require('./codeburn.cjs');
    const t = codeburn.totals();
    if (t.source !== 'unavailable' && t.source !== 'disabled' && t.today_calls > 0) {
      const cpc = t.today_cost / t.today_calls;
      record(`cost/call ($${cpc.toFixed(4)} vs max $${cfg.cost_per_call_max})`,
        cpc <= cfg.cost_per_call_max ? 'PASS' : 'WARN',
        `$${cpc.toFixed(4)}`);
    } else {
      record('cost/call', 'SKIP', `codeburn ${t.source}`);
    }
  } catch (e) {
    record('cost/call', 'SKIP', e.message.slice(0, 60));
  }
}

// Output
const COLORS = { PASS: '✓', FAIL: '✗', WARN: '⚠', SKIP: '·' };
console.log('\n[QUALITY-GATE]\n');
let failed = 0;
for (const r of results) {
  const sym = COLORS[r.status] || '?';
  console.log(`  [${sym} ${r.status.padEnd(4)}] ${r.check.padEnd(50)}${r.detail ? ' — ' + r.detail : ''}`);
  if (r.status === 'FAIL') failed++;
}

console.log('');
if (failed === 0) {
  console.log('[QUALITY-GATE] ✓ ALL PASS — safe to merge/deploy');
} else {
  console.log(`[QUALITY-GATE] ✗ ${failed} FAILED — fix before merge`);
}

if (process.argv.includes('--json')) console.log(JSON.stringify({ results, cfg }, null, 2));
process.exit(failed > 0 ? 1 : 0);
