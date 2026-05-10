'use strict';
/**
 * Centralized model pricing (USD per 1M tokens).
 * Source: Anthropic public pricing — keep this in one place to avoid drift.
 *
 * Update procedure:
 *   1. Verify against https://www.anthropic.com/pricing
 *   2. Bump PRICING_VERSION below
 *   3. Re-run: node .claude/helpers/tests/pricing.test.cjs
 */

const PRICING_VERSION = '2026.05';

const PRICING = {
  opus:   { input: 15.00, output: 75.00 },
  sonnet: { input:  3.00, output: 15.00 },
  haiku:  { input:  0.80, output:  4.00 },
};

const CACHE_CREATE_MULT = 1.25;
const CACHE_READ_MULT   = 0.10;

const MODEL_TIER_MAP = {
  // current generation (4.x)
  'claude-opus-4-7':            'opus',
  'claude-sonnet-4-6':          'sonnet',
  'claude-haiku-4-5':           'haiku',
  // dated variants (Anthropic format: <model>-<YYYYMMDD>)
  'claude-haiku-4-5-20251001':  'haiku',
};

function modelTier(modelName) {
  if (!modelName) return 'sonnet';
  const exact = MODEL_TIER_MAP[modelName];
  if (exact) return exact;
  const m = String(modelName).toLowerCase();
  if (m.includes('opus'))  return 'opus';
  if (m.includes('haiku')) return 'haiku';
  return 'sonnet';
}

function pricingFor(modelName) {
  return PRICING[modelTier(modelName)];
}

function defaultModel() {
  return 'claude-opus-4-7';
}

function lightweightModel() {
  return 'claude-haiku-4-5-20251001';
}

module.exports = {
  PRICING_VERSION,
  PRICING,
  CACHE_CREATE_MULT,
  CACHE_READ_MULT,
  MODEL_TIER_MAP,
  modelTier,
  pricingFor,
  defaultModel,
  lightweightModel,
};
