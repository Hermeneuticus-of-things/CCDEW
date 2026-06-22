# CCDEW — Claude Code Desktop Ecosystem Workspace

**Open Cload Intelligence Suite + CCDEW Core** — Un framework universal pentru agenți AI autonomi, cu integrare pentru orice tip de aplicație, învățare continuă, memorii ierarhice și auto-evoluție.

```
  ┌──────────────────────────────────────────────────────────────────┐
  │                      OPEN CLOAD (Desktop UI)                    │
  │  dashboard · notebook · monitor · LLM benchmark                 │
  └────────────────────────┬─────────────────────────────────────────┘
                           │
  ┌────────────────────────▼─────────────────────────────────────────┐
  │                      CCDEW CORE                                  │
  │   ccdew-core (npm) · MCP servers · Bridges · Ruflo · Swarm      │
  └────────────────────────┬─────────────────────────────────────────┘
                           │
  ┌────────────────────────▼─────────────────────────────────────────┐
  │                      MISSION CONTROL                             │
  │   API server · dashboard · agent manager · metrics · health      │
  └────────────────────────┬─────────────────────────────────────────┘
                           │
  ┌────────────────────────▼─────────────────────────────────────────┐
  │            INTELLIGENCE & MEMORY (Piramida 6 nivele)            │
  │  Episodic → Patterns → Techniques → Skills → Attitudes → Princ  │
  │  SSA · SAFLA · Instincts · Hologram · Auto-Learner              │
  └────────────────────────┬─────────────────────────────────────────┘
                           │
  ┌────────────────────────▼─────────────────────────────────────────┐
  │  ANY APPLICATION — via Universal Integration Framework           │
  │  Bridges · MCP · Plugins · Agents · Skills · Templates          │
  └──────────────────────────────────────────────────────────────────┘
```

---

## Ce este CCDEW

CCDEW este un **ecosistem modular** pentru construirea și rularea de agenți AI autonomi. Nu este legat de nicio aplicație anume — oferă infrastructura prin care **orice** aplicație, serviciu sau sistem poate fi integrat și controlat de agenți.

### Principii de design

- **Universal** — poți integra orice: streaming, email, home automation, social media, baze de date, APIs, device-uri, rețele
- **Auto-evolutiv** — sistemul învață din fiecare acțiune și se optimizează singur
- **Decuplat** — fiecare componentă e independentă; nimic nu depinde de o aplicație specifică
- **Securizat** — vault criptat, secret scanning, permission guard pe 3 nivele
- **Extensibil** — adaugi aplicații prin bridges, MCP servers, plugins sau skills

---

## Arhitectura

```mermaid
graph TB
  subgraph OC["Open Cload"]
    OC_DASH["Dashboard UI"]
    OC_NOTE["Notebook LM"]
    OC_BENCH["LLM Benchmark"]
    OC_MONITOR["Monitor"]
  end

  subgraph CCDEW["CCDEW Core"]
    CC_CORE["ccdew-core (npm)"]
    CC_MCP["MCP Servers<br/>orchestrator · LLM gateway<br/>content · mission-control"]
    CC_BRIDGE["Bridge Layer<br/>A2A (Agent-to-Agent)<br/>MCP Bridge · Hermes Bridge<br/>External System Bridge"]
    CC_RUFLO["Ruflo Engine<br/>agent flow execution"]
    CC_SWARM["Swarm Engine<br/>adaptive · hierarchical · mesh"]
    CC_PLUGINS["Plugin System<br/>15 OpenCode plugins"]
  end

  subgraph MC["Mission Control"]
    MC_API["REST API :8899"]
    MC_DASH["Dashboard UI"]
    MC_AGENTS["Agent Manager"]
    MC_COST["CodeBurn Cost Tracking"]
    MC_QUALITY["Quality Gate"]
  end

  subgraph MEM["Memory & Intelligence"]
    MEM_PYRAMID["Learning Pyramid (6 levels)"]
    MEM_P1["N1: Episodic — every action logged"]
    MEM_P2["N2: Patterns — Jaccard trigram clustering"]
    MEM_P3["N3: Techniques — reusable methods"]
    MEM_P4["N4: Skills — domain knowledge (133)"]
    MEM_P5["N5: Attitudes — tacit knowledge, mindset"]
    MEM_P6["N6: Principles — universal rules"]
    MEM_SSA["SSA Semantic Search"]
    MEM_SAFLA["SAFLA Adaptive Learning"]
    MEM_INST["Instincts Pattern Recognition"]
    MEM_HOLO["Hologram Fractal Engine"]
    MEM_AUTO["Auto-Consolidation Engine"]
    MEM_CORE["hermes-memory.py<br/>save → match → consolidate"]
  end

  subgraph INTEGRATION["Universal Integration Framework"]
    BRIDGE_A2A["A2A Bridge<br/>Agent-to-Agent protocol"]
    BRIDGE_MCP["MCP Bridge<br/>Model Context Protocol"]
    BRIDGE_EXT["External Bridge<br/>any TCP/UDP service"]
    BRIDGE_CLAUDE["Claude-OpenCode Bridge"]
    PLUGIN_SYS["Plugin System<br/>pre/post hooks · event bus<br/>secret scan · permission guard"]
    AGENT_LAYER["Agent Layer<br/>any agent profile<br/>(Hermes · Claude · Swarm · custom)"]
    SKILL_LAYER["Skill Layer<br/>any domain skill<br/>(133+ installed)"]
    TEMPLATE_SYS["Template System<br/>project scaffolding<br/>for any application type"]
  end

  subgraph ANY_APP["Any Application — Examples Only"]
    APP_ANY["Your application<br/>or service here"]
    APP_EXAMPLE1["Streaming service<br/>(via proxy + token bridge)"]
    APP_EXAMPLE2["Email system<br/>(via extension + API)"]
    APP_EXAMPLE3["Social media<br/>(via web bridge)"]
    APP_EXAMPLE4["Smart home<br/>(via MQTT bridge)"]
    APP_EXAMPLE5["Database / API<br/>(via direct bridge)"]
    APP_EXAMPLE6["Custom<br/>(via template)"]
  end

  OC --> CCDEW
  CCDEW --> MC
  CCDEW --> MEM
  MC --> INTEGRATION
  MEM --> INTEGRATION
  INTEGRATION --> ANY_APP

  CC_BRIDGE --> BRIDGE_A2A & BRIDGE_MCP & BRIDGE_EXT & BRIDGE_CLAUDE
  CC_PLUGINS --> PLUGIN_SYS
  AGENT_LAYER & SKILL_LAYER --> INTEGRATION

  MEM_CORE --> MEM_P1 & MEM_P2 & MEM_P3 & MEM_P4 & MEM_P5 & MEM_P6
  MEM_SSA --> MEM_CORE
  MEM_SAFLA --> MEM_CORE
  MEM_INST --> MEM_CORE
  MEM_HOLO --> MEM_CORE
  MEM_AUTO --> MEM_CORE

  style OC fill:#1a1a2e,stroke:#e94560,color:#fff
  style CCDEW fill:#16213e,stroke:#0f3460,color:#fff
  style MC fill:#0f3460,stroke:#e94560,color:#fff
  style MEM fill:#533483,stroke:#e94560,color:#fff
  style INTEGRATION fill:#e94560,stroke:#1a1a2e,color:#fff
  style ANY_APP fill:#1a1a2e,stroke:#0f3460,color:#fff,stroke-dasharray: 5 5
```

---

## Piramida Învățării — 6 Nivele

| Nivel | Ce face | Motor |
|-------|---------|-------|
| **N1 — Episodic** | Salvează fiecare acțiune și rezultat | `episodic.jsonl` |
| **N2 — Patterns** | Grupează acțiuni similare (Jaccard trigram) | `patterns.json` |
| **N3 — Techniques** | Extrage metode reutilizabile | `techniques.json` |
| **N4 — Skills** | Construiește skill-uri specializate | `skills_db.json` |
| **N5 — Attitudes** | Modelează atitudini și mindset | `tacit.json` |
| **N6 — Principles** | Stabilește principii universale | `principles.json` |

Consolidare automată: `hermes-memory.py` + `auto_learn_consolidate.py`

---

## Cum integrezi o aplicație

CCDEW oferă mai multe căi de integrare, în funcție de ce fel de aplicație/serviciu ai:

### 1. Bridge — pentru orice serviciu extern
```python
# Un bridge poate conecta ORICE protocol:
# HTTP, WebSocket, MQTT, TCP, UDP, gRPC, serial, etc.
from claude.bridge import ExternalBridge

bridge = ExternalBridge(protocol="mqtt", host="...")
bridge.register_handler("sensors/#", on_sensor_data)
bridge.start()
```

### 2. MCP Server — pentru tool-uri expuse agenților
```javascript
// Un MCP Server expune tool-uri pe care agenții le pot apela
server.tool("search_database", { query: "string" }, async (args) => {
  return await db.query(args.query);
});
```

### 3. Plugin — pentru hook-uri în ciclul de viață
```typescript
// Plugin-urile se atașează la: pre-bash, pre-edit, post-task, session-end
export const plugin: Plugin = {
  "tool.execute.before": (ctx) => { /* permission check */ },
  "tool.execute.after":  (ctx) => { /* save episode */ },
};
```

### 4. Skill — pentru cunoștințe de domeniu
Un skill conține instrucțiuni, comenzi și workflow-uri pentru un domeniu specific. Se încarcă automat când task-ul se potrivește.

### 5. Agent Profile — pentru roluri specializate
```markdown
# Un agent profile definește un rol: analyst, coder, researcher, etc.
## Role: Database Administrator
## Tools: query, backup, optimize
## Instructions: Maintain all database systems
```

### 6. Template de proiect — pentru aplicații complete
```bash
# Creează un proiect nou din template
cp -r _TEMPLATES/generic /path/to/new-app
# Ajustează CLAUDE.md, bridges, skills
```

---

## Componente interne

### MCP Servers (4)
| Server | Rol |
|--------|-----|
| **ccdew-mcp** | Orchestrator principal — 11 tool-uri |
| **opencode-llm** | Gateway LLM (OpenRouter) |
| **notebooklm** | Content intelligence |
| **mission-control** | System snapshot & health |

### Bridges
- **A2A Bridge** — protocol Agent-to-Agent
- **MCP Bridge** — conectare servicii externe
- **External Bridge** — orice protocol TCP/UDP
- **Claude-OpenCode Bridge** — conversație bidirecțională

### Ruflo Engine
Motor de workflow pentru agenți — `ruflo.cjs`. Rulează flow-uri secvențiale sau paralele.

### Enneagram Routing
Rutare pe 9 noduri cognitive — fiecare tip Enneagram tratează task-uri după profilul său.

---

## Quick start

```bash
# Bootstrap
bash bootstrap-ccdew.sh

# Pornește Mission Control
python3 .claude/helpers/mission-control.py

# Status
curl http://localhost:8899/status.json
```

---

## Structură

```
CCDEW/
├── .claude/
│   ├── helpers/       # Motoare: memory, bridges, agents, skills
│   ├── mcp/           # MCP servers
│   ├── agents/        # Agent profiles
│   ├── bridge/        # Bridge layer
│   ├── skills/        # Domain skills
│   └── commands/      # CLI commands
├── .opencode/         # Plugin system
├── ccdew-core/        # NPM library
├── _TEMPLATES/        # Project templates (generic, android, carte, etc.)
└── [your-apps]/       # Your integrated applications here
```

---

## Securitate

- **3 nivele de sensibilitate**: PUBLIC / PRIVATE / SECRET
- Vault criptat cu PIN
- Secret scanning automat (pre-commit)
- Permission guard pe comenzi bash
- Security monitoring la 12h

---

## Licență

MIT — vezi [LICENSE](./LICENSE).

---

*CCDEW — Un framework care integrează orice. Auto-vindecare. Auto-optimizare. Auto-evoluție.*
