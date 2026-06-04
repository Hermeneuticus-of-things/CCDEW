'use strict';
const fs = require('fs');
const path = require('path');

const LOG_DIR = path.join(process.cwd(), '.claude-flow', 'logs');
const LOG_PATH = path.join(LOG_DIR, 'errors.jsonl');
const MAX_LINES = 5000;

function ensureDir() {
  if (!fs.existsSync(LOG_DIR)) fs.mkdirSync(LOG_DIR, { recursive: true });
}

function logError(scope, error, extra) {
  try {
    ensureDir();
    const { redactString, redactObject } = require('./redact.cjs');
    const entry = {
      ts: new Date().toISOString(),
      scope: String(scope || 'unknown'),
      message: redactString(error && error.message ? String(error.message).slice(0, 500) : String(error || '')),
      code: error && error.code ? String(error.code) : '',
      stack: redactString(error && error.stack ? String(error.stack).split('\n').slice(0, 5).join(' | ').slice(0, 800) : ''),
      extra: extra ? redactObject(JSON.parse(JSON.stringify(extra))) : undefined,
    };
    fs.appendFileSync(LOG_PATH, JSON.stringify(entry) + '\n', 'utf-8');
    rotateIfNeeded();
  } catch { /* logger itself failed — there's nowhere to escalate */ }
}

function rotateIfNeeded() {
  try {
    const stat = fs.statSync(LOG_PATH);
    if (stat.size < 1024 * 1024) return;
    const lines = fs.readFileSync(LOG_PATH, 'utf-8').split('\n');
    if (lines.length <= MAX_LINES) return;
    const trimmed = lines.slice(-MAX_LINES).join('\n');
    fs.writeFileSync(LOG_PATH, trimmed, 'utf-8');
  } catch { /* non-fatal */ }
}

function readRecent(n = 20) {
  try {
    if (!fs.existsSync(LOG_PATH)) return [];
    const lines = fs.readFileSync(LOG_PATH, 'utf-8').trim().split('\n').filter(Boolean);
    return lines.slice(-n).map(l => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean);
  } catch { return []; }
}

module.exports = { logError, readRecent };
