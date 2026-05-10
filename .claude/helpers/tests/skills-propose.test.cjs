#!/usr/bin/env node
'use strict';
const fs = require('fs');
const os = require('os');
const path = require('path');

const ORIG = process.cwd();
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'sp-' + process.pid + '-'));
process.chdir(TMP);

delete require.cache[require.resolve('../lib/skills-propose.cjs')];
const sp = require('../lib/skills-propose.cjs');

let pass = 0, fail = 0;
function test(name, fn) {
  try { fn(); console.log(`[PASS] ${name}`); pass++; }
  catch (e) { console.log(`[FAIL] ${name}: ${e.message}`); fail++; }
}

test('filterMature drops repos under 10 stars', () => {
  const fake = [
    { full_name: 'x/a', stargazers_count: 5,  license: { key: 'mit' }, pushed_at: new Date().toISOString() },
    { full_name: 'x/b', stargazers_count: 50, license: { key: 'mit' }, pushed_at: new Date().toISOString() },
  ];
  const r = sp.filterMature(fake);
  if (r.length !== 1) throw new Error('expected 1 mature, got ' + r.length);
  if (r[0].full_name !== 'x/b') throw new Error('wrong filter');
});

test('filterMature drops archived + disabled', () => {
  const fake = [
    { full_name: 'x/a', stargazers_count: 100, archived: true,  license: { key: 'mit' }, pushed_at: new Date().toISOString() },
    { full_name: 'x/b', stargazers_count: 100, disabled: true,  license: { key: 'mit' }, pushed_at: new Date().toISOString() },
    { full_name: 'x/c', stargazers_count: 100,                  license: { key: 'mit' }, pushed_at: new Date().toISOString() },
  ];
  if (sp.filterMature(fake).length !== 1) throw new Error('archived/disabled not filtered');
});

test('filterMature drops repos with disallowed license (GPL/proprietary)', () => {
  const fake = [
    { full_name: 'x/a', stargazers_count: 100, license: { key: 'gpl-3.0' }, pushed_at: new Date().toISOString() },
    { full_name: 'x/b', stargazers_count: 100, license: { key: 'mit' },     pushed_at: new Date().toISOString() },
  ];
  const r = sp.filterMature(fake);
  if (r.length !== 1 || r[0].full_name !== 'x/b') throw new Error('license filter broken');
});

test('filterMature drops stale repos (no push >365d)', () => {
  const oldDate = new Date(Date.now() - 400 * 24 * 60 * 60 * 1000).toISOString();
  const fake = [
    { full_name: 'x/old',  stargazers_count: 100, license: { key: 'mit' }, pushed_at: oldDate },
    { full_name: 'x/new',  stargazers_count: 100, license: { key: 'mit' }, pushed_at: new Date().toISOString() },
  ];
  const r = sp.filterMature(fake);
  if (r.length !== 1 || r[0].full_name !== 'x/new') throw new Error('staleness not filtered');
});

test('summarize keeps only public-safe fields', () => {
  const repo = {
    full_name: 'foo/bar',
    stargazers_count: 42, forks_count: 7,
    license: { spdx_id: 'MIT' },
    description: 'cool tool',
    pushed_at: '2025-01-01T00:00:00Z',
    html_url: 'https://github.com/foo/bar',
    topics: ['ai', 'agent', 'cli'],
    language: 'JavaScript',
  };
  const s = sp.summarize(repo);
  if (s.name !== 'foo/bar' || s.stars !== 42) throw new Error('shape broken');
  if (typeof s.description !== 'string') throw new Error('desc missing');
});

test('summarize redacts PII from description (email)', () => {
  const repo = {
    full_name: 'foo/bar', stargazers_count: 100, html_url: 'https://github.com/foo/bar',
    description: 'contact: alice@example.com for support',
  };
  const s = sp.summarize(repo);
  if (s.description.includes('alice@example.com')) throw new Error('email leaked');
});

test('generateScaffold creates SKILL.md with frontmatter', () => {
  const cand = {
    name: 'fake/upstream',
    stars: 100, license: 'MIT',
    description: 'sample tool',
    url: 'https://github.com/fake/upstream',
    topics: ['cli', 'tool'],
  };
  const r = sp.generateScaffold(cand, 'sample-skill', 'gap test');
  if (!fs.existsSync(r.file)) throw new Error('SKILL.md not created');
  const c = fs.readFileSync(r.file, 'utf-8');
  if (!c.includes('inspired_by: fake/upstream')) throw new Error('frontmatter missing');
  if (!c.includes('triggers:')) throw new Error('triggers missing');
});

test('generateScaffold rejects invalid local name', () => {
  let caught = null;
  try {
    sp.generateScaffold({ name: 'a/b', stars: 1, url: 'x' }, 'bad name with spaces!', 'gap');
  } catch (e) { caught = e; }
  if (!caught) throw new Error('did not reject');
});

test('generateScaffold refuses to overwrite existing skill', () => {
  const cand = { name: 'fake/two', stars: 50, url: 'x', license: 'MIT', topics: [] };
  sp.generateScaffold(cand, 'dup-skill', 'first');
  let caught = null;
  try { sp.generateScaffold(cand, 'dup-skill', 'second'); } catch (e) { caught = e; }
  if (!caught) throw new Error('overwrite not blocked');
});

test('propose() rejects empty keyword', async () => {
  let caught = null;
  try { await sp.propose(''); } catch (e) { caught = e; }
  if (!caught) throw new Error('empty keyword accepted');
});

test('fromInferFindings extracts skill-related gaps', () => {
  const fake = [
    { zoom: 'MAHA', msg: 'Only 5 test suite(s) — below 50 expected' },
    { zoom: 'MAHA', msg: 'Skill coverage missing for X' },
    { zoom: 'NANO', msg: 'trailing whitespace' },
  ];
  const r = sp.fromInferFindings(fake);
  if (r.length !== 1) throw new Error(`expected 1 gap, got ${r.length}`);
});

process.chdir(ORIG);
try { fs.rmSync(TMP, { recursive: true, force: true }); } catch {}
console.log(`\n=== SUMMARY: ${pass}/${pass + fail} passed ===`);
process.exit(fail > 0 ? 1 : 0);
