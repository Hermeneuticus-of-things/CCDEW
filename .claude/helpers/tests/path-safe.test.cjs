#!/usr/bin/env node
'use strict';
const { isSafeBinaryPath, assertSafeBinaryPath } = require('../lib/path-safe.cjs');

let pass = 0, fail = 0;
function test(name, fn) {
  try { fn(); console.log(`[PASS] ${name}`); pass++; }
  catch (e) { console.log(`[FAIL] ${name}: ${e.message}`); fail++; }
}

test('safe Windows path passes', () => {
  if (!isSafeBinaryPath('C:\\nodejs\\node.exe')) throw new Error('windows path rejected');
});

test('safe POSIX path passes', () => {
  if (!isSafeBinaryPath('/usr/local/bin/codeburn')) throw new Error('posix path rejected');
});

test('safe relative path passes', () => {
  if (!isSafeBinaryPath('./helpers/codeburn.cmd')) throw new Error('relative rejected');
});

test('rejects shell metachar &', () => {
  if (isSafeBinaryPath('C:\\evil & calc.exe')) throw new Error('& accepted');
});

test('rejects pipe |', () => {
  if (isSafeBinaryPath('codeburn | rm -rf /')) throw new Error('pipe accepted');
});

test('rejects $(cmd)', () => {
  if (isSafeBinaryPath('codeburn$(rm -rf)')) throw new Error('subshell accepted');
});

test('rejects backtick', () => {
  if (isSafeBinaryPath('codeburn`rm`')) throw new Error('backtick accepted');
});

test('rejects newlines', () => {
  if (isSafeBinaryPath('codeburn\nrm -rf /')) throw new Error('newline accepted');
});

test('rejects empty / null', () => {
  if (isSafeBinaryPath('')) throw new Error('empty accepted');
  if (isSafeBinaryPath(null)) throw new Error('null accepted');
  if (isSafeBinaryPath(undefined)) throw new Error('undefined accepted');
});

test('assertSafeBinaryPath throws with EUNSAFE_PATH code', () => {
  let caught = null;
  try { assertSafeBinaryPath('evil & calc.exe'); } catch (e) { caught = e; }
  if (!caught) throw new Error('did not throw');
  if (caught.code !== 'EUNSAFE_PATH') throw new Error('wrong code: ' + caught.code);
});

console.log(`\n=== SUMMARY: ${pass}/${pass + fail} passed ===`);
process.exit(fail > 0 ? 1 : 0);
