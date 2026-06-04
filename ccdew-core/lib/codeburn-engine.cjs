'use strict';
/**
 * Native codeburn engine — reads ~/.claude/projects/ ** /*.jsonl directly.
 * No external CLI dependency. Same output format as `codeburn status`.
 *
 * Pricing (USD per 1M tokens, Anthropic public 2026):
 *   claude-opus-4-7:    input $15.00, output $75.00, cache_creation 1.25x input, cache_read 0.10x input
 *   claude-sonnet-4-6:  input  $3.00, output $15.00, cache_creation 1.25x input, cache_read 0.10x input
 *   claude-haiku-4-5:   input  $0.80, output  $4.00, cache_creation 1.25x input, cache_read 0.10x input
 *   (older sonnet-3-5/haiku-3-5: same as 4-6/4-5 for our purposes)
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { PRICING, CACHE_CREATE_MULT, CACHE_READ_MULT, modelTier } = require('./pricing.cjs');
const { todayLocal, monthLocal } = require('./local-date.cjs');

function projectsDir() {
  return path.join(os.homedir(), '.claude', 'projects');
}

function* iterJsonlFiles() {
  const root = projectsDir();
  if (!fs.existsSync(root)) return;
  for (const project of fs.readdirSync(root)) {
    const projDir = path.join(root, project);
    let stat;
    try { stat = fs.statSync(projDir); } catch { continue; }
    if (!stat.isDirectory()) continue;
    for (const f of fs.readdirSync(projDir)) {
      if (f.endsWith('.jsonl')) yield path.join(projDir, f);
    }
  }
}

function costForLine(line) {
  if (!line || line.length < 10) return null;
  if (!line.includes('"usage"')) return null;
  let obj;
  try { obj = JSON.parse(line); } catch { return null; }
  const msg = obj.message;
  if (!msg || !msg.usage) return null;

  const u = msg.usage;
  const tier = modelTier(msg.model);
  const px = PRICING[tier];

  const inputCost  = (u.input_tokens || 0) * px.input  / 1e6;
  const outputCost = (u.output_tokens || 0) * px.output / 1e6;
  const cacheCreateCost = (u.cache_creation_input_tokens || 0) * px.input * CACHE_CREATE_MULT / 1e6;
  const cacheReadCost   = (u.cache_read_input_tokens     || 0) * px.input * CACHE_READ_MULT   / 1e6;
  const total = inputCost + outputCost + cacheCreateCost + cacheReadCost;

  return {
    timestamp: obj.timestamp,
    model: msg.model,
    cost: total,
    tokens: {
      input: u.input_tokens || 0,
      output: u.output_tokens || 0,
      cache_creation: u.cache_creation_input_tokens || 0,
      cache_read: u.cache_read_input_tokens || 0,
    },
  };
}

function totals(opts = {}) {
  const today = opts.today || todayLocal();
  const month = opts.month || monthLocal();
  let today_cost = 0, today_calls = 0, month_cost = 0, month_calls = 0;

  for (const file of iterJsonlFiles()) {
    let raw;
    try { raw = fs.readFileSync(file, 'utf-8'); } catch { continue; }
    for (const line of raw.split('\n')) {
      const c = costForLine(line);
      if (!c || !c.timestamp) continue;
      const ts = c.timestamp;
      if (ts.startsWith(month)) {
        month_cost += c.cost;
        month_calls++;
        if (ts.startsWith(today)) {
          today_cost += c.cost;
          today_calls++;
        }
      }
    }
  }

  return {
    today_cost: +today_cost.toFixed(2),
    today_calls,
    month_cost: +month_cost.toFixed(2),
    month_calls,
    source: 'native',
    ts: new Date().toISOString(),
  };
}

function isAvailable() {
  return fs.existsSync(projectsDir());
}

module.exports = { totals, isAvailable, costForLine, modelTier, PRICING };
