<div align="center">

# CCDEW

**Autonomous AI Agent Ecosystem — Self-Improving · Measurable · Open Source**

[![MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Node.js](https://img.shields.io/badge/Node.js-20+-green.svg)](https://nodejs.org)

</div>

---

## The Problem

| # | Problem | Why it matters |
|---|---------|----------------|
| 1 | **LLMs never improve with use** | Same knowledge today = same knowledge tomorrow. Zero growth between sessions. |
| 2 | **One-size-fits-all reasoning** | Every task gets the same persona. No cognitive diversity. No specialization. |
| 3 | **No measurable quality metrics** | No way to tell if the system is getting better. No dashboard. No convergence target. |
| 4 | **Fragile and insecure** | One failure crashes everything. Shell injection in MCP. Race conditions in state files. |

---

## The Solution

**CCDEW is a self-improving AI agent ecosystem.** Three nested learning loops, 9 specialized cognitive nodes, and a live convergence dashboard — all running autonomously.

### Live Convergence

```
Composite: 73.4%  ███████████████████████████████████████░░░░░░  Target: 95%
```

| Node | Name | Convergence | Role |
|:----:|------|:-----------:|:-----|
| 3 | Achiever | **85.0%** | Precision execution |
| 7 | Enthusiast | **85.0%** | Exploration & possibility |
| 5 | Investigator | **80.0%** | Deep analysis |
| 2 | Helper | **79.3%** | Collaboration |
| **9** | **Orchestrator** | **73.2%** | Routing & coordination |
| 1 | Reformer | **73.6%** | Quality & principles |
| 4 | Individualist | **73.0%** | Unique perspectives |
| 6 | Loyalist | **73.0%** | Risk assessment |
| 8 | Challenger | **72.5%** | Action & execution |

> All 9 nodes above **72%** — up from 46% at session start. **111 autonomous iterations** driven by a self-training daemon that never stops. Updated every 30 seconds.

---

## How It Works — 3 Loops

| Loop | Engine | Cadence | What it does |
|:----:|--------|:-------:|--------------|
| **1** | `hermes-enneagram-core.py` + `ccdew-pipeline.py` | ≈s | Route task through 9 cognitive nodes → divergent/convergent pipeline → record to SAFLA |
| **2** | `hermes-self-train.py` + `hermes-convergence.py` | ≈30s | Pick weakest node → generate task → train → measure convergence delta → repeat |
| **3** | `hermes-memory.py` | ≈10ep | Extract patterns → techniques → attitudes → principles. Reverse mirror writes to separate channel. |

After Loop 1 runs, Loop 2 picks the weakest-performing node and trains it. Loop 3 consolidates everything into long-term memory. The system measurably improves with every cycle.

---

## Architecture

<p align="center">
  <img src="docs/ccdew-architecture.svg" alt="CCDEW Architecture" width="100%">
</p>

---

## Use Cases

| Scenario | Why CCDEW |
|----------|-----------|
| **Self-improving AI assistant** | Deploy an agent that gets better every day without manual retuning. The daemon never stops training. |
| **Multi-perspective analysis** | Route a problem through 9 cognitive personas → get 9 perspectives → converge into one verdict. |
| **Quality gate automation** | Pre-commit checks, pre-push gate, code review, risk assessment — all routed through the best-suited node. |
| **Research & learning system** | Memory pyramid auto-consolidates everything learned. N1 (raw episodes) → N6 (principles) automatically. |

---

## Benefits

| Problem | CCDEW Solution |
|---------|----------------|
| LLMs never improve with use | **Convergence engine** tracks every node. **Self-train daemon** drives toward 95%. |
| One-size reasoning | **9 Enneagram nodes** with unique system prompts, task transforms, per-node episodic memory. |
| No quality metrics | **Composite convergence score** (0–100%) — live, updated every 30s. |
| Race conditions | **HTTP bridge** — single process serves all state. Zero race conditions. |
| Failure cascades | **Non-fatal pipeline** — each sub-step wrapped in `try/except`. |
| Memory pollution | **Reverse mirror** writes to `mirror_inverse.jsonl` — separate from episodic. |
| Shell injection | **Native `http.request`** in Node.js — no `curl`, no `exec`. |

---

## Quick Start

```bash
git clone https://github.com/Hermeneuticus-of-things/CCDEW.git ~/CCDEW
cd ~/CCDEW

# Start pipeline + HTTP bridge
nohup python3 .claude/helpers/ccdew-pipeline.py serve > /tmp/ccdew-pipeline.log 2>&1 &

# Start self-training daemon
nohup python3 .claude/helpers/hermes-self-train.py --daemon > /tmp/self-train.log 2>&1 &
```

Open [OpenCode Desktop](https://opencode.ai) in the repo — `AGENTS.md` loads automatically. Ask the system what it can do.

### Structure

```
CCDEW/
├── .claude/helpers/     # Python engines (pipeline, core, convergence, memory, train)
├── .claude/mcp/         # MCP servers (native HTTP, no shell exec)
├── docs/
│   ├── ccdew-architecture.svg   # Visual architecture diagram
│   └── presentation.html        # Standalone HTML presentation (7 slides)
├── AGENTS.md                    # Auto-loaded by OpenCode
└── README.md
```

---

<p align="center"><em>Clone it. Run it. Watch it improve.</em></p>
