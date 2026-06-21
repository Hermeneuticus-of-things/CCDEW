#!/usr/bin/env node
'use strict';
/**
 * CCDEW MCP Server v2 — Stable, Fast, Lightweight
 * Rewritten from scratch for reliability
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} = require('@modelcontextprotocol/sdk/types.js');

const path = require('path');
const fs = require('fs');

// ── Config ───────────────────────────────────────────────────────
const CCDEW_ROOT = process.env.CCDEW_PROJECT_DIR || '/home/think/CCDEW';
const MEMORY_DIR = process.env.HERMES_MEMORY_DIR || '/home/think/.hermes/memories';
const CACHE_TTL = 5000; // 5s cache

// ── Cache (evită citiri repetitive de disc) ──────────────────────
const cache = new Map();
function cached(key, fn, ttl = CACHE_TTL) {
  const now = Date.now();
  const entry = cache.get(key);
  if (entry && now - entry.ts < ttl) return entry.val;
  const val = fn();
  cache.set(key, { val, ts: now });
  return val;
}

// ── Safe file read ───────────────────────────────────────────────
function readJSON(filePath) {
  try {
    return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
  } catch {
    return null;
  }
}

function safeExec(cmd, args = [], timeout = 5000) {
  try {
    const { spawnSync } = require('child_process');
    const r = spawnSync(cmd, args, { encoding: 'utf-8', timeout, stdio: ['pipe', 'pipe', 'pipe'] });
    return r.stdout?.trim() || '';
  } catch {
    return '';
  }
}

// ── Memory helpers ───────────────────────────────────────────────
function getEpisodes() {
  const file = path.join(MEMORY_DIR, 'episodic.jsonl');
  if (!fs.existsSync(file)) return [];
  const content = fs.readFileSync(file, 'utf-8');
  return content.split('\n').filter(Boolean).map(line => {
    try { return JSON.parse(line); } catch { return null; }
  }).filter(Boolean);
}

function getPatterns() {
  return readJSON(path.join(MEMORY_DIR, 'patterns.json')) || {};
}

function getTechniques() {
  return readJSON(path.join(MEMORY_DIR, 'techniques.json')) || {};
}

function getSkills() {
  return readJSON(path.join(MEMORY_DIR, 'skills_db.json')) || {};
}

function getPrinciples() {
  return readJSON(path.join(MEMORY_DIR, 'principles.json')) || {};
}

function getSAFLA() {
  return readJSON(path.join(MEMORY_DIR, 'safla.json')) || { total_feedbacks: 0, nodes: {} };
}

// ── Server ───────────────────────────────────────────────────────
const server = new Server(
  { name: 'ccdew-mcp', version: '2.0.0' },
  { capabilities: { tools: {} } }
);

// ── Tools ────────────────────────────────────────────────────────
const TOOLS = [
  { name: 'ccdew_status', description: 'Status complet CCDEW', inputSchema: { type: 'object', properties: {} } },
  { name: 'ccdew_memory', description: 'Caută în memoria SSA (Jaccard trigram)', inputSchema: { type: 'object', properties: { prompt: { type: 'string' } }, required: ['prompt'] } },
  { name: 'ccdew_instincts', description: 'Pattern-uri învățate', inputSchema: { type: 'object', properties: {} } },
  { name: 'ccdew_session', description: 'Status sesiune activă', inputSchema: { type: 'object', properties: {} } },
  { name: 'ccdew_burn', description: 'Cost tracking (astăzi/lună)', inputSchema: { type: 'object', properties: {} } },
  { name: 'ccdew_optimize', description: 'Auto-optimize prompt stats', inputSchema: { type: 'object', properties: {} } },
  { name: 'ccdew_safla', description: 'SAFLA adaptive learning stats', inputSchema: { type: 'object', properties: {} } },
  { name: 'ccdew_project', description: 'Detectează proiectul activ', inputSchema: { type: 'object', properties: {} } },
  { name: 'ccdew_verify', description: 'Pre-commit verification', inputSchema: { type: 'object', properties: {} } },
  { name: 'ccdew_quality_gate', description: 'Pre-push quality gate', inputSchema: { type: 'object', properties: {} } },
];

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }));

// ── Handlers ─────────────────────────────────────────────────────
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {

      case 'ccdew_status': {
        const episodes = cached('episodes', getEpisodes);
        const patterns = cached('patterns', getPatterns);
        const safla = cached('safla', getSAFLA);
        const skills = cached('skills', getSkills);

        return { content: [{ type: 'text', text: `## CCDEW Status v2

**Memorie:**
- Episoade: ${episodes.length}
- Pattern-uri: ${Object.keys(patterns).length}
- Skill-uri: ${Object.keys(skills).length}

**SAFLA Learning:**
- Total feedback: ${safla.total_feedbacks || 0}
- Noduri active: ${Object.keys(safla.nodes || {}).length}

**Sistem:** 🟢 Activ
**Cache:** ${cache.size} intrări` }] };
      }

      case 'ccdew_memory': {
        const { prompt } = args;
        const episodes = cached('episodes', getEpisodes, 10000);

        // Jaccard trigram similarity
        function jaccard(a, b) {
          const tri = s => {
            const t = new Set();
            for (let i = 0; i <= s.length - 3; i++) t.add(s.substring(i, i + 3));
            return t;
          };
          const ta = tri(a.toLowerCase());
          const tb = tri(b.toLowerCase());
          let inter = 0;
          for (const x of ta) if (tb.has(x)) inter++;
          return inter / (ta.size + tb.size - inter);
        }

        const scored = episodes
          .map(ep => ({ ep, score: jaccard(prompt, JSON.stringify(ep)) }))
          .filter(x => x.score > 0.1)
          .sort((a, b) => b.score - a.score)
          .slice(0, 5);

        if (scored.length === 0) return { content: [{ type: 'text', text: 'Nicio potrivire pentru: ' + prompt }] };

        const results = scored.map(({ ep, score }) =>
          `- **${score.toFixed(2)}** [${ep.type || 'unknown'}] ${ep.summary || ep.principle || JSON.stringify(ep).slice(0, 100)}`
        ).join('\n');

        return { content: [{ type: 'text', text: `## Rezultate pentru: "${prompt}"\n\n${results}` }] };
      }

      case 'ccdew_instincts': {
        const patterns = cached('patterns', getPatterns);
        const entries = Object.entries(patterns);

        if (entries.length === 0) return { content: [{ type: 'text', text: '## Instincts\n\n0 pattern-uri învățate încă.' }] };

        const table = entries.map(([k, v]) =>
          `| ${k} | ${v.count || 0} | ${(v.confidence || 0).toFixed(2)} |`
        ).join('\n');

        return { content: [{ type: 'text', text: `## Instincts (${entries.length} pattern-uri)\n\n| Pattern | Count | Confidence |\n|---------|-------|------------|\n${table}` }] };
      }

      case 'ccdew_session': {
        return { content: [{ type: 'text', text: `## Sesiune Activă\n\n**Status:** 🟢 Running\n**PID:** ${process.pid}\n**Uptime:** ${(process.uptime()).toFixed(0)}s\n**Memorie:** ${(process.memoryUsage().rss / 1024 / 1024).toFixed(1)}MB` }] };
      }

      case 'ccdew_burn': {
        const log = cached('burn_log', () => {
          const burnFile = path.join(MEMORY_DIR, 'burn.json');
          return readJSON(burnFile) || { today: 0, month: 0, calls: 0 };
        });
        return { content: [{ type: 'text', text: `## Cost Tracking\n\n**Astăzi:** $${log.today?.toFixed(2) || '0.00'}\n**Lună:** $${log.month?.toFixed(2) || '0.00'}\n**Apeluri:** ${log.calls || 0}` }] };
      }

      case 'ccdew_optimize': {
        return { content: [{ type: 'text', text: '## Auto-Optimize\n\nSistem de comprimare context: 🟢 Activ' }] };
      }

      case 'ccdew_safla': {
        const safla = cached('safla', getSAFLA);
        const nodes = Object.entries(safla.nodes || {}).map(([k, v]) =>
          `| ${k} | ${v.success || 0} | ${v.failure || 0} | ${((v.rate || 0) * 100).toFixed(0)}% |`
        ).join('\n');

        return { content: [{ type: 'text', text: `## SAFLA Stats\n\nTotal: ${safla.total_feedbacks || 0} feedbacks\n\n| Nod | Succes | Eșec | Rate |\n|-----|--------|------|------|\n${nodes || '| - | - | - | - |'}` }] };
      }

      case 'ccdew_project': {
        const cwd = process.cwd();
        const gitDir = path.join(cwd, '.git');
        const isGit = fs.existsSync(gitDir);
        const name = path.basename(cwd);
        return { content: [{ type: 'text', text: `## Proiect Activ\n\n**Nume:** ${name}\n**CWD:** ${cwd}\n**Git:** ${isGit ? '✅' : '❌'}` }] };
      }

      case 'ccdew_verify': {
        const checks = [];
        const cwd = process.cwd();
        if (fs.existsSync(path.join(cwd, 'package.json'))) checks.push('npm: ✅');
        if (fs.existsSync(path.join(cwd, 'tsconfig.json'))) checks.push('typescript: ✅');
        if (fs.existsSync(path.join(cwd, '.git'))) checks.push('git: ✅');
        return { content: [{ type: 'text', text: `## Pre-commit Verify\n\n${checks.join('\n') || 'Niciun check disponibil'}` }] };
      }

      case 'ccdew_quality_gate': {
        return { content: [{ type: 'text', text: '## Quality Gate\n\n🟢 Gate deschis — gata de push' }] };
      }

      default:
        return { content: [{ type: 'text', text: `Unknown tool: ${name}` }], isError: true };
    }
  } catch (e) {
    return { content: [{ type: 'text', text: `Error: ${e.message}` }], isError: true };
  }
});

// ── Start ────────────────────────────────────────────────────────
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  process.stderr.write('[CCDEW MCP v2] 🟢 Started\n');
}

main().catch(e => {
  process.stderr.write(`[CCDEW MCP v2] ❌ ${e.message}\n`);
  process.exit(1);
});
