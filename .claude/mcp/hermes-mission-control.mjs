#!/usr/bin/env node
/**
 * Hermes Mission Control — CCDEW MCP Integration Server
 * 
 * Expose mission-control.py HTTP API as CCDEW MCP tools.
 * All communication goes through the local HTTP server on port 51763.
 * 
 * Tools:
 *   hermes_snapshot       — Full system snapshot (agents, VPS, stats)
 *   hermes_health         — System health (CPU, RAM, disk, uptime)
 *   hermes_agent_log      — Log agent activity to mission control
 *   hermes_content_list   — List content documents
 *   hermes_content_create — Create a new content document
 *   hermes_board          — Get kanban board state
 *   hermes_sessions       — Get active sessions
 *   hermes_activity       — Get recent activity stream
 *   hermes_send_message   — Send message via Hermes gateway (SSE)
 */

const MC_PORT = process.env.HERMES_MC_PORT || "51763";
const MC_BASE = `http://127.0.0.1:${MC_PORT}`;

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  ListToolsRequestSchema,
  CallToolRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

const server = new Server(
  { name: "hermes-mission-control", version: "2.0.0" },
  { capabilities: { tools: {} } }
);

async function mcGet(path) {
  const url = `${MC_BASE}${path}`;
  const res = await fetch(url, { signal: AbortSignal.timeout(5000) });
  if (!res.ok) throw new Error(`GET ${url} → ${res.status}`);
  return res.json();
}

async function mcPost(path, body) {
  const url = `${MC_BASE}${path}`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(5000),
  });
  if (!res.ok) throw new Error(`POST ${url} → ${res.status}`);
  return res.json();
}

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "hermes_snapshot",
      description: "Full Hermes system snapshot — agents, VPS, stats, sessions, activity, memory, board",
      inputSchema: { type: "object", properties: {} },
    },
    {
      name: "hermes_health",
      description: "System health metrics — CPU %, RAM %, disk %, load, uptime",
      inputSchema: { type: "object", properties: {} },
    },
    {
      name: "hermes_agent_log",
      description: "Log agent activity to mission control database",
      inputSchema: {
        type: "object",
        properties: {
          action: { type: "string", description: "Action name (e.g. task_completed, analysis_done)" },
          details: { type: "string", description: "Description of what happened" },
          outcome: { type: "string", enum: ["success", "failure"], description: "Outcome" },
          tags: { type: "array", items: { type: "string" }, description: "Tags for filtering" },
        },
        required: ["action", "details"],
      },
    },
    {
      name: "hermes_content_list",
      description: "List all content documents in the Hermes content management system",
      inputSchema: { type: "object", properties: {} },
    },
    {
      name: "hermes_content_create",
      description: "Create a new content document in Hermes CMS",
      inputSchema: {
        type: "object",
        properties: {
          agent: { type: "string", description: "Agent name (orchestrator, analyst, writer, marketer, coder)" },
          title: { type: "string", description: "Document title" },
          content: { type: "string", description: "Document content (markdown)" },
          tags: { type: "array", items: { type: "string" }, description: "Tags" },
        },
        required: ["agent", "title", "content"],
      },
    },
    {
      name: "hermes_board",
      description: "Get the current kanban board state",
      inputSchema: { type: "object", properties: {} },
    },
    {
      name: "hermes_sessions",
      description: "Get all active Hermes sessions",
      inputSchema: { type: "object", properties: {} },
    },
    {
      name: "hermes_activity",
      description: "Get recent activity stream (last N actions)",
      inputSchema: {
        type: "object",
        properties: {
          limit: { type: "number", description: "Number of recent activities to return (default 20)" },
        },
      },
    },
  ],
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "hermes_snapshot": {
        const data = await mcGet("/api/snapshot");
        return {
          content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
        };
      }

      case "hermes_health": {
        const data = await mcGet("/api/health");
        return {
          content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
        };
      }

      case "hermes_agent_log": {
        const body = {
          action: args.action,
          details: args.details,
          outcome: args.outcome || "success",
          tags: args.tags || [],
        };
        const data = await mcPost("/api/log", body);
        return {
          content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
        };
      }

      case "hermes_content_list": {
        const data = await mcGet("/api/content");
        return {
          content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
        };
      }

      case "hermes_content_create": {
        const body = {
          agent: args.agent,
          title: args.title,
          content: args.content,
          tags: args.tags || [],
        };
        const data = await mcPost("/api/content", body);
        return {
          content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
        };
      }

      case "hermes_board": {
        const snap = await mcGet("/api/snapshot");
        return {
          content: [{ type: "text", text: JSON.stringify(snap.board || {}, null, 2) }],
        };
      }

      case "hermes_sessions": {
        const snap = await mcGet("/api/snapshot");
        return {
          content: [{ type: "text", text: JSON.stringify(snap.sessions || [], null, 2) }],
        };
      }

      case "hermes_activity": {
        const limit = args?.limit || 20;
        const snap = await mcGet("/api/snapshot");
        const activities = (snap.activity || []).slice(0, limit);
        return {
          content: [{ type: "text", text: JSON.stringify(activities, null, 2) }],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (err) {
    return {
      content: [{ type: "text", text: `Error: ${err.message}` }],
      isError: true,
    };
  }
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((err) => {
  console.error("Fatal:", err);
  process.exit(1);
});
