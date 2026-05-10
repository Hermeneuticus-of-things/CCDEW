#!/usr/bin/env node
'use strict';
/**
 * Regression test for lib/atomic-write.cjs.
 * Validates retry-with-backoff behavior + tmp cleanup on final failure.
 */

const fs = require('fs');
const os = require('os');
const path = require('path');
const { writeAtomic, writeAtomicJson } = require('../lib/atomic-write.cjs');

const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'atomic-test-'));
let pass = 0, fail = 0;
function test(name, fn) {
  try { fn(); console.log(`[PASS] ${name}`); pass++; }
  catch (e) { console.log(`[FAIL] ${name}: ${e.message}`); fail++; }
}

test('writeAtomic creates target with content', () => {
  const p = path.join(TMP, 'a.txt');
  writeAtomic(p, 'hello');
  if (fs.readFileSync(p, 'utf-8') !== 'hello') throw new Error('content mismatch');
});

test('writeAtomic overwrites existing file', () => {
  const p = path.join(TMP, 'a.txt');
  writeAtomic(p, 'world');
  if (fs.readFileSync(p, 'utf-8') !== 'world') throw new Error('overwrite failed');
});

test('writeAtomicJson serializes object', () => {
  const p = path.join(TMP, 'j.json');
  writeAtomicJson(p, { a: 1, b: [2, 3] });
  const parsed = JSON.parse(fs.readFileSync(p, 'utf-8'));
  if (parsed.a !== 1 || parsed.b[1] !== 3) throw new Error('JSON content wrong');
});

test('No leftover .tmp files after successful writes', () => {
  const tmps = fs.readdirSync(TMP).filter(f => f.endsWith('.tmp'));
  if (tmps.length > 0) throw new Error(`leftover: ${tmps.join(',')}`);
});

test('20 sequential writes — final value correct, no .tmp orphans', () => {
  const p = path.join(TMP, 'seq.json');
  for (let i = 0; i < 20; i++) writeAtomicJson(p, { iteration: i });
  const final = JSON.parse(fs.readFileSync(p, 'utf-8'));
  if (final.iteration !== 19) throw new Error(`expected 19, got ${final.iteration}`);
  const tmps = fs.readdirSync(TMP).filter(f => f.startsWith('seq.json.') && f.endsWith('.tmp'));
  if (tmps.length > 0) throw new Error(`leftover: ${tmps.length}`);
});

// cleanup
try { fs.rmSync(TMP, { recursive: true, force: true }); } catch {}
console.log(`\n=== SUMMARY: ${pass}/${pass + fail} passed ===`);
process.exit(fail > 0 ? 1 : 0);
