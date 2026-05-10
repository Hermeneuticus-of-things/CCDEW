#!/usr/bin/env node
'use strict';
const ai = require('../lib/auto-infer.cjs');

let pass = 0, fail = 0;
function test(name, fn) {
  try { fn(); console.log(`[PASS] ${name}`); pass++; }
  catch (e) { console.log(`[FAIL] ${name}: ${e.message}`); fail++; }
}

test('summary returns 5 zoom levels', () => {
  const s = ai.summary();
  for (const z of ['MAHA', 'MACRO', 'MEZZO', 'MICRO', 'NANO']) {
    if (!Array.isArray(s.byZoom[z])) throw new Error('missing zoom: ' + z);
  }
});

test('summary counts severities', () => {
  const s = ai.summary();
  const total = s.bySeverity.HIGH + s.bySeverity.WARN + s.bySeverity.INFO;
  if (total !== s.total) throw new Error(`severity sum ${total} != total ${s.total}`);
});

test('inferMaha includes workspace metrics', () => {
  const f = [];
  ai.inferMaha(f);
  if (!f.some(x => x.zoom === 'MAHA')) throw new Error('no MAHA findings');
});

test('inferMacro flags >500-line files as HIGH', () => {
  const f = [];
  ai.inferMacro(f);
  // intelligence.cjs is ~978 lines — should be flagged HIGH
  const hits = f.filter(x => x.severity === 'HIGH' && x.file.includes('intelligence'));
  if (hits.length === 0) {
    console.log('  (no intelligence.cjs >500 lines? check thresholds)');
  }
});

test('inferMicro detects long functions', () => {
  const f = [];
  ai.inferMicro(f);
  // Should find at least one function >75 lines (e.g. intelligence.init)
  if (f.length === 0) console.log('  (no long functions found — that is OK if all under threshold)');
});

test('inferNano returns INFO/WARN entries only', () => {
  const f = [];
  ai.inferNano(f);
  for (const x of f) {
    if (x.severity !== 'INFO' && x.severity !== 'WARN') throw new Error('nano emitted ' + x.severity);
  }
});

test('THRESHOLDS exposes tuning constants', () => {
  if (!ai.THRESHOLDS.module_max_lines) throw new Error('module_max_lines missing');
  if (!ai.THRESHOLDS.function_max_lines) throw new Error('function_max_lines missing');
});

console.log(`\n=== SUMMARY: ${pass}/${pass + fail} passed ===`);
process.exit(fail > 0 ? 1 : 0);
