# Claude Code Workspace — Helper Scripts

This directory holds the runtime helpers wired into Claude Code via `.claude/settings.json`. The 31 legacy V3 / daemon / swarm helpers were archived to `_ARCHIVE/dead-helpers-2026-05-08/` once they proved to be orphan code paths.

For full project documentation see the workspace root [README.md](../../README.md).

## Active helpers (wired into hooks)

### Central dispatcher
- **`hook-handler.cjs`** — central handler invoked by every Claude Code hook event (`pre-bash`, `pre-edit`, `post-edit`, `post-bash`, `inject-workflow`, `route`, `session-restore`, `session-end`, `compact-manual`/`-auto`/`-save`, `post-task`, `notify`, `status`, plus CLI subcommands like `stats`, `burn`, `flags`, `scope-status`, `scope-set`).

### Routing & workflows
- **`router.js`** — Enneagram routing (9 nodes, hexad/triangle cycles) + JS-ported BFS path-finding (`bfsPath`, `nextNode`).
- **`langgraph-micro.cjs`** — pure-CJS state-machine for multi-step workflows (`standard`, `architecture`, `quick_fix`).
- **`workspace_node_map.json`** — Enneagram workflow templates (hexad / triangle / agent capabilities).

### Context & memory
- **`ssa.cjs`** — Sparse/Selective Attention Jaccard trigram filter (top-k entries, pinned-aware).
- **`intelligence.cjs`** — PageRank-ranked memory graph (auto-memory-store, ranked-context, pending-insights jsonl with 2 MB rotation).
- **`obsidian-session-context.py`** — generates `session-critical-index.json` from `_MEMORY/` Obsidian vault (priority + tags propagated).
- **`obs.py`** — Obsidian CLI utility (search, read, fm, replace, audit) — primary CLI for memory access.
- **`auto-memory-hook.mjs`** — bridges auto-memory store on SessionStart/Stop.

### Cost & metrics
- **`codeburn.cjs`** — wraps the `codeburn` CLI for real cost data (cache-first, 60s).
- **`metrics-update.cjs`** — at SessionEnd writes `_METRICS/_DASHBOARD.md` + `_METRICS/codeburn-optimize-latest.md`, prunes old snapshots (keep last 30).
- **`graphify.cjs`** — ASCII + Markdown session reports.

### Adaptive layer
- **`safla.cjs`** — Self-Adaptive Feedback Loop, per-node weight adjustment (+0.05 success / −0.10 failure), syncs with CodeBurn.
- **`auto-optimize.cjs`** — verbose-prompt detection, suggests bloat removal.
- **`red-hat-evaluator.cjs`** — injects critical questions before architecture tasks (deterministic gate).
- **`project-scope.cjs`** — detects active `PROJECTS/<Name>/`, warns on cross-project edits.

### Multi-zoom composition
- **`enneagram_compose.py`** — multi-zoom (MAHA / MACRO / MEZZO / MICRO / NANO) × 5-lens swarm composer; reinforced via `_MEMORY/enneagram_adaptive_topology.json`.
- **`enneagram_router.py`** — Python CLI for **interactive** Enneagram exploration (`path`, `all_paths`, `route`, `spawn`). NOT in the live hook chain — the JS port in `router.js` does the live routing.

### Auto-learning (META-017)
- **`auto_learn.py`** — Stop-hook queue-only heuristic detector (zero LLM, < 100 ms).
- **`auto_learn_consolidate.py`** — SessionEnd LLM-merge of queued items into Obsidian memory.
- **`auto_learn_rotate.py`** — manual lunar archival (run `python .claude/helpers/auto_learn_rotate.py [--dry-run]`); not currently wired to a hook.

### Status line
- **`statusline.cjs`** — generates the Claude Code status line (git info, model, codeburn, SSA stats, etc.).

### Configuration
- **`feature-flags.json`** — per-component enable/disable toggles.
- **`session.js`** — atomic session lifecycle (start/restore/end/update/metric, all writes pid-suffixed tmp + rename).

## Test files

- `_test_project-scope.cjs` (13/13)
- `_test_runWithTimeout.cjs` (8/8)
- `_test_atomic_writes.cjs` (6/6 + 100 concurrent writes from 20 forked PIDs)

Run with `node .claude/helpers/_test_<name>.cjs`. They are self-contained: backup/restore real state files, leave no `.tmp` leftovers.

## Conventions

- All `.cjs` modules export pure functions, gated by `feature-flags.json` `components.<name>`.
- All multi-line state writes use atomic tmp+rename with `<pid>.<ts>.tmp` suffix to be concurrent-safe across multiple Claude Code instances on the same workspace.
- Cross-platform paths via `WORKSPACE_DIR` env or script-relative resolution; no hardcoded absolute paths.
- Every helper that runs in the hook chain stays under the 5 s global safety timeout in `hook-handler.cjs`; long-running work is `spawn`'d detached or skipped with `runWithTimeout`.

## Archived helpers

`_ARCHIVE/dead-helpers-2026-05-08/` contains 31 orphan modules from the v3 / daemon / swarm-monitor / worker-manager subsystems that were never wired into the live hook chain. Kept on disk (gitignored) for safety; can be `git restore` from history if any external user proves to need them.
