'use strict';
/**
 * SSA — Sparse/Selective Attention (v6.1 Micro)
 * Reduces context size by ranking and filtering memory entries before injection.
 * Uses trigram Jaccard similarity from shared-utils.cjs.
 *
 * API:
 *   filterContext(prompt, entries, options?) → topEntries[]
 *   summarizeStats(original, filtered)      → string
 *   getSSAEfficiency()                     → efficiency stats
 *   recordSSAUsage(originalCount, filteredCount) → void
 */

const fs = require('fs');
const path = require('path');
const { loadFlags, ensureDataDir, tokenize, trigrams, scoreEntry } = require('./shared-utils.cjs');

const FLAGS_PATH  = path.join(__dirname, 'feature-flags.json');
const OBS_INDEX   = path.join(process.cwd(), '.claude-flow', 'data', 'session-critical-index.json');
const SSA_STATS   = path.join(process.cwd(), '.claude-flow', 'data', 'ssa-stats.json');

// Re-export for external use
function loadFlagsFromPath() {
  try { return JSON.parse(fs.readFileSync(FLAGS_PATH, 'utf-8')); } catch { return {}; }
}

// ── SSA Statistics ─────────────────────────────────────────────────────────
function loadSSAStats() {
  try {
    if (fs.existsSync(SSA_STATS)) {
      return JSON.parse(fs.readFileSync(SSA_STATS, 'utf-8'));
    }
  } catch {}
  return {
    calls: 0,
    entries_total: 0,
    entries_saved: 0,
    chars_total: 0,
    chars_saved: 0,
    tokens_total: 0,
    tokens_saved: 0,
    session_start: new Date().toISOString()
  };
}

function saveSSAStats(stats) {
  try {
    fs.writeFileSync(SSA_STATS, JSON.stringify(stats, null, 2));
  } catch {}
}

function recordSSAUsage(original, filtered) {
  const stats = loadSSAStats();
  stats.calls++;
  stats.entries_total += original.length;
  stats.entries_saved += (original.length - filtered.length);
  
  // Estimate chars/tokens (rough: 4 chars per token)
  const origChars = original.reduce((s, e) => s + (e.content || '').length, 0);
  const filtChars = filtered.reduce((s, e) => s + (e.content || '').length, 0);
  stats.chars_total += origChars;
  stats.chars_saved += (origChars - filtChars);
  stats.tokens_total += Math.ceil(origChars / 4);
  stats.tokens_saved += Math.ceil((origChars - filtChars) / 4);
  
  saveSSAStats(stats);
}

/**
 * Get SSA efficiency metrics
 */
function getSSAEfficiency() {
  const stats = loadSSAStats();
  const ratio = stats.entries_total > 0
    ? Math.round((stats.entries_saved / stats.entries_total) * 100)
    : 0;
  const target = 25;
  
  return {
    calls: stats.calls,
    entries: { total: stats.entries_total, saved: stats.entries_saved },
    chars: { total: stats.chars_total, saved: stats.chars_saved },
    tokens: { total: stats.tokens_total, saved: stats.tokens_saved },
    ratio: ratio,
    target: target,
    status: ratio < target ? 'OK' : 'ABOVE_TARGET'
  };
}

/**
 * Filter a list of memory/context entries to the most relevant subset.
 * TARGET: ~20-25% reduction (keep 75-80% of entries)
 * 
 * Algorithm:
 * 1. Score all entries with trigram Jaccard
 * 2. Keep ALL entries with score > 0.05 (low threshold)
 * 3. Ensure minimum keep ratio based on entry count
 * 4. Always keep pinned entries
 * 
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

  // CONFIG: Target 20-25% reduction (keep 75-80%)
  const topK      = opts.top_k      ?? cfg.top_k      ?? 50;  // Keep up to 50
  const minScore  = opts.min_score  ?? cfg.min_score  ?? 0.02; // Very low threshold
  
  // Calculate how many to keep based on target ratio
  // Target: ~25% reduction = keep 75% of entries
  const targetRatio = 0.75; // Keep 75% minimum
  const minKeep = Math.max(Math.ceil(entries.length * targetRatio), 3);

  const promptTrigrams = trigrams(tokenize(prompt));

  // Score all entries
  const scored = entries.map(entry => ({
    entry,
    score: scoreEntry(promptTrigrams, entry),
  }));

  // Sort by score descending
  scored.sort((a, b) => b.score - a.score);

  // Get high-relevance entries (score > 0.05)
  const highRelevance = scored
    .filter(s => s.score >= minScore)
    .map(s => s.entry);

  // Get pinned entries
  const pinned = entries.filter(e => e.pinned || e.priority === 'high' || e.priority === 'critical');
  const pinnedIds = new Set(pinned.map(e => e.id || e.title).filter(Boolean));

  // Merge: pinned + high relevance (deduplicated)
  const filtered = [
    ...pinned,
    ...highRelevance.filter(e => {
      const k = e.id || e.title;
      return !k || !pinnedIds.has(k);
    })
  ];

  // ENSURE MINIMUM KEEP RATIO
  // If we have fewer than minKeep, add top-scored entries
  let result = [...filtered];
  if (result.length < minKeep && scored.length > 0) {
    const alreadyIncluded = new Set(result.map(e => e.id || e.title));
    for (const s of scored) {
      if (result.length >= minKeep) break;
      const key = s.entry.id || s.entry.title;
      if (!key || !alreadyIncluded.has(key)) {
        result.push(s.entry);
        if (key) alreadyIncluded.add(key);
      }
    }
  }

  // Limit to topK maximum, but never less than minKeep
  const finalCount = Math.min(result.length, Math.max(topK, minKeep));
  result = result.slice(0, finalCount);

  // Record usage stats
  if (result.length < entries.length) {
    recordSSAUsage(entries, result);
  }
  
  return result;
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

module.exports = { 
  filterContext, 
  summarizeStats, 
  loadObsidianEntries,
  getSSAEfficiency,
  recordSSAUsage
};
