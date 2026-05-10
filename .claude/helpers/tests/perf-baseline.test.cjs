#!/usr/bin/env node
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');

const ORIG = process.cwd();
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'perf-' + process.pid + '-'));
process.chdir(TMP);

delete require.cache[require.resolve('../lib/perf-baseline.cjs')];
const perf = require('../lib/perf-baseline.cjs');

let pass = 0, fail = 0;
function test(name, fn) {
  try { fn(); console.log(`[PASS] ${name}`); pass++; }
  catch (e) { console.log(`[FAIL] ${name}: ${e.message}`); fail++; }
}

test('record() returns regression=false on first sample', () => {
  const r = perf.record('test.metric', 10);
  if (r.regression) throw new Error('false positive on first sample');
});

test('record() builds baseline after 10 samples', () => {
  for (let i = 0; i < 10; i++) perf.record('build.test', 5 + Math.random());
  const s = perf.summary();
  if (!s['build.test']) throw new Error('not in summary');
  if (s['build.test'].baseline_p95_ms === null) throw new Error('baseline not set after 10 samples');
});

test('record() flags regression when current >> baseline', () => {
  for (let i = 0; i < 15; i++) perf.record('reg.test', 5);
  const r = perf.record('reg.test', 100); // 20× baseline
  if (!r.regression) throw new Error('did not flag regression');
  if (!r.delta_pct || r.delta_pct < 100) throw new Error('delta_pct too low: ' + r.delta_pct);
});

test('record() rolling window keeps last 30 samples', () => {
  for (let i = 0; i < 50; i++) perf.record('window.test', i);
  const data = JSON.parse(fs.readFileSync(path.join('.claude-flow', 'data', 'perf-baseline.json'), 'utf-8'));
  if (data.metrics['window.test'].samples.length !== 30) throw new Error('window broken: ' + data.metrics['window.test'].samples.length);
});

test('record() rejects non-finite values', () => {
  if (perf.record('bad', NaN) !== null) throw new Error('NaN accepted');
  if (perf.record('bad', -1) !== null) throw new Error('negative accepted');
  if (perf.record('bad', Infinity) !== null) throw new Error('Inf accepted');
});

test('summary() returns all tracked metrics', () => {
  const s = perf.summary();
  if (!s['test.metric']) throw new Error('test.metric missing');
  if (!s['build.test']) throw new Error('build.test missing');
});

process.chdir(ORIG);
try { fs.rmSync(TMP, { recursive: true, force: true }); } catch {}
console.log(`\n=== SUMMARY: ${pass}/${pass + fail} passed ===`);
process.exit(fail > 0 ? 1 : 0);
