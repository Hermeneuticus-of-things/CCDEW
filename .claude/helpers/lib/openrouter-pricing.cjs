'use strict';
/**
 * OpenRouter Pricing Engine - Real-time pricing from OpenRouter API
 * Fetches model pricing and credit balance from OpenRouter API
 * Caches locally with TTL for performance
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

const CACHE_DIR = path.join(os.homedir(), '.ccdew', 'cache');
const PRICING_CACHE = path.join(CACHE_DIR, 'openrouter-pricing.json');
const BALANCE_CACHE = path.join(CACHE_DIR, 'openrouter-balance.json');
const PRICING_TTL_MS = 6 * 60 * 60 * 1000; // 6 hours
const BALANCE_TTL_MS = 5 * 60 * 1000; // 5 minutes

const OPENROUTER_BASE = 'https://openrouter.ai/api/v1';

function ensureCacheDir() {
  if (!fs.existsSync(CACHE_DIR)) {
    fs.mkdirSync(CACHE_DIR, { recursive: true });
  }
}

function getApiKey() {
  return process.env.OPENROUTER_API_KEY || 
         process.env.OPENROUTER_API_KEY_FILE && fs.readFileSync(process.env.OPENROUTER_API_KEY_FILE, 'utf-8').trim() ||
         null;
}

async function fetchWithTimeout(url, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10000);
  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        'Authorization': `Bearer ${getApiKey()}`,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    clearTimeout(timeout);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return response.json();
  } catch (e) {
    clearTimeout(timeout);
    throw e;
  }
}

async function fetchModelsPricing() {
  const data = await fetchWithTimeout(`${OPENROUTER_BASE}/models`);
  const pricing = {};
  
  for (const model of data.data || []) {
    const id = model.id;
    const pricing_info = model.pricing || {};
    
    pricing[id] = {
      input: parseFloat(pricing_info.prompt) || 0,
      output: parseFloat(pricing_info.completion) || 0,
      // Some models have different pricing for cached tokens
      cache_read: parseFloat(pricing_info.cache_read) || 0,
      cache_write: parseFloat(pricing_info.cache_write) || 0,
      // Context length for reference
      context_length: model.context_length || 0,
      // Model metadata
      name: model.name || id,
      description: model.description || '',
      // Provider info
      provider: model.provider || 'unknown',
    };
  }
  
  return pricing;
}

async function fetchBalance() {
  const data = await fetchWithTimeout(`${OPENROUTER_BASE}/auth/key`);
  return {
    credits: parseFloat(data.data?.credits) || 0,
    limit: parseFloat(data.data?.limit) || null,
    usage: parseFloat(data.data?.usage) || 0,
    is_free: data.data?.is_free || false,
    label: data.data?.label || 'default',
  };
}

function readCache(cachePath, ttlMs) {
  try {
    if (!fs.existsSync(cachePath)) return null;
    const cached = JSON.parse(fs.readFileSync(cachePath, 'utf-8'));
    const age = Date.now() - new Date(cached.ts).getTime();
    if (age > ttlMs) return null;
    return cached.data;
  } catch { return null; }
}

function writeCache(cachePath, data) {
  ensureCacheDir();
  const payload = { ts: new Date().toISOString(), data };
  fs.writeFileSync(cachePath, JSON.stringify(payload, null, 2));
}

async function getPricing(modelId) {
  // Try cache first
  const cached = readCache(PRICING_CACHE, PRICING_TTL_MS);
  if (cached && cached[modelId]) {
    return cached[modelId];
  }
  
  // Fetch fresh pricing
  try {
    const pricing = await fetchModelsPricing();
    writeCache(PRICING_CACHE, pricing);
    return pricing[modelId] || null;
  } catch (e) {
    // Fallback to cached even if expired
    const stale = readCache(PRICING_CACHE, Infinity);
    if (stale && stale[modelId]) {
      console.warn(`[OpenRouter Pricing] Using stale cache for ${modelId}: ${e.message}`);
      return stale[modelId];
    }
    return null;
  }
}

async function getBalance() {
  const cached = readCache(BALANCE_CACHE, BALANCE_TTL_MS);
  if (cached) return cached;
  
  try {
    const balance = await fetchBalance();
    writeCache(BALANCE_CACHE, balance);
    return balance;
  } catch (e) {
    const stale = readCache(BALANCE_CACHE, Infinity);
    if (stale) {
      console.warn(`[OpenRouter Balance] Using stale cache: ${e.message}`);
      return stale;
    }
    return { credits: 0, error: e.message };
  }
}

async function calculateCost(modelId, usage) {
  const pricing = await getPricing(modelId);
  if (!pricing) return null;
  
  const u = usage;
  let cost = 0;
  
  // Standard tokens
  cost += (u.input_tokens || 0) * pricing.input / 1e6;
  cost += (u.output_tokens || 0) * pricing.output / 1e6;
  
  // Cache tokens (if available in pricing)
  if (pricing.cache_write && u.cache_creation_input_tokens) {
    cost += u.cache_creation_input_tokens * pricing.cache_write / 1e6;
  }
  if (pricing.cache_read && u.cache_read_input_tokens) {
    cost += u.cache_read_input_tokens * pricing.cache_read / 1e6;
  }
  
  return +cost.toFixed(6);
}

// Sync wrapper for codeburn compatibility
function calculateCostSync(modelId, usage) {
  // Try cached pricing only for sync
  const cached = readCache(PRICING_CACHE, PRICING_TTL_MS);
  if (cached && cached[modelId]) {
    const pricing = cached[modelId];
    const u = usage;
    let cost = 0;
    cost += (u.input_tokens || 0) * pricing.input / 1e6;
    cost += (u.output_tokens || 0) * pricing.output / 1e6;
    if (pricing.cache_write && u.cache_creation_input_tokens) {
      cost += u.cache_creation_input_tokens * pricing.cache_write / 1e6;
    }
    if (pricing.cache_read && u.cache_read_input_tokens) {
      cost += u.cache_read_input_tokens * pricing.cache_read / 1e6;
    }
    return +cost.toFixed(6);
  }
  return null;
}

// Background refresh
let refreshInterval = null;
function startBackgroundRefresh() {
  if (refreshInterval) return;
  refreshInterval = setInterval(async () => {
    try {
      await fetchModelsPricing().then(writeCache.bind(null, PRICING_CACHE));
      await fetchBalance().then(writeCache.bind(null, BALANCE_CACHE));
    } catch (e) {
      console.warn('[OpenRouter Pricing] Background refresh failed:', e.message);
    }
  }, PRICING_TTL_MS);
}

function stopBackgroundRefresh() {
  if (refreshInterval) {
    clearInterval(refreshInterval);
    refreshInterval = null;
  }
}

// CLI interface
if (require.main === module) {
  const cmd = process.argv[2];
  
  if (cmd === 'pricing') {
    fetchModelsPricing().then(p => {
      console.log(JSON.stringify(p, null, 2));
    }).catch(console.error);
  } else if (cmd === 'balance') {
    fetchBalance().then(console.log).catch(console.error);
  } else if (cmd === 'cost') {
    const model = process.argv[3];
    const input = parseInt(process.argv[4]) || 0;
    const output = parseInt(process.argv[5]) || 0;
    getPricing(model).then(p => {
      if (p) {
        const cost = (input * p.input + output * p.output) / 1e6;
        console.log(`Cost for ${model}: $${cost.toFixed(6)} (in:${input} out:${output})`);
      } else {
        console.log('Model not found');
      }
    });
  } else {
    console.log('Usage: node openrouter-pricing.cjs [pricing|balance|cost <model> <input_tokens> <output_tokens>]');
  }
}

module.exports = {
  getPricing,
  getBalance,
  calculateCost,
  calculateCostSync,
  startBackgroundRefresh,
  stopBackgroundRefresh,
  fetchModelsPricing,
  fetchBalance,
  readCache,
  writeCache,
};