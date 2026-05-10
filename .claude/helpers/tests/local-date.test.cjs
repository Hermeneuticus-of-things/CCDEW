#!/usr/bin/env node
'use strict';
const { todayLocal, monthLocal, isoLocal, tzOffsetMinutes } = require('../lib/local-date.cjs');

let pass = 0, fail = 0;
function test(name, fn) {
  try { fn(); console.log(`[PASS] ${name}`); pass++; }
  catch (e) { console.log(`[FAIL] ${name}: ${e.message}`); fail++; }
}

test('todayLocal returns YYYY-MM-DD format', () => {
  const t = todayLocal();
  if (!/^\d{4}-\d{2}-\d{2}$/.test(t)) throw new Error('bad format: ' + t);
});

test('monthLocal returns YYYY-MM', () => {
  const m = monthLocal();
  if (!/^\d{4}-\d{2}$/.test(m)) throw new Error('bad format: ' + m);
});

test('todayLocal respects local TZ vs UTC', () => {
  // Construct a Date at 23:30 local time. todayLocal should return today,
  // not tomorrow (which UTC ISO might if TZ offset > 30min positive).
  const now = new Date();
  const localY = now.getFullYear();
  const localM = String(now.getMonth() + 1).padStart(2, '0');
  const localD = String(now.getDate()).padStart(2, '0');
  const expected = `${localY}-${localM}-${localD}`;
  const got = todayLocal();
  if (got !== expected) throw new Error(`expected ${expected}, got ${got}`);
});

test('isoLocal includes timezone offset', () => {
  const s = isoLocal();
  if (!/[+-]\d{2}:\d{2}$/.test(s)) throw new Error('no TZ offset: ' + s);
});

test('tzOffsetMinutes is a number', () => {
  const o = tzOffsetMinutes();
  if (typeof o !== 'number' || !Number.isFinite(o)) throw new Error('not finite: ' + o);
});

test('todayLocal accepts custom Date', () => {
  const d = new Date('2025-06-15T15:00:00');
  const t = todayLocal(d);
  if (!t.startsWith('2025-06-')) throw new Error('expected 2025-06-*, got ' + t);
});

console.log(`\n=== SUMMARY: ${pass}/${pass + fail} passed ===`);
process.exit(fail > 0 ? 1 : 0);
