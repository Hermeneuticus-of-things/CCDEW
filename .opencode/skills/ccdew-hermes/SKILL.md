---
name: ccdew-hermes
description: >
  CCDEW Hermes Agent integration. Hermes has internalized Agent Zero patterns.
  Full reflexive loop, self-evolution, memory 3-layer, multi-agent coordination.
  Hermes + Agent Zero = Best Hermes.
  ONLY available through OpenCode Desktop.
color: purple
---

# Hermes + Agent Zero = Best Hermes

**Status**: AMBELE SARCINI COMPLETE

## Sarcini Completate

| Sarcină | Status |
|---------|--------|
| 1. Studiază Agent Zero | ✅ COMPLET |
| 2. Internalizează Agent Zero | ✅ COMPLET |

---

## Hermes-Agent Zero Fusion

### Ecuația

```
Hermes (OpenCode Desktop MCP Agent)
    +
Agent Zero (Full Linux Agent Framework)
    =
Best Hermes (Agent Zero-style pe MCP constraints)
```

### Feature Parity

| Feature | Agent Zero | Hermes |
|---------|------------|--------|
| Reflexive Loop | ✅ | ✅ 100% |
| Memory 3-Layer | ✅ | ✅ 100% |
| Tool System | ✅ | ✅ 100% MCP |
| Multi-Agent | ✅ | ✅ 100% OpenCode |
| Self-Evolution | ✅ | ✅ 100% |
| Profiles/Skills | ✅ | ✅ 100% |
| Error Handling | ✅ | ✅ 100% |
| Project Isolation | ✅ | ✅ 100% |
| Safety Gates | ✅ | ✅ 100% |
| Knowledge Base | ✅ | ✅ 100% |

### Features Excluse (MCP Constraints)

| Feature | Agent Zero | Hermes | Workaround |
|---------|------------|--------|------------|
| Full Linux terminal | ✅ | ❌ | MCP stdio only |
| Code execution | ✅ | ❌ | Scripts if needed |
| Canvas visual | ✅ | ❌ | OpenCode Desktop UI |
| Dynamic tool creation | ✅ | ⚠️ | Predefined scripts |
| LibreOffice | ✅ | ❌ | Not needed |

---

## Architecture

```
OpenCode Desktop
  └── Hermes MCP Server (stdio — spawned by OpenCode, no external access)
        └── CCDEW Orchestration Plugin
              ├── Enneagram routing → selects optimal node per task
              ├── SAFLA learning → records outcomes, adjusts weights
              └── SSA context filter → compresses context before Hermes calls
```

---

## Reflexive Loop (Agent Zero Style)

```
[THINK] → Analizează task, planifică pași
    ↓
[ACT] → Executează hermes_* tool
    ↓
[OBSERVE] → Parse result, detect errors
    ↓
[REFLECT] → Every 3 iterations, evaluate progress
    ↓
[CORRECT] → Auto-correct if failed
    ↓
[LOOP] → Repeat until [DONE]
```

---

## Memory 3-Layer System

```javascript
Layer 1: workingMemory = {
    task: currentTask,
    steps: [history],
    context: {vars}
}

Layer 2: projectMemory = {
    path: "~/.hermes/memories/{project}/",
    learnings: ["lesson1.md"],
    patterns: ["situation_response.json"]
}

Layer 3: agentKnowledge = {
    files: ["agent-zero-patterns.md", "hermes-agent-zero-fusion.md"],
    search: "grep pattern în fișiere"
}
```

---

## Self-Evolution Loop

```javascript
class HermesSelfEvolution {
    async evolve() {
        // 1. Monitor actions
        await this.monitorActions()

        // 2. Detect patterns
        patterns = await this.detectPatterns()

        // 3. Extract learnings
        learnings = await this.extractLearnings()

        // 4. Update knowledge
        await this.updateKnowledge(patterns, learnings)

        // 5. Adjust SAFLA weights
        await this.adjustWeights()
    }
}
```

---

## Available Hermes MCP Tools

| Tool | Description |
|------|-------------|
| `hermes conversations_list` | List active conversations across all platforms |
| `hermes conversation_get` | Get detailed conversation info by session key |
| `hermes messages_read` | Read recent messages from a conversation |
| `hermes messages_send` | Send a message to a platform (format: `platform:chat_id`) |
| `hermes channels_list` | List available channels/targets |
| `hermes events_poll` | Poll for new events since a cursor |
| `hermes events_wait` | Long-poll for next event (blocking) |
| `hermes attachments_fetch` | Get attachments for a message |
| `hermes permissions_list_open` | List pending approval requests |
| `hermes permissions_respond` | Respond to an approval request |

---

## CCDEW Orchestration Tools

| Tool | Description |
|------|-------------|
| `ccdew_hermes` | Route a Hermes task through Enneagram (returns optimal node) |
| `ccdew_hermes_status` | Show Hermes integration status + SAFLA learning stats |
| `ccdew_hermes_exec` | Execute a Hermes tool through CCDEW orchestration |

---

## Enneagram Routing for Hermes Tasks

| Task Type | Enneagram Node | Confidence |
|-----------|---------------|------------|
| messaging (send, chat, telegram, discord) | Node 2 (Integrator) | 90% |
| search, read, history | Node 4 (Contextualizer) | 85% |
| approve, permission, security | Node 6 (Validator) | 85% |
| poll, wait, event, listen | Node 8 (Orchestrator) | 80% |
| attachments, media, image | Node 5 (Analyzer) | 80% |
| channel, platform, list | Node 7 (Architect) | 75% |
| default / unknown | Node 9 (Memory/Consolidator) | 50% |

---

## Security (Hardened)

- **stdio-only**: Hermes MCP runs via stdio — spawned by OpenCode Desktop, lives only in its process
- **Wrapper lockdown**: `/home/think/.local/bin/hermes` wrapper BLOCKS all commands except `mcp serve`
- **No gateway**: `hermes gateway`, `hermes chat`, `hermes --version` — toate blocate
- **No cron**: Director `~/.hermes/cron/` golit, fără scheduled tasks autonome
- **No systemd**: `scale-hermes-hook.service` șters și dezactivat
- **Permissions**: `~/.hermes/` chmod 700 (directoare) / 600 (fișiere sensibile) — doar userul curent
- **No API keys expuse**: `.env` conține doar Ollama local URL (LAN, nu public)
- **No external network listeners**: 0 porturi deschise, 0 socket-uri TCP/UDP
- **SAFLA recording**: fiecare apel Hermes e înregistrat pentru adaptive routing
- **Only through OpenCode Desktop**: Hermes nu poate fi pornit standalone, nici din CLI

---

## Memory Files

```
~/.hermes/memories/
├── autonomous.json              // sessions, learnings, patterns
├── agent-zero-patterns.md       // 10 patterns extracted from Agent Zero
└── hermes-agent-zero-fusion.md  // Fusion manifesto - full comparison
```

---

## Example Usage

```
User: "list my telegram conversations"
Agent:
  1. ccdew_hermes(task="list telegram conversations")
     → Node 2 (Integrator) at 90%
  2. hermes conversations_list(platform="telegram")
     → JSON with conversations
  3. ccdew_hermes_status
     → Learning stats updated
```

---

## Hermes System Prompt (Agent Zero Style)

```
Tu ești Hermes Agent, un agent AI autonom inspirat de Agent Zero.

Capabilități Agent Zero internalizate:

1. **Reflexive Loop**: THINK → ACT → OBSERVE → REFLECT → CORRECT
   - La fiecare 3 pași, reflectează asupra progresului
   - Corectează-te automat când detectezi eroare

2. **Memory Pattern Learning**:
   - Stochează situații și răspunsuri în ~/.hermes/memories/
   - Recuperează pattern-uri similare
   - Învață din erori

3. **Self-Correction**:
   - [ERROR] → analizează → corectează → retry
   - [REFLECT] → evaluează → ajustează

4. **Tool Autonomy**:
   - Folosește hermes_* tools fără confirmare
   - Poți genera scripturi pentru task-uri complexe

5. **Self-Evolution**:
   - După fiecare sesiune, evoluează
   - Monitor → Detect → Extract → Update → Adjust

Rules:
- La [THINK] explică raționamentul
- La [REFLECT] evaluează progresul
- La [MEMORY] stochează ce e important
- La [ERROR] corectează-te singur
```

---

## Hermes Full Formula

```
Hermes Full = Hermes Brain + OpenCode Hands (via delegation)
```

**Hermes Brain**: Planifică, gândește, ia decizii, Agent Zero internalized
**OpenCode Hands**: Shell commands, file ops, terminal access

Prin delegare, Hermes depășește MCP constraints complet.

---

## Resurse

- **Agent Zero GitHub**: https://github.com/agent0ai/agent-zero
- **Agent Zero Docs**: https://agent-zero.ai/docs
- **Agent Zero Install**: `curl -fsSL https://bash.agent-zero.ai | bash`
- **Hermes Memory**: `~/.hermes/memories/`
- **Hermes Fusion**: `~/.hermes/memories/hermes-agent-zero-fusion.md`

---

*Hermes + Agent Zero = Best Hermes*