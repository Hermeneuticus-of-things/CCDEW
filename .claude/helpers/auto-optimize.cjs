'use strict';
/**
 * Auto-Optimize (v6.1 Micro)
 * Runs on UserPromptSubmit to suggest context-saving rewrites.
 * Detects verbose prompts and injects a concise reformulation hint.
 *
 * Also manages SSA stats logging for the desktop statusline.
 */

const fs   = require('fs');
const path = require('path');

const FLAGS_PATH   = path.join(__dirname, 'feature-flags.json');
const DATA_DIR     = path.join(process.cwd(), '.claude-flow', 'data');
const OPT_LOG_PATH = path.join(DATA_DIR, 'auto-optimize.jsonl');

function loadFlags() {
  try { return JSON.parse(fs.readFileSync(FLAGS_PATH, 'utf-8')); } catch { return {}; }
}

function ensureDataDir() {
  if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });
}

// Rough token estimate: 1 token ≈ 4 chars
function estimateTokens(text) {
  return Math.ceil((text || '').length / 4);
}

// Patterns that bloat context without adding signal
const BLOAT_PATTERNS = [
  { re: /\bte rog\b/gi,           replace: '' },
  { re: /\bpoti sa\b/gi,          replace: '' },
  { re: /\bvrei sa\b/gi,          replace: '' },
  { re: /\bam nevoie sa\b/gi,     replace: '' },
  { re: /\bpot sa te rog\b/gi,    replace: '' },
  { re: /\bpotrebuiesc\b/gi,      replace: '' },
  { re: /\bplease\b/gi,           replace: '' },
  { re: /\bcould you\b/gi,        replace: '' },
  { re: /\bi would like\b/gi,     replace: '' },
  { re: /\bcan you\b/gi,          replace: '' },
];

/**
 * Analyze a prompt and return optimization hints.
 * Does NOT modify the prompt — only prints suggestions.
 */
function analyze(prompt) {
  const flags = loadFlags();
  if (!flags.components || !flags.components.ssa) return;

  const originalTokens = estimateTokens(prompt);
  if (originalTokens < 20) return; // Too short to optimize

  // Strip bloat and estimate savings
  let stripped = prompt;
  for (const { re, replace } of BLOAT_PATTERNS) {
    stripped = stripped.replace(re, replace);
  }
  stripped = stripped.replace(/\s{2,}/g, ' ').trim();

  const strippedTokens = estimateTokens(stripped);
  const savedTokens    = originalTokens - strippedTokens;
  const savedPct       = Math.round((savedTokens / originalTokens) * 100);

  if (savedPct < 5) return; // Not worth reporting

  // Log to file for analytics — rotate at 1 MB to bound disk usage in 7/24.
  try {
    ensureDataDir();
    if (fs.existsSync(OPT_LOG_PATH) && fs.statSync(OPT_LOG_PATH).size > 1024 * 1024) {
      fs.renameSync(OPT_LOG_PATH, OPT_LOG_PATH + '.old');
    }
    const entry = JSON.stringify({ ts: new Date().toISOString(), original: originalTokens, stripped: strippedTokens, savedPct }) + '\n';
    fs.appendFileSync(OPT_LOG_PATH, entry, 'utf-8');
  } catch { /* non-fatal */ }

  process.stdout.write(`[AUTO-OPT] Prompt ${originalTokens} → ~${strippedTokens} tokens (${savedPct}% estimat)\n`);
}

/**
 * Return a stats summary string.
 */
function stats() {
  try {
    if (!fs.existsSync(OPT_LOG_PATH)) return '[AUTO-OPT] No data yet';
    const lines = fs.readFileSync(OPT_LOG_PATH, 'utf-8').trim().split('\n').filter(Boolean);
    if (lines.length === 0) return '[AUTO-OPT] No data yet';
    const entries = lines.map(l => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean);
    const avgSaved = Math.round(entries.reduce((s, e) => s + e.savedPct, 0) / entries.length);
    return `[AUTO-OPT] ${entries.length} prompts analyzed | avg savings ${avgSaved}%`;
  } catch { return '[AUTO-OPT] Error reading log'; }
}

module.exports = { analyze, stats };
