# CCDEW — Claude Code Desktop Ecosystem Workspace

**Open Cload Intelligence Suite + CCDEW Core** — Framework universal pentru agenți AI autonomi. Integrează orice aplicație. Auto-evoluție. Memorii ierarhice. Auto-vindecare.

```
  ╔══════════════════════════════════════════════════════════════════╗
  ║                    OPEN CLOAD (UI Layer)                        ║
  ║  Dashboard · NotebookLM · Monitor · LLM Benchmark · Cognitive   ║
  ╚══════════════════════════════════════════════════════════════════╝
                                    │
  ╔══════════════════════════════════════════════════════════════════╗
  ║                    CCDEW CORE                                   ║
  ║  ccdew-core · MCP ×4 · Bridges ×5 · Ruflo · Swarm · Plugins    ║
  ╚══════════════════════════════════════════════════════════════════╝
                                    │
  ╔══════════════════════════════════════════════════════════════════╗
  ║                    MISSION CONTROL                              ║
  ║  API :8899 · Dashboard · Agent Mgr · CodeBurn · Quality Gate    ║
  ╚══════════════════════════════════════════════════════════════════╝
                                    │
  ╔══════════════════════════════════════════════════════════════════╗
  ║           INTELLIGENCE & MEMORY — PIRAMIDA 6 NIVELE             ║
  ║  N1 Episodic → N2 Patterns → N3 Techniques → N4 Skills          ║
  ║  → N5 Attitudes → N6 Principles                                 ║
  ║  SSA · SAFLA · Instincts · Hologram · Auto-Consolidate          ║
  ╚══════════════════════════════════════════════════════════════════╝
                                    │
  ╔══════════════════════════════════════════════════════════════════╗
  ║           AGENTS · SKILLS · COMMANDS · TEMPLATES                ║
  ║  105+ agent profiles · 133 skills · 7 cmd categories · 9 tmpl   ║
  ╚══════════════════════════════════════════════════════════════════╝
                                    │
  ╔══════════════════════════════════════════════════════════════════╗
  ║                    UNIVERSAL INTEGRATION FRAMEWORK               ║
  ║  Bridge · MCP · Plugin · Skill · Agent · Template — any app     ║
  ╚══════════════════════════════════════════════════════════════════╝
```

---

## Arhitectura completă

```mermaid
graph TB
  subgraph L0_OC["OPEN CLOAD — Desktop UI"]
    OC_DASH["Dashboard / Control Panel"]
    OC_NOTE["Notebook LM Integration"]
    OC_MONITOR["System Monitor"]
    OC_BENCH["LLM Benchmark"]
    OC_COG["Cognitive Testing"]
  end

  subgraph L1_CCDEW["CCDEW CORE"]
    CC_CORE["ccdew-core (NPM library)"]
    CC_MCP["MCP Servers (4)"]
    CC_MCP1["ccdew-mcp<br/>11 tools: route, safla<br/>audit, cost, snapshot..."]
    CC_MCP2["opencode-llm<br/>5 tools: models, chat<br/>embedding, providers"]
    CC_MCP3["notebooklm<br/>content intelligence"]
    CC_MCP4["hermes-mission-control<br/>system health & snapshot"]
    CC_BRIDGES["Bridges (5)"]
    CC_BR1["A2A Agent-to-Agent"]
    CC_BR2["MCP Bridge"]
    CC_BR3["External Bridge"]
    CC_BR4["Claude-OpenCode"]
    CC_BR5["Hermes A0 Bridge"]
    CC_RUFLO["Ruflo Engine<br/>agent flow execution"]
    CC_SWARM["Swarm Engine<br/>adaptive · hierarchical · mesh"]
    CC_PLUGINS["Plugin System (15)"]
    CC_PL1["codeburn · graphify · safla<br/>instincts · verify · optimize<br/>permissions · secret-scan<br/>session · statusline · ssa<br/>project-scope · quality-gate<br/>red-hat · hermes-orch"]
    CC_ENN["Enneagram Router<br/>9 personality types"]
    CC_ENN1["T1:Reformer T2:Helper T3:Achiever<br/>T4:Individualist T5:Investigator<br/>T6:Loyalist T7:Enthusiast<br/>T8:Challenger T9:Peacemaker"]
  end

  subgraph L2_MC["MISSION CONTROL"]
    MC_API["REST API — port 8899<br/>status · channels · probe-all"]
    MC_DASH["Dashboard HTML<br/>components.js · agent list"]
    MC_MGR["Agent Manager<br/>stats · health · control"]
    MC_BURN["CodeBurn Cost Tracking<br/>session cost · monthly total"]
    MC_QUALITY["Quality Gate<br/>pre-push verification"]
    MC_METRICS["Metrics<br/>_METRICS/ · growth log"]
  end

  subgraph L3_MEM["INTELLIGENCE & MEMORY — PIRAMIDA 6 NIVELE"]
    MEM_N1["N1: EPISODIC<br/>episodic.jsonl<br/>every action saved"]
    MEM_N2["N2: PATTERNS<br/>patterns.json<br/>Jaccard trigram clusters"]
    MEM_N3["N3: TECHNIQUES<br/>techniques.json<br/>reusable methods"]
    MEM_N4["N4: SKILLS<br/>skills_db.json<br/>133 domain skills"]
    MEM_N5["N5: ATTITUDES<br/>tacit.json<br/>tacit knowledge, mindset"]
    MEM_N6["N6: PRINCIPLES<br/>principles.json<br/>14 universal rules"]
    MEM_ENGINE["Pyramid Engine<br/>hermes-memory.py"]
    MEM_SSA["SSA Semantic Search<br/>Jaccard trigram index"]
    MEM_SAFLA["SAFLA Adaptive Learning<br/>success rates · weights"]
    MEM_INST["Instincts<br/>pattern recognition"]
    MEM_HOLO["Hologram Engine<br/>fractal integration"]
    MEM_AUTO["Auto-Consolidation<br/>auto_learn_consolidate.py<br/>N2→N6 periodic"]
    MEM_MOTORS["Additional Engines<br/>hermes-memory-sync.py<br/>hermes-binary-guardian.py<br/>fractal_patterns.json<br/>self_evolution.json"]
  end

  subgraph L4_AGENTS["AGENT TREE"]
    AG_HERMES["Hermes (6+)<br/>core · autonomous<br/>memory · voice · notifier<br/>dashboard · binary-guard"]
    AG_CLAUDE["Claude Agents (105)"]
    AG_C1["core (5)<br/>coder · planner<br/>researcher · reviewer · tester"]
    AG_C2["v3 (16)<br/>architect · security · memory<br/>sparc · swarm · reasoning<br/>ADD · PII · injection<br/>performance · defense"]
    AG_C3["github (13)<br/>code-review · issue-tracker<br/>pr-manager · release-manager<br/>workflow · multi-repo-swarm<br/>project-board · repo-architect"]
    AG_C4["flow-nexus (9)<br/>app-store · auth · payments<br/>neural-network · sandbox<br/>challenges · user-tools<br/>swarm · workflow"]
    AG_C5["sparc (4)<br/>architecture · pseudocode<br/>refinement · specification"]
    AG_C6["swarm (3)<br/>adaptive · hierarchical<br/>mesh coordinator"]
    AG_C7["sublinear (5)<br/>consensus · matrix-optimizer<br/>pagerank · performance<br/>trading-predictor"]
    AG_C8["consensus (7)<br/>byzantine · raft · gossip<br/>quorum · crdt · security<br/>performance-benchmarker"]
    AG_C9["optimization (5)<br/>benchmark · load-balancer<br/>performance-monitor<br/>resource-allocator<br/>topology-optimizer"]
    AG_C10["hermes (2) + templates (9)<br/>+ analysis, architecture<br/>browser, data, devops<br/>documentation, payments<br/>sona, specialized, testing"]
    AG_ZORIN["Zorin Agents (17)<br/>tv · media · network<br/>browser · home · hardware<br/>vault · voice · scheduler<br/>bus · dev · personal<br/>launcher · bus · file<br/>hue · memory"]
    AG_SWARM["Swarm Coordinators (3)<br/>adaptive-coordinator<br/>hierarchical-coordinator<br/>mesh-coordinator"]
    AG_GX["GX Agents<br/>monitor · dispatcher<br/>agent-zero · cron"]
    AG_EMAIL["Email Intelligence<br/>bb-safe-reader<br/>email-dashboard-server<br/>inbox-triage · raport-brut"]
  end

  subgraph L5_SKILLS["SKILL TREE — 133 total"]
    SK_OC["OpenCode Skills (7)"]
    SK_OC1["hermes-ccdew · zorin-tv-system<br/>zorin-tv-repair · gx-monitor<br/>graphify · tv-identifier<br/>auto-skill"]
    SK_H["Hermes Skills (87)"]
    SK_H1["zorin-romania-tv · zorin-auto-heal<br/>zorin-disk-watch · zorin-kernel-watch<br/>zorin-memory-opt · zorin-service-guard<br/>zorin-auto-* (3)"
    SK_H2["universal-techniques<br/>qnap-access · deep-stream-finder<br/>autonomous-ai-agents"]
    SK_H3["apple (6): macos-computer-use<br/>imessage · findmy · reminders<br/>apple-notes"]
    SK_H4["creative (11): comfyui · touchdesigner<br/>songwriting · sketch · pretext<br/>pixel-art · p5js · manim · ascii<br/>architecture-diagram · design-md"]
    SK_H5["data-science · devops (3)<br/>email · gaming (2) · gifs<br/>github (6) · inference-sh"]
    SK_H6["media (6): youtube-content<br/>spotify · songsee · heartmula<br/>gif-search"]
    SK_H7["mlops (10): dspy · segment-anything<br/>audiocraft · vllm · obliteratus<br/>huggingface-hub · llama-cpp<br/>weights-and-biases<br/>lm-evaluation-harness"]
    SK_H8["research (4) · self-evolution<br/>smart-home · social-media<br/>software-development"]
    SK_H9["wondelai (30+): web-typography<br/>ux-heuristics · traction-eos<br/>top-design · system-design<br/>31 w-* design books"]
    SK_H10["workspace-dispatch · yuanbao<br/>mcp-client · note-taking<br/>productivity · red-teaming"]
    SK_C["Claude Skills (34)"]
    SK_C1["agent-browser · agentdb-* (3)<br/>browser · flow-nexus-* (3)<br/>github-* (5) · hooks-automation<br/>pair-programming · reasoningbank-*<br/>skill-builder · sparc-methodology<br/>stream-chain · swarm-* (3)<br/>v3-* (3) · verification-quality"]
    SK_OCL["Open-Cload Skills (5)<br/>5-zoom-audit · cost-tracking<br/>enneagram-routing<br/>safla-feedback · secret-scanning"]
  end

  subgraph L6_CMDS["CLI COMMANDS — 7 categorii"]
    CMD_ANALYSIS["analysis (7)<br/>bottleneck-detect · performance<br/>token-efficiency · etc"]
    CMD_AUTO["automation (7)<br/>auto-agent · self-healing<br/>session-memory · smart-spawn"]
    CMD_GITHUB["github (19)<br/>code-review · pr-manager<br/>release-manager · swarm-*"]
    CMD_HOOKS["hooks (8)<br/>overview · post-edit · post-task<br/>pre-edit · pre-task · session-end"]
    CMD_MONITOR["monitoring (6)<br/>agent-metrics · agents<br/>real-time-view · status · swarm"]
    CMD_OPT["optimization (6)<br/>auto-topology · cache-manage<br/>parallel-execute · topology-opt"]
    CMD_SPARC["sparc (32)<br/>analyzer · architect · coder<br/>debug · devops · etc"]
  end

  subgraph L7_FLOW["CLAUDE-FLOW ENGINE"]
    FLOW_CONFIG["config.yaml · CAPABILITIES.md"]
    FLOW_SESSIONS["3505 batch sessions<br/>conversation history"]
    FLOW_REPORTS["243 session reports<br/>6 evaluate reports"]
    FLOW_DATA["data (12+ files)<br/>circuit9 · safla · memory<br/>learning · skill-usage · graph<br/>harness · perf · ssa · codeburn"]
    FLOW_MEM["memory storage<br/>snapshots · indices"]
    FLOW_TEAM["team config<br/>anonymous data"]
  end

  subgraph L8_TMPL["TEMPLATES — 9 proiecte"]
    TMPL_ANDROID["Android App"]
    TMPL_CARTE["Book / Carte"]
    TMPL_DEVCONTAINER["Dev Container"]
    TMPL_GENERIC["Generic Project"]
    TMPL_GITHUB["GitHub Workflows<br/>quality-gate.yml"]
    TMPL_OC["OpenCode Desktop"]
    TMPL_PREVIEW["Markdown Preview Server"]
    TMPL_RESEARCH["Research Project"]
    TMPL_MCP["MCP Project"]
  end

  subgraph L9_CRON["AUTOMATION — Cron & Watchdogs"]
    CRON_TOKEN["token refresh (5 min)<br/>magicplaces · b1tv · qnap"]
    CRON_WATCH["watchdog (2 min)<br/>zorin-tv-watchdog.sh"]
    CRON_CLEAN["clean / probe (6h)<br/>zorin-tv-clean.py"]
    CRON_SECURITY["security monitor (12h)<br/>hermes-security · vault-monitor"]
    CRON_EVOLUTION["self-evolution<br/>auto_learn · consolidate"]
    CRON_BOOTSTRAP["startup services<br/>bootstrap-ccdew.sh"]
    CRON_SCRIPTS["helpers (15+ scripts)<br/>guidance-hooks · statusline<br/>deploy-qnap-token · fix-brave"]
  end

  subgraph L10_INFRA["INFRASTRUCTURE"]
    INFRA_CONFIG[".mcp.json · .opencode.json<br/>swarm.yaml · package.json<br/>.gitignore · .plan-status.json"]
    INFRA_MEMORY["_MEMORY/<br/>L0-sensory · L1-working<br/>L2-episodic · L3-semantic<br/>L4-identity · ADR (11)<br/>decisions · secrets (3)<br/>hermes-sync · agents"]
    INFRA_SETTINGS["_SETTINGS/<br/>RULES (17) · QUICK-START<br/>CHANGELOG · CERINTE"]
    INFRA_BEST["_BEST_PRACTICES/<br/>GROWTH_LOG.md"]
    INFRA_METRICS["_METRICS/<br/>dashboard · codeburn-latest"]
    INFRA_VAULT["VAULT · SECRETS<br/>encrypted · PIN protected<br/>3 sensitivity levels<br/>USB backup · biometric"]
    INFRA_SECURITY["Security System<br/>secret-scan · permissions<br/>OWASP guidelines<br/>firewall · monitoring"]
  end

  subgraph L11_ANY["UNIVERSAL INTEGRATION — Any Application"]
    ANY_HOW["6 integration methods"]
    ANY_BRIDGE["① Bridge<br/>HTTP · WS · MQTT · TCP · UDP<br/>gRPC · serial · custom"]
    ANY_MCP["② MCP Server<br/>expose tools to agents"]
    ANY_PLUGIN["③ Plugin<br/>hooks on lifecycle events<br/>pre-bash · pre-edit · post-task"]
    ANY_SKILL["④ Skill<br/>domain instructions<br/>auto-loaded on match"]
    ANY_AGENT["⑤ Agent Profile<br/>role definition<br/>custom tools + prompts"]
    ANY_TEMPLATE["⑥ Template<br/>full project scaffold<br/>copy + customize"]
  end

  OC_DASH & OC_NOTE & OC_MONITOR & OC_BENCH & OC_COG --> CC_CORE
  CC_CORE --> CC_MCP1 & CC_MCP2 & CC_MCP3 & CC_MCP4
  CC_CORE --> CC_BR1 & CC_BR2 & CC_BR3 & CC_BR4 & CC_BR5
  CC_CORE --> CC_RUFLO & CC_SWARM & CC_PLUGINS
  CC_CORE --> CC_ENN
  CC_ENN --> CC_ENN1
  CC_PLUGINS --> CC_PL1
  CC_MCP1 & CC_MCP2 & CC_MCP3 & CC_MCP4 --> MC_API
  MC_API --> MC_DASH & MC_MGR & MC_BURN & MC_QUALITY & MC_METRICS
  MC_MGR --> MEM_ENGINE
  MEM_ENGINE --> MEM_N1 & MEM_N2 & MEM_N3 & MEM_N4 & MEM_N5 & MEM_N6
  MEM_SSA & MEM_SAFLA & MEM_INST & MEM_HOLO & MEM_AUTO --> MEM_ENGINE
  MEM_ENGINE --> MEM_MOTORS
  MEM_N4 --> AG_HERMES & AG_CLAUDE & AG_ZORIN & AG_SWARM & AG_GX & AG_EMAIL
  AG_CLAUDE --> AG_C1 & AG_C2 & AG_C3 & AG_C4 & AG_C5 & AG_C6 & AG_C7 & AG_C8 & AG_C9 & AG_C10
  SK_OC --> SK_OC1
  SK_H --> SK_H1 & SK_H2 & SK_H3 & SK_H4 & SK_H5 & SK_H6 & SK_H7 & SK_H8 & SK_H9 & SK_H10
  SK_C --> SK_C1
  SK_OCL --> SK_OCL
  MEM_N4 --> SK_OC & SK_H & SK_C & SK_OCL
  MC_MGR --> CMD_ANALYSIS & CMD_AUTO & CMD_GITHUB & CMD_HOOKS & CMD_MONITOR & CMD_OPT & MD_SPARC
  CC_RUFLO --> FLOW_CONFIG
  FLOW_CONFIG --> FLOW_SESSIONS & FLOW_REPORTS & FLOW_DATA & FLOW_MEM & FLOW_TEAM
  TMPL_ANDROID & TMPL_CARTE & TMPL_DEVCONTAINER & TMPL_GENERIC & TMPL_GITHUB & TMPL_OC & TMPL_PREVIEW & TMPL_RESEARCH & TMPL_MCP --> MC_MGR
  CRON_TOKEN & CRON_WATCH & CRON_CLEAN & CRON_SECURITY & CRON_EVOLUTION & CRON_BOOTSTRAP & CRON_SCRIPTS --> MEM_ENGINE
  INFRA_CONFIG & INFRA_MEMORY & INFRA_SETTINGS & INFRA_BEST & INFRA_METRICS & INFRA_VAULT & INFRA_SECURITY --> CC_CORE

  ANY_BRIDGE & ANY_MCP & ANY_PLUGIN & ANY_SKILL & ANY_AGENT & ANY_TEMPLATE --> L11_ANY

  style L0_OC fill:#1a1a2e,stroke:#e94560,color:#fff
  style L1_CCDEW fill:#16213e,stroke:#0f3460,color:#fff
  style L2_MC fill:#0f3460,stroke:#e94560,color:#fff
  style L3_MEM fill:#533483,stroke:#e94560,color:#fff
  style L4_AGENTS fill:#e94560,stroke:#1a1a2e,color:#fff
  style L5_SKILLS fill:#16213e,stroke:#0f3460,color:#fff
  style L6_CMDS fill:#1a1a2e,stroke:#e94560,color:#fff
  style L7_FLOW fill:#0f3460,stroke:#533483,color:#fff
  style L8_TMPL fill:#16213e,stroke:#e94560,color:#fff
  style L9_CRON fill:#1a1a2e,stroke:#0f3460,color:#fff
  style L10_INFRA fill:#533483,stroke:#e94560,color:#fff
  style L11_ANY fill:#e94560,stroke:#1a1a2e,color:#fff,stroke-dasharray: 5 5
```

---

## Piramida învățării — detalii

| Nivel | Fișier | Conținut | Motor |
|-------|--------|----------|-------|
| **N1 Episodic** | `episodic.jsonl` | Acțiuni, comenzi, rezultate, timestamp | auto-hook post-task |
| **N2 Patterns** | `patterns.json` | Cluster-uri Jaccard trigram, frecvență | `hermes-memory.py` match |
| **N3 Techniques** | `techniques.json` | Metode reusable cu pași | consolidare N2 |
| **N4 Skills** | `skills_db.json` | 133 skill-uri cu instrucțiuni | consolidare N3 |
| **N5 Attitudes** | `tacit.json` | Mindset, atitudini, euristici | consolidare N4 |
| **N6 Principles** | `principles.json` | 14 reguli universale | consolidare N5 |

Motoare suplimentare: `ssa.cjs` (semantic search), `safla.cjs` (adaptive learning), `instincts.cjs` (pattern recognition), `hologram_engine.py` (fractal integration), `auto_learn_consolidate.py` (periodic N1→N6).

---

## Cum integrezi orice aplicație

| Metodă | Când se folosește | Exemple |
|--------|-------------------|---------|
| **Bridge** | Ai un protocol TCP/UDP/HTTP/WS/MQTT | streaming, IoT, APIs |
| **MCP Server** | Vrei să expui tool-uri agenților | baze de date, servicii externe |
| **Plugin** | Vrei hook-uri în ciclul de viață | pre-bash, pre-edit, post-task |
| **Skill** | Vrei instrucțiuni de domeniu | orice specializare |
| **Agent Profile** | Vrei un rol nou de agent | analyst, coder, researcher... |
| **Template** | Vrei un proiect complet | android, carte, devcontainer... |

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
│   ├── helpers/           # 80+ Python + CJS motoare
│   ├── mcp/               # 4 MCP servers
│   ├── agents/            # 105+ agent profiles
│   ├── bridge/            # 5 bridges
│   ├── skills/            # 34 Claude skills
│   └── commands/          # 100+ CLI comenzi în 7 categorii
├── .opencode/             # 15 plugins TS + config
├── .claude-flow/          # 3505 sesiuni, 243 rapoarte
├── ccdew-core/            # NPM library + CLI binaries
├── agents/                # 15 top-level profiles
├── _MEMORY/               # 6 nivele memorie + ADR + identitate
├── _SETTINGS/             # 17 reguli + configurații
├── _TEMPLATES/            # 9 șabloane de proiect
├── _METRICS/              # Cost & performance
├── [your-apps]            # Aplicațiile tale integrate aici
```

---

## Securitate

- 3 nivele de sensibilitate: PUBLIC / PRIVATE / SECRET
- Vault criptat (PIN protected) + biometric
- Secret scanning automat (pre-commit)
- Permission guard pe comenzi bash
- Security monitoring la 12h (OWASP guidelines)
- Firewall monitoring (UFW, porturi)

---

*CCDEW — Framework universal. Integrează orice. Auto-vindecare. Auto-evoluție.*
