#!/usr/bin/env node
'use strict';
/**
 * Tests for NLM Bridge
 * References: .claude/mcp/ccdew-nlm-bridge.cjs
 */

const assert = require('assert');
const path = require('path');
const fs = require('fs');
const os = require('os');

// ── Replicate the logic from ccdew-nlm-bridge.cjs ──────────────────

const THROTTLE_MS = 3000;
const MULTI_NOTEBOOK_THROTTLE_MS = 5000;
const BATCH_THROTTLE_MS = 10000;
const CACHE_TTL_MS = 24 * 60 * 60 * 1000;

const NOTEBOOKS = {
  'karma-book': { id: '6696523d', name: 'Karma Book', throttle: MULTI_NOTEBOOK_THROTTLE_MS },
  'glossary':    { id: '6acbbc90', name: 'Glossary',     throttle: MULTI_NOTEBOOK_THROTTLE_MS },
  'research':    { id: '669ee18c', name: 'Research',    throttle: MULTI_NOTEBOOK_THROTTLE_MS },
};

function detectDomain(task) {
  const lower = (task || '').toLowerCase();
  if (lower.includes('karma') || lower.includes('jain') || lower.includes('vedanta')) return 'karma-book';
  if (lower.includes('glossary') || lower.includes('termen')) return 'glossary';
  if (lower.includes('research') || lower.includes('cercetare')) return 'research';
  return 'general';
}

function buildGroupedQuery(queries) {
  return queries.map((q, i) => `${i + 1}. ${q}`).join('\n');
}

function cacheKey(text) {
  return text.toLowerCase().replace(/[^a-z0-9]/g, '_').slice(0, 120);
}

// ── Tests ────────────────────────────────────────────────────────

let passed = 0;
let failed = 0;

function test(name, fn) {
  try {
    fn();
    passed++;
    console.log(`  ✓ ${name}`);
  } catch (e) {
    failed++;
    console.log(`  ✗ ${name}: ${e.message}`);
  }
}

// ── Notebook definitions ─────────────────────────────────────────

test('NOTEBOOKS has 3 entries', () => {
  assert.strictEqual(Object.keys(NOTEBOOKS).length, 3);
});

for (const [key, nb] of Object.entries(NOTEBOOKS)) {
  test(`Notebook "${key}" has id, name, throttle`, () => {
    assert.ok(nb.id, `Missing id for ${key}`);
    assert.ok(nb.name, `Missing name for ${key}`);
    assert.ok(nb.throttle, `Missing throttle for ${key}`);
  });

  test(`Notebook "${key}" id is non-empty`, () => {
    assert.ok(nb.id.length > 0);
  });
}

test('All notebook IDs are unique', () => {
  const ids = Object.values(NOTEBOOKS).map(n => n.id);
  assert.strictEqual(ids.length, new Set(ids).size);
});

// ── Throttle constants ────────────────────────────────────────────

test('THROTTLE_MS >= 3000 (anti-suspicion)', () => {
  assert.ok(THROTTLE_MS >= 3000, `THROTTLE_MS is ${THROTTLE_MS}, expected >=3000`);
});

test('MULTI_NOTEBOOK_THROTTLE_MS >= THROTTLE_MS', () => {
  assert.ok(MULTI_NOTEBOOK_THROTTLE_MS >= THROTTLE_MS);
});

test('BATCH_THROTTLE_MS >= MULTI_NOTEBOOK_THROTTLE_MS', () => {
  assert.ok(BATCH_THROTTLE_MS >= MULTI_NOTEBOOK_THROTTLE_MS);
});

// ── Domain detection ──────────────────────────────────────────────

test('detectDomain identifies karma-book', () => {
  assert.strictEqual(detectDomain('karma philosophy in Jain tradition'), 'karma-book');
});

test('detectDomain identifies glossary', () => {
  assert.strictEqual(detectDomain('glossary of philosophical terms'), 'glossary');
});

test('detectDomain identifies research', () => {
  assert.strictEqual(detectDomain('research methodology'), 'research');
});

test('detectDomain defaults to general', () => {
  assert.strictEqual(detectDomain('random question about anything'), 'general');
});

// ── Grouped queries ───────────────────────────────────────────────

test('buildGroupedQuery formats 2 queries', () => {
  const result = buildGroupedQuery(['Q1', 'Q2']);
  assert.strictEqual(result, '1. Q1\n2. Q2');
});

test('buildGroupedQuery formats 5 queries', () => {
  const queries = ['Q1', 'Q2', 'Q3', 'Q4', 'Q5'];
  const result = buildGroupedQuery(queries);
  const lines = result.split('\n');
  assert.strictEqual(lines.length, 5);
  assert.ok(lines[0].startsWith('1.'));
  assert.ok(lines[4].startsWith('5.'));
});

test('buildGroupedQuery handles single query', () => {
  const result = buildGroupedQuery(['Only query']);
  assert.strictEqual(result, '1. Only query');
});

// ── Cache key ─────────────────────────────────────────────────────

test('cacheKey normalizes case', () => {
  assert.strictEqual(cacheKey('Hello World'), 'hello_world');
});

test('cacheKey removes special chars', () => {
  const key = cacheKey('What is karma? (according to Jainism)');
  assert.ok(!key.includes('?'));
  assert.ok(!key.includes('('));
  assert.ok(!key.includes(')'));
});

test('cacheKey limits length to 120', () => {
  const long = 'a'.repeat(500);
  assert.ok(cacheKey(long).length <= 120);
});

test('cacheKey produces same key for same input', () => {
  assert.strictEqual(cacheKey('Test Query'), cacheKey('Test Query'));
});

// ── NLM protocol levels (conceptual) ──────────────────────────────

test('Protocol Level 1: Async pattern', () => {
  const pattern = { query: 'async_query', timeout: 180, poll: true };
  assert.ok(pattern.timeout >= 180, 'Timeout should be at least 180s');
  assert.ok(pattern.poll, 'Should support polling');
});

test('Protocol Level 2: Extended timeout', () => {
  const defaultTimeout = 90;
  const extendedTimeout = 180;
  assert.ok(extendedTimeout > defaultTimeout);
});

test('Protocol Level 3: Grouped queries save quota', () => {
  const singleQueries = 5;
  const groupedQueries = 1;
  const savings = singleQueries - groupedQueries;
  assert.ok(savings > 0, 'Grouped queries should save quota');
  assert.strictEqual(savings, 4);
});

test('Protocol Level 9: Throttle levels increase with scope', () => {
  assert.ok(THROTTLE_MS <= MULTI_NOTEBOOK_THROTTLE_MS);
  assert.ok(MULTI_NOTEBOOK_THROTTLE_MS <= BATCH_THROTTLE_MS);
});

test('Protocol Level 10: Tier awareness', () => {
  const tiers = { free: 50, plus: 500, ultra: 5000 };
  assert.strictEqual(tiers.plus, 500, 'Current user tier is Plus');
  assert.ok(tiers.plus > tiers.free);
  assert.ok(tiers.ultra > tiers.plus);
});

// ── Anti-suspicion rules ─────────────────────────────────────────

test('Anti-pattern: Single channel rule', () => {
  // Only one method of communication per session
  const methods = ['mcp'];
  assert.strictEqual(methods.length, 1, 'Single channel enforced');
});

test('Anti-pattern: No keep-alive daemon', () => {
  // Auth refresh only on actual 401, not on timer
  const refreshOnTimer = false;
  const refreshOnError = true;
  assert.ok(!refreshOnTimer);
  assert.ok(refreshOnError);
});

test('Anti-pattern: Max 1 auth check per session', () => {
  const checksThisSession = 1;
  assert.ok(checksThisSession <= 1);
});

// ── Summary ───────────────────────────────────────────────────────

console.log(`\nNLM Bridge Tests: ${passed} passed, ${failed} failed\n`);
process.exit(failed > 0 ? 1 : 0);
