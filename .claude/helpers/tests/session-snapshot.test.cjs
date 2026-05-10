#!/usr/bin/env node
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');

const ORIG = process.cwd();
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'snap-' + process.pid + '-'));
process.chdir(TMP);

delete require.cache[require.resolve('../lib/session-snapshot.cjs')];
const ss = require('../lib/session-snapshot.cjs');

let pass = 0, fail = 0;
function test(name, fn) {
  try { fn(); console.log(`[PASS] ${name}`); pass++; }
  catch (e) { console.log(`[FAIL] ${name}: ${e.message}`); fail++; }
}

test('snapshot creates file with v1.0 schema', () => {
  const r = ss.snapshot({ note: 'unit-test' });
  if (!fs.existsSync(r.file)) throw new Error('file not created');
  if (r.snapshot.version !== '1.0') throw new Error('schema version: ' + r.snapshot.version);
});

test('snapshot includes all top-level keys', () => {
  const r = ss.snapshot();
  const required = ['version', 'session_id', 'ended_at', 'cost', 'safla', 'instincts', 'skills', 'perf', 'audit', 'errors', 'workspace'];
  for (const k of required) {
    if (!(k in r.snapshot)) throw new Error('missing key: ' + k);
  }
});

test('snapshot computes duration when startedAt provided', () => {
  const startedAt = new Date(Date.now() - 60_000).toISOString();
  const r = ss.snapshot({ startedAt });
  if (!r.snapshot.duration_sec || r.snapshot.duration_sec < 50 || r.snapshot.duration_sec > 70) {
    throw new Error('duration off: ' + r.snapshot.duration_sec);
  }
});

test('snapshot.note carries through', () => {
  const r = ss.snapshot({ note: 'audit complete' });
  if (r.snapshot.note !== 'audit complete') throw new Error('note lost');
});

test('listSessions returns chronological order', () => {
  ss.snapshot({ note: 'first' });
  ss.snapshot({ note: 'second' });
  ss.snapshot({ note: 'third' });
  const list = ss.listSessions();
  if (list.length < 3) throw new Error(`expected ≥3, got ${list.length}`);
  // Files are sorted alphabetically (timestamp-prefixed) — should be chronological
  for (let i = 1; i < list.length; i++) {
    if (list[i] < list[i - 1]) throw new Error('not sorted');
  }
});

test('compare requires ≥2 sessions', () => {
  // TMP is fresh but we just snapshot 3, so this should pass
  const r = ss.compare(5);
  if (r.error) throw new Error('compare failed: ' + r.error);
  if (!Array.isArray(r.rows)) throw new Error('rows not array');
  if (r.rows.length < 5) throw new Error('expected ≥5 metric rows, got ' + r.rows.length);
});

test('compare exposes per-session value arrays', () => {
  const r = ss.compare(3);
  for (const row of r.rows) {
    if (!Array.isArray(row.values)) throw new Error('values not array for ' + row.metric);
    if (row.values.length !== r.sessions.length) throw new Error('value count mismatch');
  }
});

test('snapshot.workspace counts modules + tests', () => {
  const r = ss.snapshot();
  // In TMP we have no .claude/helpers, so workspace stays at 0 — that's expected
  if (typeof r.snapshot.workspace.loc !== 'number') throw new Error('loc not number');
  if (typeof r.snapshot.workspace.modules !== 'number') throw new Error('modules not number');
});

process.chdir(ORIG);
try { fs.rmSync(TMP, { recursive: true, force: true }); } catch {}
console.log(`\n=== SUMMARY: ${pass}/${pass + fail} passed ===`);
process.exit(fail > 0 ? 1 : 0);
