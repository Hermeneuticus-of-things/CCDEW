#!/usr/bin/env node
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');

const ORIG_CWD = process.cwd();
const TEST_CWD = fs.mkdtempSync(path.join(os.tmpdir(), 'errlog-test-'));
process.chdir(TEST_CWD);

const { logError, readRecent } = require(path.resolve(__dirname, '..', 'lib', 'error-log.cjs'));

let pass = 0, fail = 0;
function test(name, fn) {
  try { fn(); console.log(`[PASS] ${name}`); pass++; }
  catch (e) { console.log(`[FAIL] ${name}: ${e.message}`); fail++; }
}

test('logError persists entry to errors.jsonl', () => {
  logError('test.scope', new Error('synthetic failure'), { foo: 1 });
  const recent = readRecent(5);
  if (recent.length === 0) throw new Error('no entry persisted');
  const last = recent[recent.length - 1];
  if (last.scope !== 'test.scope') throw new Error('scope wrong');
  if (!last.message.includes('synthetic')) throw new Error('message lost');
  if (!last.extra || last.extra.foo !== 1) throw new Error('extra lost');
});

test('logError with non-Error value still persists', () => {
  logError('test.string', 'plain string error');
  const recent = readRecent(5);
  const has = recent.some(e => e.scope === 'test.string' && e.message === 'plain string error');
  if (!has) throw new Error('plain string not logged');
});

test('readRecent returns at most n entries', () => {
  for (let i = 0; i < 10; i++) logError('bulk.test', new Error('bulk-' + i));
  const recent = readRecent(3);
  if (recent.length !== 3) throw new Error(`expected 3, got ${recent.length}`);
});

process.chdir(ORIG_CWD);
try { fs.rmSync(TEST_CWD, { recursive: true, force: true }); } catch {}
console.log(`\n=== SUMMARY: ${pass}/${pass + fail} passed ===`);
process.exit(fail > 0 ? 1 : 0);
