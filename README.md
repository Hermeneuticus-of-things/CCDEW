# CCDEW — Claude Code Development Efficient Workspace

[![tests](https://img.shields.io/badge/tests-147%2F147%20PASS-brightgreen)]() [![audit](https://img.shields.io/badge/audit-38%2F38%20PASS-brightgreen)]() [![suites](https://img.shields.io/badge/suites-22-blue)]() [![version](https://img.shields.io/badge/version-3.8.0-blue)]() [![license](https://img.shields.io/badge/license-MIT-green)]()

## What · How · Where — in 30 seconds

| | |
|---|---|
| **What** | A drop-in workspace wrapper for Claude Code. It sits between you and the LLM, filters context, picks the right agent, tracks cost, blocks secret leaks, and audits itself. |
| **How** | 13 lifecycle hooks + 19 slash commands. Each prompt is filtered through SSA (Jaccard trigram), routed via Enneagram (9 nodes), weighted by SAFLA (adaptive learning), and budgeted by codeburn (real-time cost). Every edit is checked for secret leaks. Every session is archived. |
| **Where** | Primary: **Claude Code** (full features). Compatible: Cursor, Codex, Gemini, OpenCode (capabilities detected, degraded gracefully). Cross-platform: Linux + macOS + Windows. |

## What you save (measured, live)

| | Without CCDEW | With CCDEW | Saved |
|---|---|---|---|
| **Context tokens / prompt** | ~10,000 | ~2,400 | **−76%** |
| **Memory injected at SessionStart** | 130+ files (~26 KB) | 2 critical + 12 SSA-filtered | **−85%** |
| **Verbose-prompt bloat** | full text | stripped patterns | **5–15%** |
| **Wrong-agent routing** | ~30% on day 1 | <10% after 50 tasks | **adaptive** |
| **Daily cost (visible live)** | unknown | `💰 $X.XX/$100/d` in statusline | budget alert at 75%, 100% |
| **Secret leaks at edit** | possible | hard-blocked (11 patterns) | **0** leaks possible |
| **Session-end overhead** | ~8.5s (v2.0) | 117ms | **−98.6%** |

## Speed (median, post-warm)

| Operation | Time |
|---|---|
| `ssa.filterContext(50)` | **0.31 ms** |
| `safla.recordOutcome` (cross-process locked) | **0.85 ms** |
| Hook `pre-edit` (incl. secret-scan) | ~30 ms |
| Hook `inject-workflow` | ~100 ms |
| Hook `route` | ~100 ms |
| Hook `session-end` (snapshot + bench) | ~150 ms |
| Full audit (`/evaluate-setup`, 38 checks) | **<1 s** |
| Full test suite (`npm test`, 147 tests) | <2 s |
| **Global hook timeout** | 5 s force-exit (hooks can never hang Claude Code) |

## Scope

```
22 test suites · 147/147 PASS · 0 FAIL
38 audit checks · 0 WARN · 0 FAIL
~7500 LOC · 47 helpers (21 lib/ + 26 top-level)
19 slash commands · 13 hook events
10 architectural decisions documented
1 external runtime dep (codeburn — optional, native fallback included)
```

---

## Detailed: what it does

A self-monitoring, self-archiving wrapper around Claude Code that:

- **Reduces context tokens by ~76%** per prompt (SSA: Jaccard trigram, top-K filter)
- **Routes prompts to the right agent** (9-node Enneagram + adaptive SAFLA + pattern Instincts)
- **Tracks real-time cost** with `codeburn` (or built-in native fallback) — daily budget alerts
- **Blocks secret leaks** before edit (11 patterns: AWS/Anthropic/OpenAI/RSA/JWT + 8 sensitive paths)
- **Audits itself at 5 zoom levels** (Maha → Macro → Mezzo → Micro → Nano)
- **Auto-runs `/verify` on `git commit`**, **`/quality-gate` on `git push`**
- **Auto-archives every session** to JSON + Obsidian Markdown
- **Survives multi-session race** (cross-process file-lock on shared state)

---

## How it looks (real output)

**Statusline (every prompt):**
```
💰 $239.25/$100/d · 1185c ⚠   │   🤖 67% ok·63fb   │   📂 CCDEW   │
```

**`npm run burn` (live cost):**
```
[CODEBURN] ALERT | Today $239.25 (1185 calls) | Month $2538.88 (18338 calls)
```

**`npm run infer` (5-zoom audit):**
```
[INFER] 10 findings · HIGH:2 WARN:7 INFO:1

MAHA:  [⚠] <tests> — Only 22 test suite(s) — below 50 expected for this LOC
       [ℹ] <workspace> — 47 helpers · 22 test suites · 33 skills · 7500 LOC
MACRO: [✗] hook-handler.cjs — 1024 lines — exceeds hard cap 500
       [✗] intelligence.cjs — 979 lines — exceeds hard cap 500
MICRO: [⚠] intelligence.cjs:325 — Function init() is 111 lines (>75)
NANO:  (clean)
```

**`inject-workflow` hint at every prompt:**
```
[AUTO-SWARM DIRECTIVE] refactor the auth module across 5 files
Node 7 (Innovator) | HEXAD | SSA:MAHA SAFLA:+0.05
SPAWN: reviewer → researcher → backend-dev → sparc-orchestrator → analyst → architecture
swarm_init(topology=hierarchical, maxAgents=6, strategy=specialized)
[SKILLS] suggested: agentdb-vector-search, github-code-review
[INSTINCT] you usually route this to node 7 (83% confidence over 6 similar prompts)
```

**`pre-edit` blocking secret leak:**
```
[BLOCKED] Secret leak risk: 1 secret pattern(s) detected: AWS Access Key
```

---

## Quick start

```bash
git clone https://github.com/Hermeneuticus-of-things/claude-code-eficient-workspace.git CCDEW
cd CCDEW
npm install -g codeburn        # optional, canonical cost data
npm test                       # 147/147 PASS expected
npm run audit                  # 38/38 PASS expected
claude                         # start using
```

## Configuration

Edit `.claude/helpers/feature-flags.json` to tune behavior:

```json
{
  "components": {
    "enneagram": true, "ssa": true, "codeburn": true, "red_hat": true,
    "safla": true, "graphify": true, "instincts": true, "secret_scan": true
  },
  "ssa": { "top_k": 12, "min_score": 0.15 },
  "codeburn": {
    "daily_budget_usd": 100.0,
    "warn_at_pct": 0.75,
    "alert_at_pct": 1.0,
    "cost_per_call_warn": 0.05
  },
  "safla": { "weight_success": 0.05, "weight_failure": -0.10, "weight_clamp": 0.5 }
}
```

Environment variables:
- `CCDEW_LANG=ro` — Romanian UI strings (partial)
- `HOOKS_SKIP=1` — bypass auto-`/verify` and auto-`/quality-gate` at git commit/push (emergency only)
- `GITHUB_TOKEN` — raises `/skills-propose` rate limit from 60/h to 5000/h
- `PYTHON_BIN` — explicit Python path (otherwise auto-detected)

---

## Walkthrough — a typical session

```
1. Open Claude Code in CCDEW/
   → SessionStart hook runs: SAFLA.sessionStart() + auto-audit (24h cadence)
   → Statusline shows: 💰 $X.XX/$100/d · Nc · 🤖 X% ok·Mfb · 📂 CCDEW

2. You type: "refactor the auth module across 5 files"
   → UserPromptSubmit fires inject-workflow + route hooks
   → Output appears as system-reminder:
     [AUTO-SWARM DIRECTIVE] Node 7 (Innovator) | HEXAD | SSA:MAHA SAFLA:+0.05
     SPAWN: reviewer → researcher → ... → architecture
     [INSTINCT] you usually route this to node 7 (83% confidence)

3. Claude edits src/auth.ts
   → pre-edit hook scans content with secret-scan.cjs
   → No leak detected → [OK] Edit validated

4. You commit: git commit -m "refactor auth"
   → pre-bash hook runs auto-/verify (typecheck + test + lint + secret + dead)
   → All pass → [AUTO-VERIFY] passed — proceeding with commit
   → Commit succeeds

5. You push: git push origin main
   → pre-bash hook runs auto-/quality-gate (verify + npm audit + coverage + cost/call)
   → All pass → [AUTO-QUALITY-GATE] passed
   → Push succeeds

6. You close Claude Code
   → SessionEnd hook fires
   → session-snapshot writes .claude-flow/sessions/session-<ts>.json
   → Plus _MEMORY/sessions/session-<ts>.md (Obsidian frontmatter)
   → perf-baseline records ssa.filterContext timing
   → Graphify writes session report
   → metricsUpdate refreshes _METRICS/_DASHBOARD.md
```

---

## Comparison

| Feature | CCDEW | [ECC](https://github.com/affaan-m/everything-claude-code) | [setup-evaluator](https://github.com/redhat-community-ai-tools/claude-code-setup-evaluator) | [ruflo](https://github.com/ruvnet/claude-flow) |
|---|---|---|---|---|
| Token reduction (SSA-style filter) | ✅ −76% | ✅ | — | — |
| Adaptive routing per-task | ✅ Enneagram + SAFLA + Instincts | ✅ | — | ✅ |
| Real-time cost tracking | ✅ codeburn + native fallback | — | — | — |
| Secret-leak pre-edit block | ✅ 11 patterns | — | ✅ | — |
| 5-zoom audit (Maha→Nano) | ✅ original | — | — | — |
| Auto-`/verify` on git commit | ✅ | — | partial | — |
| Cross-process race safety (file-lock) | ✅ | — | — | — |
| Session auto-archival (JSON + Obsidian MD) | ✅ | — | — | — |
| GitHub mature-skill scaffolding | ✅ no-code-copy | — | — | — |
| Multi-platform detection | ✅ | ✅ | — | — |
| Number of stars (community) | new | 140k+ | growing | growing |
| Typical user | dev tuning own workflow | broad ecosystem adopters | enterprise audit teams | swarm orchestration |

CCDEW positions as: **the depth-first integrator** — it picks ideas from all three above and builds on top with original layers (5-zoom audit, cross-process lock, session archival, mature-skill proposing). Honest attribution in [CREDITS.md](CREDITS.md).

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `[CODEBURN] CLI unavailable` | codeburn not installed globally | `npm install -g codeburn` (or rely on native fallback — works without it) |
| `Python was not found` on Windows | Windows Store alias trap | CCDEW v3.7+ auto-detects with `-V` probe; verify `npm run audit` shows real path |
| `ToolSearch +swarm_init` returns nothing | MCP claude-flow not loaded | restart Claude Code; `~/.claude.json` must have `"args": [..., "mcp", "start"]` |
| `[ONNX] onnxruntime-node not available` | vector embeddings disabled in ruflo | `cd D:/.../ruflo && npm install onnxruntime-node` (optional) |
| Hooks don't fire / prompts unchanged | hook config not picked up | restart Claude Code (settings.json read at startup) |
| `git commit` blocked unexpectedly | auto-`/verify` failed | run `npm run verify` standalone to see why; emergency: `HOOKS_SKIP=1 git commit ...` |
| `[BLOCKED] Secret leak risk` on legitimate file | false-positive on hex/JWT-like string | edit the file content, or temporarily disable via `feature-flags.json::components.secret_scan: false` |
| `safla.json` keeps showing `[object Object]` | bug from pre-v3.0 | run `node .claude/helpers/hook-handler.cjs safla-clean` |

For deeper diagnostics: `node .claude/helpers/hook-handler.cjs errors` (last 20 logged errors, PII-redacted).

---

## Privacy

- **No data leaves your machine** except what `codeburn` reads from `~/.claude/projects/` (your own LLM session logs) — used locally for cost computation, not transmitted.
- **GitHub API calls** only when you explicitly run `/skills-propose <keyword>` (search public repos, no auth required, optional `GITHUB_TOKEN` for higher rate limit).
- **All logs in `errors.jsonl`** are auto-redacted via `lib/redact.cjs` (emails, JWT, AWS/Anthropic/OpenAI keys, home paths → `~`). Safe to share for support.
- **Session snapshots** in `_MEMORY/sessions/` and `.claude-flow/sessions/` contain cost numbers + audit results + workspace stats — they stay local, are git-ignored.
- **Secret-scan** is local-only (regex patterns), no external service.

---

## Roadmap

| Item | Status |
|---|---|
| Split `intelligence.cjs` (979L) and `hook-handler.cjs` (1024L) | DEBT — see [`decisions/008`](_MEMORY/decisions/008-debt-structural-split.md) |
| ONNX integration (vector embeddings local) | depends on ruflo upstream |
| Full `CCDEW_LANG` propagation (currently only `codeburn.unavailable`) | LOW priority |
| `npm audit` periodic in CI | feasible — `lib/perf-baseline.cjs` pattern |
| TypeScript migration via JSDoc | being explored — `lib/jsdoc-validator.cjs` validates exports |
| MCP self-test (post-restart, validates `mcp__claude-flow__*` tools loaded) | possible via ToolSearch probe |
| Skill description-overlap fallback (v3.7) usage stats | already tracked in `.claude-flow/data/skill-usage.jsonl` |

The full architectural decisions (10 documented) live at [`_MEMORY/decisions/INDEX.md`](_MEMORY/decisions/INDEX.md).

---

## Documentation

| File | Purpose |
|---|---|
| [README.md](README.md) | This file (overview) |
| [CHANGELOG.md](CHANGELOG.md) | Version-by-version evolution v1.0 → v3.8.0 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Module map, data flow, 5-zoom design |
| [MIGRATION.md](MIGRATION.md) | Upgrade guide v2.0 → v3.x |
| [CREDITS.md](CREDITS.md) | Full attribution per source (direct deps, ancestry, inspired, original) |
| [`_MEMORY/decisions/INDEX.md`](_MEMORY/decisions/INDEX.md) | 10 architectural decisions documented |

---

## Key commands

```bash
# CLI (npm scripts)
npm test                      # run all 22 test suites
npm run audit                 # /evaluate-setup full check
npm run audit:fix             # auto-resolve drift
npm run burn                  # real-time cost
npm run verify                # quick pre-commit sweep
npm run quality-gate          # strict pass/fail before merge
npm run infer                 # 5-zoom audit
npm run optimize -- nano      # auto-fix NANO drift
npm run skills-propose -- "<keyword>"
npm run exit                  # session snapshot + Obsidian MD
npm run sessions-compare -- 5
npm run bench                 # hot-path benchmarks

# Slash commands in Claude Code
/evaluate-setup    /verify        /review            /quality-gate
/diff-explain      /research      /infer             /optimize
/skills-propose    /exit          /sessions-compare  /bench
/mcp-health        /platform      /instincts         /errors
/safla-clean       /skills-active /cost
```

---

## Auto-triggers (no manual call needed)

| When | Action |
|---|---|
| `git commit` in Bash | Auto-runs `/verify` (block on fail; bypass: `HOOKS_SKIP=1`) |
| `git push` in Bash | Auto-runs `/quality-gate` (block on fail; same bypass) |
| SessionStart (24h cadence) | Auto-runs `/evaluate-setup`, alerts only on FAIL or > 2 WARN |
| SessionEnd | Auto-saves snapshot (JSON + Obsidian MD) + benchmark hot paths |
| pre-edit | Auto-runs `secret-scan.check()` — blocks edit if leak detected |
| UserPromptSubmit | `inject-workflow` (SSA + Skills + Instincts) + `route` |

---

## Requirements

- Node.js ≥ 18
- Python 3.x (optional — used by Obsidian helpers)
- Claude Code CLI

Optional but recommended:
- `codeburn` (`npm install -g codeburn`) — canonical cost tracking
- `GITHUB_TOKEN` env — raises `/skills-propose` rate limit from 60/h to 5000/h

---

## Stability

| Aspect | Verified |
|---|---|
| Cross-process atomic writes | ✅ 200/200 outcomes survive 2 parallel `fork()` processes |
| 50 concurrent in-process atomic writes | ✅ no orphans, final state correct |
| 1000 SAFLA outcomes serial | ✅ 0 corrupt keys |
| Fuzz inputs (30+ malformed) | ✅ rejected consistently |
| Encoding edge cases (BOM, CRLF, RTL, emoji) | ✅ handled |
| Disk full / read-only / corrupt JSON | ✅ graceful degradation |
| Cross-platform (Linux + macOS + Windows) | ✅ |

---

## License

MIT — see [LICENSE](LICENSE).

CCDEW builds on permissive upstreams (codeburn MIT, ECC, Red Hat setup-evaluator, ruflo). Full attribution in [CREDITS.md](CREDITS.md).
