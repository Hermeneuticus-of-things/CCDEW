#!/usr/bin/env node
'use strict';
/**
 * OpenCode LLM Gateway MCP v2 — Lightweight
 * Lists models, basic chat completion via OpenRouter
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} = require('@modelcontextprotocol/sdk/types.js');

const https = require('https');

const OPENROUTER_KEY = process.env.OPENROUTER_API_KEY || '';
const OPENROUTER_URL = 'https://openrouter.ai/api/v1';

function orRequest(path, body) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(body);
    const req = https.request({
      hostname: 'openrouter.ai',
      path,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${OPENROUTER_KEY}`,
        'Content-Length': Buffer.byteLength(data),
      },
      timeout: 30000,
    }, res => {
      let buf = '';
      res.on('data', c => buf += c);
      res.on('end', () => {
        try { resolve(JSON.parse(buf)); } catch { resolve({ error: buf }); }
      });
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('timeout')); });
    req.write(data);
    req.end();
  });
}

const server = new Server(
  { name: 'opencode-llm-gateway', version: '2.0.0' },
  { capabilities: { tools: {} } }
);

const FREE_MODELS = [
  'openrouter/free',
  'google/gemma-4-26b-a4b-it:free',
  'google/gemma-4-31b-it:free',
  'meta-llama/llama-3.3-70b-instruct:free',
  'qwen/qwen3-coder:free',
  'nvidia/nemotron-3-ultra-550b-a55b:free',
];

const TOOLS = [
  { name: 'list_models', description: 'List available free models', inputSchema: { type: 'object', properties: {} } },
  { name: 'chat_completion', description: 'Chat via OpenRouter', inputSchema: { type: 'object', properties: { model: { type: 'string' }, messages: { type: 'array' }, max_tokens: { type: 'number', default: 1024 } }, required: ['messages'] } },
  { name: 'token_count', description: 'Estimate tokens', inputSchema: { type: 'object', properties: { text: { type: 'string' } }, required: ['text'] } },
];

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case 'list_models': {
        return { content: [{ type: 'text', text: `## Free Models\n\n${FREE_MODELS.map(m => `- ${m}`).join('\n')}` }] };
      }

      case 'chat_completion': {
        if (!OPENROUTER_KEY) return { content: [{ type: 'text', text: '❌ OPENROUTER_API_KEY not set' }], isError: true };
        const model = args.model || 'openrouter/free';
        const result = await orRequest('/chat/completions', {
          model,
          messages: args.messages,
          max_tokens: args.max_tokens || 1024,
        });
        const reply = result.choices?.[0]?.message?.content || JSON.stringify(result);
        return { content: [{ type: 'text', text: reply }] };
      }

      case 'token_count': {
        const est = Math.ceil(args.text.length / 4);
        return { content: [{ type: 'text', text: `~${est} tokens (${args.text.length} chars)` }] };
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
  process.stderr.write('[LLM Gateway v2] 🟢 Started\n');
}

main().catch(e => {
  process.stderr.write(`[LLM Gateway v2] ❌ ${e.message}\n`);
  process.exit(1);
});
