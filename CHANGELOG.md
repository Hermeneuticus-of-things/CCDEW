# CHANGELOG — CCDEW (Claude Code Development Efficient Workspace)

> Format reference: [`_SETTINGS/CHANGELOG-FORMAT.md`](_SETTINGS/CHANGELOG-FORMAT.md)
> Folder renamed in v3.1: `claude-code-eficient-workspace` → `CCEW` → `CCDEW`.
> See [`CREDITS.md`](CREDITS.md) for full source attribution.

---

## [3.8.0] — 2026-05-10 — Round 5 zone netouched: cross-process file-lock + bench + i18n

### Highlights
- **Cross-process race condition fix** — 2 parallel `fork()` processes writing SAFLA used to lose 50% of writes. New `lib/file-lock.cjs` with O_EXCL + retry-with-backoff guarantees 200/200 outcomes survive.
- **`/bench` command + auto-record at SessionEnd** — measures hot-path timings, alerts on regression > baseline p95 × 1.5.
- **i18n hot-path** — `t()` integrated for `codeburn.unavailable` message; `CCDEW_LANG=ro` partially propagated.

### Decisions
- Zones 1+2 (split `intelligence.cjs` 979L and `hook-handler.cjs` 1024L) deferred as **DEBT** — HIGH risk regression, 0 user-visible benefit. Documented in `_MEMORY/decisions/008-debt-structural-split.md`.

### Tests
- 22 suites · **147/147 PASS** · 0 FAIL
- New: `tests/file-lock.test.cjs` (6/6), `tests/cross-claude-race.test.cjs` (1/1)

---

## [3.7.0] — 2026-05-10 — Python detection + skills description fallback + NANO false-pos

### Highlights
- **Python `findPython()` real-path probe** — Windows Store alias `python3.exe` was triggering "Python was not found" promo and exit non-zero. Fix: probe with `-V`, return resolved path only on `Python X.Y` output.
- **Skills description-overlap fallback** — when SKILL.md has no `triggers` field, fall back to ≥2 word overlap with `description`. 33 skills now activatable.
- **NANO false-positive eliminated** — auto-infer no longer flags TODO/FIXME inside `/* */` block comments or string literals.
- **`tests/python-smoke.test.cjs`** — `ast.parse()` syntax check on all 7 Python helpers.

### Tests
- 20 suites · **140/140 PASS**

---

## [3.6.0] — 2026-05-10 — Skills-propose (GitHub mature search) + /exit session snapshot + /sessions-compare

### New modules
- `lib/skills-propose.cjs` — GitHub Search API + strict mature filter (≥10 stars, allowed licenses, push <365d, !archived) + scaffold generator (frontmatter only, no code copy).
- `lib/session-snapshot.cjs` — full session capture (cost+SAFLA+instincts+skills+perf+audit+errors+workspace) → JSON.

### New commands
- `/skills-propose <keyword>` — list mature candidates from GitHub
- `/skills-propose <keyword> --scaffold <local-name>` — generate `.claude/skills/<name>/SKILL.md` with attribution
- `/exit` — manual snapshot
- `/sessions-compare N` — diff across last N sessions

### Auto-trigger
- `session-end` hook now auto-saves snapshot on every Claude Code session close.

### Tests
- 19 suites · **133/133 PASS**

---

## [3.5.0] — 2026-05-10 — Stability 5-zoom + auto-learn + 7/10 round 4 zones repaired

### Repairs
| # | Zone | Solution |
|---|---|---|
| 1 | JSDoc absent | `lib/jsdoc-validator.cjs` |
| 2 | npm audit not wrapped | added in `quality-gate.cjs` |
| 3 | `_ARCHIVE/` local-only | `lib/remote-backup.cjs` warns on missing remote |
| 4 | i18n EN-only | `lib/strings.cjs` with RO+EN dict + env switch |
| 5 | Dead skill detection | `usageStats()` + `deadSkills()` + auto-track |
| 8 | No reproducibility | `package-lock.json` generated |
| 10 | Skill execution feedback | tracking auto on every `activateForPrompt()` |

Zones 6, 7, 9 skipped with documented rationale.

### New modules
- `lib/auto-learn.cjs` — dynamic threshold learning from audit history
- 5-zoom stability test suite (concurrency MACRO, stress MEZZO, fuzz MICRO, encoding NANO)

### Tests
- 17 suites · **114/114 PASS**

---

## [3.4.0] — 2026-05-10 — 5-zoom audit (Maha→Nano) + auto-infer + auto-optimize

### New modules
- `lib/auto-infer.cjs` — scans workspace at 5 zoom levels, deduces gaps without explicit user request
- `lib/auto-optimize.cjs` — applies safe NANO transforms automatically (BOM strip, CRLF→LF, trim trailing); MICRO/MEZZO/MACRO/MAHA proposal-only

### 5-zoom canon established
| Zoom | Scope |
|---|---|
| MAHA | Whole-system goal alignment |
| MACRO | Cross-module structure |
| MEZZO | Per-module cohesion |
| MICRO | Per-function complexity |
| NANO | Per-line/char hygiene |

See `_MEMORY/decisions/007-5-zoom-canon.md`.

### Tests
- 15 suites · **98/98 PASS**

---

## [3.3.0] — 2026-05-10 — perf-baseline + PII redact + auto-triggers + meta-workspace + RO docs

### Highlights
- `lib/perf-baseline.cjs` — rolling 30-sample p95 with regression detection
- `lib/redact.cjs` — automatic PII scrubbing in `error-log.cjs` (emails, JWT, API keys, home paths)
- `migrate()` framework wired into `safla.cjs::load()` — version chain v1.0→v2.0
- `repositories/` — Red Hat–style meta-workspace folder pattern
- `.claude/commands/research.md` — ECC research-first dev mode
- Auto-triggers: `git commit` → `/verify`; `git push` → `/quality-gate`; SessionStart → audit at 24h cadence

### Tests
- 13 suites · **86/86 PASS**

---

## [3.2.0] — 2026-05-10 — Adversarial round 2: TZ + i18n + shell-safe + budget + tools

### New `lib/` modules
| Module | Purpose |
|---|---|
| `lib/local-date.cjs` | TZ-aware `todayLocal()` / `monthLocal()` — non-UTC users no longer lose 2-4h "today" |
| `lib/pricing.cjs` | Centralized model pricing (PRICING_VERSION='2026.05'), single source of truth |
| `lib/migrate.cjs` | JSON migration framework with version chain + safety limit (32 steps) |
| `lib/i18n.cjs` | RO + EN routing keywords with diacritics-stripping |
| `lib/path-safe.cjs` | Shell injection mitigation: rejects `& ; \| $ ( ) ' " ! * ? \r \n` |

### Refactors
- `codeburn-engine.cjs` uses `lib/pricing` + `lib/local-date`, removed 17 hardcoded lines
- `codeburn.cjs::fetchRealStatus()` validates path with `isSafeBinaryPath()` before exec
- `hook-handler.cjs::selectWorkflow()` uses `lib/i18n` with diacritics stripping
- `metrics-update.cjs` no longer calls top-level `execSync` — uses `lib/platform.findExecutable()` lazy

### Config v3.2
- `feature-flags.json::codeburn.daily_budget_usd` (100 default), `warn_at_pct` (0.75), `alert_at_pct` (1.0)
- `settings.json::permissions.deny` +14 patterns (`.gnupg/`, `.docker/config.json`, `.npmrc`, `.pypirc`, `/etc/passwd`, `/etc/shadow`, `/etc/sudoers`, `/etc/ssh/`, `/proc/`, `C:\Windows\System32\config\`, `C:\Windows\System32\drivers\`) + dangerous Bash blocks (`mkfs.*`, fork bomb, `dd if=* of=/dev/sd*`, `rm -rf /`)
- Hook timeouts cut: `inject-workflow` 8s → 5s, `route` 10s → 5s

### Tools
- `package.json` with `engines.node >= 18` + 8 npm scripts
- `run-tests.cjs` — runner iterating `tests/*.test.cjs`
- `mcp-health` command — verifies `~/.claude.json::mcpServers` for misconfigurations
- Statusline budget alert: `💰 $X/$Y/d` with `🚨@100%` and `⚠@75%`

### Tests
- 11 suites · **70/70 PASS**

---

## [3.1.0] — 2026-05-10 — Blind-spot fixes + state restore + Instincts + auto-fix + folder rename CCEW→CCDEW

### Repairs from earlier audit blind spots
| Blind spot | Fix |
|---|---|
| SAFLA learned state lost in rebuild | Restored from `_ARCHIVE/pre-rebuild-2026-05-10/` with key validation: 8 valid nodes kept, 1 corrupt key (`[object Object]`) dropped, 45 real feedbacks recovered |
| Statusline broken | Rebuilt with lazy-require, live cost visible (`💰 $X.XX/d · Nc │ 🤖 X% ok·Nfb │ 📂 project │ 🖥 platform`) |
| Silent catches everywhere | `lib/error-log.cjs` with rotation (5k lines) at `.claude-flow/logs/errors.jsonl`; `/errors` command shows last 20 |
| Permissions deny weak | +21 patterns: `.env*`, `credentials.{json,yml}`, `secrets.*`, `id_rsa`, `id_ed25519`, `*.pem`, `*.pfx`, `.aws/credentials`, `.ssh/id_*`, `.kube/config`, `.netrc`, plus 4 `Bash` deny |
| Slash commands as dead code | Wired in `hook-handler.cjs`: `verify`, `review`, `quality-gate`, `diff-explain`, `evaluate-setup`, `platform`, `instincts`, `errors`, `safla-clean`, `skills-active` |
| Multi-platform stub unused | Wired in `/platform` with explicit capability report |
| Test isolation race | `safla-validation.test.cjs` uses `mkdtempSync` with pid + clear `require.cache` |
| Auto-fix missing | `/evaluate-setup --fix` resolves: invalid SAFLA keys, .tmp orphans, missing logs/, missing reports/ |
| v2 docs stale | `README.md` rewrite + `MIGRATION.md` complete for v2 → v3 upgrade |

### New ECC layer: Instincts
- `instincts.cjs` — pattern recognition from real usage
- Records `(prompt fingerprint, node, success)` in `.claude-flow/data/instincts.jsonl`
- Detects repeated patterns (≥3 occurrences, success_rate ≥ 50%)
- Suggests in `inject-workflow`: `[INSTINCT] you usually route this to node N (X% confidence over M similar prompts)`
- Auto-wired in `post-task` (records without explicit user request)

### Folder renamed
`claude-code-eficient-workspace/` → `CCEW/` → `CCDEW/` (final).

### Tests
- 6 suites · **35/35 PASS**

---

## [3.0.1] — 2026-05-10 — Native codeburn engine (CLI-independent fallback)

### Added
- `lib/codeburn-engine.cjs` — pure-Node parser for `~/.claude/projects/**/*.jsonl`
  - Computes cost directly from `usage.{input,output,cache_creation,cache_read}_tokens` × per-model pricing (opus/sonnet/haiku)
  - Latency: ~2.7s on 79 files (acceptable with 60s TTL cache)
  - Disclaimer: pricing is an estimate; CLI is canonical when present
- `tests/codeburn-engine.test.cjs` — 8 checks (modelTier mapping, cost computation, cache costs, totals shape)

### Changed
- `codeburn.cjs::totals()` — prefers CLI when available, falls back to native engine otherwise
- `evaluate-setup.cjs` — verifies CLI and engine separately, reports which source produces the data

### Result
System works **without `npm install -g codeburn`** (less precise on pricing).

### Tests
- 5 suites · **32/32 PASS**

---

## [3.0.0] — 2026-05-10 — Rebuild from scratch: lib/ utilities + ECC + Red Hat setup-evaluator integration

### Audit fixes (all applied)
| # | Bug | Fix |
|---|---|---|
| 1 | SAFLA silent state corruption (`[object Object]` keys) | `lib/validate.cjs` regex `^[1-9]$`; invalid silent skip |
| 2 | Codeburn Windows ENOENT (no `.cmd` ext) | `lib/platform.cjs::findExecutable` filters `.cmd|.exe|.bat` |
| 3 | Atomic rename EPERM under concurrency | `lib/atomic-write.cjs` retry-with-backoff 50/100/200ms + tmp cleanup |
| 4 | hook-handler eager-require 12 modules (~146ms cold) | Lazy `lazy(name)` cache, on-demand per command |
| 5 | Node 22 refuses `.cmd` at `execFileSync` (CVE-2024-27980) | `shell: true` only for `.cmd|.bat`, fixed args |

### New architecture under `.claude/helpers/`
```
helpers/
├── lib/                          ← reusable utilities
├── tests/                        ← regression test suites
├── hook-handler.cjs              ← LAZY-REQUIRE dispatcher
├── safla.cjs                     ← validation + atomic write + clamp
├── codeburn.cjs                  ← Win-aware `.cmd` + shell:true execFileSync
├── secret-scan.cjs               ← NEW: 11 secret patterns + 8 sensitive paths (ECC-style)
├── evaluate-setup.cjs            ← NEW: 38-check audit (Red Hat–style)
├── platform-detect.cjs           ← NEW: Claude/Cursor/Codex/Gemini/OpenCode detection
└── skills-activator.cjs          ← NEW: scans .claude/skills/*/SKILL.md
```

### ECC layer (everything-claude-code)
- `secret-scan.cjs` integrated in `pre-edit` hook (blocks AWS/Anthropic/OpenAI/GitHub/Stripe/RSA keys + sensitive paths)
- `skills-activator.cjs` scans `.claude/skills/<name>/SKILL.md` frontmatter and suggests active skills per prompt
- `platform-detect.cjs` — multi-platform stub: Cursor / Codex / Gemini / OpenCode / Claude Code

### Red Hat setup-evaluator layer
- `/evaluate-setup` — comprehensive audit (38 checks across config, modules, performance, state, cost, security, platform)
- `/verify` — quick sanity sweep (typecheck/test/lint/secret/dead-code)
- `/review` — 3-agent review swarm (reviewer + analyst + tester)
- `/quality-gate` — strict pass/fail before merge/deploy
- `/diff-explain` — plain-English summary of git diff

### Live audit (2026-05-10)
- 4 test suites: 24/24 PASS
- evaluate-setup: 38/38 PASS
- codeburn live: $5.98/d ~~(estimated reproducible — actually varies per machine)~~
- ssa.filterContext(50): 0.83ms median
- safla.recordOutcome: 1.22ms median

### Backup safety
Pre-rebuild snapshot at `_ARCHIVE/pre-rebuild-2026-05-10/.claude/` (2.9MB) and `.claude-flow/` (66KB) — instant rollback available.

---

## [2.0.0] — 2026-05-08 — v6.1 Micro: SSA + CodeBurn + SAFLA + Graphify + LangGraph Micro

**Request:** Complete token-efficiency optimization system + cost observability + adaptive feedback loop for Claude Code Desktop.

### Architecture (9 new modules, zero external deps except codeburn)

| Module | Role | LOC |
|---|---|---|
| `feature-flags.json` | Toggle on/off per component (lite/full) | — |
| `codeburn.cjs` | Real `codeburn` CLI integration (npm v0.9.7) | 107 |
| `red-hat-evaluator.cjs` | Inject critical questions before architecture tasks | 79 |
| `ssa.cjs` | Sparse/Selective Attention — Jaccard trigram filter, 76% context reduction | 140 |
| `auto-optimize.cjs` | Verbose-prompt detection → estimated token savings | 92 |
| `safla.cjs` | Self-Adaptive Feedback Loop — track success/failure per Enneagram node + sync with CodeBurn | 175 |
| `graphify.cjs` | ASCII + Markdown session reports (CodeBurn + SAFLA + Obsidian + AutoOpt) | 220 |
| `langgraph-micro.cjs` | CJS state machine workflow (standard/architecture/quick_fix), no Python | 255 |
| `metrics-update.cjs` | Auto-update `_DASHBOARD.md` + `_METRICS/` at SessionEnd (background non-blocking export) | 185 |

### Hook-handler.cjs — extended with all wirings

**UserPromptSubmit (route):**
- SSA filters intelligence context + Obsidian entries (top-3 relevant)
- AutoOptimize detects verbose prompts
- RedHat injects critical questions (architecture ≥12 words + verb+noun)
- LangGraph starts matching workflow (standard/architecture/quick_fix)
- SAFLA shows adaptive hint per node
- Enneagram routes to optimal agent

**inject-workflow:** extended with SSA zoom level (NANO/MICRO/MAHA) + SAFLA weight adjustment

**SessionStart:** SAFLA.sessionStart() + obsidian-session-context.py → populates index

**SessionEnd:**
- CodeBurn.totals() (cache-first, 117ms vs 8500ms previously)
- SAFLA.syncWithCodeBurn() — penalizes high-cost nodes
- Graphify.generateReport() → `.claude-flow/reports/session-*.md`
- MetricsUpdate → `_DASHBOARD.md` + `_METRICS/codeburn-optimize-latest.md`
- LangGraph.clearActive()

### New commands

| CLI command | Action |
|---|---|
| `node hook-handler.cjs flags` | Status of all components |
| `node hook-handler.cjs burn` | Real cost today + month (codeburn CLI) |
| `node hook-handler.cjs safla` | Performance history per Enneagram node |
| `node hook-handler.cjs graphify` | ASCII summary + save MD report |
| `node hook-handler.cjs lg` | Active LangGraph workflow |

### New slash command
- `.claude/commands/cost.md` → `/cost`, `/cost today`, `/cost month`, `/cost optimize`, `/cost report`

### New workspace files
- `_DASHBOARD.md` — auto-updated at SessionEnd with CodeBurn metrics
- `_METRICS/` — JSON snapshot + `codeburn-optimize-latest.md`

### Benchmark results
- `session-end` overhead: **8500ms → 117ms** (−98.6%)
- SSA context reduction: **76%** (50 entries → 12)
- All hooks: **93–185ms**

### External dependencies added
- `codeburn@0.9.7` (npm global) — sole external package

### Architectural decisions
- SAFLA, Graphify, LangGraph: custom CJS implementations (no npm/pip equivalents)
- SSA: Jaccard trigram (not Python sparse attention — complexity not justified)
- CrewAI: permanently disabled (redundant with Ruflo)
- Codeburn export: `spawn detached` (non-blocking) at SessionEnd

---

## [1.1.0] — 2026-05-04 — META-017 Auto-Learn Hook (silent background learning)

**Request:** Continuous reactive auto-learning system that captures lessons from conversations without explicit prompting; holographic, semantic-filtered, batch-consolidated to Obsidian-compatible memory.

### Architecture (3-component pipeline)
- `auto_learn.py` (Stop hook, ~1ms) — QUEUE-ONLY: heuristic detector + project router + Karma editorial guard + atomic file-locked queue append with idempotency (md5 dedupe)
- `auto_learn_consolidate.py` (SessionEnd hook + manual `--force`) — Single LLM call (judge+distill+merge in one Anthropic API request, optional with `ANTHROPIC_API_KEY`); fallback to template-based merge; integration with semantic UPDATE-vs-NEW logic; respects Obsidian Memory v1 protocol (`## [Claude]` + `## [User]` sections); auto-creates per-project `MEMORY.md` indexes
- `auto_learn_rotate.py` (manual/cron) — monthly archival of low-confidence (`_version=1`, age >60 days) auto-learned files to `_ARCHIVE/auto_learned/<YYYY-MM>/`; cleanup MEMORY.md indexes

### Key features
- Crash recovery: spawn detached consolidate when queue ≥8 (Windows DETACHED_PROCESS / Unix start_new_session) with sentinel anti-double-spawn
- Race-free queue: dedicated lock-file (`learn_queue.lock`) serializes load+dedupe+write
- Dynamic project detection: scans `PROJECTS/` folder (no hardcoded names)
- Tag normalization: spaces → dashes, alphanumeric+dash only (Obsidian-safe)
- Split MEMORY.md routing: per-project lessons indexed in `PROJECTS/<N>/_MEMORY/MEMORY.md`, global lessons in root `memory/MEMORY.md`
- Karma Book editorial guard: skips when paths match `.scriv|_NANO/|_MAP/|Cap.|_BLOG|illustration|alogen` (avoids polluting memory with text-edit corrections)
- 7-node holographic audit applied (5 lenses + 2 zoom levels): all 12 critical/high/medium issues fixed before release

### Files added
- `.claude/helpers/auto_learn.py` (~280 LOC)
- `.claude/helpers/auto_learn_consolidate.py` (~520 LOC)
- `.claude/helpers/auto_learn_rotate.py` (~190 LOC)

### Hook config
- `Stop` hook timeout 5s (queue-light)
- `SessionEnd` adds consolidate `--force` (timeout 30s)

### Optional dependencies
- `pyyaml` (already required), `ANTHROPIC_API_KEY` env (for LLM-quality consolidation; falls back to template if missing)

---

## [1.0.0] — 2026-05-01 — Initial template release

**Request:** Create complete GitHub template repo for Claude Code workspace with Enneagram optimizations.

### What was done
- `.claude/` — full hook system (hook-handler.cjs, router.js, enneagram_router.py, intelligence.cjs, obs.py, etc.)
- `.claude/settings.json` — all hooks wired (UserPromptSubmit, SessionStart, SessionEnd, SubagentStart, SubagentStop, etc.)
- `CLAUDE.md` — workspace rules (sanitized, no personal data)
- `BEST_PRACTICES.md` — universal patterns
- `_SETTINGS/RULES/` — all operational rules (11 files)
- `_TEMPLATES/` — scaffolding for android/book/generic/research/preview-live-server
- `_BEST_PRACTICES/GROWTH_LOG.md`
- `memory/MEMORY.md` — template index
- `_MEMORY/` — protocol + inbox + dashboard + user notes templates
- `README.md` — full English documentation
- `.gitignore` — excludes personal data, runtime, node_modules

### Files created
50+
