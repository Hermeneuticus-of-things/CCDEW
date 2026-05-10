#!/usr/bin/env node
'use strict';
const { migrate, isCurrentVersion } = require('../lib/migrate.cjs');

let pass = 0, fail = 0;
function test(name, fn) {
  try { fn(); console.log(`[PASS] ${name}`); pass++; }
  catch (e) { console.log(`[FAIL] ${name}: ${e.message}`); fail++; }
}

test('migrate from 1.0 → 2.0 applies single step', () => {
  const data = { version: '1.0', count: 5 };
  const steps = [
    { from: '1.0', to: '2.0', up: d => ({ ...d, version: '2.0', count_x2: d.count * 2 }) },
  ];
  const out = migrate(data, 'test', steps);
  if (out.version !== '2.0') throw new Error('version not bumped');
  if (out.count_x2 !== 10) throw new Error('up() not called');
});

test('migrate chains multiple steps', () => {
  const data = { version: '1.0', x: 1 };
  const steps = [
    { from: '1.0', to: '2.0', up: d => ({ ...d, version: '2.0', x: d.x + 1 }) },
    { from: '2.0', to: '3.0', up: d => ({ ...d, version: '3.0', x: d.x * 10 }) },
  ];
  const out = migrate(data, 'chain', steps);
  if (out.version !== '3.0') throw new Error('not at 3.0: ' + out.version);
  if (out.x !== 20) throw new Error('expected (1+1)*10=20, got ' + out.x);
});

test('migrate stops if no step matches', () => {
  const data = { version: '5.0', x: 1 };
  const steps = [{ from: '1.0', to: '2.0', up: d => d }];
  const out = migrate(data, 'no-match', steps);
  if (out.version !== '5.0') throw new Error('changed when no match');
});

test('migrate handles missing version (treats as 0.0)', () => {
  const data = { x: 1 };
  const steps = [{ from: '0.0', to: '1.0', up: d => ({ ...d, version: '1.0' }) }];
  const out = migrate(data, 'fresh', steps);
  if (out.version !== '1.0') throw new Error('did not migrate from missing version');
});

test('isCurrentVersion checks correctly', () => {
  if (!isCurrentVersion({ version: '2.0' }, '2.0')) throw new Error('false neg');
  if (isCurrentVersion({ version: '1.0' }, '2.0')) throw new Error('false pos');
  if (isCurrentVersion(null, '2.0')) throw new Error('null pos');
});

test('migrate returns data unchanged for non-object', () => {
  if (migrate(null, 't', []) !== null) throw new Error('null mutated');
  if (migrate('str', 't', []) !== 'str') throw new Error('string mutated');
});

console.log(`\n=== SUMMARY: ${pass}/${pass + fail} passed ===`);
process.exit(fail > 0 ? 1 : 0);
