#!/usr/bin/env node
/**
 * bridge-mcp-server.js — Claude Code ↔ OpenCode MCP Bridge
 *
 * Claude Code: adauga in mcp.json ca MCP server stdio.
 * Cand Claude apeleaza un tool, merge prin bridge catre OpenCode si invers.
 *
 * Foloseste un bridge TCP pe localhost:9130 ca backend.
 */

// ── MCP Protocol (stdio JSON-RPC) ──────────────────────────────────────────
const BRIDGE_URL = "http://localhost:9130";
const BRIDGE_TOKEN = "bridge-2026";

// ── Readline for stdin ─────────────────────────────────────────────────────
const readline = require("readline");
const http = require("http");

const rl = readline.createInterface({ input: process.stdin });
let buffer = "";
let requestId = 0;

function jsonRpc(method, params) {
  requestId++;
  return JSON.stringify({ jsonrpc: "2.0", id: requestId, method, params }) + "\n";
}

function send(msg) {
  process.stdout.write(JSON.stringify(msg) + "\n");
}

async function bridgeSend(to, type, payload) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify({ to, type, payload, token: BRIDGE_TOKEN });
    const req = http.request(`${BRIDGE_URL}/send`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Content-Length": Buffer.byteLength(data),
        "X-Bridge-Token": BRIDGE_TOKEN,
      },
    }, (res) => {
      let body = "";
      res.on("data", (chunk) => body += chunk);
      res.on("end", () => resolve(JSON.parse(body)));
    });
    req.on("error", reject);
    req.write(data);
    req.end();
  });
}

async function bridgePoll(to) {
  return new Promise((resolve, reject) => {
    http.get(`${BRIDGE_URL}/pending?to=${to}&token=${BRIDGE_TOKEN}`, (res) => {
      let body = "";
      res.on("data", (chunk) => body += chunk);
      res.on("end", () => {
        try { resolve(JSON.parse(body)); }
        catch { resolve({ messages: [] }); }
      });
    }).on("error", reject);
  });
}

// ── Tool handlers ──────────────────────────────────────────────────────────
const TOOLS = {
  send_to_opencode: {
    name: "send_to_opencode",
    description: "Trimite un task sau un mesaj catre OpenCode. OpenCode il va procesa si intoarce rezultatul.",
    inputSchema: {
      type: "object",
      properties: {
        task: { type: "string", description: "Task-ul sau intrebarea pentru OpenCode" },
        context: { type: "string", description: "Context optional (fisiere relevante, stare curenta)" },
        priority: { type: "string", enum: ["low", "normal", "high"], description: "Prioritate" },
      },
      required: ["task"],
    },
    handler: async (args) => {
      const result = await bridgeSend("opencode", "task", {
        task: args.task,
        context: args.context || "",
        priority: args.priority || "normal",
        source: "claude",
        timestamp: new Date().toISOString(),
      });
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    },
  },
  read_from_opencode: {
    name: "read_from_opencode",
    description: "Citeste mesajele/pending tasks primite de la OpenCode.",
    inputSchema: {
      type: "object",
      properties: {
        mark_read: { type: "boolean", description: "Marcheaza mesajele ca citite" },
      },
    },
    handler: async (args) => {
      const result = await bridgePoll("claude");
      const msgs = result.messages || [];
      if (msgs.length === 0) {
        return { content: [{ type: "text", text: "Niciun mesaj de la OpenCode." }] };
      }
      const text = msgs.map((m, i) => `[${i + 1}] ${m.type.toUpperCase()}: ${m.payload?.task || m.payload?.text || JSON.stringify(m.payload)}\n  La: ${m.timestamp}`).join("\n\n");
      return { content: [{ type: "text", text }] };
    },
  },
};

// ── MCP lifecycle ──────────────────────────────────────────────────────────
async function initialize() {
  // Ping bridge to make sure it's alive
  try {
    await bridgeSend("claude", "ping", { text: "Claude Code connected" });
  } catch (e) {
    // Bridge might not be running yet - log but don't fail
  }
}

rl.on("line", async (line) => {
  buffer += line;
  try {
    const msg = JSON.parse(buffer);
    buffer = "";

    if (msg.method === "initialize") {
      await initialize();
      send({
        jsonrpc: "2.0",
        id: msg.id,
        result: {
          protocolVersion: "2024-11-05",
          capabilities: {
            tools: {},
            resources: {},
          },
          serverInfo: { name: "bridge-claude-opencode", version: "1.0.0" },
        },
      });
    } else if (msg.method === "tools/list") {
      send({
        jsonrpc: "2.0",
        id: msg.id,
        result: { tools: Object.values(TOOLS) },
      });
    } else if (msg.method === "tools/call") {
      const tool = TOOLS[msg.params.name];
      if (!tool) {
        send({ jsonrpc: "2.0", id: msg.id, error: { code: -32601, message: `Tool not found: ${msg.params.name}` } });
        return;
      }
      try {
        const result = await tool.handler(msg.params.arguments || {});
        send({ jsonrpc: "2.0", id: msg.id, result });
      } catch (e) {
        send({ jsonrpc: "2.0", id: msg.id, error: { code: -32000, message: e.message } });
      }
    } else if (msg.method === "notifications/initialized") {
      // ignore
    } else {
      send({ jsonrpc: "2.0", id: msg.id || null, error: { code: -32601, message: `Unknown method: ${msg.method}` } });
    }
  } catch (e) {
    // Incomplete line - wait for more
  }
});

process.stdin.on("end", () => process.exit(0));
