'use strict';
/**
 * SSA — Sparse/Selective Attention v6.1 SLIM
 * Enhanced multi-dimensional scoring for intelligent context selection.
 * 
 * Scoring dimensions:
 * 1. Semantic similarity (Jaccard trigram)
 * 2. Enneagram distance (node affinity)
 * 3. Holographic related: links
 * 4. Recent memory (episodic)
 * 5. Pinned priority
 * 
 * API:
 *   filterContext(prompt, entries, options?) → topEntries[]
 *   summarizeStats(original, filtered)      → string
 *   getSSAEfficiency()                       → { ratio, tokens_saved, target }
 */

const fs = require('fs');
const path = require('path');

const FLAGS_PATH  = path.join(__dirname, 'feature-flags.json');
const OBS_INDEX   = path.join(process.cwd(), '.claude-flow', 'data', 'session-critical-index.json');
const MEMORY_DIR  = path.join(process.cwd(), '.claude-flow', 'data');

const ENNEAGRAM_DISTANCE = {
  1:  { strengths: [7, 5], weaknesses: [3, 6], weight: 1.2 },
  2:  { strengths: [1, 3], weaknesses: [8, 5], weight: 1.2 },
  3:  { strengths: [6, 2], weaknesses: [9, 4], weight: 1.2 },
  4:  { strengths: [5, 9], weaknesses: [1, 3], weight: 1.2 },
  5:  { strengths: [4, 7], weaknesses: [2, 6], weight: 1.2 },
  6:  { strengths: [3, 9], weaknesses: [4, 7], weight: 1.2 },
  7:  { strengths: [8, 5], weaknesses: [1, 2], weight: 1.2 },
  8:  { strengths: [7, 1], weaknesses: [5, 3], weight: 1.2 },
  9:  { strengths: [6, 4], weaknesses: [2, 8], weight: 1.2 },
};

const STOP_WORDS = new Set([
  'the','a','an','is','are','was','were','have','has','do','does','did',
  'to','of','in','for','on','with','at','by','and','but','or','not',
  'this','that','it','its','i','we','you','they','he','she',
  'ca','la','de','si','cu','din','pe','un','o','sa','se','nu',
]);

let _stats = { total_tokens: 0, saved_tokens: 0, calls: 0 };

function loadFlags() {
  try { return JSON.parse(fs.readFileSync(FLAGS_PATH, 'utf-8')); } catch { return {}; }
}

function tokenize(text) {
  if (!text) return [];
  return String(text).toLowerCase()
    .replace(/[^a-z0-9\s\-_]/g, ' ')
    .split(/\s+/)
    .filter(w => w.length > 2 && !STOP_WORDS.has(w));
}

function trigrams(words) {
  const t = new Set();
  for (const w of words) {
    for (let i = 0; i <= w.length - 3; i++) t.add(w.slice(i, i + 3));
  }
  return t;
}

function jaccard(a, b) {
  if (a.size === 0 && b.size === 0) return 0;
  let inter = 0;
  for (const x of a) { if (b.has(x)) inter++; }
  return inter / (a.size + b.size - inter);
}

function getEnneagramScore(entry, currentNode) {
  if (!currentNode || !ENNEAGRAM_DISTANCE[currentNode]) return 0.5;
  const cfg = ENNEAGRAM_DISTANCE[currentNode];
  const entryTags = (entry.tags || []).map(t => t.toLowerCase());
  let score = 0.5;
  for (const tag of entryTags) {
    if (cfg.strengths.some(s => tag.includes('node' + s))) score = Math.min(score + 0.15, 1);
    if (cfg.weaknesses.some(w => tag.includes('node' + w))) score = Math.max(score - 0.15, 0);
  }
  return score;
}

function getHolographicBonus(entry, allEntries) {
  if (!entry.related || !Array.isArray(entry.related)) return 0;
  const relatedCount = entry.related.length;
  return Math.min(relatedCount * 0.03, 0.15);
}

function getRecencyBonus(entry) {
  if (!entry.timestamp) return 0;
  const ageMs = Date.now() - new Date(entry.timestamp).getTime();
  const ageHours = ageMs / 3600000;
  if (ageHours < 1) return 0.10;
  if (ageHours < 4) return 0.05;
  if (ageHours < 24) return 0.02;
  return 0;
}

function getPinnedScore(entry) {
  if (entry.pinned || entry.priority === 'high' || entry.priority === 'critical') return 0.5;
  return 0;
}

function multiScore(promptTrigrams, entry, currentNode, allEntries) {
  const semantic = scoreEntry(promptTrigrams, entry);
  const ennea = getEnneagramScore(entry, currentNode);
  const holo = getHolographicBonus(entry, allEntries);
  const recency = getRecencyBonus(entry);
  const pinned = getPinnedScore(entry);
  const weights = { semantic: 0.6, ennea: 0.15, holo: 0.1, recency: 0.05, pinned: 0.1 };
  const raw = (semantic * weights.semantic) + (ennea * weights.ennea) + (holo * weights.holo) + 
              (recency * weights.recency) + (pinned * weights.pinned);
  return Math.max(0, Math.min(1, raw));
}

function scoreEntry(promptTrigrams, entry) {
  const text = [
    entry.content || entry.text || entry.body || '',
    entry.title   || entry.name  || '',
    entry.tags    ? entry.tags.join(' ') : '',
  ].join(' ');
  const entryTrigrams = trigrams(tokenize(text));
  return jaccard(promptTrigrams, entryTrigrams);
}

function getCurrentNode() {
  try {
    const saflaPath = path.join(MEMORY_DIR, 'safla.json');
    if (fs.existsSync(saflaPath)) {
      const data = JSON.parse(fs.readFileSync(saflaPath, 'utf-8'));
      if (data.nodes && Object.keys(data.nodes).length > 0) {
        let maxSuccess = 0, bestNode = null;
        for (const [k, v] of Object.entries(data.nodes)) {
          if (v.success > maxSuccess) { maxSuccess = v.success; bestNode = k; }
        }
        return bestNode;
      }
    }
  } catch {}
  return null;
}

function filterContext(prompt, entries, opts = {}) {
  const flags = loadFlags();
  const cfg   = (flags.ssa || {});

  if (!flags.components || !flags.components.ssa) return entries;
  if (!Array.isArray(entries) || entries.length === 0) return entries;

  const topK     = opts.top_k     ?? cfg.top_k     ?? 12;
  const minScore = opts.min_score ?? cfg.min_score ?? 0.15;
  const currentNode = opts.node ?? getCurrentNode();

  const promptTrigrams = trigrams(tokenize(prompt));

  const scored = entries.map(entry => ({
    entry,
    score: multiScore(promptTrigrams, entry, currentNode, entries),
  }));

  scored.sort((a, b) => b.score - a.score);

  const filtered = scored
    .filter(s => s.score >= minScore)
    .slice(0, topK)
    .map(s => s.entry);

  const pinned = entries.filter(e => e.pinned || e.priority === 'high' || e.priority === 'critical');
  const pinnedIds = new Set(pinned.map(e => e.id || e.title).filter(Boolean));
  const merged = [...pinned, ...filtered.filter(e => {
    const k = e.id || e.title;
    return !k || !pinnedIds.has(k);
  })];

  const result = merged.slice(0, Math.max(topK, pinned.length));

  _stats.total_tokens += entries.length;
  _stats.saved_tokens += (entries.length - result.length);
  _stats.calls++;

  return result;
}

function summarizeStats(original, filtered) {
  if (!Array.isArray(original) || !Array.isArray(filtered)) return '';
  const pct = original.length > 0
    ? Math.round((1 - filtered.length / original.length) * 100)
    : 0;
  return `[SSA] ${original.length} → ${filtered.length} entries (${pct}% reduction)`;
}

function getSSAEfficiency() {
  const ratio = _stats.total_tokens > 0 ? _stats.saved_tokens / _stats.total_tokens : 0;
  return {
    ratio: Math.round(ratio * 100) / 100,
    tokens_saved: _stats.saved_tokens,
    total_tokens: _stats.total_tokens,
    calls: _stats.calls,
    target: '<25%',
    status: ratio >= 0.25 ? 'OK' : 'BELOW_TARGET',
    note: 'Ratio = tokens_saved / total_tokens. With diverse content (mixed topics), expect 25-35%. With homogeneous test data, ratio can be 60-90%.',
  };
}

function loadObsidianEntries() {
  try {
    if (!fs.existsSync(OBS_INDEX)) return [];
    const idx = JSON.parse(fs.readFileSync(OBS_INDEX, 'utf-8'));
    const entries = [];
    const source = idx.all || Object.values(idx.by_project || {}).flat();
    for (const e of source) {
      entries.push({
        id:      e.file || e.path || '',
        content: e.content || e.body || e.summary || e.compact || '',
        title:   e.title || e.name || e.file || '',
        tags:    e.tags || [],
        pinned:  e.priority === 'critical' || e.tags?.includes('session-critical'),
        timestamp: e.timestamp,
        related: e.related,
      });
    }
    return entries;
  } catch { return []; }
}

module.exports = { 
  filterContext, 
  summarizeStats, 
  loadObsidianEntries,
  getSSAEfficiency,
  getCurrentNode,
  ENNEAGRAM_DISTANCE,
};