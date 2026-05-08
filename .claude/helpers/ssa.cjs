'use strict';
/**
 * SSA — Sparse/Selective Attention (v6.1 Micro)
 * Reduces context size by ranking and filtering memory entries before injection.
 * Uses trigram Jaccard similarity (same approach as intelligence.cjs).
 *
 * API:
 *   filterContext(prompt, entries, options?) → topEntries[]
 *   summarizeStats(original, filtered)      → string
 */

const fs = require('fs');
const path = require('path');

const FLAGS_PATH  = path.join(__dirname, 'feature-flags.json');
const OBS_INDEX   = path.join(process.cwd(), '.claude-flow', 'data', 'session-critical-index.json');

function loadFlags() {
  try { return JSON.parse(fs.readFileSync(FLAGS_PATH, 'utf-8')); } catch { return {}; }
}

const STOP_WORDS = new Set([
  'the','a','an','is','are','was','were','have','has','do','does','did',
  'to','of','in','for','on','with','at','by','and','but','or','not',
  'this','that','it','its','i','we','you','they','he','she',
  'ca','la','de','si','cu','din','pe','un','o','sa','se','nu',
]);

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

function scoreEntry(promptTrigrams, entry) {
  const text = [
    entry.content || entry.text || entry.body || '',
    entry.title   || entry.name  || '',
    entry.tags    ? entry.tags.join(' ') : '',
  ].join(' ');
  const entryTrigrams = trigrams(tokenize(text));
  return jaccard(promptTrigrams, entryTrigrams);
}

/**
 * Filter a list of memory/context entries to the most relevant subset.
 * @param {string}   prompt   — current user prompt
 * @param {object[]} entries  — memory entries (any shape with text/content)
 * @param {object}   opts     — override flags defaults
 * @returns {object[]}        — sorted, filtered entries
 */
function filterContext(prompt, entries, opts = {}) {
  const flags = loadFlags();
  const cfg   = (flags.ssa || {});

  if (!flags.components || !flags.components.ssa) return entries;
  if (!Array.isArray(entries) || entries.length === 0) return entries;

  const topK    = opts.top_k    || cfg.top_k    || 12;
  const minScore= opts.min_score|| cfg.min_score|| 0.15;

  const promptTrigrams = trigrams(tokenize(prompt));

  const scored = entries.map(entry => ({
    entry,
    score: scoreEntry(promptTrigrams, entry),
  }));

  scored.sort((a, b) => b.score - a.score);

  const filtered = scored
    .filter(s => s.score >= minScore)
    .slice(0, topK)
    .map(s => s.entry);

  // Always include pinned entries regardless of score
  const pinned = entries.filter(e => e.pinned || e.priority === 'high');
  const pinnedIds = new Set(pinned.map(e => e.id || e.title));
  const merged = [...pinned, ...filtered.filter(e => !pinnedIds.has(e.id || e.title))];

  return merged.slice(0, Math.max(topK, pinned.length));
}

/**
 * Human-readable reduction stats.
 */
function summarizeStats(original, filtered) {
  if (!Array.isArray(original) || !Array.isArray(filtered)) return '';
  const pct = original.length > 0
    ? Math.round((1 - filtered.length / original.length) * 100)
    : 0;
  return `[SSA] ${original.length} → ${filtered.length} entries (${pct}% reduction)`;
}

/**
 * Încarcă entries din Obsidian session-critical-index.json.
 * Returnează array flat de entries compatibile cu filterContext().
 */
function loadObsidianEntries() {
  try {
    if (!fs.existsSync(OBS_INDEX)) return [];
    const idx = JSON.parse(fs.readFileSync(OBS_INDEX, 'utf-8'));
    const entries = [];
    // Index format: { by_project: { proj: [entries] }, by_tag: { tag: [entries] }, all: [...] }
    const source = idx.all || Object.values(idx.by_project || {}).flat();
    for (const e of source) {
      entries.push({
        id:      e.file || e.path || '',
        // obsidian-session-context.py writes 'compact' and 'name'; other sources use content/body/title
        content: e.content || e.body || e.summary || e.compact || '',
        title:   e.title || e.name || e.file || '',
        tags:    e.tags || [],
        pinned:  e.priority === 'critical' || e.tags?.includes('session-critical'),
      });
    }
    return entries;
  } catch { return []; }
}

module.exports = { filterContext, summarizeStats, loadObsidianEntries };
