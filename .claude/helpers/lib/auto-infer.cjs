'use strict';
/**
 * Auto-infer — scans the workspace at 5 zoom levels and deduces what's
 * drifting / missing / over-budget without explicit user request.
 *
 * MAHA  — goal alignment (workspace serves "ultra-efficient" promise)
 * MACRO — cross-module structure (file sizes, deps, coupling)
 * MEZZO — per-module cohesion (responsibility, exports)
 * MICRO — per-function complexity (length, args, nesting)
 * NANO  — per-line hygiene (trailing whitespace, magic numbers, dead chars)
 *
 * Output: prioritized findings array { zoom, severity, file, line?, msg, suggestion? }.
 * Pure read-only — never mutates files. See `auto-optimize.cjs` for the writer.
 */

const fs = require('fs');
const path = require('path');

const WORK = process.cwd();
const HELPERS = path.join(WORK, '.claude', 'helpers');
const LIB = path.join(HELPERS, 'lib');

const THRESHOLDS = {
  module_max_lines: 500,
  module_warn_lines: 300,
  function_max_lines: 75,
  function_warn_lines: 50,
  function_max_args: 5,
  total_loc_warn: 8000,
  test_min_count: 50,
  audit_max_fail: 0,
  audit_max_warn: 2,
};

function listJsFiles(dir) {
  const out = [];
  if (!fs.existsSync(dir)) return out;
  for (const f of fs.readdirSync(dir)) {
    const full = path.join(dir, f);
    const stat = fs.statSync(full);
    if (stat.isDirectory() && !f.startsWith('.') && f !== 'tests') {
      out.push(...listJsFiles(full));
    } else if (/\.(cjs|js|mjs)$/.test(f)) {
      out.push(full);
    }
  }
  return out;
}

function inferMaha(findings) {
  const helpers = listJsFiles(HELPERS);
  const totalLoc = helpers.reduce((s, f) => s + (fs.readFileSync(f, 'utf-8').split('\n').length || 0), 0);
  const tests = (fs.existsSync(path.join(HELPERS, 'tests')) ? fs.readdirSync(path.join(HELPERS, 'tests')).filter(f => f.endsWith('.test.cjs')) : []).length;
  const skills = fs.existsSync(path.join(WORK, '.claude', 'skills')) ? fs.readdirSync(path.join(WORK, '.claude', 'skills')).filter(d => fs.statSync(path.join(WORK, '.claude', 'skills', d)).isDirectory()).length : 0;
  if (totalLoc > THRESHOLDS.total_loc_warn) {
    findings.push({ zoom: 'MAHA', severity: 'WARN', file: '<workspace>', msg: `Total LOC ${totalLoc} > soft cap ${THRESHOLDS.total_loc_warn}`, suggestion: 'Consider extracting non-essential helpers into separate package' });
  }
  if (tests < THRESHOLDS.test_min_count) {
    findings.push({ zoom: 'MAHA', severity: 'WARN', file: '<tests>', msg: `Only ${tests} test suite(s) — below ${THRESHOLDS.test_min_count} expected for this LOC`, suggestion: 'Add tests for under-covered modules' });
  }
  const audits = fs.existsSync(path.join(WORK, '.claude-flow', 'reports')) ? fs.readdirSync(path.join(WORK, '.claude-flow', 'reports')).filter(f => f.startsWith('evaluate-')) : [];
  if (audits.length === 0) {
    findings.push({ zoom: 'MAHA', severity: 'WARN', file: '<audits>', msg: 'No audit history — never ran /evaluate-setup', suggestion: 'Run: npm run audit' });
  }
  findings.push({ zoom: 'MAHA', severity: 'INFO', file: '<workspace>', msg: `${helpers.length} helpers · ${tests} test suites · ${skills} skills · ${totalLoc} LOC` });
}

function inferMacro(findings) {
  const helpers = listJsFiles(HELPERS);
  for (const f of helpers) {
    const lines = fs.readFileSync(f, 'utf-8').split('\n').length;
    const rel = path.relative(WORK, f);
    if (lines > THRESHOLDS.module_max_lines) {
      findings.push({ zoom: 'MACRO', severity: 'HIGH', file: rel, msg: `${lines} lines — exceeds hard cap ${THRESHOLDS.module_max_lines}`, suggestion: `Split into ${Math.ceil(lines / 400)} modules by responsibility` });
    } else if (lines > THRESHOLDS.module_warn_lines) {
      findings.push({ zoom: 'MACRO', severity: 'WARN', file: rel, msg: `${lines} lines — over soft cap ${THRESHOLDS.module_warn_lines}` });
    }
  }
  const helpersToHelpers = [];
  for (const f of helpers) {
    if (f.includes(`${path.sep}lib${path.sep}`)) continue;
    const c = fs.readFileSync(f, 'utf-8');
    const m = c.match(/require\(['"]\.\/[^'"\/]+\.cjs['"]\)/g) || [];
    for (const r of m) {
      const target = r.match(/'\.\/([^']+)\.cjs'/) || r.match(/"\.\/([^"]+)\.cjs"/);
      if (target && target[1] !== 'lib' && !target[1].startsWith('lib/')) {
        helpersToHelpers.push({ from: path.basename(f), to: target[1] });
      }
    }
  }
  if (helpersToHelpers.length > 5) {
    findings.push({ zoom: 'MACRO', severity: 'WARN', file: '<helpers/>', msg: `${helpersToHelpers.length} helpers↔helpers couplings (consider lib extraction)` });
  }
}

function inferMezzo(findings) {
  const helpers = listJsFiles(HELPERS);
  for (const f of helpers) {
    const c = fs.readFileSync(f, 'utf-8');
    const exportMatch = c.match(/module\.exports\s*=\s*\{([^}]+)\}/);
    if (!exportMatch) continue;
    const exports = exportMatch[1].split(',').map(s => s.trim().split(':')[0].trim()).filter(Boolean);
    const rel = path.relative(WORK, f);
    if (exports.length > 12) {
      findings.push({ zoom: 'MEZZO', severity: 'WARN', file: rel, msg: `${exports.length} exports — module may have too many responsibilities`, suggestion: 'Group related exports into sub-modules' });
    }
  }
}

function inferMicro(findings) {
  const helpers = listJsFiles(HELPERS);
  for (const f of helpers) {
    const c = fs.readFileSync(f, 'utf-8');
    const lines = c.split('\n');
    let depth = 0, fnStart = -1, fnName = '', fnArgs = 0;
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const fnMatch = line.match(/^(?:function\s+(\w+)|const\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>|(\w+)\s*\([^)]*\)\s*\{)/);
      if (fnMatch && depth === 0) {
        fnStart = i;
        fnName = fnMatch[1] || fnMatch[2] || fnMatch[3] || 'anonymous';
        const argMatch = line.match(/\(([^)]*)\)/);
        fnArgs = argMatch && argMatch[1].trim() ? argMatch[1].split(',').length : 0;
      }
      depth += (line.match(/\{/g) || []).length;
      depth -= (line.match(/\}/g) || []).length;
      if (fnStart >= 0 && depth === 0 && i > fnStart) {
        const fnLines = i - fnStart + 1;
        const rel = path.relative(WORK, f);
        if (fnLines > THRESHOLDS.function_max_lines) {
          findings.push({ zoom: 'MICRO', severity: 'WARN', file: rel, line: fnStart + 1, msg: `Function ${fnName}() is ${fnLines} lines (>${THRESHOLDS.function_max_lines})`, suggestion: 'Extract sub-functions or split file' });
        }
        if (fnArgs > THRESHOLDS.function_max_args) {
          findings.push({ zoom: 'MICRO', severity: 'WARN', file: rel, line: fnStart + 1, msg: `Function ${fnName}() has ${fnArgs} args (>${THRESHOLDS.function_max_args})`, suggestion: 'Group args into options object' });
        }
        fnStart = -1;
      }
    }
  }
}

function inferNano(findings) {
  const helpers = listJsFiles(HELPERS);
  for (const f of helpers) {
    if (f.includes(`${path.sep}tests${path.sep}`)) continue;
    const c = fs.readFileSync(f, 'utf-8');
    const lines = c.split('\n');
    const rel = path.relative(WORK, f);
    let trailing = 0, mixed = 0, todoCount = 0;
    let inBlockComment = false;
    for (let i = 0; i < lines.length; i++) {
      if (/[ \t]+$/.test(lines[i])) trailing++;
      if (/^\t.* {2,}|^ {4,}\t/.test(lines[i])) mixed++;
      const l = lines[i];
      if (inBlockComment) {
        if (l.includes('*/')) inBlockComment = false;
        continue;
      }
      if (l.includes('/*') && !l.includes('*/')) inBlockComment = true;
      const code = l.replace(/\/\/.*$/, '').replace(/\/\*.*?\*\//g, '').replace(/['"`][^'"`]*['"`]/g, '');
      if (/\b(FIXME|XXX|HACK)\b/.test(code)) todoCount++;
    }
    if (trailing > 0) findings.push({ zoom: 'NANO', severity: 'INFO', file: rel, msg: `${trailing} line(s) with trailing whitespace`, suggestion: 'Run /optimize --nano' });
    if (mixed > 0) findings.push({ zoom: 'NANO', severity: 'INFO', file: rel, msg: `${mixed} line(s) with mixed tabs+spaces` });
    if (todoCount > 0) findings.push({ zoom: 'NANO', severity: 'WARN', file: rel, msg: `${todoCount} TODO/FIXME marker(s)`, suggestion: 'Resolve or convert to issues' });
  }
}

function inferAll() {
  const findings = [];
  inferMaha(findings);
  inferMacro(findings);
  inferMezzo(findings);
  inferMicro(findings);
  inferNano(findings);
  return findings;
}

function summary() {
  const all = inferAll();
  const byZoom = { MAHA: [], MACRO: [], MEZZO: [], MICRO: [], NANO: [] };
  const bySeverity = { HIGH: 0, WARN: 0, INFO: 0 };
  for (const f of all) {
    if (byZoom[f.zoom]) byZoom[f.zoom].push(f);
    if (bySeverity[f.severity] != null) bySeverity[f.severity]++;
  }
  return { findings: all, byZoom, bySeverity, total: all.length };
}

module.exports = { inferAll, summary, inferMaha, inferMacro, inferMezzo, inferMicro, inferNano, THRESHOLDS };
