#!/usr/bin/env node
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');
const engine = require('../lib/codeburn-engine.cjs');

let pass = 0, fail = 0;
function test(name, fn) {
  try { fn(); console.log(`[PASS] ${name}`); pass++; }
  catch (e) { console.log(`[FAIL] ${name}: ${e.message}`); fail++; }
}

test('modelTier maps families correctly', () => {
  if (engine.modelTier('claude-opus-4-7') !== 'opus') throw new Error('opus map');
  if (engine.modelTier('claude-sonnet-4-6') !== 'sonnet') throw new Error('sonnet map');
  if (engine.modelTier('claude-haiku-4-5-20251001') !== 'haiku') throw new Error('haiku map');
  if (engine.modelTier(null) !== 'sonnet') throw new Error('null fallback');
  if (engine.modelTier('') !== 'sonnet') throw new Error('empty fallback');
});

test('costForLine returns null for non-usage lines', () => {
  const r = engine.costForLine('{"type":"queue-operation","content":"x"}');
  if (r !== null) throw new Error('expected null for non-usage line');
});

test('costForLine returns null for invalid JSON', () => {
  const r = engine.costForLine('{not json');
  if (r !== null) throw new Error('expected null for invalid JSON');
});

test('costForLine computes cost for opus message', () => {
  const line = JSON.stringify({
    timestamp: '2026-05-10T08:00:00Z',
    message: {
      model: 'claude-opus-4-7',
      usage: { input_tokens: 1000, output_tokens: 500, cache_creation_input_tokens: 0, cache_read_input_tokens: 0 },
    },
  });
  const r = engine.costForLine(line);
  if (!r) throw new Error('expected cost result');
  // 1000 * 15/1M = $0.015 input, 500 * 75/1M = $0.0375 output → $0.0525 total
  const expected = (1000 * 15 + 500 * 75) / 1e6;
  if (Math.abs(r.cost - expected) > 0.0001) {
    throw new Error(`expected $${expected.toFixed(4)}, got $${r.cost.toFixed(4)}`);
  }
});

test('costForLine includes cache costs', () => {
  const line = JSON.stringify({
    timestamp: '2026-05-10T08:00:00Z',
    message: {
      model: 'claude-sonnet-4-6',
      usage: { input_tokens: 0, output_tokens: 0, cache_creation_input_tokens: 1000, cache_read_input_tokens: 1000 },
    },
  });
  const r = engine.costForLine(line);
  // sonnet input $3/M; cache_create 1.25x = $3.75/M; cache_read 0.1x = $0.30/M
  // 1000 * 3.75 + 1000 * 0.30 / 1M = $0.00405
  const expected = (1000 * 3 * 1.25 + 1000 * 3 * 0.10) / 1e6;
  if (Math.abs(r.cost - expected) > 0.0001) {
    throw new Error(`expected $${expected.toFixed(5)}, got $${r.cost.toFixed(5)}`);
  }
});

test('totals() returns numeric fields with correct shape', () => {
  const t = engine.totals();
  if (typeof t.today_cost !== 'number') throw new Error('today_cost not number');
  if (typeof t.today_calls !== 'number') throw new Error('today_calls not number');
  if (typeof t.month_cost !== 'number') throw new Error('month_cost not number');
  if (typeof t.month_calls !== 'number') throw new Error('month_calls not number');
  if (t.source !== 'native') throw new Error(`source=${t.source}`);
  if (t.today_cost < 0 || t.month_cost < 0) throw new Error('negative cost');
});

test('totals() with synthetic date in past returns 0/0', () => {
  const t = engine.totals({ today: '1970-01-01', month: '1970-01' });
  if (t.today_calls !== 0) throw new Error(`expected 0 calls, got ${t.today_calls}`);
  if (t.month_calls !== 0) throw new Error(`expected 0 month calls, got ${t.month_calls}`);
});

test('isAvailable returns true when ~/.claude/projects exists', () => {
  if (!engine.isAvailable()) throw new Error('expected true on this system');
});

console.log(`\n=== SUMMARY: ${pass}/${pass + fail} passed ===`);
process.exit(fail > 0 ? 1 : 0);
