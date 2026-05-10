#!/usr/bin/env node
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');

const ORIG = process.cwd();
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'lock-' + process.pid + '-'));
process.chdir(TMP);

const { acquire, release, withLock, lockPathFor } = require('../lib/file-lock.cjs');

let pass = 0, fail = 0;
function test(name, fn) {
  try { fn(); console.log(`[PASS] ${name}`); pass++; }
  catch (e) { console.log(`[FAIL] ${name}: ${e.message}`); fail++; }
}

test('acquire creates .lock file', () => {
  const target = path.join(TMP, 'a.json');
  const h = acquire(target);
  if (!fs.existsSync(h.lockPath)) throw new Error('lock not created');
  release(h);
});

test('release removes .lock file', () => {
  const target = path.join(TMP, 'b.json');
  const h = acquire(target);
  release(h);
  if (fs.existsSync(h.lockPath)) throw new Error('lock not released');
});

test('acquire while held → timeout', () => {
  const target = path.join(TMP, 'c.json');
  const h1 = acquire(target);
  let caught = null;
  try { acquire(target, { timeoutMs: 100 }); }
  catch (e) { caught = e; }
  release(h1);
  if (!caught) throw new Error('did not timeout');
  if (caught.code !== 'ELOCK_TIMEOUT') throw new Error('wrong code: ' + caught.code);
});

test('withLock runs function and releases', () => {
  const target = path.join(TMP, 'd.json');
  let ran = false;
  const r = withLock(target, () => { ran = true; return 42; });
  if (!ran) throw new Error('fn not called');
  if (r !== 42) throw new Error('return value lost');
  if (fs.existsSync(lockPathFor(target))) throw new Error('lock not released after withLock');
});

test('withLock releases even on throw', () => {
  const target = path.join(TMP, 'e.json');
  let caught = null;
  try { withLock(target, () => { throw new Error('boom'); }); }
  catch (e) { caught = e; }
  if (!caught) throw new Error('did not propagate');
  if (fs.existsSync(lockPathFor(target))) throw new Error('lock leaked on throw');
});

test('stale lock (>30s) gets auto-cleaned', () => {
  const target = path.join(TMP, 'f.json');
  const lockPath = lockPathFor(target);
  fs.writeFileSync(lockPath, '{}', 'utf-8');
  const oldTime = new Date(Date.now() - 60_000);
  fs.utimesSync(lockPath, oldTime, oldTime);
  const h = acquire(target, { timeoutMs: 1000 });
  release(h);
});

process.chdir(ORIG);
try { fs.rmSync(TMP, { recursive: true, force: true }); } catch {}
console.log(`\n=== SUMMARY: ${pass}/${pass + fail} passed ===`);
process.exit(fail > 0 ? 1 : 0);
