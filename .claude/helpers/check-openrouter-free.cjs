const https = require('https');
const http = require('http');

const OR_URL = 'https://openrouter.ai/api/v1/models';
const TIMEOUT = 15000;

function fetch(url) {
  return new Promise((resolve, reject) => {
    const mod = url.startsWith('https') ? https : http;
    const req = mod.get(url, { timeout: TIMEOUT }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try { resolve(JSON.parse(data)); }
        catch { reject(new Error('Parse error')); }
      });
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('Timeout')); });
  });
}

// modele care suporta tool use (function calling) - known set
const TOOL_CAPABLE = new Set([
  'claude', 'gpt', 'mistral', 'llama', 'deepseek',
  'qwen', 'gemini', 'command', 'wizardlm', 'dbrx',
  'reka', 'cohere', 'perplexity', 'sonnet', 'haiku',
  'opus', 'mixtral', 'nous', 'hermes', 'functionary',
  'grok', 'aya', 'nemotron', 'minicpm', 'phi',
]);

function supportsToolUse(model) {
  const id = (model.id || '').toLowerCase();
  if (model.arch?.function_calling === true) return true;
  if (model.arch?.tool_use === true) return true;
  for (const kw of TOOL_CAPABLE) {
    if (id.includes(kw)) return true;
  }
  return false;
}

async function main() {
  console.log('Fetching OpenRouter models...\n');
  const data = await fetch(OR_URL);
  const models = data.data || [];

  const freeModels = models.filter(m => {
    const p = m.pricing || {};
    return parseFloat(p.prompt || 1) === 0 && parseFloat(p.completion || 1) === 0;
  });

  const withToolUse = freeModels.filter(m => supportsToolUse(m));

  console.log('=== MODELE GRATUITE PE OPENROUTER ===\n');
  console.log(`Total modele OpenRouter: ${models.length}`);
  console.log(`Modele gratuite: ${freeModels.length}`);
  console.log(`Gratuite + tool use: ${withToolUse.length}\n`);

  if (withToolUse.length === 0) {
    console.log('❌ Niciun model gratuit nu suporta tool use momentan.\n');
    console.log('Modele gratuite disponibile (fara tool use):');
    freeModels.forEach(m => console.log(`  - ${m.id}`));
    return;
  }

  console.log('Modele care functioneaza cu OpenCode:\n');
  withToolUse.forEach(m => {
    const p = m.pricing || {};
    console.log(`  ✅ ${m.id}`);
    console.log(`     Context: ${(m.context_length || '?').toLocaleString()} tokens`);
    console.log(`     Pricing: prompt=$${p.prompt}, completion=$${p.completion}\n`);
  });

  const extra = freeModels.filter(m => !supportsToolUse(m));
  if (extra.length > 0) {
    console.log(`\nModele gratuite FARA tool use (${extra.length}):`);
    extra.forEach(m => console.log(`  ❌ ${m.id}`));
  }
}

main().catch(err => {
  console.error('Eroare:', err.message);
  process.exit(1);
});
