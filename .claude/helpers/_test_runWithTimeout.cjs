// Standalone test for runWithTimeout (copy from hook-handler.cjs:128-156)
const INTELLIGENCE_TIMEOUT_MS = 200;

function runWithTimeout(fn, label) {
  return new Promise((resolve) => {
    let settled = false;
    const timer = setTimeout(() => {
      if (settled) return;
      settled = true;
      process.stderr.write("[WARN] " + label + " timed out after " + INTELLIGENCE_TIMEOUT_MS + "ms, skipping\n");
      resolve(null);
    }, INTELLIGENCE_TIMEOUT_MS);
    Promise.resolve()
      .then(() => fn())
      .then((result) => {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        resolve(result);
      })
      .catch(() => {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        resolve(null);
      });
  });
}

let unhandled = 0;
process.on('unhandledRejection', (r) => { unhandled++; console.log('[UNHANDLED]', r); });

const results = [];
function record(name, pass, duration, detail) {
  results.push({ name, pass, duration, detail });
  const tag = pass ? '[PASS]' : '[FAIL]';
  console.log(`${tag} ${name} (${duration}ms)${detail ? ' -- ' + detail : ''}`);
}

async function runTest(name, minMs, maxMs, fn, valueCheck) {
  const t0 = Date.now();
  let value, err;
  try { value = await fn(); } catch (e) { err = e; }
  const dt = Date.now() - t0;
  let pass = true, detail = '';
  if (err) { pass = false; detail = `threw: ${err.message}`; }
  if (dt < minMs || dt > maxMs) { pass = false; detail = `duration ${dt}ms outside [${minMs},${maxMs}]`; }
  if (pass && valueCheck) {
    const v = valueCheck(value);
    if (v !== true) { pass = false; detail = `value mismatch: ${v} (got ${JSON.stringify(value)})`; }
  }
  record(name, pass, dt, detail);
}

(async () => {
  await runTest('1. sync returns 42', 0, 50,
    () => runWithTimeout(() => 42, 'sync'),
    (v) => v === 42 ? true : 'expected 42');

  await runTest('2. sync throws -> null', 0, 50,
    () => runWithTimeout(() => { throw new Error('boom'); }, 'sync-throw'),
    (v) => v === null ? true : 'expected null');

  await runTest('3. async resolves quick', 0, 50,
    () => runWithTimeout(() => Promise.resolve('quick'), 'async-quick'),
    (v) => v === 'quick' ? true : "expected 'quick'");

  await runTest('4. async rejects -> null', 0, 50,
    () => runWithTimeout(() => Promise.reject(new Error('x')), 'async-rej'),
    (v) => v === null ? true : 'expected null');

  await runTest('5. async hangs -> timeout ~200ms (CRITICAL)', 180, 260,
    () => runWithTimeout(() => new Promise(() => {}), 'hang'),
    (v) => v === null ? true : 'expected null on timeout');

  // 6. Late resolve must not corrupt the already-settled outcome
  {
    const t0 = Date.now();
    const lateValue = await runWithTimeout(() => new Promise(r => setTimeout(() => r('late'), 400)), 'late');
    const dt = Date.now() - t0;
    const pass = lateValue === null && dt >= 180 && dt <= 260;
    record('6a. late resolve -> null at ~200ms', pass, dt,
      pass ? '' : `got value=${JSON.stringify(lateValue)} dt=${dt}`);
    await new Promise(r => setTimeout(r, 300)); // wait past late resolve
    record('6b. no unhandled rejection after late resolve', unhandled === 0, 0,
      unhandled === 0 ? '' : `unhandled=${unhandled}`);
  }

  await runTest('7. async 195ms (just under timeout)', 180, 260,
    () => runWithTimeout(() => new Promise(r => setTimeout(() => r('ok'), 195)), 'tight'),
    (v) => v === 'ok' ? true : `expected 'ok'`);

  const passed = results.filter(r => r.pass).length;
  const total = results.length;
  console.log(`\n=== SUMMARY: ${passed}/${total} passed ===`);
  if (passed !== total) {
    console.log('Failures:');
    results.filter(r => !r.pass).forEach(r => console.log(`  - ${r.name}: ${r.detail}`));
    process.exit(1);
  }
})();
