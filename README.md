<div align="center">

# CCDEW

**An AI ecosystem that evolves itself — measurably, autonomously, transparently**

[![MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

</div>

---

## The Problem

Every AI system today suffers from the same four limitations. CCDEW was designed from day one to solve all of them.

| # | Problem | Why it hurts |
|---|---------|-------------|
| 1 | **LLMs plateau** | The model that answers your question today will give you the same answer tomorrow. Zero growth. Zero compounding improvement. |
| 2 | **One-size reasoning** | Every task — code review, creative writing, risk analysis — gets the same generic persona. No specialization. No cognitive diversity. |
| 3 | **No metrics** | You have no way to tell whether your AI system is improving or degrading. No dashboard. No convergence target. Blind operation. |
| 4 | **Brittle architecture** | One unhandled exception crashes the entire system. Shared state files corrupt under concurrent writes. Shell injection lurks in MCP tools. |

---

## The Solution

CCDEW replaces static, monolithic AI agents with a **self-improving ecosystem** of 9 specialized cognitive nodes, organized in three nested learning loops, measured by a live convergence score.

### Live Convergence

```
  Composite: 73.4%  ███████████████████████████████████████░░░░░░  Target: 95%
                                                                    
  111 auto-iterations · 187 episodes · 9 nodes tracked · converging
```

| Node | Name | Convergence | Specialization |
|:----:|------|:-----------:|:-------------|
| 3 | Achiever | **85.0%** | Gets things done with precision |
| 7 | Enthusiast | **85.0%** | Explores new possibilities |
| 5 | Investigator | **80.0%** | Analyzes deeply and systematically |
| 2 | Helper | **79.3%** | Collaborates and connects |
| **9** | **Orchestrator** | **73.2%** | Routes tasks and coordinates nodes |
| 1 | Reformer | **73.6%** | Enforces quality and principles |
| 4 | Individualist | **73.0%** | Brings unique perspectives |
| 6 | Loyalist | **73.0%** | Assesses risk and consistency |
| 8 | Challenger | **72.5%** | Drives action and execution |

> Every node above 72% — up from 46% at session start. The self-training daemon never stops.

---

## How It Works — 3 Learning Loops

| Loop | Cadence | What happens |
|:----:|:-------:|-------------|
| **1 — Execution** | ≈s | A task arrives. The Enneagram Core evaluates all 9 nodes and selects the best match. The chosen node processes through a divergent/convergent pipeline. The outcome feeds SAFLA, the adaptive learning engine. |
| **2 — Self-Training** | ≈30s | A daemon identifies the node with the lowest convergence score, generates a training task calibrated for its persona, runs the full cycle, and measures improvement. This never stops. |
| **3 — Consolidation** | ≈10ep | Raw episodic data is distilled into patterns, techniques, skills, attitudes, and ultimately universal principles. A reverse mirror writes metacognitive reflections to a separate channel — introspection never pollutes the action log. |

---

## Architecture

<p align="center">
  <img src="docs/ccdew-architecture.svg" alt="CCDEW Architecture" width="100%">
</p>

---

## Use Cases

| Scenario | What CCDEW gives you |
|----------|----------------------|
| **Self-improving assistant** | An AI that measurably improves every day without manual retuning. The daemon trains the weakest node autonomously. |
| **Multi-perspective analysis** | Route a problem through 9 distinct cognitive personalities. Get 9 perspectives. Converge into one synthetic verdict. |
| **Quality gate automation** | Pre-commit checks, pre-push verification, code review — each step routed through the best-suited cognitive node. |
| **Research & learning system** | Knowledge auto-consolidates from raw actions (N1) to abstract principles (N6). Nothing lost between sessions. |

---

## Quick Start

```bash
git clone https://github.com/Hermeneuticus-of-things/CCDEW.git ~/CCDEW
cd ~/CCDEW

# Start pipeline + HTTP bridge (no shared files, no race conditions)
nohup python3 .claude/helpers/ccdew-pipeline.py serve > /tmp/ccdew-pipeline.log 2>&1 &

# Start self-training daemon (finds and trains the weakest node every 30s)
nohup python3 .claude/helpers/hermes-self-train.py --daemon > /tmp/self-train.log 2>&1 &
```

### View the presentation

```bash
open docs/dashboard.html       # Animated live dashboard
open docs/presentation.html    # Interactive slide deck (← → navigate)
```

---

## Structure

```
CCDEW/
├── .claude/helpers/      # Python engines (pipeline, core, convergence, memory, train)
├── .claude/mcp/          # MCP servers — native HTTP, no shell exec
├── docs/
│   ├── ccdew-architecture.svg   # Architecture diagram
│   ├── dashboard.html           # Animated live dashboard
│   └── presentation.html        # Interactive slide deck
├── AGENTS.md                    # Auto-loaded by OpenCode Desktop
└── README.md
```

---

<p align="center"><em>Clone it. Run it. Watch it improve.</em></p>
