'use strict';
/**
 * UI string map — RO + EN.
 * Default: EN. User can set CCDEW_LANG=ro to flip.
 *
 * Usage:
 *   const { t } = require('./strings.cjs');
 *   console.log(t('audit.no_issues'));
 */

const LANG = (process.env.CCDEW_LANG || 'en').toLowerCase();

const STRINGS = {
  en: {
    'audit.no_issues':       'no issues found',
    'audit.fail_count':      'FAILED checks: {n}',
    'audit.warn_count':      'WARN checks: {n}',
    'optimize.dryrun_label': '(DRY-RUN)',
    'optimize.applied':      '{n} file(s) modified',
    'verify.scope':          'scope:',
    'verify.changed':        'changed files: {n}',
    'verify.summary':        '{pass}/{total} PASS, {fail} FAIL, {skip} SKIP',
    'codeburn.unavailable':  'codeburn CLI unavailable — install: npm install -g codeburn',
    'codeburn.alert':        'ALERT',
    'codeburn.warn':         'WARN',
    'codeburn.ok':           'OK',
    'safla.no_data':         'no feedback recorded yet',
    'instinct.suggested':    'you usually route this to node {n} ({pct}% confidence)',
    'mcp.misconfigured':     'MISCONFIGURED (likely prints help and exits)',
  },
  ro: {
    'audit.no_issues':       'fără probleme',
    'audit.fail_count':      'verificări FAILED: {n}',
    'audit.warn_count':      'verificări WARN: {n}',
    'optimize.dryrun_label': '(DRY-RUN — neaplicat)',
    'optimize.applied':      '{n} fișier(e) modificate',
    'verify.scope':          'scope:',
    'verify.changed':        'fișiere modificate: {n}',
    'verify.summary':        '{pass}/{total} PASS, {fail} FAIL, {skip} SKIP',
    'codeburn.unavailable':  'codeburn CLI indisponibil — instalează: npm install -g codeburn',
    'codeburn.alert':        'ALERTĂ',
    'codeburn.warn':         'AVERTIZARE',
    'codeburn.ok':           'OK',
    'safla.no_data':         'încă fără feedback înregistrat',
    'instinct.suggested':    'rutezi de obicei la nodul {n} ({pct}% încredere)',
    'mcp.misconfigured':     'CONFIGURARE GREȘITĂ (probabil afișează help și iese)',
  },
};

function t(key, vars = {}) {
  const dict = STRINGS[LANG] || STRINGS.en;
  let s = dict[key] || STRINGS.en[key] || key;
  for (const [k, v] of Object.entries(vars)) {
    s = s.replaceAll(`{${k}}`, String(v));
  }
  return s;
}

function setLang(lang) {
  if (STRINGS[lang]) process.env.CCDEW_LANG = lang;
}

function currentLang() { return LANG; }

module.exports = { t, setLang, currentLang, STRINGS };
