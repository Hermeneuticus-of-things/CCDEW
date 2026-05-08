'use strict';
/**
 * CodeBurn — integrare cu pachetul real codeburn@0.9.7 (getagentseal)
 * Citește date reale din ~/.claude/projects/ via CLI `codeburn status`
 * Fallback: estimare locală dacă CLI-ul nu e disponibil.
 */

const fs                       = require('fs');
const path                     = require('path');
const { execSync, execFileSync } = require('child_process');

const FLAGS_PATH = path.join(__dirname, 'feature-flags.json');
const DATA_DIR   = path.join(process.cwd(), '.claude-flow', 'data');
const CACHE_PATH = path.join(DATA_DIR, 'codeburn-cache.json');

// Calea CLI detectată la instalare
const CODEBURN_BIN = (() => {
  const home = process.env.HOME || process.env.USERPROFILE || '';
  const candidates = [
    path.join(home, '.npm-global', 'bin', 'codeburn'),
    path.join(home, '.local', 'bin', 'codeburn'),
    '/usr/local/bin/codeburn',
    '/usr/bin/codeburn',
  ];
  for (const c of candidates) {
    if (fs.existsSync(c)) return c;
  }
  try {
    return execSync('which codeburn', { encoding: 'utf-8', timeout: 2000 }).trim();
  } catch { return null; }
})();

function loadFlags() {
  try { return JSON.parse(fs.readFileSync(FLAGS_PATH, 'utf-8')); } catch { return {}; }
}

function ensureDataDir() {
  if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });
}

// ── Real codeburn CLI calls ──────────────────────────────────────────────────

/**
 * Rulează `codeburn status` și parsează output-ul.
 * Returnează { today_cost, month_cost, today_calls, month_calls } sau null.
 */
function fetchRealStatus() {
  if (!CODEBURN_BIN) return null;
  try {
    // execFileSync with array args — no shell, immune to path-injection if
    // CODEBURN_BIN ever contains spaces or shell metacharacters.
    const raw = execFileSync(CODEBURN_BIN, ['status'], { encoding: 'utf-8', timeout: 5000, stdio: ['ignore', 'pipe', 'ignore'] });
    // Format: "  Today  $3.35  101 calls    Month  $230.37  2153 calls"
    const todayMatch = raw.match(/Today\s+\$([0-9.]+)\s+(\d+)\s+calls/);
    const monthMatch = raw.match(/Month\s+\$([0-9.]+)\s+(\d+)\s+calls/);
    if (!todayMatch) return null;
    const result = {
      today_cost:   parseFloat(todayMatch[1]),
      today_calls:  parseInt(todayMatch[2]),
      month_cost:   monthMatch ? parseFloat(monthMatch[1]) : 0,
      month_calls:  monthMatch ? parseInt(monthMatch[2])   : 0,
      source:       'real',
      ts:           new Date().toISOString(),
    };
    // Cache pentru statusline (evită exec la fiecare render)
    ensureDataDir();
    fs.writeFileSync(CACHE_PATH, JSON.stringify(result, null, 2), 'utf-8');
    return result;
  } catch { return null; }
}

/**
 * Citește cache-ul (maxim 60s vechi) pentru apeluri frecvente (statusline).
 */
function readCache() {
  try {
    if (!fs.existsSync(CACHE_PATH)) return null;
    const d = JSON.parse(fs.readFileSync(CACHE_PATH, 'utf-8'));
    const age = Date.now() - new Date(d.ts).getTime();
    if (age < 60000) return d; // Cache valid 60 secunde
  } catch { /* ignore */ }
  return null;
}

// ── Public API ───────────────────────────────────────────────────────────────

/**
 * Status rapid — folosit de hook-handler și statusline.
 * Returnează string de o linie cu date reale.
 */
function status() {
  const flags = loadFlags();
  if (!flags.components || !flags.components.codeburn) return '';

  const cached = readCache() || fetchRealStatus();
  if (!cached) return '🔥 BURN n/a (codeburn CLI unavailable)';

  let badge = '🟢';
  if (cached.today_cost > 10)  badge = '🔴';
  else if (cached.today_cost > 5) badge = '🟡';

  return `${badge} Today $${cached.today_cost.toFixed(2)} (${cached.today_calls} calls) | Month $${cached.month_cost.toFixed(2)}`;
}

/**
 * Date complete — cache-first (max 120s), fallback CLI.
 * La session-end cache e suficient — nu forțăm un CLI call lent.
 */
function totals() {
  // Cache valid 120s la session-end (nu avem nevoie de date live)
  try {
    if (fs.existsSync(CACHE_PATH)) {
      const d   = JSON.parse(fs.readFileSync(CACHE_PATH, 'utf-8'));
      const age = Date.now() - new Date(d.ts).getTime();
      if (age < 120000) return d; // 2 minute cache
    }
  } catch { /* ignore */ }
  return fetchRealStatus() || { today_cost: 0, month_cost: 0, today_calls: 0, month_calls: 0, source: 'unavailable' };
}

/**
 * Rulează `codeburn report` interactiv în terminal (apelat manual de utilizator).
 */
function openDashboard() {
  if (!CODEBURN_BIN) { console.log('[CODEBURN] CLI not found'); return; }
  try {
    execFileSync(CODEBURN_BIN, ['report'], { stdio: 'inherit', timeout: 30000 });
  } catch { /* user closed dashboard */ }
}

/**
 * record() păstrat pentru compatibilitate — nu mai estimăm din file size.
 * Codeburn real citește direct din ~/.claude/projects/.
 */
function record() { /* no-op — real codeburn tracks automatically */ }

/**
 * reset() nu are sens pentru codeburn real — datele sunt gestionate de CLI.
 */
function reset() { console.log('[CODEBURN] Reset not applicable — real codeburn manages its own data.'); }

module.exports = { status, totals, record, reset, openDashboard, fetchRealStatus };
