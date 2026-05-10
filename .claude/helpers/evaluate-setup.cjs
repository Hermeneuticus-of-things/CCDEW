#!/usr/bin/env node
'use strict';
/**
 * /evaluate-setup backend — comprehensive workspace audit.
 * Inspired by Red Hat's claude-code-setup-evaluator.
 *
 * Run: node .claude/helpers/evaluate-setup.cjs [--json]
 */

const fs = require('fs');
const path = require('path');
const { findExecutable, findPython, IS_WIN } = require('./lib/platform.cjs');
const { isValidNodeId } = require('./lib/validate.cjs');
const { isEnabled, load: loadFlags } = require('./lib/flags.cjs');

const WORK = process.cwd();
const HELPERS = path.join(__dirname);
const results = { sections: {}, summary: { pass: 0, warn: 0, fail: 0 } };

function record(section, name, status, detail) {
  results.sections[section] = results.sections[section] || [];
  results.sections[section].push({ name, status, detail: detail || '' });
  results.summary[status.toLowerCase()]++;
}

function printRow(name, status, detail) {
  const sym = status === 'PASS' ? '✓' : status === 'WARN' ? '⚠' : '✗';
  const pad = name.length > 50 ? name.slice(0, 47) + '...' : name.padEnd(50);
  console.log(`  [${sym} ${status.padEnd(4)}] ${pad}${detail ? ' — ' + detail : ''}`);
}

function header(t) {
  console.log('\n' + '═'.repeat(70));
  console.log('  ' + t);
  console.log('═'.repeat(70));
}

function timed(fn) {
  const t0 = process.hrtime.bigint();
  fn();
  return Number(process.hrtime.bigint() - t0) / 1e6;
}

// ── A. Config ───────────────────────────────────────────────────────────
header('A. CONFIG VALIDATION');
let settings;
try {
  settings = JSON.parse(fs.readFileSync(path.join(WORK, '.claude', 'settings.json'), 'utf8'));
  printRow('settings.json parses', 'PASS', `${Object.keys(settings.hooks || {}).length} hook events`);
  record('config', 'settings.json parses', 'PASS');
} catch (e) {
  printRow('settings.json parses', 'FAIL', e.message);
  record('config', 'settings.json parses', 'FAIL', e.message);
}
if (settings && settings.hooks) {
  for (const ev of ['PreToolUse', 'PostToolUse', 'UserPromptSubmit', 'SessionStart', 'SessionEnd']) {
    const ok = !!settings.hooks[ev];
    printRow(`event ${ev}`, ok ? 'PASS' : 'FAIL');
    record('config', `event ${ev}`, ok ? 'PASS' : 'FAIL');
  }
}

let flags;
try {
  flags = loadFlags();
  const enabled = Object.entries(flags.components || {}).filter(([,v]) => v).map(([k]) => k);
  printRow('feature-flags.json', 'PASS', `${enabled.length} active`);
  record('config', 'feature-flags.json', 'PASS', enabled.join(','));
} catch (e) {
  printRow('feature-flags.json', 'FAIL', e.message);
  record('config', 'feature-flags.json', 'FAIL');
}

// ── B. Modules + lib ──────────────────────────────────────────────────
header('B. MODULES + LIB UTILITIES');
const required = [
  'hook-handler.cjs', 'safla.cjs', 'codeburn.cjs', 'graphify.cjs',
  'intelligence.cjs', 'langgraph-micro.cjs', 'red-hat-evaluator.cjs',
  'auto-optimize.cjs', 'metrics-update.cjs', 'project-scope.cjs',
  'secret-scan.cjs', 'enneagram_router.py', 'enneagram_compose.py',
  'lib/atomic-write.cjs', 'lib/platform.cjs', 'lib/flags.cjs', 'lib/validate.cjs',
];
for (const m of required) {
  const ok = fs.existsSync(path.join(HELPERS, m));
  printRow(m, ok ? 'PASS' : 'FAIL');
  record('modules', m, ok ? 'PASS' : 'FAIL');
}

// ── C. Hot-path performance ───────────────────────────────────────────
header('C. HOT-PATH PERFORMANCE (in-process median)');
function loadFresh(p) {
  const abs = require.resolve(p);
  delete require.cache[abs];
  return require(p);
}
const ssa = loadFresh(path.join(HELPERS, 'ssa.cjs'));
const safla = loadFresh(path.join(HELPERS, 'safla.cjs'));
const corpus = Array.from({ length: 50 }, (_, i) => ({
  id: `e-${i}`, text: `entry ${i} ${['a','b','c','d','e'][i%5]}`, pinned: i < 2, score: 0.5,
}));
const ssaMs = timed(() => ssa.filterContext('refactor module', corpus, { topK: 12 }));
printRow('ssa.filterContext(50)', ssaMs < 5 ? 'PASS' : 'WARN', `${ssaMs.toFixed(2)}ms`);
record('perf', 'ssa.filterContext(50)', ssaMs < 5 ? 'PASS' : 'WARN', `${ssaMs.toFixed(2)}ms`);

const saflaMs = timed(() => safla.recordOutcome && safla.recordOutcome(3, true, 'audit-perf-bench'));
printRow('safla.recordOutcome', saflaMs < 10 ? 'PASS' : 'WARN', `${saflaMs.toFixed(2)}ms`);
record('perf', 'safla.recordOutcome', saflaMs < 10 ? 'PASS' : 'WARN', `${saflaMs.toFixed(2)}ms`);

// ── D. SAFLA state integrity ──────────────────────────────────────────
header('D. STATE INTEGRITY');
const saflaPath = path.join(WORK, '.claude-flow', 'data', 'safla.json');
if (fs.existsSync(saflaPath)) {
  try {
    const data = JSON.parse(fs.readFileSync(saflaPath, 'utf-8'));
    const allKeys = Object.keys(data.nodes || {});
    const invalid = allKeys.filter(k => !isValidNodeId(k));
    if (invalid.length === 0) {
      printRow('safla.json node keys', 'PASS', `${allKeys.length} valid`);
      record('state', 'safla.json node keys', 'PASS');
    } else {
      printRow('safla.json node keys', 'FAIL', `${invalid.length} invalid: ${invalid.join(',')}`);
      record('state', 'safla.json node keys', 'FAIL', invalid.join(','));
    }
  } catch (e) {
    printRow('safla.json valid', 'FAIL', e.message);
    record('state', 'safla.json valid', 'FAIL');
  }
} else {
  printRow('safla.json present', 'WARN', 'not yet — fresh workspace');
  record('state', 'safla.json present', 'WARN', 'fresh workspace');
}

const dataDir = path.join(WORK, '.claude-flow', 'data');
if (fs.existsSync(dataDir)) {
  const tmps = fs.readdirSync(dataDir).filter(f => f.endsWith('.tmp'));
  const ok = tmps.length === 0;
  printRow('no .tmp orphans', ok ? 'PASS' : 'WARN', ok ? '' : `${tmps.length} found`);
  record('state', 'no .tmp orphans', ok ? 'PASS' : 'WARN');
}

// ── E. Cost tracking (codeburn) ────────────────────────────────────────
header('E. COST TRACKING');
const cbBin = findExecutable('codeburn');
if (cbBin) {
  printRow('codeburn CLI on PATH', 'PASS', cbBin);
  record('cost', 'codeburn CLI on PATH', 'PASS', cbBin);
  if (IS_WIN && /\.(cmd|bat)$/i.test(cbBin)) {
    printRow('Win .cmd extension picked', 'PASS');
    record('cost', 'Win .cmd extension picked', 'PASS');
  }
} else {
  printRow('codeburn CLI on PATH', 'WARN', 'fallback to native engine');
  record('cost', 'codeburn CLI on PATH', 'WARN', 'fallback to native engine');
}

try {
  const nativeEngine = loadFresh(path.join(HELPERS, 'lib', 'codeburn-engine.cjs'));
  if (nativeEngine.isAvailable()) {
    printRow('native engine (~/.claude/projects)', 'PASS', 'fallback ready');
    record('cost', 'native engine', 'PASS');
  } else {
    printRow('native engine', 'WARN', '~/.claude/projects not present');
    record('cost', 'native engine', 'WARN');
  }
} catch (e) {
  printRow('native engine loads', 'FAIL', e.message);
  record('cost', 'native engine loads', 'FAIL');
}

try {
  const codeburn = loadFresh(path.join(HELPERS, 'codeburn.cjs'));
  const t = codeburn.totals({ fresh: true });
  if (t.source === 'real') {
    printRow('totals (CLI)', 'PASS', `$${t.today_cost.toFixed(2)} today, ${t.today_calls} calls`);
    record('cost', 'totals', 'PASS', `cli/$${t.today_cost.toFixed(2)}/${t.today_calls}`);
  } else if (t.source === 'native') {
    printRow('totals (native fallback)', 'PASS', `$${t.today_cost.toFixed(2)} today, ${t.today_calls} calls`);
    record('cost', 'totals', 'PASS', `native/$${t.today_cost.toFixed(2)}/${t.today_calls}`);
  } else {
    printRow('totals', 'WARN', `source=${t.source}`);
    record('cost', 'totals', 'WARN', t.source);
  }
} catch (e) {
  printRow('codeburn.totals', 'FAIL', e.message);
  record('cost', 'codeburn.totals', 'FAIL');
}

// ── F. Security ────────────────────────────────────────────────────────
header('F. SECURITY');
try {
  const secretScan = loadFresh(path.join(HELPERS, 'secret-scan.cjs'));
  const r = secretScan.check({ filePath: 'x.js', content: 'AKIAIOSFODNN7EXAMPLE' });
  printRow('secret-scan detects AWS key', !r.safe ? 'PASS' : 'FAIL', r.reason || '');
  record('security', 'secret-scan detects AWS key', !r.safe ? 'PASS' : 'FAIL');
  const r2 = secretScan.check({ filePath: 'src/x.js', content: 'console.log("ok")' });
  printRow('secret-scan no false-positive', r2.safe ? 'PASS' : 'FAIL');
  record('security', 'secret-scan no false-positive', r2.safe ? 'PASS' : 'FAIL');
} catch (e) {
  printRow('secret-scan loads', 'FAIL', e.message);
  record('security', 'secret-scan loads', 'FAIL');
}
const denyRules = (settings?.permissions?.deny || []).length;
printRow('settings deny rules', denyRules > 0 ? 'PASS' : 'WARN', `${denyRules} deny patterns`);
record('security', 'settings deny rules', denyRules > 0 ? 'PASS' : 'WARN');

// ── G. Cross-platform ──────────────────────────────────────────────────
header('G. CROSS-PLATFORM');
printRow('platform detected', 'PASS', IS_WIN ? 'Windows' : process.platform);
record('platform', 'platform', 'PASS', process.platform);
const py = findPython();
printRow('Python interpreter', py ? 'PASS' : 'WARN', py || 'not found');
record('platform', 'python', py ? 'PASS' : 'WARN', py || 'not found');
const node = findExecutable('node');
if (node) {
  printRow('Node executable resolved', 'PASS', node);
  record('platform', 'node executable', 'PASS', node);
  if (IS_WIN && !/\.(cmd|exe|bat)$/i.test(node)) {
    printRow('Win Node has proper extension', 'WARN', 'no .exe/.cmd suffix');
    record('platform', 'win node ext', 'WARN');
  }
}

// ── Summary ────────────────────────────────────────────────────────────
header('SUMMARY');
console.log(`  PASS: ${results.summary.pass}`);
console.log(`  WARN: ${results.summary.warn}`);
console.log(`  FAIL: ${results.summary.fail}`);
const total = results.summary.pass + results.summary.warn + results.summary.fail;
console.log(`  Total: ${total} checks`);

const reportsDir = path.join(WORK, '.claude-flow', 'reports');
if (!fs.existsSync(reportsDir)) fs.mkdirSync(reportsDir, { recursive: true });
const stamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
const reportFile = path.join(reportsDir, `evaluate-${stamp}.json`);
fs.writeFileSync(reportFile, JSON.stringify(results, null, 2));
console.log(`  Report: ${reportFile}`);

// ── Auto-fix mode (--fix) ─────────────────────────────────────────────
if (process.argv.includes('--fix')) {
  console.log('\n' + '═'.repeat(70));
  console.log('  AUTO-FIX MODE');
  console.log('═'.repeat(70));
  let fixed = 0;

  // Fix 1: clean SAFLA invalid keys
  const saflaP = path.join(WORK, '.claude-flow', 'data', 'safla.json');
  if (fs.existsSync(saflaP)) {
    try {
      const data = JSON.parse(fs.readFileSync(saflaP, 'utf-8'));
      const before = Object.keys(data.nodes || {}).length;
      for (const k of Object.keys(data.nodes || {})) if (!isValidNodeId(k)) delete data.nodes[k];
      const after = Object.keys(data.nodes).length;
      if (before !== after) {
        const { writeAtomicJson } = require('./lib/atomic-write.cjs');
        writeAtomicJson(saflaP, data);
        console.log(`  [✓ FIXED] safla.json: dropped ${before - after} invalid keys`);
        fixed++;
      }
    } catch (e) { console.log(`  [✗ SKIP] safla cleanup: ${e.message}`); }
  }

  // Fix 2: clean .tmp orphans
  const dataD = path.join(WORK, '.claude-flow', 'data');
  if (fs.existsSync(dataD)) {
    const tmps = fs.readdirSync(dataD).filter(f => f.endsWith('.tmp'));
    for (const t of tmps) { try { fs.unlinkSync(path.join(dataD, t)); } catch {} }
    if (tmps.length > 0) {
      console.log(`  [✓ FIXED] removed ${tmps.length} .tmp orphan(s)`);
      fixed++;
    }
  }

  // Fix 3: ensure logs/ dir exists
  const logsD = path.join(WORK, '.claude-flow', 'logs');
  if (!fs.existsSync(logsD)) {
    fs.mkdirSync(logsD, { recursive: true });
    console.log('  [✓ FIXED] created .claude-flow/logs/');
    fixed++;
  }

  // Fix 4: ensure reports/ dir exists
  const repD = path.join(WORK, '.claude-flow', 'reports');
  if (!fs.existsSync(repD)) {
    fs.mkdirSync(repD, { recursive: true });
    console.log('  [✓ FIXED] created .claude-flow/reports/');
    fixed++;
  }

  console.log(`\n  Auto-fix applied ${fixed} change(s).`);
  if (fixed === 0) console.log('  All checks already in good state.');
}

if (process.argv.includes('--json')) console.log(JSON.stringify(results, null, 2));
process.exit(results.summary.fail > 0 ? 1 : 0);
