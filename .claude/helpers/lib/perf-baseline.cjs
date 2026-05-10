'use strict';
/**
 * Performance baseline — track p50/p95 of hot-path functions across runs.
 * Detects regressions: alerts when current run's p95 > baseline p95 + tolerance.
 *
 * Storage: .claude-flow/data/perf-baseline.json (rolling 30-sample window).
 */

const fs = require('fs');
const path = require('path');
const { writeAtomicJson } = require('./atomic-write.cjs');
const { todayLocal } = require('./local-date.cjs');

const DATA_DIR = path.join(process.cwd(), '.claude-flow', 'data');
const BASELINE_PATH = path.join(DATA_DIR, 'perf-baseline.json');
const WINDOW = 30;
const TOLERANCE_PCT = 50;

function ensureDir() {
  if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });
}

function load() {
  try {
    if (fs.existsSync(BASELINE_PATH)) return JSON.parse(fs.readFileSync(BASELINE_PATH, 'utf-8'));
  } catch { /* corrupt → fresh */ }
  return { version: '1.0', updated: '', metrics: {} };
}

function record(metricName, valueMs) {
  if (!Number.isFinite(valueMs) || valueMs < 0) return null;
  ensureDir();
  const data = load();
  data.metrics = data.metrics || {};
  const m = data.metrics[metricName] || { samples: [], baseline_p95: null };
  // Snapshot baseline BEFORE adding the new sample, so a sudden spike
  // doesn't immediately re-baseline itself out of detection.
  const prevBaselineP95 = m.baseline_p95;
  const prevSampleCount = m.samples.length;
  m.samples.push({ v: +valueMs.toFixed(2), d: todayLocal() });
  if (m.samples.length > WINDOW) m.samples = m.samples.slice(-WINDOW);
  if (m.samples.length >= 10) {
    const sorted = m.samples.map(s => s.v).sort((a, b) => a - b);
    m.baseline_p95 = sorted[Math.floor(sorted.length * 0.95)];
  }
  data.metrics[metricName] = m;
  data.updated = new Date().toISOString();
  writeAtomicJson(BASELINE_PATH, data);
  return checkRegression(metricName, valueMs, { baseline_p95: prevBaselineP95, samples: { length: prevSampleCount } });
}

function checkRegression(metricName, currentMs, m) {
  if (!m.baseline_p95 || m.samples.length < 10) return { regression: false };
  const limit = m.baseline_p95 * (1 + TOLERANCE_PCT / 100);
  if (currentMs > limit) {
    return {
      regression: true,
      metric: metricName,
      current_ms: +currentMs.toFixed(2),
      baseline_p95_ms: m.baseline_p95,
      limit_ms: +limit.toFixed(2),
      delta_pct: +(((currentMs - m.baseline_p95) / m.baseline_p95) * 100).toFixed(0),
    };
  }
  return { regression: false };
}

function summary() {
  const data = load();
  const out = {};
  for (const [name, m] of Object.entries(data.metrics || {})) {
    out[name] = {
      samples: m.samples.length,
      baseline_p95_ms: m.baseline_p95,
      latest_ms: m.samples.length > 0 ? m.samples[m.samples.length - 1].v : null,
    };
  }
  return out;
}

module.exports = { record, summary, checkRegression };
