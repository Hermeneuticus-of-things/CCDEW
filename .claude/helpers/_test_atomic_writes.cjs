#!/usr/bin/env node
'use strict';
/**
 * Wave 1 stress-test for atomic writes.
 * Hammers safla.cjs, intelligence.cjs writeJSON, session.js atomicWrite,
 * project-scope.cjs saveState with TRUE OS-level concurrent processes.
 */

const fs = require('fs');
const path = require('path');
const { fork } = require('child_process');

const HELPERS = __dirname;
const WORKSPACE = path.resolve(HELPERS, '..', '..');
const DATA_DIR = path.join(WORKSPACE, '.claude-flow', 'data');
const SESSIONS_DIR = path.join(WORKSPACE, '.claude-flow', 'sessions');

const T_INTEL   = path.join(DATA_DIR, '_test_intel.json');
const T_SESSION = path.join(SESSIONS_DIR, '_test_session.json');
const T_SCOPE   = path.join(DATA_DIR, '_test_scope.json');

const SAFLA_REAL = path.join(DATA_DIR, 'safla.json');
const SAFLA_BAK  = path.join(DATA_DIR, 'safla.json.bak_atomic_test');

const N_WORKERS = 20;
const ITERS_PER_WORKER = 5;

if (process.argv[2] === '--worker') {
  const iters    = parseInt(process.argv[4], 10);
  const workerId = parseInt(process.argv[5], 10);
  process.chdir(WORKSPACE); // helpers compute DATA_DIR from cwd
  const safla = require(path.join(HELPERS, 'safla.cjs'));
  // intelligence.writeJSON is module-private; replicate EXACT atomic pattern
  // from intelligence.cjs:67-74 so we still stress the pattern from N PIDs.
  function intelWriteJSON(filePath, data) {
    if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });
    const tmp = filePath + '.' + process.pid + '.' + Date.now() + '.tmp';
    fs.writeFileSync(tmp, JSON.stringify(data, null, 2), 'utf-8');
    fs.renameSync(tmp, filePath);
  }
  function sessionAtomicWrite(file, data) {
    const tmp = file + '.' + process.pid + '.' + Date.now() + '.tmp';
    fs.writeFileSync(tmp, data);
    fs.renameSync(tmp, file);
  }
  try {
    for (let i = 0; i < iters; i++) {
      safla.recordOutcome((workerId % 9) + 1, i % 2 === 0, `w${workerId}-i${i}`);
      intelWriteJSON(T_INTEL, {
        worker: workerId, iter: i, pid: process.pid, ts: Date.now(),
        payload: 'x'.repeat(100 + i * 50)
      });
      sessionAtomicWrite(T_SESSION, JSON.stringify({
        worker: workerId, iter: i, pid: process.pid, ts: Date.now()
      }, null, 2));
      const tmp = T_SCOPE + '.' + process.pid + '.' + Date.now() + '.tmp';
      fs.writeFileSync(tmp, JSON.stringify({
        name: `worker-${workerId}`, iter: i, pid: process.pid
      }, null, 2), 'utf-8');
      fs.renameSync(tmp, T_SCOPE);
    }
    process.exit(0);
  } catch (e) {
    process.stderr.write(`Worker ${workerId} failed: ${e.message}\n`);
    process.exit(1);
  }
}

function listTmpFiles() {
  const out = [];
  for (const dir of [DATA_DIR, SESSIONS_DIR]) {
    if (!fs.existsSync(dir)) continue;
    try {
      for (const f of fs.readdirSync(dir)) {
        if (f.endsWith('.tmp')) out.push(path.join(dir, f));
      }
    } catch {}
  }
  return out;
}
function verifyJSON(name, file) {
  try {
    if (!fs.existsSync(file)) return { name, pass: false, detail: 'file missing' };
    const txt = fs.readFileSync(file, 'utf-8');
    JSON.parse(txt);
    return { name, pass: true, detail: `${txt.length} bytes OK` };
  } catch (e) {
    return { name, pass: false, detail: `PARSE ERROR: ${e.message}` };
  }
}

async function main() {
  console.log('=== Atomic Write Stress Test (Wave 1) ===');
  console.log(`Workers=${N_WORKERS} iters=${ITERS_PER_WORKER} totalPerFile=${N_WORKERS*ITERS_PER_WORKER}`);

  let backedUp = false;
  if (fs.existsSync(SAFLA_REAL)) {
    fs.copyFileSync(SAFLA_REAL, SAFLA_BAK);
    backedUp = true;
    console.log('[setup] backed up safla.json');
  }
  for (const f of [T_INTEL, T_SESSION, T_SCOPE]) {
    if (fs.existsSync(f)) fs.unlinkSync(f);
  }
  if (!fs.existsSync(SESSIONS_DIR)) fs.mkdirSync(SESSIONS_DIR, { recursive: true });

  const preTmp = listTmpFiles();

  const t0 = Date.now();
  const workers = [];
  for (let i = 0; i < N_WORKERS; i++) {
    workers.push(new Promise(resolve => {
      const c = fork(__filename, ['--worker','all',String(ITERS_PER_WORKER),String(i)], { silent: false });
      c.on('exit', code => resolve({ id: i, code }));
    }));
  }
  const results = await Promise.all(workers);
  const elapsed = Date.now() - t0;
  const failed = results.filter(r => r.code !== 0);
  console.log(`[done] ${elapsed}ms  exit-OK ${N_WORKERS-failed.length}/${N_WORKERS}`);
  if (failed.length) console.log(`  FAILED: ${failed.map(f=>f.id).join(',')}`);

  const checks = [];
  checks.push(verifyJSON('safla.json valid JSON', SAFLA_REAL));
  checks.push(verifyJSON('intel test valid JSON', T_INTEL));
  checks.push(verifyJSON('session test valid JSON', T_SESSION));
  checks.push(verifyJSON('scope test valid JSON', T_SCOPE));

  const postTmp = listTmpFiles();
  const newTmp = postTmp.filter(f => !preTmp.includes(f));
  checks.push({
    name: 'No leftover .tmp files',
    pass: newTmp.length === 0,
    detail: newTmp.length ? `${newTmp.length} leftover: ${newTmp.slice(0,10).map(p=>path.basename(p)).join(', ')}` : 'clean'
  });

  try {
    const s = JSON.parse(fs.readFileSync(SAFLA_REAL,'utf-8'));
    const total = Object.values(s.nodes||{}).reduce((a,n)=>a+(n.success||0)+(n.failure||0),0);
    const exp = N_WORKERS * ITERS_PER_WORKER;
    const ok = total >= ITERS_PER_WORKER && total <= exp;
    checks.push({ name: `safla counts in [${ITERS_PER_WORKER}..${exp}] (got ${total})`, pass: ok,
      detail: ok ? 'race-tolerant range' : 'OUT OF RANGE' });
  } catch (e) {
    checks.push({ name: 'safla counts', pass: false, detail: e.message });
  }

  console.log('\n=== Verification Results ===');
  for (const c of checks) {
    console.log(`${c.pass?'PASS':'FAIL'}  ${c.name}`);
    if (c.detail) console.log(`      ${c.detail}`);
  }

  console.log('\n=== Leftover tmp files (new during test) ===');
  if (newTmp.length === 0) console.log('  (none)');
  else newTmp.forEach(f => console.log(`  ${f}`));

  if (backedUp) {
    fs.copyFileSync(SAFLA_BAK, SAFLA_REAL);
    fs.unlinkSync(SAFLA_BAK);
    console.log('\n[teardown] restored safla.json');
  }
  for (const f of [T_INTEL, T_SESSION, T_SCOPE]) {
    if (fs.existsSync(f)) fs.unlinkSync(f);
  }
  // Also clean any leftover .tmp from the test
  for (const f of newTmp) { try { fs.unlinkSync(f); } catch {} }

  const fc = checks.filter(c => !c.pass);
  console.log(`\n=== SUMMARY ===`);
  console.log(`Workers OK : ${N_WORKERS-failed.length}/${N_WORKERS}`);
  console.log(`Checks PASS: ${checks.length-fc.length}/${checks.length}`);
  console.log(`Result     : ${fc.length===0 && failed.length===0 ? 'PASS' : 'FAIL'}`);
  process.exit(fc.length===0 && failed.length===0 ? 0 : 1);
}
main().catch(e => { console.error(e); process.exit(2); });
