# CCDEW Architecture v3.8.0

> Complete module map, data flow, and design decisions across the 5 zoom levels (Maha → Nano).

---

## Maha — system as a whole

CCDEW is a **self-monitoring, self-archiving wrapper around Claude Code** that adds:
1. **Cost visibility** (codeburn + native fallback)
2. **Adaptive routing** (Enneagram + SAFLA + Instincts)
3. **Pre-flight safety** (secret-scan, path-safe, permissions deny)
4. **Lifecycle hooks** (every prompt, edit, bash, session boundary)
5. **Self-audit at 5 zoom levels** (`/infer` + `/optimize`)
6. **Session archival** (JSON + Obsidian MD per `/exit`)
7. **Cross-process safety** (file-lock for shared state)

**Total surface:** 22 test suites · 147 tests · 38 audit checks · ~7500 LOC · 19 slash commands · 13 hook events.

---

## Macro — module boundaries

### Layer separation (one-way deps)

```
helpers/
   ↓ depends on
lib/
   ↓ depends on
(stdlib only — no transitive deps in lib/)
```

`lib/` modules **never** depend on top-level `helpers/`. Helpers may depend on each other only at boundaries (e.g. `verify.cjs` → `secret-scan.cjs`). Validated by audit.

### Module groups

#### `lib/` — 21 reusable libraries

| Group | Modules |
|---|---|
| **Storage** | `atomic-write`, `migrate`, `file-lock` |
| **Platform** | `platform`, `path-safe` |
| **State + flags** | `flags`, `validate` |
| **Observability** | `error-log`, `redact`, `perf-baseline` |
| **Cost** | `codeburn-engine`, `pricing` |
| **Time** | `local-date` |
| **i18n** | `strings`, `i18n` |
| **5-zoom audit** | `auto-infer`, `auto-optimize`, `auto-learn` |
| **Quality** | `jsdoc-validator`, `remote-backup` |
| **Skills/sessions** | `skills-propose`, `session-snapshot` |

#### `helpers/` (top-level) — 26 modules

| Group | Modules |
|---|---|
| **Dispatcher** | `hook-handler.cjs` (lazy-require, 19 commands) |
| **Routing** | `router.js`, `enneagram_router.py`, `enneagram_compose.py` |
| **Context** | `ssa.cjs`, `intelligence.cjs`, `obs.py`, `obsidian-session-context.py` |
| **Adaptive** | `safla.cjs`, `instincts.cjs`, `auto-optimize.cjs` |
| **Skills** | `skills-activator.cjs` |
| **Cost** | `codeburn.cjs` |
| **Reporting** | `graphify.cjs`, `metrics-update.cjs` |
| **Workflow** | `langgraph-micro.cjs`, `red-hat-evaluator.cjs`, `auto-optimize.cjs` |
| **Lifecycle** | `session.js`, `auto-memory-hook.mjs` |
| **Audit slash** | `evaluate-setup.cjs`, `verify.cjs`, `review.cjs`, `quality-gate.cjs`, `diff-explain.cjs` |
| **Security** | `secret-scan.cjs` |
| **Platform** | `platform-detect.cjs`, `statusline.cjs` |
| **Tools** | `run-tests.cjs` |
| **Continuous learning** | `auto_learn.py`, `auto_learn_consolidate.py`, `auto_learn_rotate.py` |

---

## Mezzo — per-module responsibilities

Each module is single-responsibility. The audit flags any module with > 12 exports as "potentially over-responsibility". Currently all are within bounds.

### Notable per-module designs

#### `hook-handler.cjs` (~1024 lines, dispatcher)
- 19 named commands
- **Lazy-require pattern** — modules loaded only when their command is invoked
- Top-level imports kept minimal: `path`, `fs`, `lib/flags`, `lib/platform`
- All modules loaded with `safeRequire` (suppresses startup-time stdout noise)

#### `intelligence.cjs` (~979 lines, memory graph)
- PageRank computation on prompt history graph
- Trigram-tokenized similarity for context ranking
- Used by `/route` to find related prior work

#### Both above are flagged HIGH by `/infer` for being > 500 lines. **DEBT documented** in `_MEMORY/decisions/008-debt-structural-split.md` — split deferred, not blocked.

---

## Micro — function design

### Function size policy
- Soft cap: 50 lines
- Hard cap: 75 lines (audit WARN)
- Argument cap: 5 (use options object beyond)

### Currently over cap (3 functions in `intelligence.cjs`)
| Function | Lines | Cap | Status |
|---|---|---|---|
| `init()` | 111 | 75 | DEBT — refactor when split happens |
| `consolidate()` | 150 | 75 | DEBT |
| `stats()` | 191 | 75 | DEBT |

### Common patterns

#### Atomic write
```js
const { writeAtomicJson } = require('./lib/atomic-write.cjs');
writeAtomicJson(path, obj); // pid+ts-suffixed tmp + retry-with-backoff on EPERM
```

#### Cross-process lock
```js
const { withLock } = require('./lib/file-lock.cjs');
withLock(SAFLA_PATH, () => {
  const data = load();
  // modify
  save(data);
}, { timeoutMs: 5000 });
```

#### Error logging (auto-redacted)
```js
try { /* ... */ }
catch (e) { require('./lib/error-log.cjs').logError('module.scope', e, { context }); }
```

#### Lazy require with cache
```js
const _cache = {};
function lazy(name) {
  if (name in _cache) return _cache[name];
  // ... try .cjs/.js/index.cjs/index.js variants
}
```

---

## Nano — char-level conventions

### Whitespace
- LF line endings (CRLF auto-normalized by `/optimize nano`)
- 2-space indent (no tabs)
- No trailing whitespace (auto-stripped)
- No BOM (auto-removed)

### Strings
- Single quotes for code, double for JSON
- Template literals for interpolation
- Diacritics stripped via `String.normalize('NFD')` for routing keywords

### Comments
- `'use strict';` at top of every file
- JSDoc with `@param` + `@returns` for public exports (validated by `lib/jsdoc-validator.cjs`)
- No multi-line `// commented out` blocks (use git history)

---

## Data flow — UserPromptSubmit example

```
User types prompt
  ↓
[Hook] UserPromptSubmit fired (Claude Code → settings.json)
  ↓
hook-handler.cjs `inject-workflow`
  ├─ Lazy load: router, ssa, safla, langGraph, projectScope, skillsActivator, instincts
  ├─ Tokenize prompt (i18n.tokensOf with diacritics-strip)
  ├─ router.routeTask() → Enneagram node
  ├─ selectWorkflow() → hexad/triangle (with i18n keywords + node bias)
  ├─ safla.getWeightAdj(node) → ±0.5 confidence delta
  ├─ skillsActivator.activateForPrompt() → top 3 skill names
  ├─ instincts.suggest() → "you usually route this to node N"
  ├─ projectScope.hintLine() → "Active: PROJECTS/<name>"
  └─ Output:
     [AUTO-SWARM DIRECTIVE] or [WORKFLOW SUGGESTION]
     Node N | HEXAD/TRIANGLE | SSA:zoom SAFLA:adj
     SPAWN: <agent chain>
     [SKILLS] suggested: <names>
     [INSTINCT] you usually route this to node N
     [SCOPE] Active: PROJECTS/<name>
  ↓
hook-handler.cjs `route` (second hook in same event)
  ├─ Load intelligence (PageRank context)
  ├─ ssa.filterContext() — Jaccard top-K
  ├─ autoOptimize.analyze() — verbose-prompt detection
  ├─ redHat.evaluate() — critical questions for arch tasks
  ├─ langGraph.startWorkflow()
  └─ Output: routing recommendation table
  ↓
Claude Code receives both outputs as system-reminders
  ↓
LLM responds, takes actions
  ↓
[Hook] PreToolUse / PostToolUse / SubagentStart / SubagentStop fire
  ├─ pre-bash: secret-scan + git-commit/push gates
  ├─ pre-edit: secret-scan check
  ├─ post-edit: instincts.record + intelligence.recordEdit + codeburn.statusLine
  ├─ post-task: SAFLA.recordOutcome + instincts.record + langGraph.advance
  ↓
[Hook] SessionEnd
  ├─ session-snapshot.snapshot() → JSON + Obsidian MD
  ├─ codeburn.totals() + safla.syncWithCodeBurn() → SAFLA cost-aware penalty
  ├─ graphify.generateReport() → ASCII + MD report
  ├─ metricsUpdate.run() → _DASHBOARD.md update
  ├─ perf-baseline auto-bench ssa.filterContext (regression alert)
  ├─ langGraph.clearActive()
```

---

## Auto-evolving subsystems

### SAFLA — feedback weights
Per-Enneagram-node `(success, failure, weight_adj)`. Weight adjusts +0.05 / −0.10 per outcome, clamped to [-0.5, +0.5]. Read by `route` to bias confidence. Synced with codeburn at SessionEnd: high-cost nodes get penalty bias.

### Instincts — pattern recognition
Records `(fingerprint, node, success)` per task. After ≥3 occurrences with success rate ≥ 50%, becomes a "learned pattern". Surfaces as `[INSTINCT] you usually route this to node N`.

### Auto-learn — dynamic thresholds
Reads last 20 audit history files, learns rolling average pass/warn/fail. `shouldAlert(currentSummary)` returns `alert: true` only if **deviation > learned baseline**.

### Perf-baseline — regression detection
Rolling 30-sample p95 per metric. SessionEnd auto-records `ssa.filterContext` timing. If current run > baseline × 1.5 → log `[PERF] 🚨 regression`.

### Skill activation tracking
Every `activateForPrompt()` writes to `skill-usage.jsonl`. `deadSkills()` returns names with 0 activations across history.

---

## Storage layout

```
.claude-flow/
├── data/
│   ├── safla.json              ← per-node SAFLA state (versioned, locked)
│   ├── codeburn-cache.json     ← cost cache (60s TTL)
│   ├── perf-baseline.json      ← rolling 30-sample p95 per metric
│   ├── instincts.jsonl         ← (fingerprint, node, success) log
│   ├── skill-usage.jsonl       ← skill activation log
│   ├── pending-insights.jsonl  ← intelligence layer
│   ├── session-critical-index.json ← Obsidian context
│   ├── learned-thresholds.json ← auto-learn output
│   ├── graph-state.json        ← intelligence graph
│   ├── ranked-context.json     ← intelligence ranking
│   └── auto-memory-store.json  ← auto-memory-hook.mjs storage
├── sessions/                   ← per-session JSON snapshots
├── reports/                    ← evaluate-* JSON + graphify-* MD
└── logs/
    └── errors.jsonl            ← redacted error log (rotated 5k lines)

_MEMORY/                        ← Obsidian vault
├── _DASHBOARD.md               ← live evolution table
├── _INBOX.md                   ← user → Claude drop zone
├── _PROTOCOL.md                ← bidirectional vault rules
├── _USER_NOTES.md              ← user-only space
├── decisions/                  ← 11 architectural decisions
├── sessions/                   ← Obsidian MD per /exit
└── agents/                     ← (reserved)

_METRICS/                       ← codeburn snapshots + dashboard MD
_ARCHIVE/                       ← rollback snapshots + optimize backups
```

---

## Configuration

### `feature-flags.json` (feature toggles)
```json
{
  "components": {
    "enneagram": true, "ssa": true, "codeburn": true, "red_hat": true,
    "safla": true, "graphify": true, "langraph": true, "project_scope": true,
    "intelligence": true, "auto_optimize": true, "instincts": true, "secret_scan": true
  },
  "ssa": { "max_context_tokens": 8000, "top_k": 12, "min_score": 0.15 },
  "codeburn": {
    "warn_tokens": 50000, "alert_tokens": 100000,
    "daily_budget_usd": 100.0, "warn_at_pct": 0.75, "alert_at_pct": 1.0,
    "cost_per_call_warn": 0.05
  },
  "red_hat": { "trigger_min_words": 10, "always_on_for_architecture": true },
  "safla": { "weight_success": 0.05, "weight_failure": -0.10, "weight_clamp": 0.5 }
}
```

### `~/.claude.json` (MCP servers — Claude Code global config)
```json
{
  "mcpServers": {
    "claude-flow": {
      "type": "stdio",
      "command": "<node>",
      "args": ["<path>/ruflo/bin/cli.js", "mcp", "start"]
    }
  }
}
```

---

## Cross-platform notes

- Path resolution: `lib/platform.cjs::findExecutable()` filters `.cmd/.exe/.bat` on Windows; first-line on POSIX
- Python detection: `findPython()` probes `-V` to skip Windows Store aliases
- Atomic write: pid + timestamp + random suffix in tmp filename to avoid race
- File lock: `O_EXCL` open is atomic on both Windows NTFS and POSIX filesystems
- Date: `toLocaleDateString('en-CA')` produces `YYYY-MM-DD` in local TZ on all platforms

---

## See also

- [`README.md`](README.md) — user-facing overview + commands
- [`CHANGELOG.md`](CHANGELOG.md) — version-by-version evolution
- [`CREDITS.md`](CREDITS.md) — full attribution
- [`MIGRATION.md`](MIGRATION.md) — v2 → v3 upgrade
- [`_MEMORY/decisions/INDEX.md`](_MEMORY/decisions/INDEX.md) — 10 design decisions explained
