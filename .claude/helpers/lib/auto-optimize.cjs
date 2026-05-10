'use strict';
/**
 * Auto-optimize — applies SAFE transforms surfaced by auto-infer.
 * Only the NANO and (selected) MICRO transforms are applied automatically.
 * MEZZO/MACRO/MAHA changes (split, extract, rebuild) require human judgment.
 *
 * Modes:
 *   nano  — trim trailing whitespace, normalize line endings (LF), strip BOM
 *   micro — (proposal-only — no auto-fix; reports what could be done)
 *   mezzo, macro, maha — proposal-only
 *
 * Always backs up before mutating: <file>.bak.<ts>
 */

const fs = require('fs');
const path = require('path');

const WORK = process.cwd();
const HELPERS = path.join(WORK, '.claude', 'helpers');

function listJsFiles(dir) {
  const out = [];
  if (!fs.existsSync(dir)) return out;
  for (const f of fs.readdirSync(dir)) {
    const full = path.join(dir, f);
    const stat = fs.statSync(full);
    if (stat.isDirectory() && !f.startsWith('.') && f !== 'tests' && f !== 'node_modules') {
      out.push(...listJsFiles(full));
    } else if (/\.(cjs|js|mjs)$/.test(f)) {
      out.push(full);
    }
  }
  return out;
}

function backupFile(filePath) {
  const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  const bak = filePath + '.bak.' + ts;
  fs.copyFileSync(filePath, bak);
  return bak;
}

function optimizeNano(opts = {}) {
  const dryRun = !!opts.dryRun;
  const files = listJsFiles(HELPERS);
  const changes = [];
  for (const f of files) {
    if (f.includes(`${path.sep}tests${path.sep}`)) continue;
    const orig = fs.readFileSync(f, 'utf-8');
    let out = orig;
    let bomStripped = false;
    if (out.charCodeAt(0) === 0xFEFF) { out = out.slice(1); bomStripped = true; }
    const lfNormalized = out.includes('\r\n');
    out = out.replace(/\r\n/g, '\n');
    const beforeTrim = out.length;
    out = out.split('\n').map(l => l.replace(/[ \t]+$/, '')).join('\n');
    const afterTrim = out.length;
    if (out !== orig) {
      const ops = [];
      if (bomStripped) ops.push('strip-BOM');
      if (lfNormalized) ops.push('normalize-LF');
      if (afterTrim < beforeTrim) ops.push(`trim-trailing(-${beforeTrim - afterTrim} chars)`);
      changes.push({ file: path.relative(WORK, f), ops });
      if (!dryRun) {
        backupFile(f);
        fs.writeFileSync(f, out, 'utf-8');
      }
    }
  }
  return { mode: 'nano', dryRun, changes_count: changes.length, changes };
}

function optimizeMicroPlan() {
  const { inferMicro } = require('./auto-infer.cjs');
  const findings = [];
  inferMicro(findings);
  return {
    mode: 'micro',
    note: 'proposal-only — micro changes require human judgment',
    proposals: findings.map(f => ({
      file: f.file, line: f.line, action: f.suggestion, why: f.msg,
    })),
  };
}

function optimizeMezzoPlan() {
  const { inferMezzo, inferMacro } = require('./auto-infer.cjs');
  const findings = [];
  inferMezzo(findings);
  inferMacro(findings);
  return {
    mode: 'mezzo+macro',
    note: 'proposal-only — structural changes require human judgment',
    proposals: findings.filter(f => f.suggestion).map(f => ({
      file: f.file, action: f.suggestion, why: f.msg,
    })),
  };
}

function optimizeMahaPlan() {
  const { inferMaha } = require('./auto-infer.cjs');
  const findings = [];
  inferMaha(findings);
  return {
    mode: 'maha',
    note: 'proposal-only — system-level changes require human judgment',
    proposals: findings.filter(f => f.suggestion).map(f => ({
      file: f.file, action: f.suggestion, why: f.msg,
    })),
  };
}

module.exports = { optimizeNano, optimizeMicroPlan, optimizeMezzoPlan, optimizeMahaPlan };
