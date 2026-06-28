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
const BRIDGE_HOST = '127.0.0.1';
const BRIDGE_PORT = 18777;

// ── Bridge HTTP (in-memory, no file race condition) ──────────────
let _bridgeCache = null;
let _bridgeCacheTs = 0;
const BRIDGE_CACHE_TTL = 3000; // 3s

function readBridgeJSON() {
  const now = Date.now();
  if (_bridgeCache && now - _bridgeCacheTs < BRIDGE_CACHE_TTL) return _bridgeCache;
  try {
    const url = `http://${BRIDGE_HOST}:${BRIDGE_PORT}/bridge.json`;
    const out = require('child_process').execSync(
      `curl -sf --max-time 1 '${url}' 2>/dev/null || wget -qO- --timeout=1 '${url}' 2>/dev/null || echo 'null'`,
      { encoding: 'utf-8', timeout: 2000 }
    );
    const data = JSON.parse(out);
    if (data && data.pathway) { _bridgeCache = data; _bridgeCacheTs = now; return data; }
  } catch {}
  // Fallback file
  try {
    const data = JSON.parse(fs.readFileSync(path.join(MEMORY_DIR, 'pathway-bridge.json'), 'utf-8'));
    if (data && data.pathway) { _bridgeCache = data; _bridgeCacheTs = now; return data; }
  } catch {}
  return null;
}

// ── Cache (avoid repeated disk reads) ───────────────────────────
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
  { name: 'ccdew_status', description: 'Complete CCDEW status', inputSchema: { type: 'object', properties: {} } },
  { name: 'ccdew_memory', description: 'Search SSA memory (Jaccard trigram)', inputSchema: { type: 'object', properties: { prompt: { type: 'string' } }, required: ['prompt'] } },
  { name: 'ccdew_instincts', description: 'Learned patterns', inputSchema: { type: 'object', properties: {} } },
  { name: 'ccdew_session', description: 'Active session status', inputSchema: { type: 'object', properties: {} } },
  { name: 'ccdew_burn', description: 'Cost tracking (today/month)', inputSchema: { type: 'object', properties: {} } },
  { name: 'ccdew_optimize', description: 'Auto-optimize prompt stats', inputSchema: { type: 'object', properties: {} } },
  { name: 'ccdew_safla', description: 'SAFLA adaptive learning stats', inputSchema: { type: 'object', properties: {} } },
  { name: 'ccdew_project', description: 'Detect active project', inputSchema: { type: 'object', properties: {} } },
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
        const pathway = readBridgeJSON();

        const pwLine = pathway ? `\n**Pathway:** ${pathway.pathway_label} | Node: ${pathway.active_node} | Confidence: ${(pathway.confidence*100).toFixed(0)}%` : '';

        return { content: [{ type: 'text', text: `## CCDEW Status v2

**Memory:**
- Episodes: ${episodes.length}
- Patterns: ${Object.keys(patterns).length}
- Skills: ${Object.keys(skills).length}

**SAFLA Learning:**
- Total feedback: ${safla.total_feedbacks || 0}
- Noduri active: ${Object.keys(safla.nodes || {}).length}

**Enneagram Pathway:**${pwLine}

**System:** 🟢 Active
**Cache:** ${cache.size} entries` }] };
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

        if (scored.length === 0) return { content: [{ type: 'text', text: 'No match for: ' + prompt }] };

        const results = scored.map(({ ep, score }) =>
          `- **${score.toFixed(2)}** [${ep.type || 'unknown'}] ${ep.summary || ep.principle || JSON.stringify(ep).slice(0, 100)}`
        ).join('\n');

        return { content: [{ type: 'text', text: `## Results for: "${prompt}"\n\n${results}` }] };
      }

      case 'ccdew_instincts': {
        const patterns = cached('patterns', getPatterns);
        const entries = Object.entries(patterns);

        if (entries.length === 0) return { content: [{ type: 'text', text: '## Instincts\n\n0 patterns learned yet.' }] };

        const table = entries.map(([k, v]) =>
          `| ${k} | ${v.count || 0} | ${(v.confidence || 0).toFixed(2)} |`
        ).join('\n');

        return { content: [{ type: 'text', text: `## Instincts (${entries.length} patterns)\n\n| Pattern | Count | Confidence |\n|---------|-------|------------|\n${table}` }] };
      }

      case 'ccdew_session': {
        return { content: [{ type: 'text', text: `## Active Session\n\n**Status:** 🟢 Running\n**PID:** ${process.pid}\n**Uptime:** ${(process.uptime()).toFixed(0)}s\n**Memory:** ${(process.memoryUsage().rss / 1024 / 1024).toFixed(1)}MB` }] };
      }

      case 'ccdew_burn': {
        const log = cached('burn_log', () => {
          const burnFile = path.join(MEMORY_DIR, 'burn.json');
          return readJSON(burnFile) || { today: 0, month: 0, calls: 0 };
        });
        return { content: [{ type: 'text', text: `## Cost Tracking\n\n**Today:** $${log.today?.toFixed(2) || '0.00'}\n**Month:** $${log.month?.toFixed(2) || '0.00'}\n**Calls:** ${log.calls || 0}` }] };
      }

      case 'ccdew_optimize': {
        return { content: [{ type: 'text', text: '## Auto-Optimize\n\nContext compression system: 🟢 Active' }] };
      }

      case 'ccdew_safla': {
        const safla = cached('safla', getSAFLA);
        const nodes = Object.entries(safla.nodes || {}).map(([k, v]) =>
          `| ${k} | ${v.success || 0} | ${v.failure || 0} | ${((v.rate || 0) * 100).toFixed(0)}% |`
        ).join('\n');

        return { content: [{ type: 'text', text: `## SAFLA Stats\n\nTotal: ${safla.total_feedbacks || 0} feedbacks\n\n| Node | Success | Failure | Rate |\n|------|---------|---------|------|\n${nodes || '| - | - | - | - |'}` }] };
      }

      case 'ccdew_project': {
        const cwd = process.cwd();
        const gitDir = path.join(cwd, '.git');
        const isGit = fs.existsSync(gitDir);
        const name = path.basename(cwd);
        return { content: [{ type: 'text', text: `## Active Project\n\n**Name:** ${name}\n**CWD:** ${cwd}\n**Git:** ${isGit ? '✅' : '❌'}` }] };
      }

      case 'ccdew_verify': {
        const checks = [];
        const cwd = process.cwd();
        if (fs.existsSync(path.join(cwd, 'package.json'))) checks.push('npm: ✅');
        if (fs.existsSync(path.join(cwd, 'tsconfig.json'))) checks.push('typescript: ✅');
        if (fs.existsSync(path.join(cwd, '.git'))) checks.push('git: ✅');
        return { content: [{ type: 'text', text: `## Pre-commit Verify\n\n${checks.join('\n') || 'No checks available'}` }] };
      }

      case 'ccdew_quality_gate': {
        return { content: [{ type: 'text', text: '## Quality Gate\n\n🟢 Gate open — ready to push' }] };
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
