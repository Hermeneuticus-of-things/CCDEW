# claude-code-efficient-workspace v2.0

**An ultra-efficient workspace for Claude Code** with Enneagram routing, automatic token optimization, real cost tracking, and adaptive feedback loop.

> Based on: [Hermeneuticus-of-things/claude-code-eficient-workspace](https://github.com/Hermeneuticus-of-things/claude-code-eficient-workspace)  
> Extended with: v6.1 Micro — SSA + CodeBurn + SAFLA + Graphify + LangGraph Micro

---

## Why this workspace? — What you save and how

### The problem

Claude Code consumes tokens at every interaction. Without optimization:
- **At every SessionStart** the entire available memory is injected (130+ files), even if 90% is irrelevant to the current task.
- **At every prompt** context grows incrementally — Claude "forgets" what worked and what didn't.
- **No cost visibility** — you don't know which tasks cost the most or where the waste is.
- **No intelligent routing** — Claude treats `"fix bug"` and `"redesign architecture"` the same way.

### The solution — 5 mechanisms working together

#### 1. SSA — Context filtering (−76% injected tokens)
At every prompt, instead of injecting all memory, SSA calculates **Jaccard trigram similarity** between the prompt and each memory entry. Result: from 50 entries, only 12 are injected — the most relevant ones. The Obsidian index is included automatically.

```
Without SSA:  50 entries × ~200 tokens = ~10,000 tokens context
With SSA:     12 entries × ~200 tokens =  ~2,400 tokens context
Savings:      ~7,600 tokens per prompt
```

#### 2. Enneagram Routing — Right agent for the right task
The system automatically classifies each prompt into one of 9 task types and selects the specialized agent. A bug fix goes to `tester` (Node 6), not `sparc-orchestrator` (Node 8). Right agent → shorter and more precise response → fewer tokens.

```
Simple task  → TRIANGLE (3 agents): coder → tester → memory-specialist
Complex task → HEXAD (6 agents):   reviewer → researcher → ... → analyst
```

#### 3. CodeBurn — Complete cost visibility
Reads directly from `~/.claude/projects/` and displays in the status line:

```
🔥 $3.81 today  |  $230.82 this month  |  112 calls
```

At SessionEnd it automatically generates `_METRICS/codeburn-optimize-latest.md` with concrete suggestions: "152 calls today → group small tasks".

#### 4. SAFLA — System that learns from experience
Tracks which agent worked or not for each task type. If Node 3 (coder) failed 3 times on architecture tasks, the system penalizes this routing by −0.30 and favors Node 7 (architecture). Syncs with CodeBurn: nodes with high cost/call are automatically penalized.

#### 5. Red Hat Evaluator — Prevents over-engineering
Before any architecture task, injects 2-3 critical questions:
- *"What tacit assumptions does this solution contain?"*
- *"Is there a simpler approach with ≤50% of the complexity?"*

Prevents building complex solutions that then require refactoring (= double tokens).

### Measured results

| Metric | Value |
|--------|-------|
| Context reduction per prompt | **76%** (SSA) |
| Overhead per hook event | **93–185ms** |
| Session-end overhead | **117ms** (optimized from 8.5s) |
| Cost visibility | **real-time** via codeburn CLI |

---

## What it does

At every prompt, the system:

1. **Filters context** — SSA reduces injected memory by ~76% (Jaccard trigram, top-12 relevant entries)
2. **Critically evaluates** — Red Hat asks 2-3 questions before complex architectures
3. **Routes intelligently** — Enneagram sends the task to the optimal agent (9 nodes, hexad/triangle)
4. **Tracks cost** — CodeBurn displays `$X.XX today / $X.XX this month` in the status line
5. **Learns** — SAFLA adjusts weights per node based on successes/failures
6. **Reports** — Graphify generates a report at the end of each session

---

## Quick Setup

### 1. Requirements

- Node.js ≥ 18
- Python 3.x
- Claude Code CLI

### 2. Clone the workspace

```bash
git clone https://github.com/Hermeneuticus-of-things/claude-code-eficient-workspace.git workspace
cd workspace
```

### 3. Install CodeBurn (the only external package)

```bash
npm install -g codeburn
```

### 4. Start Claude Code

```bash
claude
```

On the first prompt, the system auto-initializes. Verify:

```bash
node .claude/helpers/hook-handler.cjs flags
```

---

## Workspace structure

```
workspace/
├── .claude/
│   ├── settings.json          ← 13 active hooks
│   ├── helpers/               ← 40+ modules (JS + Python)
│   │   ├── hook-handler.cjs   ← central dispatcher
│   │   ├── feature-flags.json ← component toggles
│   │   ├── codeburn.cjs       ← real cost tracking
│   │   ├── ssa.cjs            ← context filtering
│   │   ├── safla.cjs          ← adaptive feedback
│   │   ├── graphify.cjs       ← session reports
│   │   ├── langgraph-micro.cjs← workflow state machine
│   │   ├── red-hat-evaluator.cjs ← critical evaluation
│   │   ├── auto-optimize.cjs  ← verbose prompt detection
│   │   ├── metrics-update.cjs ← dashboard + metrics
│   │   ├── enneagram_router.py← 9-node routing
│   │   ├── enneagram_compose.py← multi-zoom swarm composer
│   │   ├── intelligence.cjs   ← PageRank memory graph
│   │   └── obsidian-session-context.py ← Obsidian context
│   └── commands/
│       └── cost.md            ← /cost command
├── PROJECTS/                  ← your projects
├── _BEST_PRACTICES/           ← wisdom per project type
├── _TEMPLATES/                ← scaffolding (android/book/generic)
├── _SETTINGS/RULES/           ← workspace protocols
├── _MEMORY/                   ← Obsidian memory vault
├── _METRICS/                  ← codeburn snapshots + optimize
├── _DASHBOARD.md              ← auto-updated at SessionEnd
└── BEST_PRACTICES.md          ← loaded at every session start
```

---

## Components and feature flags

Edit `.claude/helpers/feature-flags.json` to enable/disable:

```json
{
  "components": {
    "enneagram": true,   // intelligent routing
    "ssa":       true,   // context filtering -76%
    "codeburn":  true,   // real cost tracking
    "red_hat":   true,   // critical evaluation
    "safla":     true,   // adaptive feedback
    "graphify":  true,   // session reports
    "langraph":  true,   // workflow tracking
    "crewai":    false   // permanently disabled
  }
}
```

---

## CLI commands

```bash
# System status
node .claude/helpers/hook-handler.cjs flags

# Real cost (reads from ~/.claude/projects/)
node .claude/helpers/hook-handler.cjs burn

# Performance per Enneagram agent
node .claude/helpers/hook-handler.cjs safla

# ASCII session report
node .claude/helpers/hook-handler.cjs graphify

# Active workflow
node .claude/helpers/hook-handler.cjs lg

# Intelligence/memory diagnostics
node .claude/helpers/hook-handler.cjs stats
```

## Slash commands in Claude Code

```
/cost           → codeburn status (today + month)
/cost today     → current day details
/cost month     → current month details
/cost report    → interactive TUI dashboard
/cost optimize  → waste reduction suggestions
```

---

## Enneagram — intelligent routing

9 specialized nodes, 2 work cycles:

| Node | Agent | Role | Cycle |
|------|-------|------|-------|
| 1 | reviewer | QA, code review | hexad |
| 2 | backend-dev | integration, API | hexad |
| 3 | coder | direct implementation | triangle |
| 4 | researcher | context, documentation | hexad |
| 5 | analyst | analysis, debugging | hexad |
| 6 | tester | validation, testing | triangle |
| 7 | architecture | system design | hexad |
| 8 | sparc-orchestrator | complex orchestration | hexad |
| 9 | memory-specialist | memory, consolidation | triangle |

**HEXAD** (1→4→2→8→5→7): complex tasks, cross-project, ≥6 agents  
**TRIANGLE** (3→6→9): fast tasks, direct implementation, 3 agents

---

## SSA — Sparse/Selective Attention

Reduces injected context at every prompt:

- **Input:** all entries from the Intelligence memory graph + Obsidian index
- **Algorithm:** Jaccard trigram similarity between prompt and each entry
- **Output:** top-12 most relevant entries + pinned (`critical` priority)
- **Typical result:** 50 entries → 12 entries (76% reduction)

**SSA Zoom levels** (auto-detected from prompt length):
- `NANO` — short prompt (<15 words): minimal context
- `MICRO` — medium prompt (15-30 words): moderate context
- `MAHA` — long prompt (>30 words): maximum context

---

## SAFLA — Adaptive feedback

Tracks what works for each agent:

- **+0.05** weight adjustment on successful task
- **-0.10** weight adjustment on failed task (asymmetric — larger penalty)
- **Sync with CodeBurn:** when cost/call > $0.05 → automatic penalty on active nodes
- **Range:** [-0.5, +0.5] per node

---

## Enneagram Compose — Multi-zoom swarm composer

For hexad (complex) tasks, `enneagram_compose.py` automatically selects the correct swarm composition across **5 zoom levels** and **5 lenses**:

| Zoom | Scope | Checks |
|------|-------|--------|
| MAHA | Entire system/project | center of gravity, balance |
| MACRO | Cross-module/cross-chapter | cross-references, drift |
| MEZZO | Module/chapter | canonical host, rhythm |
| MICRO | Function/paragraph | internal logic, distinctions |
| NANO | Character/token | ASCII vs Unicode, punctuation |

**5 lenses:** stylistic (Node 4) · doctrinal (Node 5) · structural (Node 7) · regression (Node 6) · memory (Node 9)

Complexity is auto-determined from file count:
- **1-2 files:** no swarm — use Edit/Write directly
- **3-4 files:** MEDIUM — 3 lenses minimum, 4 phases
- **5-9 files:** COMPLEX — all 5 lenses, parallel cross-check
- **≥10 files:** MASSIVE — full protocol with DAG decomposition + Bargain-Triangle consensus

---

## Automatic dashboard

At every SessionEnd, the system automatically updates:

- **`_DASHBOARD.md`** — live CodeBurn metrics (cost today/month, calls, cost/call)
- **`_METRICS/codeburn-optimize-latest.md`** — waste reduction suggestions
- **`_METRICS/codeburn-<timestamp>.json`** — full snapshot (background)
- **`.claude-flow/reports/session-<timestamp>.md`** — complete Graphify report

---

## Performance

| Hook | Overhead |
|------|----------|
| UserPromptSubmit | ~104ms |
| PreToolUse | ~95ms |
| PostToolUse | ~100ms |
| SessionStart | ~185ms |
| SessionEnd | ~117ms |

---

## Architecture connections

```
UserPromptSubmit
    ├── SSA.filterContext(intelligence + Obsidian)
    ├── AutoOptimize.analyze(prompt)
    ├── RedHat.evaluate(prompt)
    ├── LangGraph.startWorkflow(prompt)
    ├── SAFLA.hint(node)
    ├── Enneagram.routeTask(prompt)
    └── EnneagramCompose.compose(prompt, files)  ← hexad only

SessionStart
    ├── SAFLA.sessionStart()
    └── obsidian-session-context.py → session-critical-index.json

PreCompact
    └── compact-save (CodeBurn + SAFLA + metrics — no duplicate session-end)

SessionEnd
    ├── CodeBurn.totals() [cache-first]
    ├── SAFLA.syncWithCodeBurn(burnTotals)
    ├── Graphify.generateReport()
    ├── MetricsUpdate → _DASHBOARD.md + _METRICS/
    └── LangGraph.clearActive()
```

---

## Add a new project

```bash
# Copy the appropriate template
cp -r _TEMPLATES/generic/ PROJECTS/ProjectName/

# Edit the project CLAUDE.md
nano PROJECTS/ProjectName/CLAUDE.md

# Add to the projects table in root CLAUDE.md
```

---

## Credits

- **Original workspace:** [Hermeneuticus-of-things](https://github.com/Hermeneuticus-of-things/claude-code-eficient-workspace)
- **Ruflo/claude-flow:** [ruvnet](https://github.com/ruvnet/ruflo)
- **CodeBurn:** [getagentseal](https://github.com/getagentseal/codeburn)
- **v6.1 Micro extensions:** implemented in session 2026-05-08
