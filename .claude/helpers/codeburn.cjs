'use strict';
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const { writeAtomicJson } = require('./lib/atomic-write.cjs');
const { isEnabled } = require('./lib/flags.cjs');
const { findExecutable } = require('./lib/platform.cjs');
const nativeEngine = require('./lib/codeburn-engine.cjs');

const DATA_DIR   = path.join(process.cwd(), '.claude-flow', 'data');
const CACHE_PATH = path.join(DATA_DIR, 'codeburn-cache.json');
const CACHE_TTL_MS = 60_000;

let resolvedBin = null;
let resolveAttempted = false;

function getBin() {
  if (resolveAttempted) return resolvedBin;
  resolveAttempted = true;
  resolvedBin = findExecutable('codeburn');
  return resolvedBin;
}

function isAvailable() { return getBin() !== null || nativeEngine.isAvailable(); }

function ensureDataDir() {
  if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });
}

function fetchRealStatus() {
  const bin = getBin();
  if (!bin) return null;
  try {
    const { isSafeBinaryPath } = require('./lib/path-safe.cjs');
    if (!isSafeBinaryPath(bin)) {
      try { require('./lib/error-log.cjs').logError('codeburn.unsafe_path', new Error('shell metachar in bin path'), { bin }); } catch {}
      return null;
    }
    const isWinScript = /\.(cmd|bat)$/i.test(bin);
    const raw = execFileSync(bin, ['status'], {
      encoding: 'utf-8', timeout: 5000,
      stdio: ['ignore', 'pipe', 'ignore'],
      shell: isWinScript,
    });
    const todayMatch = raw.match(/Today\s+\$([0-9.]+)\s+(\d+)\s+calls/);
    const monthMatch = raw.match(/Month\s+\$([0-9.]+)\s+(\d+)\s+calls/);
    if (!todayMatch) return null;
    const result = {
      version:     '1.0',
      today_cost:  parseFloat(todayMatch[1]),
      today_calls: parseInt(todayMatch[2], 10),
      month_cost:  monthMatch ? parseFloat(monthMatch[1]) : 0,
      month_calls: monthMatch ? parseInt(monthMatch[2], 10) : 0,
      source: 'real',
      ts: new Date().toISOString(),
    };
    ensureDataDir();
    try { writeAtomicJson(CACHE_PATH, result); } catch { /* non-fatal */ }
    return result;
  } catch { return null; }
}

function readCache() {
  try {
    if (!fs.existsSync(CACHE_PATH)) return null;
    const cached = JSON.parse(fs.readFileSync(CACHE_PATH, 'utf-8'));
    const age = Date.now() - new Date(cached.ts).getTime();
    if (age > CACHE_TTL_MS) return null;
    return cached;
  } catch { return null; }
}

function fetchNativeStatus() {
  try {
    if (!nativeEngine.isAvailable()) return null;
    const t = nativeEngine.totals();
    ensureDataDir();
    try { writeAtomicJson(CACHE_PATH, t); } catch { /* non-fatal */ }
    return t;
  } catch { return null; }
}

function totals(opts = {}) {
  if (!isEnabled('codeburn')) {
    return { today_cost: 0, today_calls: 0, month_cost: 0, month_calls: 0, source: 'disabled' };
  }
  if (!opts.fresh) {
    const c = readCache();
    if (c) return c;
  }
  // Prefer external CLI (faster + canonical pricing); fall back to native engine.
  const real = fetchRealStatus();
  if (real) return real;
  const native = fetchNativeStatus();
  if (native) return native;
  return { today_cost: 0, today_calls: 0, month_cost: 0, month_calls: 0, source: 'unavailable' };
}

function statusLine() {
  const t = totals();
  if (t.source === 'unavailable') return '🔥 BURN n/a (codeburn CLI not installed)';
  if (t.source === 'disabled')    return '';
  const flag = (t.today_calls > 0 && t.today_cost / t.today_calls > 0.05) ? ' ⚠' : '';
  return `🔥 $${t.today_cost.toFixed(2)} today | $${t.month_cost.toFixed(2)} month | ${t.today_calls} calls${flag}`;
}

module.exports = { totals, statusLine, isAvailable };
