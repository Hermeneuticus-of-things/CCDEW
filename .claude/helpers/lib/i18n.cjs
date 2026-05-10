'use strict';
/**
 * Multi-language routing keywords — RO + EN at minimum.
 * Used by hook-handler.cjs::selectWorkflow to pick hexad vs triangle.
 *
 * Add new languages by extending KEYWORDS_HEXAD / KEYWORDS_TRIANGLE.
 */

const KEYWORDS_HEXAD = new Set([
  // English
  'refactor', 'audit', 'review', 'architect', 'design', 'analyze', 'investigate',
  'integrate', 'orchestrate', 'cross', 'multi', 'complex',
  // Romanian
  'refactorizare', 'refactorizez', 'auditeaza', 'audita', 'auditezi',
  'arhitectura', 'analiza', 'analizeaza', 'investigheaza',
  'integreaza', 'orchestreaza', 'multi-fisier', 'multi-modul',
]);

const KEYWORDS_TRIANGLE = new Set([
  // English
  'fix', 'bug', 'patch', 'tweak', 'small', 'quick', 'simple',
  'add', 'rename', 'typo',
  // Romanian
  'fix', 'fixeaza', 'repara', 'repari', 'reparare',
  'modifica', 'modific', 'modificare',
  'adauga', 'adaug', 'adaug',
  'redenumeste', 'redenumire', 'simplu',
]);

function tokensOf(text) {
  if (!text) return [];
  return text.toLowerCase()
    .normalize('NFD').replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9 -]/g, ' ')
    .split(/\s+/)
    .filter(Boolean);
}

function classify(text) {
  const t = tokensOf(text);
  let hexad = 0, triangle = 0;
  for (const w of t) {
    if (KEYWORDS_HEXAD.has(w)) hexad++;
    if (KEYWORDS_TRIANGLE.has(w)) triangle++;
  }
  return { hexad, triangle };
}

module.exports = { KEYWORDS_HEXAD, KEYWORDS_TRIANGLE, tokensOf, classify };
