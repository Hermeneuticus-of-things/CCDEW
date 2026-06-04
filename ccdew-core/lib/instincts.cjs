'use strict';
/**
 * ECC-style Instincts — pattern recognition from usage.
 *
 * Records every prompt + outcome (route + success/failure) to a JSONL log.
 * Detects repeated patterns: same intent → same agent → success.
 * Surfaces "you usually do X for Y" hints in inject-workflow.
 *
 * Storage: .claude-flow/data/instincts.jsonl (append-only, rotated at 5k lines)
 */

const fs = require('fs');
const path = require('path');
const { writeAtomicJson } = require('./atomic-write.cjs');
const { logError } = require('./error-log.cjs');

const DATA_DIR = path.join(process.cwd(), '.claude-flow', 'data');
const INSTINCTS_LOG = path.join(DATA_DIR, 'instincts.jsonl');
const PATTERNS_PATH = path.join(DATA_DIR, 'instincts-patterns.json');
const MAX_LINES = 5000;
const MIN_OCCURRENCES = 3;

function ensureDataDir() {
  if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });
}

function fingerprint(prompt) {
  if (!prompt) return '';
  return prompt.toLowerCase()
    .replace(/[^a-z0-9\s]/g, ' ')
    .split(/\s+/)
    .filter(w => w.length >= 4 && !STOP_WORDS.has(w))
    .sort()
    .slice(0, 8)
    .join(' ');
}

const STOP_WORDS = new Set([
  'this', 'that', 'these', 'those', 'with', 'from', 'into', 'about',
  'have', 'should', 'would', 'could', 'please', 'thanks',
]);

function record(event) {
  try {
    ensureDataDir();
    const entry = {
      ts: new Date().toISOString(),
      fp: fingerprint(event.prompt || ''),
      node: event.node || null,
      success: !!event.success,
      cost: typeof event.cost === 'number' ? event.cost : null,
    };
    if (!entry.fp) return;
    fs.appendFileSync(INSTINCTS_LOG, JSON.stringify(entry) + '\n', 'utf-8');
    rotateIfNeeded();
  } catch (e) { logError('instincts.record', e); }
}

function rotateIfNeeded() {
  try {
    if (!fs.existsSync(INSTINCTS_LOG)) return;
    const stat = fs.statSync(INSTINCTS_LOG);
    if (stat.size < 512 * 1024) return;
    const lines = fs.readFileSync(INSTINCTS_LOG, 'utf-8').split('\n');
    if (lines.length <= MAX_LINES) return;
    fs.writeFileSync(INSTINCTS_LOG, lines.slice(-MAX_LINES).join('\n'), 'utf-8');
  } catch (e) { logError('instincts.rotate', e); }
}

function buildPatterns() {
  try {
    if (!fs.existsSync(INSTINCTS_LOG)) return {};
    const lines = fs.readFileSync(INSTINCTS_LOG, 'utf-8').trim().split('\n').filter(Boolean);
    const byFp = {};
    for (const line of lines) {
      let e; try { e = JSON.parse(line); } catch { continue; }
      if (!e.fp || !e.node) continue;
      const k = e.fp;
      byFp[k] = byFp[k] || { count: 0, success: 0, nodes: {} };
      byFp[k].count++;
      if (e.success) byFp[k].success++;
      byFp[k].nodes[e.node] = (byFp[k].nodes[e.node] || 0) + 1;
    }
    const patterns = {};
    for (const [fp, data] of Object.entries(byFp)) {
      if (data.count < MIN_OCCURRENCES) continue;
      const dominantNode = Object.entries(data.nodes).sort((a, b) => b[1] - a[1])[0];
      patterns[fp] = {
        count: data.count,
        success_rate: +(data.success / data.count).toFixed(2),
        dominant_node: parseInt(dominantNode[0], 10),
        node_confidence: +(dominantNode[1] / data.count).toFixed(2),
      };
    }
    writeAtomicJson(PATTERNS_PATH, patterns);
    return patterns;
  } catch (e) { logError('instincts.buildPatterns', e); return {}; }
}

function loadPatterns() {
  try {
    if (!fs.existsSync(PATTERNS_PATH)) return {};
    return JSON.parse(fs.readFileSync(PATTERNS_PATH, 'utf-8'));
  } catch { return {}; }
}

function suggest(prompt) {
  const fp = fingerprint(prompt);
  if (!fp) return null;
  const patterns = loadPatterns();
  const match = patterns[fp];
  if (!match || match.count < MIN_OCCURRENCES) return null;
  if (match.success_rate < 0.5) return null;
  return {
    suggestion: `you usually route this to node ${match.dominant_node} (${Math.round(match.node_confidence * 100)}% confidence over ${match.count} similar prompts, ${Math.round(match.success_rate * 100)}% success rate)`,
    node: match.dominant_node,
    confidence: match.node_confidence,
    samples: match.count,
  };
}

function stats() {
  const patterns = loadPatterns();
  const count = Object.keys(patterns).length;
  let logLines = 0;
  try {
    if (fs.existsSync(INSTINCTS_LOG)) {
      logLines = fs.readFileSync(INSTINCTS_LOG, 'utf-8').trim().split('\n').filter(Boolean).length;
    }
  } catch {}
  return { patterns: count, log_entries: logLines };
}

module.exports = { record, suggest, buildPatterns, loadPatterns, stats, fingerprint };
