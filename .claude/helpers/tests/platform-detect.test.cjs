#!/usr/bin/env node
'use strict';
/**
 * Regression test for findExecutable() on Windows.
 * Bug fixed in v3.0: `where codeburn` returns 2 lines on Windows
 * (script-without-extension + .cmd). Old code took line[0] -> ENOENT
 * because Node's execFileSync can't run no-extension files on Win.
 *
 * Test passes on any platform; on Windows specifically validates that
 * findExecutable picks .cmd|.exe|.bat over the bare-name fallback.
 */

const path = require('path');
const { findExecutable, IS_WIN } = require('../lib/platform.cjs');
const { execFileSync } = require('child_process');

let pass = 0, fail = 0;
function test(name, fn) {
  try { fn(); console.log(`[PASS] ${name}`); pass++; }
  catch (e) { console.log(`[FAIL] ${name}: ${e.message}`); fail++; }
}

test('findExecutable("node") returns a path that execFileSync can run', () => {
  const p = findExecutable('node');
  if (!p) throw new Error('node not found on PATH');
  if (IS_WIN && !/\.(cmd|exe|bat)$/i.test(p)) {
    throw new Error(`Win: expected .cmd/.exe/.bat extension, got: ${p}`);
  }
  const out = execFileSync(p, ['-e', 'process.stdout.write("ok")'], {
    encoding: 'utf-8', timeout: 5000, stdio: ['ignore', 'pipe', 'ignore'],
  });
  if (out !== 'ok') throw new Error(`expected "ok", got "${out}"`);
});

test('findExecutable("nonexistent-binary-xyz123") returns null', () => {
  const p = findExecutable('nonexistent-binary-xyz123');
  if (p !== null) throw new Error(`expected null, got: ${p}`);
});

test('findExecutable("npm") returns a runnable path', () => {
  const p = findExecutable('npm');
  if (!p) throw new Error('npm not found on PATH');
  if (IS_WIN && !/\.(cmd|exe|bat)$/i.test(p)) {
    throw new Error(`Win: expected .cmd ext, got: ${p}`);
  }
});

if (IS_WIN) {
  test('Win: where output may have multiple lines, .cmd is chosen', () => {
    const { execSync } = require('child_process');
    let lines;
    try {
      lines = execSync('where node', { encoding: 'utf-8', timeout: 2000, stdio: ['ignore', 'pipe', 'ignore'] })
        .trim().split(/\r?\n/).filter(Boolean);
    } catch { lines = []; }
    if (lines.length === 0) throw new Error('where node returned nothing');
    const p = findExecutable('node');
    if (!p) throw new Error('findExecutable returned null');
    if (lines.length > 1 && !/\.(cmd|exe|bat)$/i.test(p)) {
      throw new Error(`expected ext-suffixed path on multi-line where output, got: ${p}`);
    }
  });
}

console.log(`\n=== SUMMARY: ${pass}/${pass + fail} passed ===`);
process.exit(fail > 0 ? 1 : 0);
