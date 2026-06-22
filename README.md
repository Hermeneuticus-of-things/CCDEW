# CCDEW — Claude Code Desktop Ecosystem Workspace

**Open Cload Intelligence Suite + CCDEW Core** — Un ecosistem complet pentru agenți AI autonomi, cu învățare continuă, memorii ierarhice, rutare Enneagram și auto-evoluție.

```
  ┌──────────────────────────────────────────────────────────────────┐
  │                      OPEN CLOAD (Desktop UI)                    │
  │  dashboard · cognitive test · notebook · benchmark · monitor    │
  └────────────────────────┬─────────────────────────────────────────┘
                           │
  ┌────────────────────────▼─────────────────────────────────────────┐
  │                      CCDEW CORE                                  │
  │   ccdew-core (npm) · MCP servers · Bridges · Ruflo · Swarm      │
  └────────────────────────┬─────────────────────────────────────────┘
                           │
  ┌────────────────────────▼─────────────────────────────────────────┐
  │                      MISSION CONTROL                             │
  │   mission-control.py · dashboard API · agents · metrics          │
  └────────────────────────┬─────────────────────────────────────────┘
                           │
  ┌────────────────────────▼─────────────────────────────────────────┐
  │            INTELLIGENCE & MEMORY (Piramida 6 nivele)            │
  │  N1 Episodic → N2 Patterns → N3 Techniques → N4 Skills          │
  │  → N5 Attitudes → N6 Principles                                 │
  │  SSA semantic · SAFLA learning · Instincts · Hologram           │
  └────────────────────────┬─────────────────────────────────────────┘
                           │
  ┌────────────────────────▼─────────────────────────────────────────┐
  │  AGENTS · SKILLS · BRIDGES · APPS                               │
  │  Hermes · Claude · Zorin · Swarm · GitHub · GX · TV · Email     │
  └──────────────────────────────────────────────────────────────────┘
```

---

## Arhitectura completă

```mermaid
graph TB
  subgraph OC["Open Cload"]
    OC_DASH["Dashboard UI"]
    OC_COG["Cognitive Test"]
    OC_NOTE["Notebook LM"]
    OC_BENCH["LLM Benchmark"]
    OC_MONITOR["OpenCode Monitor"]
  end

  subgraph CCDEW["CCDEW Core"]
    CC_CORE["ccdew-core<br/>(npm library)"]
    CC_MCP["MCP Servers<br/>ccdew-mcp · opencode-llm<br/>notebooklm · mission-control"]
    CC_BRIDGE["Bridges<br/>A2A · Claude-OpenCode<br/>Bridge-MCP · Hermes A0"]
    CC_RUFLO["Ruflo Engine<br/>(agent flow execution)"]
    CC_SWARM["Swarm Config<br/>swarm.yaml + swarm_api.py"]
    CC_PLUGINS["OpenCode Plugins<br/>(15 TypeScript plugins)"]
  end

  subgraph MC["Mission Control"]
    MC_API["mission-control.py<br/>REST API :8899"]
    MC_DASH["Dashboard HTML<br/>components.js"]
    MC_AGENTS["Agent Manager<br/>stats · health · control"]
    MC_METRICS["Metrics · CodeBurn<br/>cost · session · quality"]
  end

  subgraph MEM["Memory & Learning Pyramid"]
    L1["N1: Episodic<br/>episodic.jsonl<br/>actions + outcomes"]
    L2["N2: Patterns<br/>Jaccard trigram<br/>clustering"]
    L3["N3: Techniques<br/>reusable methods<br/>techniques.json"]
    L4["N4: Skills<br/>133 skills total<br/>skills_db.json"]
    L5["N5: Attitudes<br/>tacit knowledge<br/>tacit.json"]
    L6["N6: Principles<br/>universal rules<br/>principles.json"]
    MEM_CORE["hermes-memory.py<br/>save_episode · consolidate<br/>match · pyramid engine"]
    MEM_SSA["SSA Semantic Search<br/>Jaccard trigram index"]
    MEM_SAFLA["SAFLA Adaptive Learning<br/>success rates · feedback"]
    MEM_INST["Instincts<br/>pattern recognition"]
    MEM_HOLO["Hologram Engine<br/>fractal integration"]
    MEM_AUTO["Auto-Learner<br/>auto_learn_consolidate.py"]
  end

  subgraph AGENTS["Agent Layer"]
    HERMES_AGENTS["Hermes Agents<br/>core · autonomous · memory<br/>voice · notifier · dashboard"]
    CLAUDE_AGENTS["Claude Agents (105)<br/>core · v3 · github · flow-nexus<br/>sparc · swarm · sublinear<br/>consensus · optimization"]
    ZORIN_AGENTS["Zorin Agents (17)<br/>tv · media · network · browser<br/>home · hardware · vault · voice<br/>scheduler · bus · dev · personal"]
    SWARM_AGENTS["Swarm Agents<br/>adaptive · hierarchical · mesh"]
    GX_AGENTS["GX Agents<br/>monitor · dispatcher · agent-zero"]
    EMAIL_AGENTS["Email Intelligence<br/>bb-safe-reader · dashboard<br/>inbox triage · raport"]
  end

  subgraph SKILLS["Skills Layer — 133 total"]
    SK_OPENCODE["OpenCode Skills (7)<br/>hermes-ccdew · zorin-tv<br/>gx-monitor · graphify<br/>tv-identifier · tv-repair"]
    SK_HERMES["Hermes Skills (87)<br/>zorin · qnap · apple · creative<br/>data-science · devops · email<br/>github · gaming · media · mlops<br/>research · self-evolution<br/>smart-home · social-media<br/>universal-techniques"]
    SK_CLAUDE["Claude Skills (34)<br/>agent-browser · flow-nexus<br/>github-* · hooks-automation<br/>sparc-methodology · swarm-*<br/>v3-* · reasoningbank"]
    SK_OCLOAD["Open-Cload Skills (5)<br/>5-zoom-audit · cost-tracking<br/>enneagram-routing · safla-feedback<br/>secret-scanning"]
  end

  subgraph APPS["Applications"]
    APP_TV["Zorin TV<br/>176 channels · 13 categories<br/>failover · proxy · token refresh"]
    APP_EMAIL["BetterBird Email<br/>extension · dashboard · triage<br/>intelligence · cache reader"]
    APP_DASH["Dashboards<br/>hermes · email · status<br/>control panel · overlay"]
    APP_OBS["OBS Integration<br/>streaming · scenes"]
    APP_OBSIDIAN["Obsidian Vault<br/>Hermes-Command-Center"]
  end

  subgraph INFRA["Infrastructure & Config"]
    INFRA_MCP[".mcp.json · .opencode.json<br/>swarm.yaml · package.json"]
    INFRA_FLOW["claude-flow engine<br/>3505 sessions · 243 reports"]
    INFRA_SCRIPTS["Shell Scripts (15)<br/>bootstrap · setup · watchdogs"]
    INFRA_TEMPLATES["Templates (9)<br/>android · carte · devcontainer<br/>github-workflows · research"]
    INFRA_MEM["_MEMORY · _SETTINGS · _BEST_PRACTICES<br/>METRICS · decisions · ADR"]
    INFRA_VAULT["Vault · Secrets<br/>encrypted · PIN protected"]
  end

  subgraph ENNEAGRAM["Enneagram Routing"]
    E9["Type 1 · 2 · 3 · 4 · 5 · 6 · 7 · 8 · 9"]
    ER["Router<br/>enneagram_router.py"]
    EC["Composer<br/>enneagram_compose.py"]
  end

  OC --> CCDEW
  CCDEW --> MC
  CCDEW --> MEM
  CCDEW --> ENNEAGRAM
  MEM --> AGENTS
  MEM --> SKILLS
  AGENTS --> APPS
  SKILLS --> APPS
  MC --> AGENTS
  ENNEAGRAM --> AGENTS
  MC --> APPS
  CC_RUFLO --> AGENTS
  CC_BRIDGE --> AGENTS
  CC_PLUGINS --> MC
  MEM_CORE --> L1 & L2 & L3 & L4 & L5 & L6
  MEM_SSA --> MEM_CORE
  MEM_SAFLA --> MEM_CORE
  MEM_INST --> MEM_CORE
  MEM_HOLO --> MEM_CORE
  MEM_AUTO --> MEM_CORE

  style OC fill:#1a1a2e,stroke:#e94560,color:#fff
  style CCDEW fill:#16213e,stroke:#0f3460,color:#fff
  style MC fill:#0f3460,stroke:#e94560,color:#fff
  style MEM fill:#533483,stroke:#e94560,color:#fff
  style AGENTS fill:#e94560,stroke:#1a1a2e,color:#fff
  style SKILLS fill:#16213e,stroke:#0f3460,color:#fff
  style APPS fill:#1a1a2e,stroke:#e94560,color:#fff
  style INFRA fill:#16213e,stroke:#0f3460,color:#fff
  style ENNEAGRAM fill:#533483,stroke:#e94560,color:#fff
```

---

## Piramida Învățării — 6 Nivele

| Nivel | Ce conține | Unde |
|-------|-----------|------|
| **N1 — Episodic** | Acțiuni, comenzi, rezultate | `episodic.jsonl` |
| **N2 — Patterns** | Pattern-uri Jaccard trigram | `patterns.json` |
| **N3 — Techniques** | Metode reusable | `techniques.json` |
| **N4 — Skills** | 133 skill-uri specializate | `skills_db.json` |
| **N5 — Attitudes** | Cunoștințe tacite, mindset | `tacit.json` |
| **N6 — Principles** | 14 principii universale | `principles.json` |

Motor: `hermes-memory.py` — salvare episoade, match pattern-uri, consolidare automată.

---

## Componente cheie

### MCP Servers
| Server | Tools | Rol |
|--------|-------|-----|
| **ccdew-mcp** | 11 (route, safla, audit, cost, snapshot, compact...) | Orchestrator principal |
| **opencode-llm** | 5 (models, providers, chat, embedding, cost) | Gateway LLM (OpenRouter) |
| **notebooklm** | NotebookLM integration | Content intelligence |
| **hermes-mission-control** | Hermes MC API | System snapshot & health |

### Agenți principali
- **Hermes** — Agent central cu autonomie, voce, notificări, dashboard
- **105 Claude Agents** — Core, v3, GitHub, Flow-Nexus, SPARC, Swarm, Sublinear, Consensus, Optimization
- **17 Zorin Agents** — TV, media, rețea, browser, home, hardware, vault, voice, etc.
- **Swarm Agents** — Adaptive, hierarchical, mesh coordinators
- **GX Agents** — Monitor, dispatcher, agent-zero

### Bridges
- **A2A Bridge** — Agent-to-Agent prin MCP
- **Claude-OpenCode Bridge** — Conversație bidirectională
- **Bridge-MCP Server** — MCP bridge extern
- **Hermes A0** — Agent-Zero bridge

### Ruflo Engine
Motor de workflow pentru agenți — `ruflo.cjs`. Rulează flow-uri de agenți cu execuție secvențială/paralelă.

### Enneagram Routing
Rutare pe 9 noduri (tipurile Enneagram) — fiecare nod tratează task-uri după profilul său cognitiv. `enneagram_router.py` + `enneagram_compose.py`.

---

## Cum rulează

```bash
# Bootstrap complet
bash /home/think/CCDEW/bootstrap-ccdew.sh

# Pornește Mission Control
python3 .claude/helpers/mission-control.py

# Pornește Ruflo
node .claude/helpers/ruflo.cjs

# Status live
http://localhost:8899/status.json
http://localhost:8899/channels.json
```

---

## Structura directorului

```
CCDEW/
├── .claude/
│   ├── helpers/         # Python + CJS scripts (engine)
│   ├── mcp/             # MCP servers
│   ├── agents/          # 105 agent profiles
│   ├── bridge/          # A2A + Claude-OpenCode bridges
│   ├── skills/          # 34 Claude skill directories
│   └── commands/        # CLI commands (analysis, automation, github, etc.)
├── .opencode/           # OpenCode plugins + config
├── .claude-flow/        # Flow engine (3505 sessions)
├── agents/              # 15 top-level agent profiles
├── ccdew-core/          # NPM library (CLI binaries)
├── _MEMORY/             # Memory files (L0-L4, ADRs, identity)
├── _SETTINGS/           # Rules, configs, changelogs
├── _TEMPLATES/          # Project templates
├── _METRICS/            # Cost & optimization metrics
├── betterbird-ccdew/    # BetterBird Thunderbird extension
├── Open-Cload/          # Open Cload desktop variant
├── Hermes-Command-Center/ # Obsidian vault
├── hermes-mcp-stdio/    # MCP stdio interface
├── safla-weights/       # SAFLA adaptive weights
└── project-arch/        # Architecture plugin
```

---

## Aplicații integrate

### Zorin TV Romania
176 canale live, 13 categorii, failover automat p11→p13→p9, token refresh la 5 min, watchdog la 2 min, clean/probe la 6h.

### BetterBird Email Intelligence
Extensie Thunderbird cu dashboard, cache reader, raport brut, triaj inbox, intelligence engine.

### Dashboards
- Hermes Dashboard (`/status.json`)
- Email Dashboard (`/claude/helpers/email-dashboard-server.py`)
- CCDEW Control Panel (`ccdew-panel.html`)
- Open Cload Dashboard (`/Open-Cload/.opencode/dashboard.html`)

---

## Securitate

- Vault criptat cu PIN protected
- Secret scanning automat (pre-commit hook)
- Permission guard pe comenzi bash
- Security monitoring la 12h
- 3 nivele de sensibilitate: PUBLIC / PRIVATE / SECRET

---

## Licență

MIT — vezi [LICENSE](./LICENSE).

---

*CCDEW — Un ecosistem care crește singur. Auto-vindecare. Auto-optimizare. Auto-evoluție.*
