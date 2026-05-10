---
name: MCP claude-flow `mcp start` arg fix
severity: HIGH
version: v3.1
date: 2026-05-10
status: applied (requires Claude Code restart to take effect)
tags: [mcp, ruflo, integration, blocker]
---

# MCP claude-flow `mcp start` arg fix

## Context
`~/.claude.json::mcpServers["claude-flow"].args` was `["D:/Cloude Code/ruflo/bin/cli.js"]` — without the `mcp start` subcommand. Invoking ruflo CLI without args prints help and exits in 611ms. Claude Code attempts JSON-RPC handshake on stdin/stdout, receives help text + exit 0, marks MCP dead. **The user has to restart Claude Code each time hoping it works.**

## Investigation
- Manual handshake test: `echo '{"jsonrpc":"2.0",...}' | ruflo mcp start` → responds correctly with `{"name":"ruflo","version":"3.0.0","capabilities":{...}}`
- ONNX warning on stderr (does not corrupt stdout JSON-RPC)
- Server is functional, only the start command was missing in config

## Decision
**Patch `~/.claude.json` with `args: [..., "mcp", "start"]`.**

## Rationale
- The single change required for MCP to attach permanently
- Backup created: `~/.claude.json.bak.2026-05-10` (22915 bytes, identical pre-fix)
- Instantly reversible: `cp .claude.json.bak.2026-05-10 .claude.json`

## Consequences
- ⚠️ Requires **Claude Code restart** (config is read at startup)
- ✅ After restart: `mcp__claude-flow__*` tools become available (`swarm_init`, `agent_spawn`, `memory_search`, etc.)
- ✅ The 12 persisted Ruflo agents become spawn-able for real (they were idle due to missing MCP)
- ⚠️ ONNX onnxruntime-node still missing in `D:/Cloude Code/ruflo/` — local vector embeddings disabled

## Current status
- Config patched: ✅
- Restart needed for effect: ⏳ pending user action
- ONNX install needed: `cd D:/Cloude Code/ruflo && npm install onnxruntime-node`

## Manual post-restart verification
```bash
# In a new Claude Code session:
# ToolSearch +swarm_init  → must find mcp__claude-flow__swarm_init
# (in current pre-restart session: "No matching deferred tools found")
```
