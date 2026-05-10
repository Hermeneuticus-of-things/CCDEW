#!/usr/bin/env node
'use strict';
const { t, setLang, currentLang, STRINGS } = require('../lib/strings.cjs');

let pass = 0, fail = 0;
function test(name, fn) {
  try { fn(); console.log(`[PASS] ${name}`); pass++; }
  catch (e) { console.log(`[FAIL] ${name}: ${e.message}`); fail++; }
}

test('t() returns string for known key', () => {
  if (typeof t('audit.no_issues') !== 'string') throw new Error('not a string');
});

test('t() interpolates {var}', () => {
  const r = t('audit.fail_count', { n: 3 });
  if (!r.includes('3')) throw new Error('not interpolated: ' + r);
});

test('t() falls back to EN if RO missing', () => {
  setLang('ro');
  const r = t('audit.no_issues');
  if (!r) throw new Error('empty for ro');
  setLang('en');
});

test('STRINGS has both en and ro', () => {
  if (!STRINGS.en) throw new Error('no en dict');
  if (!STRINGS.ro) throw new Error('no ro dict');
});

test('t() returns key as fallback if missing', () => {
  const r = t('totally.nonexistent.key');
  if (r !== 'totally.nonexistent.key') throw new Error('fallback failed: ' + r);
});

test('Romanian dict has key parity with English', () => {
  for (const k of Object.keys(STRINGS.en)) {
    if (!(k in STRINGS.ro)) throw new Error(`missing RO key: ${k}`);
  }
});

console.log(`\n=== SUMMARY: ${pass}/${pass + fail} passed ===`);
process.exit(fail > 0 ? 1 : 0);
