# CCDEW — Claude Code Desktop Ecosystem Workspace

[![CI](https://github.com/Hermeneuticus-of-things/CCDEW/actions/workflows/ci.yml/badge.svg)](https://github.com/Hermeneuticus-of-things/CCDEW/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Node.js](https://img.shields.io/badge/Node.js-20+-green.svg)](https://nodejs.org)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

**Open Cload Intelligence Suite + CCDEW Core** — Universal framework for autonomous AI agents. Integrates any application. Self-evolution. Hierarchical memories. Self-healing.

---

## What is CCDEW?

CCDEW is a **custom** AI agent ecosystem built on top of [Claude Code Desktop](https://opencode.ai). It's not a public product you can install from a package manager — it's a complete, opinionated framework that you clone and run yourself.

### Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| [Node.js](https://nodejs.org) | 20+ | Runtime for MCP servers and JS tools |
| [Python](https://python.org) | 3.10+ | Runtime for AI engines and helpers |
| [Claude Code Desktop](https://opencode.ai) | latest | The AI CLI that hosts the ecosystem |
| git | any | To clone the repo |
| (optional) [OpenRouter key](https://openrouter.ai) | — | For LLM gateway features |
| (optional) [Google NotebookLM CLI](https://pypi.org/project/notebooklm/) | — | For NLM integration |

### Installation

```bash
git clone https://github.com/Hermeneuticus-of-things/CCDEW.git ~/CCDEW
cd ~/CCDEW
# Optional: install dependencies (if using ccdew-core NPM tools)
npm install
# Optional: install Python helpers
pip install -r requirements.txt  # if present
```

Point your Claude Code Desktop config to the repo and the `.claude/` structure will be auto-discovered.

### What can you do with it?

| Use Case | How CCDEW Helps |
|----------|----------------|
| **Multi-agent thinking** | Divergent/Convergent pipeline generates many perspectives, then synthesizes one verdict |
| **Long-running research** | NLM Bridge queries your NotebookLM notebooks with async + cache — never lose context |
| **Self-improving agents** | 6-level memory pyramid (N1 episodic → N6 principles) — agents learn from every session |
| **Fractal analysis** | Enneagram Router zooms from Maha (big picture) to Nano (detail) across 5 levels |
| **CI/CD for AI** | Quality gate, pre-commit verification, cost tracking — treat AI like code |
| **Any app integration** | 6 methods (Bridge, MCP, Plugin, Skill, Agent, Template) to connect anything |
| **Security-first** | 3 sensitivity levels, encrypted vault, secret scanning, permission guards |

### Who is it for?

- **AI power users** who want more than a chat interface — full agent orchestration
- **Developers** building autonomous AI workflows with structured memory and reasoning
- **Researchers** who need grounded (non-hallucinating) answers from their own source materials
- **Anyone** who wants AI agents that remember, adapt, and improve across sessions

### Why hasn't your LLM heard of it?

CCDEW is a **private, custom-built framework** — it lives in this GitHub repo and on the creator's machine. It's not trained into any public LLM's weights. OpenRouter models (DeepSeek, Qwen, Gemma, etc.) don't know about it unless they read this repo. That's normal and expected — CCDEW is designed to extend what an LLM can do, not to be known by one.

```
  ╔══════════════════════════════════════════════════════════════════╗
  ║                    OPEN CLOAD (UI Layer)                        ║
  ║  Dashboard · NotebookLM · Monitor · LLM Benchmark · Cognitive   ║
  ╚══════════════════════════════════════════════════════════════════╝
                                    │
  ╔══════════════════════════════════════════════════════════════════╗
  ║         LLM & MODELS — OpenRouter Gateway · Free Models        ║
  ║  deepseek-v4:free · qwen3-80b:free · gemma-4 · mistral ·       ║
  ║  llama · minimax · pricing · benchmark · agent→model mapping    ║
  ╚══════════════════════════════════════════════════════════════════╝
                                    │
  ╔══════════════════════════════════════════════════════════════════╗
  ║                    CCDEW CORE                                   ║
  ║  ccdew-core · MCP ×6 · Bridges ×5 · Ruflo · Swarm · Plugins    ║
║  Convergent/Divergent · NLM Bridge · Fractal Enneagram          ║
  ╚══════════════════════════════════════════════════════════════════╝
                                    │
  ╔══════════════════════════════════════════════════════════════════╗
  ║                    MISSION CONTROL                              ║
  ║  API :8899 · Dashboard · Agent Mgr · CodeBurn · Quality Gate    ║
  ╚══════════════════════════════════════════════════════════════════╝
                                    │
  ╔══════════════════════════════════════════════════════════════════╗
  ║           INTELLIGENCE & MEMORY — 6 LEVEL PYRAMID               ║
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

## Complete Architecture

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
    CC_MCP["MCP Servers x6"]
    CC_MCP1["ccdew-mcp<br/>11 tools: route, safla<br/>audit, cost, snapshot..."]
    CC_MCP2["opencode-llm<br/>5 tools: models, chat<br/>embedding, providers"]
    CC_MCP3["notebooklm<br/>content intelligence"]
    CC_MCP4["hermes-mission-control<br/>system health and snapshot"]
    CC_MCP5["ccdew-convergent-divergent<br/>5 tools: divergent, convergent<br/>pipeline, wings, domains"]
    CC_MCP6["ccdew-nlm-bridge<br/>7 tools: async, grouped, batch<br/>cache, multi, quota, auth"]
    CC_BRIDGES["Bridges x5"]
    CC_BR1["A2A Agent-to-Agent"]
    CC_BR2["MCP Bridge"]
    CC_BR3["External Bridge"]
    CC_BR4["Claude-OpenCode"]
    CC_BR5["Hermes A0 Bridge"]
    CC_RUFLO["Ruflo Engine<br/>agent flow execution"]
    CC_SWARM["Swarm Engine<br/>adaptive · hierarchical · mesh"]
    CC_PLUGINS["Plugin System x15"]
    CC_PL1["codeburn · graphify · safla<br/>instincts · verify · optimize<br/>permissions · secret-scan<br/>session · statusline · ssa<br/>project-scope · quality-gate<br/>red-hat · hermes-orch"]
    CC_ENN["Enneagram Router<br/>9 types + 5 zooms + 5 lenses<br/>18 wings · priority matrix"]
    CC_ENN1["T1:Reformer T2:Helper T3:Achiever<br/>T4:Individualist T5:Investigator<br/>T6:Loyalist T7:Enthusiast<br/>T8:Challenger T9:Peacemaker"]
  end

  subgraph L1b_MODELS["LLM and MODELS — Gateway and Free Models"]
    MODEL_GW["OpenRouter Gateway<br/>opencode-llm-mcp.cjs<br/>5 tools: models, chat<br/>embedding, providers, cost"]
    MODEL_FREE["Free Models Available<br/>deepseek/deepseek-v4-flash:free<br/>qwen/qwen3-80b:free<br/>google/gemma-4-*:free<br/>mistralai/*:free · meta-llama/*:free<br/>minimax/m2.5:free · and more"]
    MODEL_DIR["Model Directory and Pricing<br/>pricing.cjs · openrouter-pricing.cjs<br/>check-openrouter-free.cjs<br/>openrouter-note.md"]
    MODEL_BENCH["LLM Benchmark Suite<br/>llm-benchmark.py<br/>Open Cload cognitive tests<br/>performance comparison"]
    MODEL_MAP["Agent -> Model Mapping<br/>Hermes -> qwen3-80b:free<br/>Claude Agents -> Anthropic Claude<br/>GX Phone -> minimax-m2.5:free<br/>OpenCode -> deepseek-v4:free<br/>Swarm -> varies by task"]
    MODEL_OCONFIG["OpenCode Model Config<br/>.opencode.json · free list<br/>model fallback chain<br/>provider routing"]
    MODEL_HERMES["Hermes Model Usage<br/>Enneagram routing per node<br/>SAFLA selects best model<br/>auto-fallback on failure"]
  end

  subgraph L2_MC["MISSION CONTROL"]
    MC_API["REST API — port 8899<br/>status · channels · probe-all"]
    MC_DASH["Dashboard HTML<br/>components.js · agent list"]
    MC_MGR["Agent Manager<br/>stats · health · control"]
    MC_BURN["CodeBurn Cost Tracking<br/>session cost · monthly total"]
    MC_QUALITY["Quality Gate<br/>pre-push verification"]
    MC_METRICS["Metrics<br/>_METRICS/ · growth log"]
  end

  subgraph L3_MEM["INTELLIGENCE and MEMORY — 6 LEVEL PYRAMID"]
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
    MEM_AUTO["Auto-Consolidation<br/>auto_learn_consolidate.py<br/>N2->N6 periodic"]
    MEM_MOTORS["Additional Engines<br/>hermes-memory-sync.py<br/>hermes-binary-guardian.py<br/>fractal_patterns.json<br/>self_evolution.json"]
  end

  subgraph L4_AGENTS["AGENT TREE"]
    AG_HERMES["Hermes x6+<br/>core · autonomous<br/>memory · voice · notifier<br/>dashboard · binary-guard"]
    AG_CLAUDE["Claude Agents x105"]
    AG_C1["core x5<br/>coder · planner<br/>researcher · reviewer · tester"]
    AG_C2["v3 x16<br/>architect · security · memory<br/>sparc · swarm · reasoning<br/>ADD · PII · injection<br/>performance · defense"]
    AG_C3["github x13<br/>code-review · issue-tracker<br/>pr-manager · release-manager<br/>workflow · multi-repo-swarm<br/>project-board · repo-architect"]
    AG_C4["flow-nexus x9<br/>app-store · auth · payments<br/>neural-network · sandbox<br/>challenges · user-tools<br/>swarm · workflow"]
    AG_C5["sparc x4<br/>architecture · pseudocode<br/>refinement · specification"]
    AG_C6["swarm x3<br/>adaptive · hierarchical<br/>mesh coordinator"]
    AG_C7["sublinear x5<br/>consensus · matrix-optimizer<br/>pagerank · performance<br/>trading-predictor"]
    AG_C8["consensus x7<br/>byzantine · raft · gossip<br/>quorum · crdt · security<br/>performance-benchmarker"]
    AG_C9["optimization x5<br/>benchmark · load-balancer<br/>performance-monitor<br/>resource-allocator<br/>topology-optimizer"]
    AG_C10["hermes x2 + templates x9<br/>+ analysis, architecture<br/>browser, data, devops<br/>documentation, payments<br/>sona, specialized, testing"]
    AG_ZORIN["Zorin Agents x17<br/>tv · media · network<br/>browser · home · hardware<br/>vault · voice · scheduler<br/>bus · dev · personal<br/>launcher · bus · file<br/>hue · memory"]
    AG_SWARM["Swarm Coordinators x3<br/>adaptive-coordinator<br/>hierarchical-coordinator<br/>mesh-coordinator"]
    AG_GX["GX Agents<br/>monitor · dispatcher<br/>agent-zero · cron"]
    AG_EMAIL["Email Intelligence<br/>bb-safe-reader<br/>email-dashboard-server<br/>inbox-triage · raport-brut"]
  end

  subgraph L5_SKILLS["SKILL TREE — 133 total"]
    SK_OC["OpenCode Skills x7"]
    SK_OC1["hermes-ccdew · zorin-tv-system<br/>zorin-tv-repair · gx-monitor<br/>graphify · tv-identifier<br/>auto-skill"]
    SK_H["Hermes Skills x87"]
    SK_H1["zorin-romania-tv · zorin-auto-heal<br/>zorin-disk-watch · zorin-kernel-watch<br/>zorin-memory-opt · zorin-service-guard<br/>zorin-auto-* x3"]
    SK_H2["universal-techniques<br/>qnap-access · deep-stream-finder<br/>autonomous-ai-agents"]
    SK_H3["apple x6: macos-computer-use<br/>imessage · findmy · reminders<br/>apple-notes"]
    SK_H4["creative x11: comfyui · touchdesigner<br/>songwriting · sketch · pretext<br/>pixel-art · p5js · manim · ascii<br/>architecture-diagram · design-md"]
    SK_H5["data-science · devops x3<br/>email · gaming x2 · gifs<br/>github x6 · inference-sh"]
    SK_H6["media x6: youtube-content<br/>spotify · songsee · heartmula<br/>gif-search"]
    SK_H7["mlops x10: dspy · segment-anything<br/>audiocraft · vllm · obliteratus<br/>huggingface-hub · llama-cpp<br/>weights-and-biases<br/>lm-evaluation-harness"]
    SK_H8["research x4 · self-evolution<br/>smart-home · social-media<br/>software-development"]
    SK_H9["wondelai x30+: web-typography<br/>ux-heuristics · traction-eos<br/>top-design · system-design<br/>31 w-* design books"]
    SK_H10["workspace-dispatch · yuanbao<br/>mcp-client · note-taking<br/>productivity · red-teaming"]
    SK_C["Claude Skills x34"]
    SK_C1["agent-browser · agentdb-* x3<br/>browser · flow-nexus-* x3<br/>github-* x5 · hooks-automation<br/>pair-programming · reasoningbank-*<br/>skill-builder · sparc-methodology<br/>stream-chain · swarm-* x3<br/>v3-* x3 · verification-quality"]
    SK_OCL["Open-Cload Skills x5<br/>5-zoom-audit · cost-tracking<br/>enneagram-routing<br/>safla-feedback · secret-scanning"]
  end

  subgraph L6_CMDS["CLI COMMANDS — 7 Categories"]
    CMD_ANALYSIS["analysis x7<br/>bottleneck-detect · performance<br/>token-efficiency · etc"]
    CMD_AUTO["automation x7<br/>auto-agent · self-healing<br/>session-memory · smart-spawn"]
    CMD_GITHUB["github x19<br/>code-review · pr-manager<br/>release-manager · swarm-*"]
    CMD_HOOKS["hooks x8<br/>overview · post-edit · post-task<br/>pre-edit · pre-task · session-end"]
    CMD_MONITOR["monitoring x6<br/>agent-metrics · agents<br/>real-time-view · status · swarm"]
    CMD_OPT["optimization x6<br/>auto-topology · cache-manage<br/>parallel-execute · topology-opt"]
    CMD_SPARC["sparc x32<br/>analyzer · architect · coder<br/>debug · devops · etc"]
  end

  subgraph L7_FLOW["CLAUDE-FLOW ENGINE"]
    FLOW_CONFIG["config.yaml · CAPABILITIES.md"]
    FLOW_SESSIONS["3505 batch sessions<br/>conversation history"]
    FLOW_REPORTS["243 session reports<br/>6 evaluate reports"]
    FLOW_DATA["data x12+ files<br/>circuit9 · safla · memory<br/>learning · skill-usage · graph<br/>harness · perf · ssa · codeburn"]
    FLOW_MEM["memory storage<br/>snapshots · indices"]
    FLOW_TEAM["team config<br/>anonymous data"]
  end

  subgraph L8_TMPL["TEMPLATES — 9 Projects"]
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

  subgraph L9_CRON["AUTOMATION — Cron and Watchdogs"]
    CRON_TOKEN["token refresh 5min<br/>magicplaces · b1tv · qnap"]
    CRON_WATCH["watchdog 2min<br/>zorin-tv-watchdog.sh"]
    CRON_CLEAN["clean / probe 6h<br/>zorin-tv-clean.py"]
    CRON_SECURITY["security monitor 12h<br/>hermes-security · vault-monitor"]
    CRON_EVOLUTION["self-evolution<br/>auto_learn · consolidate"]
    CRON_BOOTSTRAP["startup services<br/>bootstrap-ccdew.sh"]
    CRON_SCRIPTS["helpers 15+ scripts<br/>guidance-hooks · statusline<br/>deploy-qnap-token · fix-brave"]
  end

  subgraph L10_INFRA["INFRASTRUCTURE"]
    INFRA_CONFIG[".mcp.json · .opencode.json<br/>swarm.yaml · package.json<br/>.gitignore · .plan-status.json"]
    INFRA_MEMORY["_MEMORY/<br/>L0-sensory · L1-working<br/>L2-episodic · L3-semantic<br/>L4-identity · ADR x11<br/>decisions · secrets<br/>hermes-sync · agents"]
    INFRA_SETTINGS["_SETTINGS/<br/>RULES x17 · QUICK-START<br/>CHANGELOG · CERINTE"]
    INFRA_BEST["_BEST_PRACTICES/<br/>GROWTH_LOG.md"]
    INFRA_METRICS["_METRICS/<br/>dashboard · codeburn-latest"]
    INFRA_VAULT["VAULT · SECRETS<br/>encrypted · PIN protected<br/>3 sensitivity levels<br/>USB backup · biometric"]
    INFRA_SECURITY["Security System<br/>secret-scan · permissions<br/>OWASP guidelines<br/>firewall · monitoring"]
  end

  subgraph L11_ANY["UNIVERSAL INTEGRATION — Any Application"]
    ANY_HOW["6 integration methods"]
    ANY_BRIDGE["(1) Bridge<br/>HTTP · WS · MQTT · TCP · UDP<br/>gRPC · serial · custom"]
    ANY_MCP["(2) MCP Server<br/>expose tools to agents"]
    ANY_PLUGIN["(3) Plugin<br/>hooks on lifecycle events<br/>pre-bash · pre-edit · post-task"]
    ANY_SKILL["(4) Skill<br/>domain instructions<br/>auto-loaded on match"]
    ANY_AGENT["(5) Agent Profile<br/>role definition<br/>custom tools + prompts"]
    ANY_TEMPLATE["(6) Template<br/>full project scaffold<br/>copy + customize"]
  end

  OC_DASH and OC_NOTE and OC_MONITOR and OC_BENCH and OC_COG --> MODEL_GW
  MODEL_GW --> MODEL_FREE and MODEL_DIR and MODEL_BENCH and MODEL_MAP and MODEL_OCONFIG and MODEL_HERMES
  MODEL_GW --> CC_CORE
  MODEL_MAP --> CC_MCP2
  CC_CORE --> CC_MCP1 and CC_MCP2 and CC_MCP3 and CC_MCP4 and CC_MCP5 and CC_MCP6
  CC_CORE --> CC_BR1 and CC_BR2 and CC_BR3 and CC_BR4 and CC_BR5
  CC_CORE --> CC_RUFLO and CC_SWARM and CC_PLUGINS
  CC_CORE --> CC_ENN
  CC_ENN --> CC_ENN1
  CC_PLUGINS --> CC_PL1
  CC_MCP1 and CC_MCP2 and CC_MCP3 and CC_MCP4 and CC_MCP5 and CC_MCP6 --> MC_API
  MC_API --> MC_DASH and MC_MGR and MC_BURN and MC_QUALITY and MC_METRICS
  MC_MGR --> MEM_ENGINE
  MEM_ENGINE --> MEM_N1 and MEM_N2 and MEM_N3 and MEM_N4 and MEM_N5 and MEM_N6
  MEM_SSA and MEM_SAFLA and MEM_INST and MEM_HOLO and MEM_AUTO --> MEM_ENGINE
  MEM_ENGINE --> MEM_MOTORS
  MEM_N4 --> AG_HERMES and AG_CLAUDE and AG_ZORIN and AG_SWARM and AG_GX and AG_EMAIL
  AG_CLAUDE --> AG_C1 and AG_C2 and AG_C3 and AG_C4 and AG_C5 and AG_C6 and AG_C7 and AG_C8 and AG_C9 and AG_C10
  SK_OC --> SK_OC1
  SK_H --> SK_H1 and SK_H2 and SK_H3 and SK_H4 and SK_H5 and SK_H6 and SK_H7 and SK_H8 and SK_H9 and SK_H10
  SK_C --> SK_C1
  SK_OCL --> SK_OCL
  MEM_N4 --> SK_OC and SK_H and SK_C and SK_OCL
  MC_MGR --> CMD_ANALYSIS and CMD_AUTO and CMD_GITHUB and CMD_HOOKS and CMD_MONITOR and CMD_OPT and CMD_SPARC
  CC_RUFLO --> FLOW_CONFIG
  FLOW_CONFIG --> FLOW_SESSIONS and FLOW_REPORTS and FLOW_DATA and FLOW_MEM and FLOW_TEAM
  TMPL_ANDROID and TMPL_CARTE and TMPL_DEVCONTAINER and TMPL_GENERIC and TMPL_GITHUB and TMPL_OC and TMPL_PREVIEW and TMPL_RESEARCH and TMPL_MCP --> MC_MGR
  CRON_TOKEN and CRON_WATCH and CRON_CLEAN and CRON_SECURITY and CRON_EVOLUTION and CRON_BOOTSTRAP and CRON_SCRIPTS --> MEM_ENGINE
  INFRA_CONFIG and INFRA_MEMORY and INFRA_SETTINGS and INFRA_BEST and INFRA_METRICS and INFRA_VAULT and INFRA_SECURITY --> CC_CORE

  ANY_BRIDGE and ANY_MCP and ANY_PLUGIN and ANY_SKILL and ANY_AGENT and ANY_TEMPLATE --> L11_ANY

  style L0_OC fill:#1a1a2e,stroke:#e94560,color:#fff
  style L1b_MODELS fill:#0f3460,stroke:#e94560,color:#fff
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

## Learning Pyramid — Details

| Level | File | Content | Engine |
|-------|------|---------|--------|
| **N1 Episodic** | `episodic.jsonl` | Actions, commands, results, timestamp | auto-hook post-task |
| **N2 Patterns** | `patterns.json` | Jaccard trigram clusters, frequency | `hermes-memory.py` match |
| **N3 Techniques** | `techniques.json` | Reusable methods with steps | consolidation N2 |
| **N4 Skills** | `skills_db.json` | 133 skills with instructions | consolidation N3 |
| **N5 Attitudes** | `tacit.json` | Mindset, attitudes, heuristics | consolidation N4 |
| **N6 Principles** | `principles.json` | 14 universal rules | consolidation N5 |

Additional engines: `ssa.cjs` (semantic search), `safla.cjs` (adaptive learning), `instincts.cjs` (pattern recognition), `hologram_engine.py` (fractal integration), `auto_learn_consolidate.py` (periodic N1→N6).

---

## LLM & Models — Gateway and Free Models

### OpenRouter Gateway
Any agent can route LLM traffic through an OpenRouter gateway (e.g., `opencode-llm-mcp.cjs`). Exposes tools for model discovery, chat completion, embeddings, provider info, and cost estimation. Swap models without changing agent code — just update config.

### Free Models Available — Any Provider
| Model | Provider | Typical Use |
|-------|----------|-------------|
| `deepseek/deepseek-*:free` | DeepSeek | Default general purpose |
| `qwen/qwen3-*:free` | Alibaba | Heavy tasks, long context |
| `google/gemma-4-*:free` | Google | Light tasks, fallback |
| `mistralai/*:free` | Mistral | Text analysis, embeddings |
| `meta-llama/*:free` | Meta | Reasoning, planning |
| `minimax/*:free` | MiniMax | Mobile/edge agents |

More free models appear regularly. The gateway auto-discovers available ones.

### How Any Agent Can Select a Model
- **By profile** — route heavy tasks to capable models, light tasks to fast ones
- **By cost** — prefer free models, fall back to paid only when needed
- **By capability** — reasoning, code generation, embeddings, vision, etc.
- **Adaptive** — success/failure history adjusts model selection over time
- **Configurable** — model lists, fallback chains, and routing rules live in a single config file

### Benchmark & Monitoring
Use benchmark tools to compare models on your specific tasks. Monitor cost per session. Track which models succeed or fail on which task types. Adapt routing dynamically.

The MCP gateway (`opencode-llm-mcp.cjs`) exposes `list_models`, `chat_completion`, `embedding`, `provider_info`, and `cost_estimation` tools — integrate from any agent or application.

---

## How to Integrate Any Application

| Method | When to Use | Examples |
|--------|-------------|---------|
| **Bridge** | You have a TCP/UDP/HTTP/WS/MQTT protocol | streaming, IoT, APIs |
| **MCP Server** | You want to expose tools to agents | databases, external services |
| **Plugin** | You want hooks in the lifecycle | pre-bash, pre-edit, post-task |
| **Skill** | You want domain instructions | any specialization |
| **Agent Profile** | You want a new agent role | analyst, coder, researcher... |
| **Template** | You want a complete project | android, book, devcontainer... |

---

## Quick start

```bash
# Bootstrap
bash bootstrap-ccdew.sh

# Start Mission Control
python3 .claude/helpers/mission-control.py

# Status
curl http://localhost:8899/status.json
```

---

## Structure

```
CCDEW/
├── .claude/
│   ├── helpers/           # 80+ Python + CJS engines
│   ├── mcp/               # 6 MCP servers
│   ├── agents/            # 105+ agent profiles
│   ├── bridge/            # 5 bridges
│   ├── skills/            # 34 Claude skills
│   └── commands/          # 100+ CLI commands in 7 categories
├── .opencode/             # 15 plugins TS + config
├── .claude-flow/          # 3505 sessions, 243 reports
├── ccdew-core/            # NPM library + CLI binaries
├── agents/                # 15 top-level profiles
├── _MEMORY/               # 6 memory levels + ADR + identity
├── _SETTINGS/             # 17 rules + configurations
├── _TEMPLATES/            # 9 project templates
├── _METRICS/              # Cost & performance
├── [your-apps]            # Your applications integrated here
```

---

## New Active Components

### Convergent/Divergent Engine (v1)
`ccdew-convergent-divergent.cjs` — Implements the protocol from `multi_agent_divergent_convergent.md` as an active MCP server.

| Tool | Description |
|------|-------------|
| `ccdew_divergent` | Generates N agents with distinct Enneagram wings (max 18 wings) |
| `ccdew_convergent` | Synthesizes N divergent outputs into integrated verdict |
| `ccdew_divergent_convergent` | Full pipeline in one call |
| `ccdew_wings_list` | Lists all 18 wings (zoom, lenses, perspectives, modalities) |
| `ccdew_domain_wings` | Shows domain → recommended wings mapping |

### NLM Bridge (v1) — NotebookLM Integration
**What is NotebookLM?** Google NotebookLM is an AI that answers questions exclusively from documents you upload (PDF, YouTube, web, text, audio) — zero hallucination, because it never invents outside your sources. Think of it as a personal research assistant that *only* talks about what you've given it.

**How it helps CCDEW:** Agents get secure, grounded access to your notebooks (knowledge bases). Instead of guessing or hallucinating, they query NotebookLM and get factual answers from your curated sources. The bridge adds async queries, cache, rate-limit avoidance, batch processing, and quota management — so agents can interrogate notebooks efficiently without triggering Google's anti-suspicion throttles.

`ccdew-nlm-bridge.cjs` — Implements the async 10-level protocol from `nlm_async_multi_channel_protocol.md` + `nlm_anti_suspicion.md`.

| Tool | Level | Description |
|------|-------|-------------|
| `nlm_async_query` | 1+2 | Async query with 180s timeout + automatic poll |
| `nlm_grouped_queries` | 3 | 2-5 sub-questions in a single query |
| `nlm_batch` | 4 | Multi-notebook batch with throttle between them |
| `nlm_cache` | 7 | Local cache management (stat, clear, search) |
| `nlm_multi_channel` | all | Full pipeline: auth → cache → grouped → batch |
| `nlm_quota` | 10 | Check remaining daily quota |
| `nlm_auth_check` | safe | Checks auth once per session |

### Fractal Enneagram Router (v2)
`enneagram_router.py` — Now supports fractal zooms + lenses.

| Command | Description |
|---------|-------------|
| `zoom [level]` | Zoom details: Maha, Macro, Mezzo, Micro, Nano |
| `lenses [name]` | Lens details: stylistic, doctrinal, structural, regression, memory |
| `priority` | Priority matrix per task type (editorial, security, etc.) |
| `compose <task> [--files N]` | Complete swarm composition (Phase 1-4) based on META-014 |
| `wings` | Complete registry with 18 Enneagram wings |

### NLM Session Hook
`nlm-session-hook.cjs` — Auto-check NLM auth at each session, with anti-suspicion pattern (max 1 check/session, not on every query).

---

## Security

- 3 sensitivity levels: PUBLIC / PRIVATE / SECRET
- Vault encrypted with PIN + biometric
- Automatic secret scanning (pre-commit)
- Permission guard on bash commands
- Security monitoring every 12h (OWASP guidelines)
- Firewall monitoring (UFW, ports)

---

*CCDEW — Universal framework. Integrates anything. Self-healing. Self-evolution.*
