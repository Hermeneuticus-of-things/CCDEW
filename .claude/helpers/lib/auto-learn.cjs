'use strict';
/**
 * Auto-learn — observes audit history and adjusts auto-infer thresholds dynamically.
 *
 * Reads .claude-flow/reports/evaluate-*.json + .claude-flow/data/perf-baseline.json,
 * computes rolling averages, raises (or lowers) auto-infer THRESHOLDS so the system
 * stops flagging things that are normal at this scale.
 *
 * Stored config: .claude-flow/data/learned-thresholds.json
 */

const fs = require('fs');
const path = require('path');
const { writeAtomicJson } = require('./atomic-write.cjs');

const DATA_DIR = path.join(process.cwd(), '.claude-flow', 'data');
const REPORTS_DIR = path.join(process.cwd(), '.claude-flow', 'reports');
const LEARNED_PATH = path.join(DATA_DIR, 'learned-thresholds.json');

function ensureDir() {
  if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });
}

function loadLearned() {
  try {
    if (fs.existsSync(LEARNED_PATH)) return JSON.parse(fs.readFileSync(LEARNED_PATH, 'utf-8'));
  } catch {}
  return { version: '1.0', updated: '', thresholds: {} };
}

function loadAuditHistory(maxFiles = 20) {
  if (!fs.existsSync(REPORTS_DIR)) return [];
  const files = fs.readdirSync(REPORTS_DIR)
    .filter(f => f.startsWith('evaluate-') && f.endsWith('.json'))
    .sort().slice(-maxFiles);
  const out = [];
  for (const f of files) {
    try { out.push(JSON.parse(fs.readFileSync(path.join(REPORTS_DIR, f), 'utf-8'))); } catch {}
  }
  return out;
}

function learn(opts = {}) {
  ensureDir();
  const minSamples = opts.minSamples || 5;
  const history = loadAuditHistory();
  if (history.length < minSamples) {
    return { learned: false, reason: `need ≥${minSamples} audits, have ${history.length}` };
  }

  const passCounts = history.map(h => (h.summary && h.summary.pass) || 0);
  const warnCounts = history.map(h => (h.summary && h.summary.warn) || 0);
  const failCounts = history.map(h => (h.summary && h.summary.fail) || 0);

  const avg = arr => arr.reduce((s, n) => s + n, 0) / arr.length;
  const max = arr => arr.reduce((m, n) => n > m ? n : m, 0);

  const learned = loadLearned();
  learned.thresholds = {
    expected_pass: Math.round(avg(passCounts)),
    max_warn_normal: Math.max(2, max(warnCounts)),
    max_fail_normal: Math.max(0, max(failCounts)),
    samples_used: history.length,
  };
  learned.updated = new Date().toISOString();
  writeAtomicJson(LEARNED_PATH, learned);

  return { learned: true, thresholds: learned.thresholds };
}

function shouldAlert(currentSummary) {
  const learned = loadLearned();
  const t = learned.thresholds;
  if (!t || t.samples_used < 5) {
    return { alert: currentSummary.fail > 0, reason: 'no learned baseline yet' };
  }
  const failExceeded = currentSummary.fail > t.max_fail_normal;
  const warnExceeded = currentSummary.warn > t.max_warn_normal + 2;
  const passDrop = currentSummary.pass < t.expected_pass - 3;
  return {
    alert: failExceeded || warnExceeded || passDrop,
    reasons: { failExceeded, warnExceeded, passDrop },
    learned: t,
    current: currentSummary,
  };
}

module.exports = { learn, loadLearned, shouldAlert };
