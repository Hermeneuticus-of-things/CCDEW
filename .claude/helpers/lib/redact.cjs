'use strict';
/**
 * PII redaction for logs — minimal but real.
 * Replaces: emails, phone-like numbers, JWT tokens, long hex strings,
 * absolute home paths (preserves the structure).
 */

const PATTERNS = [
  { re: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/g, repl: '<email>' },
  { re: /\b\+?\d[\d\s().-]{7,15}\b/g,                          repl: '<phone?>' },
  { re: /\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b/g, repl: '<jwt>' },
  { re: /\b[a-f0-9]{40,}\b/g,                                  repl: '<hex>' },
  { re: /\bsk-(ant-)?[A-Za-z0-9_-]{20,}\b/g,                   repl: '<api-key>' },
  { re: /\bAKIA[0-9A-Z]{16}\b/g,                               repl: '<aws-key>' },
];

function redactString(s) {
  if (typeof s !== 'string' || s.length === 0) return s;
  let out = s;
  for (const { re, repl } of PATTERNS) out = out.replace(re, repl);
  // Path redaction — replace user-home with ~
  const home = process.env.HOME || process.env.USERPROFILE;
  if (home) out = out.replaceAll(home, '~');
  return out;
}

function redactObject(obj, depth = 0) {
  if (depth > 5) return obj;
  if (obj == null) return obj;
  if (typeof obj === 'string') return redactString(obj);
  if (Array.isArray(obj)) return obj.map(v => redactObject(v, depth + 1));
  if (typeof obj === 'object') {
    const out = {};
    for (const [k, v] of Object.entries(obj)) out[k] = redactObject(v, depth + 1);
    return out;
  }
  return obj;
}

module.exports = { redactString, redactObject, PATTERNS };
