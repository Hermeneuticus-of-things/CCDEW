#!/usr/bin/env node
/**
 * shared-utils.cjs — Common utilities shared across CCDEW modules
 * 
 * Consolidates duplicate functions to single source of truth.
 * Functions: loadFlags, ensureDataDir, tokenize, trigrams, etc.
 */

'use strict';

const fs = require('fs');
const path = require('path');

const CCDEW_PATH = '/home/think/CCDEW';
const DATA_DIR = path.join(CCDEW_PATH, '.claude-flow/data');
const FLAGS_FILE = path.join(CCDEW_PATH, '.claude/helpers/feature-flags.json');

// ── FLAG MANAGEMENT ──────────────────────────────────────────────────────
function loadFlags() {
  try {
    if (fs.existsSync(FLAGS_FILE)) {
      return JSON.parse(fs.readFileSync(FLAGS_FILE, 'utf-8'));
    }
  } catch {}
  return {};
}

// ── DATA DIRECTORY ───────────────────────────────────────────────────────
function ensureDataDir() {
  if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
  }
}

// ── TEXT PROCESSING (trigram/Jaccard) ───────────────────────────────────
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

// ── FILE OPERATIONS ─────────────────────────────────────────────────────
function readJSON(filePath) {
  try {
    if (fs.existsSync(filePath)) {
      return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
    }
  } catch {}
  return null;
}

function writeJSON(filePath, data) {
  try {
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
    return true;
  } catch(e) {
    return false;
  }
}

// ── STATE MANAGEMENT ─────────────────────────────────────────────────────
function loadState() {
  const stateFile = path.join(DATA_DIR, 'state.json');
  return readJSON(stateFile) || {};
}

function saveState(state) {
  ensureDataDir();
  const stateFile = path.join(DATA_DIR, 'state.json');
  return writeJSON(stateFile, state);
}

// ── SCORE ENTRY (trigram similarity) ────────────────────────────────────
function scoreEntry(promptTrigrams, entry) {
  const text = [
    entry.content || entry.text || entry.body || '',
    entry.title   || entry.name  || '',
    entry.tags    ? entry.tags.join(' ') : '',
  ].join(' ');
  const entryTrigrams = trigrams(tokenize(text));
  return jaccard(promptTrigrams, entryTrigrams);
}

// ── EXPORTS ─────────────────────────────────────────────────────────────
module.exports = {
  loadFlags,
  ensureDataDir,
  tokenize,
  trigrams,
  jaccard,
  readJSON,
  writeJSON,
  loadState,
  saveState,
  scoreEntry,
  DATA_DIR,
  FLAGS_FILE
};