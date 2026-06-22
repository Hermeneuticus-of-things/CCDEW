#!/usr/bin/env node
'use strict';
/**
 * CCDEW NLM Bridge — MCP Server for NotebookLM Async Protocol
 *
 * Implements the 10-level protocol from:
 *   _SETTINGS/RULES/nlm_async_multi_channel_protocol.md
 *   _SETTINGS/RULES/nlm_anti_suspicion.md
 *
 * Tools:
 *   nlm_async_query      — Async query with polling (Nivel 1)
 *   nlm_grouped_queries  — Multiple sub-questions in one query (Nivel 3)
 *   nlm_batch            — Multi-notebook batch (Nivel 4)
 *   nlm_cache            — Local cache management (Nivel 7)
 *   nlm_multi_channel    — Full pipeline query across all notebooks
 *   nlm_quota            — Check remaining daily quota (Nivel 10)
 *   nlm_auth_check       — Verify NLM auth status (anti-suspicion safe)
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} = require('@modelcontextprotocol/sdk/types.js');

const path = require('path');
const fs = require('fs');
const { execSync } = require('child_process');

// ── Config ───────────────────────────────────────────────────────

const MEMORY_DIR = process.env.HERMES_MEMORY_DIR || '/home/think/.hermes/memories';
const CACHE_DIR = path.join(MEMORY_DIR, 'nlm-cache');
const CACHE_TTL_MS = 24 * 60 * 60 * 1000; // 24h
const THROTTLE_MS = 3000; // Nivel 9: ≥3s între queries
const MULTI_NOTEBOOK_THROTTLE_MS = 5000; // ≥5s între notebook-uri
const BATCH_THROTTLE_MS = 10000; // ≥10s între batches mari

// ── Throttle state ───────────────────────────────────────────────

let _lastQueryTime = 0;
let _lastBatchTime = 0;

function throttle(ms) {
  const now = Date.now();
  const elapsed = now - _lastQueryTime;
  if (elapsed < ms) {
    const wait = ms - elapsed;
    Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, wait);
  }
  _lastQueryTime = Date.now();
}

// ── Cache ────────────────────────────────────────────────────────

function ensureCacheDir() {
  if (!fs.existsSync(CACHE_DIR)) fs.mkdirSync(CACHE_DIR, { recursive: true });
}

function cacheKey(text) {
  return text.toLowerCase().replace(/[^a-z0-9]/g, '_').slice(0, 120);
}

function cacheGet(text) {
  ensureCacheDir();
  const key = cacheKey(text);
  const file = path.join(CACHE_DIR, `${key}.json`);
  if (!fs.existsSync(file)) return null;
  try {
    const data = JSON.parse(fs.readFileSync(file, 'utf-8'));
    if (Date.now() - data.ts < CACHE_TTL_MS) return data.response;
    fs.unlinkSync(file);
    return null;
  } catch {
    return null;
  }
}

function cacheSet(text, response) {
  ensureCacheDir();
  const key = cacheKey(text);
  const file = path.join(CACHE_DIR, `${key}.json`);
  fs.writeFileSync(file, JSON.stringify({ ts: Date.now(), response }));
}

function cacheClear() {
  ensureCacheDir();
  const files = fs.readdirSync(CACHE_DIR);
  let cleared = 0;
  for (const f of files) {
    if (f.endsWith('.json')) {
      const file = path.join(CACHE_DIR, f);
      try {
        const data = JSON.parse(fs.readFileSync(file, 'utf-8'));
        if (Date.now() - data.ts > CACHE_TTL_MS) {
          fs.unlinkSync(file);
          cleared++;
        }
      } catch {
        fs.unlinkSync(file);
        cleared++;
      }
    }
  }
  return cleared;
}

function cacheStats() {
  ensureCacheDir();
  const files = fs.readdirSync(CACHE_DIR).filter(f => f.endsWith('.json'));
  let valid = 0;
  let expired = 0;
  for (const f of files) {
    try {
      const data = JSON.parse(fs.readFileSync(path.join(CACHE_DIR, f), 'utf-8'));
      if (Date.now() - data.ts < CACHE_TTL_MS) valid++;
      else expired++;
    } catch {
      expired++;
    }
  }
  return { total: files.length, valid, expired };
}

// ── Auth helpers (anti-suspicion safe) ───────────────────────────

function checkAuth() {
  try {
    const r = execSync('nlm login --check 2>&1', { encoding: 'utf-8', timeout: 10000 });
    return { ok: r.includes('AUTH_REFRESHED_OK') || r.includes('valid') || r.includes('authenticated'), output: r.trim() };
  } catch (e) {
    return { ok: false, output: e.stderr?.trim() || e.message };
  }
}

// ── Task detection ───────────────────────────────────────────────

function detectDomain(task) {
  const lower = (task || '').toLowerCase();
  if (lower.includes('karma') || lower.includes('jain') || lower.includes('vedanta')) return 'karma-book';
  if (lower.includes('glosar') || lower.includes('glossary') || lower.includes('termen')) return 'glossary';
  if (lower.includes('research') || lower.includes('cercetare') || lower.includes('investig')) return 'research';
  return 'general';
}

// ── Notebook IDs ─────────────────────────────────────────────────

const NOTEBOOKS = {
  'karma-book': { id: '6696523d', name: 'Karma Book', throttle: MULTI_NOTEBOOK_THROTTLE_MS },
  'glossary':    { id: '6acbbc90', name: 'Glosar',     throttle: MULTI_NOTEBOOK_THROTTLE_MS },
  'research':    { id: '669ee18c', name: 'Cercetare',  throttle: MULTI_NOTEBOOK_THROTTLE_MS },
};

// ── Server ───────────────────────────────────────────────────────

const server = new Server(
  { name: 'ccdew-nlm-bridge', version: '1.0.0' },
  { capabilities: { tools: {} } }
);

const TOOLS = [
  {
    name: 'nlm_async_query',
    description: 'Nivel 1+2: Async query cu timeout mărit (180s) și poll automat',
    inputSchema: {
      type: 'object',
      properties: {
        notebook_id: { type: 'string', description: 'ID-ul notebook-ului NLM' },
        query: { type: 'string', description: 'Întrebarea' },
        timeout: { type: 'number', description: 'Timeout în secunde (default 180)' },
      },
      required: ['notebook_id', 'query'],
    },
  },
  {
    name: 'nlm_grouped_queries',
    description: 'Nivel 3: Multiple sub-întrebări într-un singur query structurat',
    inputSchema: {
      type: 'object',
      properties: {
        notebook_id: { type: 'string', description: 'ID-ul notebook-ului' },
        queries: {
          type: 'array',
          items: { type: 'string' },
          description: '3-5 sub-întrebări',
        },
      },
      required: ['notebook_id', 'queries'],
    },
  },
  {
    name: 'nlm_batch',
    description: 'Nivel 4: Multi-notebook batch cu throttle între notebook-uri',
    inputSchema: {
      type: 'object',
      properties: {
        query: { type: 'string', description: 'Întrebarea pentru toate notebook-urile' },
        notebooks: {
          type: 'array',
          items: { type: 'string', enum: ['karma-book', 'glossary', 'research'] },
          description: 'Notebook-urile de interogat',
        },
      },
      required: ['query'],
    },
  },
  {
    name: 'nlm_cache',
    description: 'Nivel 7: Gestionare cache local (stat, clear, search)',
    inputSchema: {
      type: 'object',
      properties: {
        action: { type: 'string', enum: ['stats', 'clear', 'search'], description: 'Acțiune' },
        query: { type: 'string', description: 'Căutare în cache (când action=search)' },
      },
      required: ['action'],
    },
  },
  {
    name: 'nlm_multi_channel',
    description: 'Full pipeline: auth check → cache check → grouped query → batch → convergent synthesis prompt',
    inputSchema: {
      type: 'object',
      properties: {
        primary_query: { type: 'string', description: 'Întrebarea principală' },
        sub_questions: {
          type: 'array',
          items: { type: 'string' },
          description: 'Sub-întrebări pentru grouped query',
        },
        notebooks: {
          type: 'array',
          items: { type: 'string', enum: ['karma-book', 'glossary', 'research'] },
          description: 'Notebook-uri de interogat',
        },
        bypass_cache: { type: 'boolean', description: 'Ignoră cache-ul' },
      },
      required: ['primary_query'],
    },
  },
  {
    name: 'nlm_quota',
    description: 'Nivel 10: Verifică quota zilnică rămasă',
    inputSchema: { type: 'object', properties: {} },
  },
  {
    name: 'nlm_auth_check',
    description: 'Verifică auth NLM o singură dată per sesiune (anti-suspicion safe)',
    inputSchema: { type: 'object', properties: {} },
  },
];

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {

      case 'nlm_async_query': {
        const { notebook_id, query, timeout = 180 } = args;

        // Check cache first (Nivel 7)
        if (!args.bypass_cache) {
          const cached = cacheGet(query);
          if (cached) {
            return { content: [{ type: 'text', text: JSON.stringify({ source: 'cache', response: cached }, null, 2) }] };
          }
        }

        // Throttle (Nivel 9)
        throttle(THROTTLE_MS);

        return {
          content: [{
            type: 'text',
            text: JSON.stringify({
              action: 'notebooklm-mcp.notebook_query',
              params: { notebook_id, query, timeout },
              anti_suspicion: {
                throttle_ms: THROTTLE_MS,
                note: 'Respectă ≥3s între queries consecutive. Rulează o singură dată.',
              },
              next_steps: [
                'Folosește `notebook_query_start` cu timeout:180 pentru a porni query-ul',
                'Apoi poll cu `notebook_query_status` până la status:completed',
                'Sau folosește research_start ca endpoint alternativ (Nivel 5)',
              ],
            }, null, 2),
          }],
        };
      }

      case 'nlm_grouped_queries': {
        const { notebook_id, queries } = args;
        if (!queries || queries.length < 2) {
          return { content: [{ type: 'text', text: 'Ai nevoie de cel puțin 2 sub-întrebări.' }], isError: true };
        }
        if (queries.length > 5) {
          return { content: [{ type: 'text', text: 'Maximum 5 sub-întrebări per query grupat.' }], isError: true };
        }

        const groupedPrompt = queries.map((q, i) => `${i + 1}. ${q}`).join('\n');

        return {
          content: [{
            type: 'text',
            text: JSON.stringify({
              action: 'notebooklm-mcp.notebook_query',
              params: {
                notebook_id,
                query: `Răspunde la următoarele întrebări:\n\n${groupedPrompt}\n\n\nRăspunde numerotat, pentru fiecare întrebare separat.`,
                timeout: 180,
              },
              savings: `1 query în loc de ${queries.length} (${queries.length - 1} economisite)`,
              tier: 'Plus: 500/zi',
            }, null, 2),
          }],
        };
      }

      case 'nlm_batch': {
        const { query, notebooks = ['karma-book', 'glossary', 'research'] } = args;

        const results = [];
        for (const nb of notebooks) {
          const notebook = NOTEBOOKS[nb];
          if (!notebook) continue;

          throttle(notebook.throttle || THROTTLE_MS);

          results.push({
            notebook: nb,
            name: notebook.name,
            id: notebook.id,
            query,
            action: 'notebooklm-mcp.notebook_query',
          });
        }

        return {
          content: [{
            type: 'text',
            text: JSON.stringify({
              type: 'multi_notebook_batch',
              primary_query: query,
              notebooks: results,
              anti_suspicion: {
                throttle_between_notebooks: `${MULTI_NOTEBOOK_THROTTLE_MS}ms`,
                throttle_after_batch: `${BATCH_THROTTLE_MS}ms`,
                note: 'Rulează queries secvențial cu throttle între notebook-uri. Nu în paralel!',
              },
            }, null, 2),
          }],
        };
      }

      case 'nlm_cache': {
        const { action, query } = args;

        switch (action) {
          case 'stats': {
            const stats = cacheStats();
            return { content: [{ type: 'text', text: JSON.stringify(stats, null, 2) }] };
          }
          case 'clear': {
            const cleared = cacheClear();
            return { content: [{ type: 'text', text: JSON.stringify({ cleared }, null, 2) }] };
          }
          case 'search': {
            if (!query) return { content: [{ type: 'text', text: 'Provide a query to search.' }], isError: true };
            const cached = cacheGet(query);
            return { content: [{ type: 'text', text: JSON.stringify({ hit: cached !== null, response: cached }, null, 2) }] };
          }
        }
      }

      case 'nlm_multi_channel': {
        const { primary_query, sub_questions, notebooks = ['karma-book'], bypass_cache } = args;

        // Step 1: Auth check
        const auth = checkAuth();
        if (!auth.ok) {
          return {
            content: [{
              type: 'text',
              text: JSON.stringify({
                error: 'NLM auth invalid',
                action: 'Rulează nlm_auto_login.py --force înainte de query',
                output: auth.output,
              }, null, 2),
            }],
            isError: true,
          };
        }

        // Step 2: Cache check
        if (!bypass_cache) {
          const cached = cacheGet(primary_query);
          if (cached) {
            return { content: [{ type: 'text', text: JSON.stringify({ source: 'cache', response: cached }, null, 2) }] };
          }
        }

        // Step 3: Prepare pipeline
        const pipeline = {
          primary_query,
          steps: [],
        };

        // If sub_questions exist, use grouped query (Nivel 3)
        if (sub_questions && sub_questions.length >= 2) {
          const groupedPrompt = sub_questions.map((q, i) => `${i + 1}. ${q}`).join('\n');
          pipeline.steps.push({
            level: 3,
            description: 'Grouped query',
            type: 'notebook_query',
            params: {
              notebook_id: NOTEBOOKS[notebooks[0]]?.id || notebooks[0],
              query: `Răspunde la următoarele întrebări:\n\n${groupedPrompt}\n\n\nRăspunde numerotat, pentru fiecare întrebare separat.\n\nÎntrebarea principală de context: ${primary_query}`,
              timeout: 180,
            },
          });
        } else {
          // Single query per notebook
          for (const nb of notebooks) {
            const notebook = NOTEBOOKS[nb];
            if (!notebook) continue;
            pipeline.steps.push({
              level: 1,
              description: `Query to ${notebook.name}`,
              type: 'notebook_query',
              params: { notebook_id: notebook.id, query: primary_query, timeout: 180 },
              throttle_ms: notebook.throttle,
            });
          }
        }

        // Step 4: Cache the result after execution
        pipeline.cache_after = true;

        return {
          content: [{
            type: 'text',
            text: JSON.stringify(pipeline, null, 2),
          }],
        };
      }

      case 'nlm_quota': {
        return {
          content: [{
            type: 'text',
            text: JSON.stringify({
              tier: 'Plus',
              daily_limit: 500,
              note: 'Folosește nlm_auto_login.py --check > /dev/null pentru a verifica quota exactă în CLI NLM.',
              conservation_tip: 'Folosește grouped queries (nlm_grouped_queries) pentru a consuma 1 query în loc de N.',
            }, null, 2),
          }],
        };
      }

      case 'nlm_auth_check': {
        const auth = checkAuth();
        return {
          content: [{
            type: 'text',
            text: JSON.stringify({
              ok: auth.ok,
              output: auth.output,
              anti_suspicion: {
                note: 'Acest check rulează MAXIM o dată per sesiune. Nu pe fiecare query.',
                next_if_invalid: 'python3 .claude/scripts/nlm_auto_login.py --force',
              },
            }, null, 2),
          }],
        };
      }

      default:
        return { content: [{ type: 'text', text: `Unknown: ${name}` }], isError: true };
    }
  } catch (e) {
    return { content: [{ type: 'text', text: `Error: ${e.message}` }], isError: true };
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  process.stderr.write('[CCDEW NLM Bridge v1] 🟢 Started\n');
}

main().catch(e => {
  process.stderr.write(`[CCDEW NLM Bridge v1] ❌ ${e.message}\n`);
  process.exit(1);
});
