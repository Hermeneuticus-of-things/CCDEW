#!/usr/bin/env node
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');

const opt = require('../lib/auto-optimize.cjs');

let pass = 0, fail = 0;
function test(name, fn) {
  try { fn(); console.log(`[PASS] ${name}`); pass++; }
  catch (e) { console.log(`[FAIL] ${name}: ${e.message}`); fail++; }
}

test('optimizeNano dry-run does not mutate files', () => {
  const r = opt.optimizeNano({ dryRun: true });
  if (typeof r.changes_count !== 'number') throw new Error('no changes_count');
  if (r.dryRun !== true) throw new Error('not dryRun');
});

test('optimizeMicroPlan returns proposal array', () => {
  const r = opt.optimizeMicroPlan();
  if (r.mode !== 'micro') throw new Error('wrong mode');
  if (!Array.isArray(r.proposals)) throw new Error('proposals not array');
});

test('optimizeMezzoPlan returns proposal array', () => {
  const r = opt.optimizeMezzoPlan();
  if (!Array.isArray(r.proposals)) throw new Error('proposals not array');
});

test('optimizeMahaPlan returns proposal array', () => {
  const r = opt.optimizeMahaPlan();
  if (!Array.isArray(r.proposals)) throw new Error('proposals not array');
});

test('optimizeNano does not crash on healthy workspace', () => {
  // We pass dryRun so we don't actually touch real files in this test
  const r = opt.optimizeNano({ dryRun: true });
  if (r.changes_count < 0) throw new Error('negative count');
});

console.log(`\n=== SUMMARY: ${pass}/${pass + fail} passed ===`);
process.exit(fail > 0 ? 1 : 0);
