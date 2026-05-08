#!/usr/bin/env node
/**
 * Wave 4 graceful-degradation test.
 */
const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '../..');
const HANDLER = path.join(__dirname, 'hook-handler.cjs');
const DATA = path.join(ROOT, '.claude-flow', 'data');
const PROJECTS = path.join(ROOT, 'PROJECTS');
const MEMORY = path.join(ROOT, '_MEMORY');

const results = [];
function record(name, ok, observed) {
  results.push({ name, result: ok ? 'PASS' : 'FAIL', observed });
}
const NODE_BIN = process.execPath;
const SAFE_PATH = '/usr/bin:/bin';
function runHook(args, env = {}) {
  return spawnSync(NODE_BIN, [HANDLER, ...args], {
    cwd: ROOT, env: { ...process.env, ...env },
    encoding: 'utf8', timeout: 30000,
  });
}
function backupFile(p) {
  if (fs.existsSync(p)) { const bak = p + '.test-bak'; fs.copyFileSync(p, bak); return bak; }
  return null;
}
function restoreFile(p, bak) {
  if (bak && fs.existsSync(bak)) { fs.copyFileSync(bak, p); fs.unlinkSync(bak); }
}

// 1: codeburn CLI missing
try {
  const r1 = runHook(['route'], { PATH: SAFE_PATH, PROMPT: 'route this user authentication request' });
  const r2 = runHook(['post-edit', 'test.txt']);
  const r3 = runHook(['session-end']);
  record('1.codeburn-missing', r1.status === 0 && r2.status === 0 && r3.status === 0,
    `route=${r1.status} edit=${r2.status} end=${r3.status}`);
} catch (e) { record('1.codeburn-missing', false, e.message); }

// 2: No PROJECTS/
{
  const saved = PROJECTS + '-saved-test'; let renamed = false;
  try {
    if (fs.existsSync(PROJECTS)) { fs.renameSync(PROJECTS, saved); renamed = true; }
    const r1 = runHook(['inject-workflow'], { PROMPT: 'test' });
    const r2 = runHook(['scope-status']);
    record('2.no-PROJECTS', r1.status === 0 && r2.status === 0,
      `inject=${r1.status} scope=${r2.status}`);
  } catch (e) { record('2.no-PROJECTS', false, e.message); }
  finally { if (renamed && fs.existsSync(saved)) fs.renameSync(saved, PROJECTS); }
}

// 3: No _MEMORY/
{
  const saved = MEMORY + '-saved-test'; let renamed = false;
  try {
    if (fs.existsSync(MEMORY)) { fs.renameSync(MEMORY, saved); renamed = true; }
    const r = runHook(['session-restore']);
    record('3.no-_MEMORY', r.status === 0, `session-restore=${r.status}`);
  } catch (e) { record('3.no-_MEMORY', false, e.message); }
  finally { if (renamed && fs.existsSync(saved)) fs.renameSync(saved, MEMORY); }
}

// 4: No .claude-flow/data/
{
  const saved = DATA + '-saved-test'; let renamed = false;
  try {
    if (fs.existsSync(DATA)) { fs.renameSync(DATA, saved); renamed = true; }
    const r1 = runHook(['post-task', 'test-task']);
    const r2 = runHook(['stats']);
    const recreated = fs.existsSync(DATA);
    record('4.no-data-dir', r1.status === 0 && r2.status === 0,
      `post-task=${r1.status} stats=${r2.status} recreated=${recreated}`);
  } catch (e) { record('4.no-data-dir', false, e.message); }
  finally {
    if (renamed && fs.existsSync(saved)) {
      if (fs.existsSync(DATA)) {
        for (const f of fs.readdirSync(saved)) {
          const src = path.join(saved, f); const dst = path.join(DATA, f);
          if (!fs.existsSync(dst)) fs.renameSync(src, dst);
        }
        fs.rmSync(saved, { recursive: true, force: true });
      } else { fs.renameSync(saved, DATA); }
    }
  }
}

// 5: Corrupt safla.json
{
  const f = path.join(DATA, 'safla.json'); const bak = backupFile(f);
  try {
    fs.mkdirSync(DATA, { recursive: true });
    fs.writeFileSync(f, '{not json');
    const r = runHook(['post-task'], { PROMPT: 'fix the broken authentication flow today' });
    let valid = false;
    try { JSON.parse(fs.readFileSync(f, 'utf8')); valid = true; } catch {}
    record('5.corrupt-safla', r.status === 0 && valid,
      `exit=${r.status} json-valid=${valid}`);
  } catch (e) { record('5.corrupt-safla', false, e.message); }
  finally { restoreFile(f, bak); }
}

// 6: Corrupt session-critical-index.json
{
  const f = path.join(DATA, 'session-critical-index.json'); const bak = backupFile(f);
  try {
    fs.mkdirSync(DATA, { recursive: true });
    fs.writeFileSync(f, 'garbage-not-json{{{');
    const r = runHook(['inject-workflow'], { PROMPT: 'test' });
    record('6.corrupt-ssa-index', r.status === 0, `exit=${r.status}`);
  } catch (e) { record('6.corrupt-ssa-index', false, e.message); }
  finally { restoreFile(f, bak); }
}

// 7: Python3 missing
try {
  const r = runHook(['session-restore'], { PATH: '/var/empty-no-python' });
  record('7.no-python3', r.status === 0, `session-restore=${r.status}`);
} catch (e) { record('7.no-python3', false, e.message); }

// 8: Read-only fs
{
  let chmodded = false;
  try {
    if (fs.existsSync(DATA)) { fs.chmodSync(DATA, 0o555); chmodded = true; }
    const r = runHook(['post-task', 'readonly-test']);
    record('8.readonly-fs', r.status === 0, `post-task=${r.status}`);
  } catch (e) { record('8.readonly-fs', false, e.message); }
  finally { if (chmodded) { try { fs.chmodSync(DATA, 0o755); } catch {} } }
}

console.log('\n=== Wave 4 Graceful Degradation Report ===');
console.log('Scenario | Result | Observed');
for (const r of results) console.log(`${r.name} | ${r.result} | ${r.observed}`);
const failed = results.filter(r => r.result === 'FAIL').length;
console.log(`\nTotal: ${results.length}  Passed: ${results.length - failed}  Failed: ${failed}`);
process.exit(failed > 0 ? 1 : 0);
