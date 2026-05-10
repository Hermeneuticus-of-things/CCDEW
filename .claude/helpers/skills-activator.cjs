'use strict';
/**
 * Skills auto-activate framework — inspired by everything-claude-code.
 *
 * Scans `.claude/skills/<skill-name>/SKILL.md` files, parses the YAML
 * frontmatter `description` + `triggers`, and matches them against the
 * incoming user prompt. The activated skill names are surfaced to Claude
 * via inject-workflow as a hint, so the model can decide to invoke them.
 *
 * Skill format expected (YAML frontmatter):
 *   ---
 *   name: my-skill
 *   description: Use when user asks about X, Y, Z
 *   triggers: [keyword1, keyword2]
 *   ---
 *
 * For backward compatibility with skills that have only `description:`,
 * we extract trigger words from it via simple keyword extraction.
 */

const fs = require('fs');
const path = require('path');

const SKILLS_DIR = path.join(process.cwd(), '.claude', 'skills');

let _cached = null;
let _cachedAt = 0;
const CACHE_TTL_MS = 30_000;

function listSkillFiles() {
  if (!fs.existsSync(SKILLS_DIR)) return [];
  const out = [];
  for (const entry of fs.readdirSync(SKILLS_DIR, { withFileTypes: true })) {
    if (!entry.isDirectory()) continue;
    const skillFile = path.join(SKILLS_DIR, entry.name, 'SKILL.md');
    if (fs.existsSync(skillFile)) out.push({ name: entry.name, file: skillFile });
  }
  return out;
}

function parseFrontmatter(content) {
  const m = content.match(/^---\s*\n([\s\S]*?)\n---/);
  if (!m) return {};
  const body = m[1];
  const out = {};
  for (const line of body.split('\n')) {
    const kv = line.match(/^(\w[\w-]*)\s*:\s*(.*)$/);
    if (!kv) continue;
    const k = kv[1];
    let v = kv[2].trim();
    if (v.startsWith('[') && v.endsWith(']')) {
      v = v.slice(1, -1).split(',').map(s => s.trim().replace(/^['"]|['"]$/g, '')).filter(Boolean);
    } else if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) {
      v = v.slice(1, -1);
    }
    out[k] = v;
  }
  return out;
}

function extractKeywords(text) {
  if (!text) return [];
  return text.toLowerCase()
    .replace(/[^a-z0-9\s-]/g, ' ')
    .split(/\s+/)
    .filter(w => w.length >= 4)
    .slice(0, 20);
}

function loadSkills() {
  const now = Date.now();
  if (_cached && (now - _cachedAt) < CACHE_TTL_MS) return _cached;
  _cached = [];
  for (const { name, file } of listSkillFiles()) {
    try {
      const content = fs.readFileSync(file, 'utf-8');
      const meta = parseFrontmatter(content);
      const triggers = Array.isArray(meta.triggers) ? meta.triggers : extractKeywords(meta.description || '');
      _cached.push({
        name, description: meta.description || '',
        triggers: triggers.map(t => String(t).toLowerCase()),
      });
    } catch { /* skip broken skill */ }
  }
  _cachedAt = now;
  return _cached;
}

const USAGE_LOG = path.join(process.cwd(), '.claude-flow', 'data', 'skill-usage.jsonl');

function _trackUsage(suggested) {
  if (!Array.isArray(suggested) || suggested.length === 0) return;
  try {
    const dir = path.dirname(USAGE_LOG);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    const entry = { ts: new Date().toISOString(), suggested };
    fs.appendFileSync(USAGE_LOG, JSON.stringify(entry) + '\n', 'utf-8');
  } catch { /* non-fatal */ }
}

function usageStats() {
  if (!fs.existsSync(USAGE_LOG)) return { total: 0, by_skill: {} };
  try {
    const lines = fs.readFileSync(USAGE_LOG, 'utf-8').trim().split('\n').filter(Boolean);
    const bySkill = {};
    for (const line of lines) {
      let e; try { e = JSON.parse(line); } catch { continue; }
      for (const s of e.suggested || []) bySkill[s] = (bySkill[s] || 0) + 1;
    }
    return { total: lines.length, by_skill: bySkill };
  } catch { return { total: 0, by_skill: {} }; }
}

function deadSkills() {
  const all = listSkillFiles().map(s => s.name);
  const stats = usageStats();
  return all.filter(name => !stats.by_skill[name]);
}

function activateForPrompt(prompt, opts = {}) {
  const max = opts.max || 3;
  const minMatch = opts.minMatch || 1;
  const skills = loadSkills();
  if (skills.length === 0) return [];
  const promptLower = (prompt || '').toLowerCase();
  const promptWords = new Set(promptLower.split(/\W+/).filter(w => w.length >= 4));
  const scored = [];
  for (const s of skills) {
    let score = 0;
    for (const t of s.triggers) {
      if (!t) continue;
      if (promptLower.includes(t)) score += 2;
      else if (promptWords.has(t)) score += 1;
    }
    if (score === 0 && s.description) {
      const descWords = new Set(String(s.description).toLowerCase().split(/\W+/).filter(w => w.length >= 4));
      let overlap = 0;
      for (const w of promptWords) if (descWords.has(w)) overlap++;
      if (overlap >= 2) score = overlap;
    }
    if (score >= minMatch) scored.push({ name: s.name, score });
  }
  scored.sort((a, b) => b.score - a.score);
  const top = scored.slice(0, max).map(s => s.name);
  if (opts.silent !== true) _trackUsage(top);
  return top;
}

module.exports = { loadSkills, activateForPrompt, listSkillFiles, usageStats, deadSkills };
