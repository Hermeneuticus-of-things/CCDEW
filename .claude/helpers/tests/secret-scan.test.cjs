#!/usr/bin/env node
'use strict';
const { check } = require('../secret-scan.cjs');

let pass = 0, fail = 0;
function test(name, fn) {
  try { fn(); console.log(`[PASS] ${name}`); pass++; }
  catch (e) { console.log(`[FAIL] ${name}: ${e.message}`); fail++; }
}

test('clean file passes', () => {
  const r = check({ filePath: 'src/index.js', content: 'console.log("hi");' });
  if (!r.safe) throw new Error('expected safe, got: ' + r.reason);
});

test('AWS access key blocked', () => {
  const r = check({ filePath: 'src/x.js', content: 'const k = "AKIAIOSFODNN7EXAMPLE";' });
  if (r.safe) throw new Error('expected blocked');
  if (!r.reason.includes('AWS')) throw new Error('wrong reason: ' + r.reason);
});

test('Anthropic API key blocked', () => {
  const r = check({ filePath: 'config.js', content: 'API="sk-ant-api03-abcdefghij1234567890XYZ"' });
  if (r.safe) throw new Error('expected blocked');
  if (!r.reason.includes('Anthropic')) throw new Error('wrong: ' + r.reason);
});

test('Private RSA key blocked', () => {
  const r = check({ filePath: 'a.txt', content: '-----BEGIN RSA PRIVATE KEY-----\nMIIE...' });
  if (r.safe) throw new Error('expected blocked');
  if (!r.reason.includes('Private Key')) throw new Error('wrong: ' + r.reason);
});

test('.env path flagged even with empty content', () => {
  const r = check({ filePath: '.env', content: '' });
  if (r.safe) throw new Error('expected blocked');
  if (!r.reason.includes('sensitive filename')) throw new Error('wrong: ' + r.reason);
});

test('id_rsa path flagged', () => {
  const r = check({ filePath: '/home/user/.ssh/id_rsa', content: 'irrelevant' });
  if (r.safe) throw new Error('expected blocked');
});

test('GitHub PAT blocked', () => {
  const r = check({ filePath: 'x.js', content: 'token: "ghp_abcdefghij1234567890ABCDEFGHIJ123456"' });
  if (r.safe) throw new Error('expected blocked');
  if (!r.reason.includes('GitHub')) throw new Error('wrong: ' + r.reason);
});

test('regular password word does not false-positive (no value)', () => {
  const r = check({ filePath: 'README.md', content: '# How to set your password.' });
  if (!r.safe) throw new Error('false positive on docs: ' + r.reason);
});

console.log(`\n=== SUMMARY: ${pass}/${pass + fail} passed ===`);
process.exit(fail > 0 ? 1 : 0);
