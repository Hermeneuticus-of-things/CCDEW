#!/usr/bin/env node
'use strict';
/**
 * Cross-Claude session race test — 2 parallel processes write SAFLA outcomes
 * via child_process.fork. Validates atomic-write retry survives concurrent
 * rename across processes (real OS-level race, not in-process).
 */

const fs = require('fs');
const os = require('os');
const path = require('path');
const cp = require('child_process');

const ORIG = process.cwd();
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'cc-race-' + process.pid + '-'));
process.chdir(TMP);

const HELPERS = path.resolve(__dirname, '..');

const worker = `
const { recordOutcome } = require(${JSON.stringify(path.join(HELPERS, 'safla.cjs'))});
const sessionId = process.argv[2];
const count = parseInt(process.argv[3], 10);
for (let i = 0; i < count; i++) recordOutcome((i % 9) + 1, i % 3 === 0, 'race-' + sessionId + '-' + i);
console.log('done');
`;

const workerPath = path.join(TMP, 'race-worker.cjs');
fs.writeFileSync(workerPath, worker, 'utf-8');

let pass = 0, fail = 0;

function runRace() {
  return new Promise((resolve) => {
    const a = cp.fork(workerPath, ['A', '100'], { cwd: TMP, silent: true });
    const b = cp.fork(workerPath, ['B', '100'], { cwd: TMP, silent: true });
    let done = 0, err = null;
    const onExit = (code, label) => {
      if (code !== 0) err = new Error(`${label} exited ${code}`);
      done++;
      if (done === 2) resolve(err);
    };
    a.on('exit', c => onExit(c, 'A'));
    b.on('exit', c => onExit(c, 'B'));
    setTimeout(() => { if (done < 2) resolve(new Error('timeout 30s')); }, 30_000);
  });
}

(async () => {
  const err = await runRace();
  if (err) {
    console.log('[FAIL] race: ' + err.message);
    fail++;
  } else {
    try {
      const data = JSON.parse(fs.readFileSync(path.join(TMP, '.claude-flow', 'data', 'safla.json'), 'utf-8'));
      for (const k of Object.keys(data.nodes)) {
        if (!/^[1-9]$/.test(k)) throw new Error('corrupt key: ' + k);
      }
      if ((data.total_feedbacks || 0) < 150) throw new Error('lost writes: ' + data.total_feedbacks + ' (expected ≥150)');
      const tmps = fs.readdirSync(path.join(TMP, '.claude-flow', 'data')).filter(f => f.endsWith('.tmp'));
      if (tmps.length > 0) throw new Error('tmp orphans: ' + tmps.length);
      console.log(`[PASS] cross-process race: ${data.total_feedbacks} feedbacks survived, no orphans, no corrupt keys`);
      pass++;
    } catch (e) {
      console.log('[FAIL] race verify: ' + e.message);
      fail++;
    }
  }

  process.chdir(ORIG);
  try { fs.rmSync(TMP, { recursive: true, force: true }); } catch {}
  console.log(`\n=== SUMMARY: ${pass}/${pass + fail} passed ===`);
  process.exit(fail > 0 ? 1 : 0);
})();
