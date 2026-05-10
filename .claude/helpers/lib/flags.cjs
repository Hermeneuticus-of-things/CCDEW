'use strict';
const fs = require('fs');
const path = require('path');

const FLAGS_PATH = path.join(__dirname, '..', 'feature-flags.json');

let cached = null;
let cachedAt = 0;
const TTL_MS = 5000;

function load() {
  const now = Date.now();
  if (cached && (now - cachedAt) < TTL_MS) return cached;
  try {
    cached = JSON.parse(fs.readFileSync(FLAGS_PATH, 'utf-8'));
    cachedAt = now;
  } catch {
    cached = { components: {} };
    cachedAt = now;
  }
  return cached;
}

function isEnabled(component) {
  const f = load();
  return !!(f.components && f.components[component]);
}

module.exports = { load, isEnabled };
