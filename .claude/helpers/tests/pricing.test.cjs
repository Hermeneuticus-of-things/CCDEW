#!/usr/bin/env node
'use strict';
const { PRICING, modelTier, pricingFor, defaultModel, lightweightModel, PRICING_VERSION } = require('../lib/pricing.cjs');

let pass = 0, fail = 0;
function test(name, fn) {
  try { fn(); console.log(`[PASS] ${name}`); pass++; }
  catch (e) { console.log(`[FAIL] ${name}: ${e.message}`); fail++; }
}

test('PRICING has 3 tiers with input+output', () => {
  for (const tier of ['opus', 'sonnet', 'haiku']) {
    if (!PRICING[tier]) throw new Error('missing tier ' + tier);
    if (typeof PRICING[tier].input !== 'number') throw new Error(tier + '.input not number');
    if (typeof PRICING[tier].output !== 'number') throw new Error(tier + '.output not number');
    if (PRICING[tier].output <= PRICING[tier].input) throw new Error(tier + ' output should exceed input');
  }
});

test('opus > sonnet > haiku in input pricing', () => {
  if (!(PRICING.opus.input > PRICING.sonnet.input)) throw new Error('opus !> sonnet');
  if (!(PRICING.sonnet.input > PRICING.haiku.input)) throw new Error('sonnet !> haiku');
});

test('modelTier handles all canonical names', () => {
  if (modelTier('claude-opus-4-7') !== 'opus') throw new Error('opus map');
  if (modelTier('claude-sonnet-4-6') !== 'sonnet') throw new Error('sonnet map');
  if (modelTier('claude-haiku-4-5-20251001') !== 'haiku') throw new Error('haiku dated');
  if (modelTier(null) !== 'sonnet') throw new Error('null fallback');
  if (modelTier('') !== 'sonnet') throw new Error('empty fallback');
  if (modelTier('claude-haiku-99-99') !== 'haiku') throw new Error('haiku fuzzy');
});

test('pricingFor returns object with input/output', () => {
  const p = pricingFor('claude-opus-4-7');
  if (!p || typeof p.input !== 'number') throw new Error('bad pricingFor');
});

test('defaultModel + lightweightModel are non-empty strings', () => {
  if (typeof defaultModel() !== 'string' || !defaultModel()) throw new Error('defaultModel');
  if (typeof lightweightModel() !== 'string' || !lightweightModel()) throw new Error('lightweightModel');
});

test('PRICING_VERSION is YYYY.MM format', () => {
  if (!/^\d{4}\.\d{2}$/.test(PRICING_VERSION)) throw new Error('bad version: ' + PRICING_VERSION);
});

console.log(`\n=== SUMMARY: ${pass}/${pass + fail} passed ===`);
process.exit(fail > 0 ? 1 : 0);
