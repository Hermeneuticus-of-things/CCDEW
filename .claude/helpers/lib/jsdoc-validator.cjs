'use strict';
/**
 * JSDoc validator — checks that public exports of a module have JSDoc with @param + @returns.
 * Not a full TS replacement, but catches the "exported function with zero docs" case.
 */

const fs = require('fs');
const path = require('path');

function findExports(content) {
  const m = content.match(/module\.exports\s*=\s*\{([\s\S]*?)\}/);
  if (!m) return [];
  return m[1].split(',').map(s => s.trim().split(':')[0].trim()).filter(s => /^[a-zA-Z_$][\w$]*$/.test(s));
}

function findFunctionDef(content, name) {
  const patterns = [
    new RegExp(`(?:^|\\n)((?:[\\t ]*\\/\\*\\*[\\s\\S]*?\\*\\/\\s*)?)(?:async\\s+)?function\\s+${name}\\s*\\(`, 'm'),
    new RegExp(`(?:^|\\n)((?:[\\t ]*\\/\\*\\*[\\s\\S]*?\\*\\/\\s*)?)(?:const|let|var)\\s+${name}\\s*=`, 'm'),
  ];
  for (const re of patterns) {
    const m = content.match(re);
    if (m) return { matched: true, jsdoc: (m[1] || '').trim() };
  }
  return { matched: false };
}

function validateFile(filePath) {
  const c = fs.readFileSync(filePath, 'utf-8');
  const exports = findExports(c);
  const issues = [];
  for (const name of exports) {
    const def = findFunctionDef(c, name);
    if (!def.matched) continue; // re-export or not a function
    if (!def.jsdoc.startsWith('/**')) {
      issues.push({ name, missing: 'jsdoc' });
      continue;
    }
    const hasParam = /@param\s/.test(def.jsdoc);
    const hasReturns = /@returns?\s/.test(def.jsdoc);
    const sigArgs = (c.match(new RegExp(`function\\s+${name}\\s*\\(([^)]*)\\)`)) || [, ''])[1].trim();
    const argCount = sigArgs ? sigArgs.split(',').length : 0;
    if (argCount > 0 && !hasParam) issues.push({ name, missing: '@param' });
    if (!hasReturns && argCount > 0) issues.push({ name, missing: '@returns' });
  }
  return { file: filePath, exports: exports.length, issues };
}

function validateDir(dir, opts = {}) {
  const out = [];
  if (!fs.existsSync(dir)) return out;
  for (const f of fs.readdirSync(dir)) {
    const full = path.join(dir, f);
    const stat = fs.statSync(full);
    if (stat.isDirectory() && f !== 'tests' && !f.startsWith('.')) {
      out.push(...validateDir(full, opts));
    } else if (/\.cjs$/.test(f) && !f.endsWith('.test.cjs')) {
      try { out.push(validateFile(full)); } catch (e) { /* skip */ }
    }
  }
  return out;
}

module.exports = { validateFile, validateDir, findExports };
