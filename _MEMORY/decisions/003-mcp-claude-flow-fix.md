---
name: MCP claude-flow `mcp start` arg fix
severity: HIGH
version: v3.1
date: 2026-05-10
status: applied (necesită Claude Code restart pentru efect)
tags: [mcp, ruflo, integration, blocker]
---

# MCP claude-flow `mcp start` arg fix

## Context
`~/.claude.json::mcpServers["claude-flow"].args` era `["D:/Cloude Code/ruflo/bin/cli.js"]` — fără subcomandă `mcp start`. Apelul ruflo CLI fără args printează help și iese în 611ms. Claude Code încearcă handshake JSON-RPC pe stdin/stdout, primește text help + exit 0, marchează MCP mort. **Userul trebuie să repornească Claude Code de fiecare dată sperând că merge.**

## Investigație
- Test manual handshake: `echo '{"jsonrpc":"2.0",...}' | ruflo mcp start` → răspunde corect cu `{"name":"ruflo","version":"3.0.0","capabilities":{...}}`
- ONNX warning pe stderr (nu corupe stdout JSON-RPC)
- Server-ul e funcțional, doar comanda de start nu o avea în config

## Decizie
**Patch `~/.claude.json` cu `args: [..., "mcp", "start"]`.**

## Motiv
- Singura modificare necesară pentru ca MCP să se atașeze permanent
- Backup creat: `~/.claude.json.bak.2026-05-10` (22915 bytes, identical pre-fix)
- Reversible instant: `cp .claude.json.bak.2026-05-10 .claude.json`

## Consecințe
- ⚠️ Necesită **Claude Code restart** (config citit la startup)
- ✅ După restart: `mcp__claude-flow__*` tools devin disponibile (`swarm_init`, `agent_spawn`, `memory_search`, etc.)
- ✅ 12 agenți Ruflo persistați devin spawn-able real (au fost idle din lipsa MCP)
- ⚠️ ONNX onnxruntime-node încă lipsește în `D:/Cloude Code/ruflo/` — vector embeddings local disabled

## Status curent
- Config patched: ✅
- Necesită restart pentru efect: ⏳ pending user action
- ONNX install needed: `cd D:/Cloude Code/ruflo && npm install onnxruntime-node`

## Verificare manuală post-restart
```bash
# În sesiunea Claude Code nouă:
# ToolSearch +swarm_init  → trebuie să găsească mcp__claude-flow__swarm_init
# (în sesiunea curentă pre-restart: "No matching deferred tools found")
```
