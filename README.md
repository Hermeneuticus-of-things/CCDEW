<div align="center">
  <h1>CCDEW</h1>
  <p><strong>Autonomous AI Agent Ecosystem — Self-Improving · Measurable · Open</strong></p>
  <p>
    <a href="https://github.com/Hermeneuticus-of-things/CCDEW"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT"></a>
    <a href="CONTRIBUTING.md"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome"></a>
  </p>
  <br>
</div>

---

## Live Convergence

```
                  ┌─────────────────────────────────────────────────────┐
Composite: 73.4%  │███████████████████████████████████████░░░░░░░░░░░░░│  Target: 95%
                  └─────────────────────────────────────────────────────┘
```

| Node | Name | Convergence | Role |
|:----:|------|:-----------:|------|
| 3 | Achiever | **85.0%** | Precision execution |
| 7 | Enthusiast | **85.0%** | Exploration & possibility |
| 5 | Investigator | **80.0%** | Deep analysis |
| 2 | Helper | **79.3%** | Collaboration |
| 9 | **Orchestrator** | **73.2%** | Routing & coordination |
| 1 | Reformer | **73.6%** | Quality & principles |
| 4 | Individualist | **73.0%** | Unique perspectives |
| 6 | Loyalist | **73.0%** | Risk assessment |
| 8 | Challenger | **72.5%** | Action & execution |

> All 9 nodes above **72%** — up from 46% at session start. **111 autonomous iterations** driven by the self-training daemon. Updated every 30 seconds.

---

## Architecture

<p align="center">
  <img src="docs/ccdew-architecture.svg" alt="CCDEW Architecture Diagram" width="100%">
</p>

---

## The Three Loops

| Loop | Engine | Cadence | What it does |
|------|--------|---------|--------------|
| **1 — Execution** | `hermes-enneagram-core.py` + `ccdew-pipeline.py` | ~seconds | Route task through 9 cognitive nodes → divergent/convergent pipeline → record to SAFLA |
| **2 — Self-Train** | `hermes-self-train.py` + `hermes-convergence.py` | ~30s | Pick weakest node → generate task → train → measure convergence delta |
| **3 — Consolidation** | `hermes-memory.py` | ~10 episodes | Extract patterns → techniques → attitudes → principles. Reverse mirror to separate channel |

---

## Infrastructure

| Component | What |
|-----------|------|
| **HTTP Bridge** | `127.0.0.1:18777` — single process serves all state. Zero race conditions |
| **SAFLA State** | Written only by `pipeline.py`. Others read/write via HTTP POST/GET |
| **MCP Servers** | 4 active — native Node.js HTTP (no shell injection) |
| **Inner Observer** | Metacognitive daemon — writes `consciousness.jsonl` (append-only) |
| **Centralized Logging** | All components → `POST /log` → `ccdew.log` |

---

## Benefits

| Problem | Solution |
|---------|----------|
| LLMs never improve with use | Convergence engine tracks every node. Self-train daemon drives toward 95%. |
| One-size-fits-all reasoning | 9 Enneagram nodes with unique system prompts, task transforms, and per-node episodic memory |
| Race conditions in state files | HTTP bridge with single writer — others read/write via HTTP |
| Failure cascades crash everything | Non-fatal pipeline — each sub-step wrapped in `try/except` |
| Memory polluted by reflections | Reverse mirror writes to `mirror_inverse.jsonl` — separate from episodic |
| MCP tools use shell exec (security risk) | Native `http.request` in Node.js — no `curl`, no `exec` |
| No way to know if the system is improving | Composite convergence score (0–100%) — live, updated every 30s |

---

## Quick Start

```bash
git clone https://github.com/Hermeneuticus-of-things/CCDEW.git ~/CCDEW
cd ~/CCDEW
nohup python3 .claude/helpers/ccdew-pipeline.py serve > /tmp/ccdew-pipeline.log 2>&1 &
nohup python3 .claude/helpers/hermes-self-train.py --daemon > /tmp/self-train.log 2>&1 &
```

OpenCode Desktop reads `AGENTS.md` automatically — ask the system what it can do.

---

## Project Structure

```
CCDEW/
├── .claude/
│   ├── helpers/            # Python engines (pipeline, core, convergence, memory, train)
│   └── mcp/                # MCP servers (notebooklm, convergence, llm gateway)
├── docs/
│   └── ccdew-architecture.svg
├── AGENTS.md               # Auto-loaded by OpenCode Desktop
└── README.md
```

---

<p align="center"><em>CCDEW — Built to improve itself.</em></p>
