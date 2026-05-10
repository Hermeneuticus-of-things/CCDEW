#!/usr/bin/env node
'use strict';
/**
 * Python helpers smoke test — verifies every .py file is syntactically valid.
 * Catches incomplete edits / merge conflicts / encoding issues.
 * Skips test if Python is not installed.
 */

const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');
const { findPython } = require('../lib/platform.cjs');

const HELPERS = path.resolve(__dirname, '..');

let pass = 0, fail = 0;
function test(name, fn) {
  try { fn(); console.log(`[PASS] ${name}`); pass++; }
  catch (e) { console.log(`[FAIL] ${name}: ${e.message}`); fail++; }
}

const py = findPython();
if (!py) {
  console.log('[SKIP] Python interpreter not found');
  console.log(`\n=== SUMMARY: 0/0 passed (skipped) ===`);
  process.exit(0);
}

function checkSyntax(file) {
  const r = spawnSync(py, ['-c', `import ast; ast.parse(open(${JSON.stringify(file)}, encoding='utf-8').read())`], {
    encoding: 'utf-8', timeout: 10_000, stdio: ['ignore', 'pipe', 'pipe'],
  });
  if (r.status !== 0) {
    throw new Error('syntax error: ' + (r.stderr || '').trim().slice(0, 200));
  }
}

const pyFiles = fs.readdirSync(HELPERS).filter(f => f.endsWith('.py')).map(f => path.join(HELPERS, f));
if (pyFiles.length === 0) {
  console.log('[SKIP] no Python files');
  process.exit(0);
}
for (const f of pyFiles) {
  test(`syntax: ${path.basename(f)}`, () => checkSyntax(f));
}

console.log(`\n=== SUMMARY: ${pass}/${pass + fail} passed ===`);
process.exit(fail > 0 ? 1 : 0);
