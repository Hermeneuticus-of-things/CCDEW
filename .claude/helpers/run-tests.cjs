#!/usr/bin/env node
'use strict';
/**
 * Test runner — runs every *.test.cjs in tests/ and reports cumulative pass/fail.
 * Used by `npm test`.
 */

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const TESTS_DIR = path.join(__dirname, 'tests');
if (!fs.existsSync(TESTS_DIR)) {
  console.log('[RUN-TESTS] no tests/ dir');
  process.exit(0);
}

const tests = fs.readdirSync(TESTS_DIR).filter(f => f.endsWith('.test.cjs')).sort();
console.log(`[RUN-TESTS] ${tests.length} suite(s) found\n`);

let totalPass = 0, totalFail = 0;
const failures = [];

for (const t of tests) {
  const file = path.join(TESTS_DIR, t);
  process.stdout.write(`▶ ${t.padEnd(35)} `);
  const r = spawnSync(process.execPath, [file], {
    encoding: 'utf-8', timeout: 60_000, stdio: ['ignore', 'pipe', 'pipe'],
  });
  const out = (r.stdout || '') + (r.stderr || '');
  const m = out.match(/SUMMARY:\s*(\d+)\/(\d+)\s*passed/i);
  if (m) {
    const passed = parseInt(m[1], 10);
    const total = parseInt(m[2], 10);
    totalPass += passed;
    totalFail += (total - passed);
    if (passed === total) {
      console.log(`✓ ${passed}/${total}`);
    } else {
      console.log(`✗ ${passed}/${total}`);
      failures.push({ test: t, output: out });
    }
  } else if (r.status === 0) {
    console.log('· (no SUMMARY tag)');
  } else {
    console.log(`✗ exit=${r.status}`);
    totalFail++;
    failures.push({ test: t, output: out.slice(-500) });
  }
}

console.log('');
console.log(`Total: ${totalPass} pass, ${totalFail} fail`);
if (failures.length > 0) {
  console.log('\n=== Failure details ===');
  for (const f of failures) {
    console.log(`\n--- ${f.test} ---`);
    console.log(f.output.slice(-500));
  }
}
process.exit(totalFail > 0 ? 1 : 0);
