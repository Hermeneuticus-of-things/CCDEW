#!/usr/bin/env node
'use strict';
const { tokensOf, classify, KEYWORDS_HEXAD, KEYWORDS_TRIANGLE } = require('../lib/i18n.cjs');

let pass = 0, fail = 0;
function test(name, fn) {
  try { fn(); console.log(`[PASS] ${name}`); pass++; }
  catch (e) { console.log(`[FAIL] ${name}: ${e.message}`); fail++; }
}

test('tokensOf strips diacritics', () => {
  const t = tokensOf('refactorizează modulul');
  if (!t.includes('refactorizeaza')) throw new Error('diacritics not stripped: ' + t.join(','));
});

test('tokensOf lowercases', () => {
  const t = tokensOf('REFACTOR Module');
  if (!t.includes('refactor') || !t.includes('module')) throw new Error('not lowered');
});

test('classify English "refactor module across 5 files" → hexad', () => {
  const c = classify('refactor module across 5 files');
  if (c.hexad === 0) throw new Error('hexad=0 unexpectedly');
});

test('classify Romanian "refactorizare modul" → hexad', () => {
  const c = classify('refactorizare modul');
  if (c.hexad === 0) throw new Error('RO refactorizare not detected');
});

test('classify English "fix bug" → triangle', () => {
  const c = classify('fix this bug quickly');
  if (c.triangle === 0) throw new Error('triangle=0');
});

test('classify Romanian "fixează bug" → triangle', () => {
  const c = classify('fixeaza bug-ul rapid');
  if (c.triangle === 0) throw new Error('RO fixeaza not detected');
});

test('keywords sets are non-empty', () => {
  if (KEYWORDS_HEXAD.size < 5) throw new Error('hexad too small');
  if (KEYWORDS_TRIANGLE.size < 5) throw new Error('triangle too small');
});

console.log(`\n=== SUMMARY: ${pass}/${pass + fail} passed ===`);
process.exit(fail > 0 ? 1 : 0);
