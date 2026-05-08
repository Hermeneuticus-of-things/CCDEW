# CHANGELOG — claude-code-eficient-workspace

> Format: [`_SETTINGS/CHANGELOG-FORMAT.md`](_SETTINGS/CHANGELOG-FORMAT.md)

---

## [2.0.0] — v6.1 Micro: SSA + CodeBurn + SAFLA + Graphify + LangGraph Micro

**Data:** 2026-05-08  
**Request:** Sistem complet de optimizare token efficiency + cost observability + feedback loop adaptiv pentru Claude Code Desktop.

**Arhitectură (9 module noi, zero dependențe externe):**

### Module noi în `.claude/helpers/`

| Modul | Rol | LOC |
|---|---|---|
| `feature-flags.json` | Toggle on/off per componentă (lite/full) | — |
| `codeburn.cjs` | Integrare `codeburn` CLI real (npm v0.9.7) — date reale din `~/.claude/projects/` | 107 |
| `red-hat-evaluator.cjs` | Injectare întrebări critice pre-execuție pentru task-uri de arhitectură | 79 |
| `ssa.cjs` | Sparse/Selective Attention — filtrare Jaccard trigram, 76% reducere context + integrare Obsidian index | 140 |
| `auto-optimize.cjs` | Detectare prompt verbos → estimare % tokeni economisiți | 92 |
| `safla.cjs` | Self-Adaptive Feedback Loop — tracking success/failure per nod Enneagram + sync cu CodeBurn | 175 |
| `graphify.cjs` | Rapoarte ASCII + Markdown sesiune (CodeBurn + SAFLA + Obsidian + AutoOpt) | 220 |
| `langgraph-micro.cjs` | State machine workflow CJS (standard/architecture/quick_fix) fără Python | 255 |
| `metrics-update.cjs` | Auto-update `_DASHBOARD.md` + `_METRICS/` la SessionEnd (export background non-blocking) | 185 |

### Hook-handler.cjs — extins cu toate conexiunile

**UserPromptSubmit (route):**
- SSA filtrează context intelligence + entries Obsidian (top-3 relevante)
- AutoOptimize detectează prompturi verbale
- RedHat injectează întrebări critice (arhitectură ≥12 cuvinte + verb+substantiv)
- LangGraph pornește workflow potrivit (standard/architecture/quick_fix)
- SAFLA afișează hint adaptiv per nod
- Enneagram rutează spre agent optim

**inject-workflow:** extins cu SSA zoom level (NANO/MICRO/MAHA) + SAFLA weight adjustment

**SessionStart:** SAFLA.sessionStart() + obsidian-session-context.py → populează index

**SessionEnd:**
- CodeBurn.totals() (cache-first, 117ms vs 8500ms anterior)
- SAFLA.syncWithCodeBurn() — penalizează noduri cu cost ridicat
- Graphify.generateReport() → `.claude-flow/reports/session-*.md`
- MetricsUpdate → `_DASHBOARD.md` + `_METRICS/codeburn-optimize-latest.md`
- LangGraph.clearActive()

### Comenzi noi

| Comandă CLI | Acțiune |
|---|---|
| `node hook-handler.cjs flags` | Status toate componentele |
| `node hook-handler.cjs burn` | Cost real azi + luna (codeburn CLI) |
| `node hook-handler.cjs safla` | Performance history per nod Enneagram |
| `node hook-handler.cjs graphify` | ASCII summary + save raport MD |
| `node hook-handler.cjs lg` | Workflow activ LangGraph |

### Slash command nou
- `.claude/commands/cost.md` → `/cost`, `/cost today`, `/cost month`, `/cost optimize`, `/cost report`

### Fișiere noi workspace
- `_DASHBOARD.md` — actualizat automat la SessionEnd cu metrici CodeBurn
- `_METRICS/` — snapshot JSON + `codeburn-optimize-latest.md`

### Rezultate benchmark
- `session-end` overhead: **8500ms → 117ms** (−98.6%)
- SSA context reduction: **76%** (50 entries → 12)
- Toate hookurile: **93–185ms**
- Cost real sesiune: **$5.98/zi, $232.99/lună**

**Dependențe externe adăugate:**
- `codeburn@0.9.7` (npm global) — singurul pachet extern

**Decizii arhitecturale:**
- SAFLA, Graphify, LangGraph: implementări custom CJS (nu pachete externe — nu există pe npm/pip)
- SSA: Jaccard trigram (nu sparse attention Python — complexitate nejustificată)
- CrewAI: dezactivat permanent (redundant cu Ruflo)
- Export codeburn: `spawn detached` (non-blocking) la SessionEnd

---

## [1.1.0] — META-017 Auto-Learn Hook (silent background learning)

**Request:** Continuous reactive auto-learning system that captures lessons from conversations without explicit prompting; holographic, semantic-filtered, batch-consolidated to Obsidian-compatible memory.

**Architecture (3-component pipeline):**
- `auto_learn.py` (Stop hook, ~1ms) — QUEUE-ONLY: heuristic detector + project router + Karma editorial guard + atomic file-locked queue append with idempotency (md5 dedupe)
- `auto_learn_consolidate.py` (SessionEnd hook + manual `--force`) — Single LLM call (judge+distill+merge in one Anthropic API request, optional with `ANTHROPIC_API_KEY`); fallback to template-based merge; integration with semantic UPDATE-vs-NEW logic; respects Obsidian Memory v1 protocol (`## [Claude]` + `## [User]` sections); auto-creates per-project `MEMORY.md` indexes
- `auto_learn_rotate.py` (manual/cron) — lunar archival of low-confidence (`_version=1`, age >60 days) auto-learned files to `_ARCHIVE/auto_learned/<YYYY-MM>/`; cleanup MEMORY.md indexes

**Key features:**
- Crash-recovery: spawn detached consolidate when queue ≥8 (Windows DETACHED_PROCESS / Unix start_new_session) with sentinel anti-double-spawn
- Race-free queue: dedicated lock-file (`learn_queue.lock`) serializes load+dedupe+write
- Dynamic project detection: scans `PROJECTS/` folder (no hardcoded names)
- Tag normalization: spaces → dashes, alphanumeric+dash only (Obsidian-safe)
- Split MEMORY.md routing: per-project lessons indexed in `PROJECTS/<N>/_MEMORY/MEMORY.md`, global lessons in root `memory/MEMORY.md`
- Karma Book editorial guard: skips when paths match `.scriv|_NANO/|_MAP/|Cap.|_BLOG|ilustra|alogen` (avoids polluting memory with text-edit corrections)
- 7-node holographic audit applied (5 lenses + 2 zoom levels): all 12 critical/high/medium issues fixed before release

**Files added:**
- `.claude/helpers/auto_learn.py` (~280 LOC)
- `.claude/helpers/auto_learn_consolidate.py` (~520 LOC)
- `.claude/helpers/auto_learn_rotate.py` (~190 LOC)

**Hook config:**
- `Stop` hook timeout 5s (queue-light)
- `SessionEnd` adds consolidate `--force` (timeout 30s)

**Optional dependencies:** `pyyaml` (already required), `ANTHROPIC_API_KEY` env (for LLM-quality consolidation; falls back to template if missing)

---

## [1.0.0] — Initial template release

**Request:** Create complete GitHub template repo for Claude Code workspace with Enneagram optimizations.

**What was done:**
- `.claude/` — full hook system (hook-handler.cjs, router.js, enneagram_router.py, intelligence.cjs, obs.py, etc.)
- `.claude/settings.json` — all hooks wired (UserPromptSubmit, SessionStart, SessionEnd, SubagentStart, SubagentStop, etc.)
- `CLAUDE.md` — workspace rules (sanitized, no personal data)
- `BEST_PRACTICES.md` — universal patterns
- `_SETTINGS/RULES/` — all operational rules (11 files)
- `_TEMPLATES/` — scaffolding for android/carte/generic/research/preview-live-server
- `_BEST_PRACTICES/GROWTH_LOG.md`
- `memory/MEMORY.md` — template index
- `_MEMORY/` — protocol + inbox + dashboard + user notes templates
- `README.md` — full English documentation
- `.gitignore` — excludes personal data, runtime, node_modules

**Files created:** 50+
