#!/usr/bin/env node
'use strict';
const { redactString, redactObject } = require('../lib/redact.cjs');

let pass = 0, fail = 0;
function test(name, fn) {
  try { fn(); console.log(`[PASS] ${name}`); pass++; }
  catch (e) { console.log(`[FAIL] ${name}: ${e.message}`); fail++; }
}

test('email redacted', () => {
  if (redactString('contact me at john@example.com please') !== 'contact me at <email> please') throw new Error('not redacted');
});

test('AWS key redacted', () => {
  const r = redactString('key=AKIAIOSFODNN7EXAMPLE');
  if (!r.includes('<aws-key>')) throw new Error('aws not redacted: ' + r);
});

test('Anthropic API key redacted', () => {
  const r = redactString('Bearer sk-ant-api03-abcdefghij1234567890XYZ');
  if (!r.includes('<api-key>')) throw new Error('not redacted: ' + r);
});

test('JWT redacted', () => {
  const r = redactString('token: eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkw.SflKxwRJSMeKKF2QT4fwpMeJf36POk');
  if (!r.includes('<jwt>')) throw new Error('jwt not redacted');
});

test('long hex redacted', () => {
  const r = redactString('hash=' + 'a'.repeat(64));
  if (!r.includes('<hex>')) throw new Error('hex not redacted');
});

test('home path replaced with ~', () => {
  const home = process.env.HOME || process.env.USERPROFILE || '';
  if (!home) { console.log('  skip — no HOME'); return; }
  const input = home + '/secrets/file.txt';
  const r = redactString(input);
  if (r.includes(home)) throw new Error('home path leaked: ' + r);
  if (!r.startsWith('~')) throw new Error('not replaced with ~: ' + r);
});

test('redactObject recurses', () => {
  const obj = { user: 'a@b.com', nested: { token: 'sk-ant-1234567890abcdefghij' } };
  const r = redactObject(obj);
  if (r.user !== '<email>') throw new Error('top-level not redacted');
  if (!r.nested.token.includes('<api-key>')) throw new Error('nested not redacted');
});

test('redactObject preserves non-strings', () => {
  const obj = { count: 42, ok: true, items: [1, 2, 3] };
  const r = redactObject(obj);
  if (r.count !== 42 || r.ok !== true || r.items.length !== 3) throw new Error('mutated non-strings');
});

test('redactObject handles null + undefined safely', () => {
  if (redactObject(null) !== null) throw new Error('null mutated');
  if (redactObject(undefined) !== undefined) throw new Error('undefined mutated');
});

test('redactString handles non-strings', () => {
  if (redactString(null) !== null) throw new Error('null');
  if (redactString(123) !== 123) throw new Error('number');
  if (redactString('') !== '') throw new Error('empty');
});

console.log(`\n=== SUMMARY: ${pass}/${pass + fail} passed ===`);
process.exit(fail > 0 ? 1 : 0);
