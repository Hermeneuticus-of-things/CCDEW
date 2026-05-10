# Migration v2.0 → v3.x (CCDEW)

Upgrade guide for users moving from `claude-code-eficient-workspace v2.0` to **CCDEW v3.8.0** (current).

---

## TL;DR

```bash
# 1. Backup your current workspace
cp -r your-workspace your-workspace-backup-pre-ccdew

# 2. Clone CCDEW v3.8
git clone <CCDEW-repo> CCDEW
cd CCDEW

# 3. Install codeburn (canonical cost data — optional but recommended)
npm install -g codeburn

# 4. Generate package-lock for reproducibility
npm install --package-lock-only

# 5. Run a full audit to verify
npm run audit          # 38/38 PASS expected
npm test               # 147/147 PASS expected

# 6. Migrate any state worth keeping (see below)
```

---

## Folder rename: `claude-code-eficient-workspace` → `CCDEW`

The directory was renamed in v3.1 (`CCEW`) and again in v3.1.x (`CCDEW`). All internal references use **relative paths** or the `${WORKSPACE_DIR}` env var — no code changes needed beyond the rename.

If you cloned the v2 repo at `claude-code-eficient-workspace/`:
```bash
mv claude-code-eficient-workspace CCDEW
# Re-clone is also fine; nothing in user state ties to the folder name except external references.
```

External references that DO mention the old name:
- Root `D:/Cloude Code/CHANGELOG.md` → keep as-is (historical commit SHAs)
- GitHub upstream repo name remains `claude-code-eficient-workspace` (out of CCDEW's control)

---

## Module reorganization

### v2.0 layout
All helpers at the top of `.claude/helpers/`:
```
.claude/helpers/
├── hook-handler.cjs
├── safla.cjs
├── codeburn.cjs
├── ... (12 modules with eager-require)
```

### v3.x layout
Reusable utilities extracted into `lib/`, tests into `tests/`:
```
.claude/helpers/
├── lib/                       ← 21 reusable libraries
│   ├── atomic-write.cjs
│   ├── platform.cjs
│   ├── flags.cjs
│   ├── validate.cjs
│   ├── error-log.cjs
│   ├── codeburn-engine.cjs
│   ├── local-date.cjs
│   ├── pricing.cjs
│   ├── migrate.cjs
│   ├── i18n.cjs
│   ├── path-safe.cjs
│   ├── redact.cjs
│   ├── perf-baseline.cjs
│   ├── jsdoc-validator.cjs
│   ├── remote-backup.cjs
│   ├── strings.cjs
│   ├── auto-learn.cjs
│   ├── file-lock.cjs
│   ├── auto-infer.cjs
│   ├── auto-optimize.cjs
│   ├── skills-propose.cjs
│   └── session-snapshot.cjs
├── tests/                     ← 22 regression suites
│   ├── *.test.cjs (147 tests total)
├── hook-handler.cjs           ← LAZY-REQUIRE dispatcher
└── (other helpers — same names as v2)
```

All `require()` paths now use **explicit `.cjs` extensions** (Node 22 compatibility — bare names with `.cjs` extensions are not auto-resolved).

---

## State migration

### SAFLA state (`safla.json`)
v2 format is **forward-compatible**. v3 adds `version: '2.0'` field. The `migrate()` framework auto-upgrades on load:

```bash
# Optional cleanup of corrupt keys (e.g. "[object Object]" from v2 silent corruption):
node .claude/helpers/hook-handler.cjs safla-clean
```

This drops keys that don't match `^[1-9]$` while preserving all valid Enneagram node weight adjustments and feedback counts.

### Codeburn cache
v3 adds `version: '1.0'` field to `codeburn-cache.json`. No action needed — old caches are simply re-fetched on next call.

### Sessions, instincts, perf-baseline
All new in v3 — no v2 equivalent to migrate.

### Obsidian vault (`_MEMORY/`)
v2 had only template files. v3 populates:
- `_DASHBOARD.md` (auto-updated with version evolution table)
- `decisions/` (11 files: INDEX + 10 architectural decisions)
- `sessions/` (auto-populated at every `/exit` and SessionEnd)

If you have user notes in `_MEMORY/_USER_NOTES.md` from v2, they remain untouched.

---

## Codeburn — now optional

v2 hard-required `npm install -g codeburn` for cost tracking. v3 falls back to a **built-in native parser** (`lib/codeburn-engine.cjs`) that reads `~/.claude/projects/**/*.jsonl` directly.

| | CLI present | CLI absent |
|---|---|---|
| `source` field | `'real'` | `'native'` |
| Pricing accuracy | canonical (Anthropic CLI) | estimate (CCDEW pricing table v2026.05) |
| Latency | ~150ms | ~2.7s on 79 files |

The CLI is **strongly recommended** but no longer mandatory.

---

## New slash commands (v3.x additions)

Inspired by `claude-code-setup-evaluator` (Red Hat) and ECC:

| Command | v2 | v3 |
|---|---|---|
| `/evaluate-setup` | ❌ | ✅ Full health check (38 checks, 7 categories) |
| `/verify` | ❌ | ✅ Quick sweep (typecheck + tests + lint + secret-scan + dead-code) |
| `/review` | ❌ | ✅ 3-agent swarm brief (reviewer + analyst + tester) |
| `/quality-gate` | ❌ | ✅ Strict pass/fail before merge (incl. `npm audit`) |
| `/diff-explain` | ❌ | ✅ Plain-English git diff summary |
| `/research` | ❌ | ✅ ECC research-first dev mode |
| `/infer` | ❌ | ✅ 5-zoom audit (Maha → Nano) |
| `/optimize <zoom>` | ❌ | ✅ Auto-fix NANO + proposals for higher zooms |
| `/skills-propose` | ❌ | ✅ GitHub mature search + scaffold (no code copy) |
| `/exit` | ❌ | ✅ Full session snapshot (JSON + Obsidian MD) |
| `/sessions-compare` | ❌ | ✅ Diff across N snapshots |
| `/bench` | ❌ | ✅ Hot-path benchmarks + perf-baseline record |
| `/mcp-health` | ❌ | ✅ Verify `~/.claude.json` MCP servers |
| `/platform` | ❌ | ✅ Claude Code / Cursor / Codex / Gemini / OpenCode capabilities |
| `/instincts` | ❌ | ✅ Pattern recognition stats |
| `/errors` | ❌ | ✅ Last 20 logged errors (with PII redaction) |
| `/safla-clean` | ❌ | ✅ Remove corrupt SAFLA keys |
| `/skills-active` | ❌ | ✅ Skills matching current prompt |

All also callable via `node .claude/helpers/hook-handler.cjs <command>` or `npm run <command>`.

---

## New hooks behavior

### `pre-edit` now blocks secret leaks
v3 wires `lib/secret-scan.cjs` (11 secret patterns + 8 sensitive paths) into the `pre-edit` hook. **Edits with detected leaks are blocked** with `[BLOCKED] Secret leak risk: <reason>`.

### `pre-bash` auto-runs gates on git commit/push
- `git commit*` → auto-runs `/verify`; blocks if fail (bypass: `HOOKS_SKIP=1 git commit ...`)
- `git push*` (without `--no-verify`) → auto-runs `/quality-gate`; same bypass

### `inject-workflow` adds new hint lines
- `[SKILLS] suggested: <names>` — auto-activated by `skills-activator.cjs`
- `[INSTINCT] you usually route this to node N (X% confidence)` — from `lib/instincts.cjs`

### `post-task` records to instincts + SAFLA
Tuples `(prompt fingerprint, routed node, success)` are logged to `.claude-flow/data/instincts.jsonl` automatically.

### `SessionEnd` auto-saves snapshot + benchmarks
Every session-end:
- Writes `.claude-flow/sessions/session-<localISO>-<pid>.json` (machine-readable)
- Writes `_MEMORY/sessions/session-<localISO>-<pid>.md` (Obsidian Markdown)
- Runs benchmark for `ssa.filterContext`, records to `perf-baseline`
- Detects regression > baseline p95 × 1.5

### `SessionStart` auto-audit
Once per 24h, runs `/evaluate-setup --json` silently. Alerts only on FAIL or > 2 WARN.

---

## Permissions tightened

v3 adds **21 new** `Read(...)` deny patterns and **4 dangerous Bash** blocks. See [`README.md`](README.md#permissions-deny-list-security-baseline) for the full list.

---

## CLI changes

### v2 → v3 command map
| v2 | v3 |
|---|---|
| `node hook-handler.cjs flags` | `npm run flags` (or same direct call) |
| (manual codeburn check) | `npm run burn` |
| (manual evaluation) | `npm run audit` |
| (no test runner) | `npm test` (runs all 22 suites) |

### New env vars
- `CCDEW_LANG=ro` — switch UI strings to Romanian (partial coverage; English fallback always works)
- `HOOKS_SKIP=1` — bypass auto-verify / auto-quality-gate at git commit/push (use sparingly!)
- `GITHUB_TOKEN` — raises `/skills-propose` rate limit from 60/h to 5000/h

---

## What's NOT changed (intentional)

- Workspace top-level structure: `PROJECTS/`, `_BEST_PRACTICES/`, `_TEMPLATES/`, `_SETTINGS/`, `_MEMORY/`
- Enneagram routing topology (9 nodes, hexad/triangle cycles, BFS paths)
- `feature-flags.json` schema (extended with new keys, but old keys still work)
- All existing skills under `.claude/skills/`
- Workspace `CLAUDE.md`, `BEST_PRACTICES.md` content (only the folder name updated in references)

---

## Rollback

Every CCDEW operation that mutates files creates a backup. To revert to a pre-rebuild state:

```bash
# Pre-v3 rebuild snapshot (auto-created at v3.0 rebuild):
rm -rf .claude .claude-flow
cp -r _ARCHIVE/pre-rebuild-2026-05-10/.claude .
cp -r _ARCHIVE/pre-rebuild-2026-05-10/.claude-flow .

# Per-/optimize backups:
ls _ARCHIVE/optimize-bak-<date>/

# Pre-v3 .claude.json (MCP config) backup:
cp ~/.claude.json.bak.2026-05-10 ~/.claude.json
```

---

## Verifying after migration

```bash
# 1. All tests
npm test
# Expected: Total: 147 pass, 0 fail

# 2. Full audit
npm run audit
# Expected: PASS: 38 · WARN: 0 · FAIL: 0

# 3. 5-zoom auto-infer
npm run infer
# Should produce findings (warnings about debt are expected)

# 4. Auto-fix any drift
npm run audit:fix

# 5. First /exit to seed Obsidian sessions
npm run exit -- "post-migration verify"
# Check: ls _MEMORY/sessions/  (1 .md file expected)
```

---

## Help & support

If you hit issues:
1. `npm run audit:fix` — clears most drift automatically
2. `cat .claude-flow/logs/errors.jsonl | tail` — check redacted error log
3. Check `_MEMORY/decisions/` — the 10 documented decisions explain the why behind every major design choice
4. Open an issue with the redacted output (PII auto-stripped by `lib/redact.cjs`)
