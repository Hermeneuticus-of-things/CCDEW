#!/usr/bin/env node
'use strict';
/**
 * Regression test for safla.cjs validation.
 * Bug fixed in v3.0: recordOutcome accepted any nodeId and silently
 * created corrupt keys like "[object Object]". Now validates with
 * lib/validate.isValidNodeId regex ^[1-9]$.
 */

const fs = require('fs');
const path = require('path');

const ORIG_CWD = process.cwd();
const TEST_CWD = fs.mkdtempSync(path.join(require('os').tmpdir(), 'safla-test-' + process.pid + '-'));
process.chdir(TEST_CWD);

// Need a feature-flags.json with safla=true so recordOutcome doesn't no-op
const helpersDir = path.resolve(__dirname, '..');
const flagsPath = path.join(helpersDir, 'feature-flags.json');
const flags = JSON.parse(fs.readFileSync(flagsPath, 'utf-8'));
if (!flags.components.safla) {
  console.log('[SKIP] safla disabled in feature-flags.json');
  process.exit(0);
}

// Force fresh module load — ignoring cache from prior test runs
const saflaPath = require.resolve('../safla.cjs');
delete require.cache[saflaPath];
const safla = require('../safla.cjs');
const SAFLA_PATH = path.join(TEST_CWD, '.claude-flow', 'data', 'safla.json');

let pass = 0, fail = 0;
function test(name, fn) {
  try { fn(); console.log(`[PASS] ${name}`); pass++; }
  catch (e) { console.log(`[FAIL] ${name}: ${e.message}`); fail++; }
}

test('recordOutcome(3, true, "task") creates node 3', () => {
  safla.recordOutcome(3, true, 'unit-test-node3');
  const data = JSON.parse(fs.readFileSync(SAFLA_PATH, 'utf-8'));
  if (!data.nodes['3']) throw new Error('node 3 not created');
  if (data.nodes['3'].success !== 1) throw new Error(`success=${data.nodes['3'].success}`);
});

test('recordOutcome({node:3,...}) (object) is REJECTED, no [object Object] key', () => {
  safla.recordOutcome({ node: 3, success: true }, true, 'should-be-rejected');
  const data = JSON.parse(fs.readFileSync(SAFLA_PATH, 'utf-8'));
  if (data.nodes['[object Object]']) throw new Error('corrupt key created!');
  if (Object.keys(data.nodes).some(k => !/^[1-9]$/.test(k))) {
    throw new Error('non-validated key found: ' + Object.keys(data.nodes).join(','));
  }
});

test('recordOutcome(0, ...) (out of range) is REJECTED', () => {
  safla.recordOutcome(0, true, 'should-be-rejected');
  const data = JSON.parse(fs.readFileSync(SAFLA_PATH, 'utf-8'));
  if (data.nodes['0']) throw new Error('node 0 incorrectly accepted');
});

test('recordOutcome(10, ...) (out of range) is REJECTED', () => {
  safla.recordOutcome(10, true, 'should-be-rejected');
  const data = JSON.parse(fs.readFileSync(SAFLA_PATH, 'utf-8'));
  if (data.nodes['10']) throw new Error('node 10 incorrectly accepted');
});

test('recordOutcome("foo", ...) (non-numeric) is REJECTED', () => {
  safla.recordOutcome('foo', true, 'should-be-rejected');
  const data = JSON.parse(fs.readFileSync(SAFLA_PATH, 'utf-8'));
  if (data.nodes['foo']) throw new Error('non-numeric key incorrectly accepted');
});

test('weight_adj clamped to [-0.5, +0.5] under heavy success', () => {
  for (let i = 0; i < 50; i++) safla.recordOutcome(7, true, `clamp-test-${i}`);
  const data = JSON.parse(fs.readFileSync(SAFLA_PATH, 'utf-8'));
  const adj = data.nodes['7'].weight_adj;
  if (adj > 0.5 || adj < -0.5) throw new Error(`clamp failed: ${adj}`);
});

test('stats() returns only valid node keys', () => {
  const s = safla.stats();
  for (const k of Object.keys(s.nodes)) {
    if (!/^[1-9]$/.test(k)) throw new Error(`stats returned invalid key: ${k}`);
  }
});

// cleanup
process.chdir(ORIG_CWD);
try { fs.rmSync(TEST_CWD, { recursive: true, force: true }); } catch {}
console.log(`\n=== SUMMARY: ${pass}/${pass + fail} passed ===`);
process.exit(fail > 0 ? 1 : 0);
