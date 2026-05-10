# CCDEW — Claude Code Development Efficient Workspace v3.8.0

**An ultra-efficient, self-monitoring, self-archiving workspace for Claude Code** with Enneagram routing, automatic token optimization, real-time cost tracking, adaptive feedback (SAFLA), pattern recognition (Instincts), secret-leak prevention, 5-zoom audit, GitHub-mature skill proposing, and cross-process safety.

> See [`CREDITS.md`](CREDITS.md) for full source attribution.
> See [`MIGRATION.md`](MIGRATION.md) for upgrade from earlier versions.
> Romanian docs: [`README.ro.md`](README.ro.md).

---

## Live metrics (v3.8.0)

| Metric | Value |
|---|---|
| Test suites | **22** |
| Tests | **147 / 147 PASS** · 0 FAIL |
| Audit checks (`/evaluate-setup`) | **38 / 38 PASS** · 0 WARN · 0 FAIL |
| Production helpers (`.claude/helpers/`) | **47 modules** (21 in `lib/` + 26 top-level) |
| Total lines of code | **~7500** |
| Slash commands | **19** |
| Hook events wired | **13** |
| Skills (`.claude/skills/`) | 33 |
| Architectural decisions documented | **10** (in `_MEMORY/decisions/`) |
| External runtime dependencies | **1** (`codeburn`, optional — native fallback if absent) |

---

## Why CCDEW exists

Claude Code consumes tokens at every interaction. Without optimization:
- At every SessionStart the entire memory is injected (130+ files), even if 90% is irrelevant.
- At every prompt context grows incrementally — Claude "forgets" what worked.
- No cost visibility — you don't know which tasks cost the most or where the waste is.
- No intelligent routing — Claude treats `"fix bug"` and `"redesign architecture"` the same way.

CCDEW addresses all of these and adds layers for security, observability, and self-evolution.

---

## Core mechanisms (live, measured)

### 1. SSA — Sparse/Selective Attention (−76% injected tokens)
At every prompt, instead of injecting all memory, SSA computes Jaccard trigram similarity between the prompt and each memory entry. Result: from 50 entries, only 12 are injected — the most relevant ones. The Obsidian index is included automatically.

### 2. Enneagram Routing — right agent for the right task
The system classifies each prompt into one of 9 task types and selects the specialized agent. A bug fix goes to `tester` (Node 6), not `sparc-orchestrator` (Node 8). Right agent → shorter response → fewer tokens.

```
Simple task  → TRIANGLE (3 agents): coder → tester → memory-specialist
Complex task → HEXAD (6 agents):    reviewer → researcher → backend-dev → sparc-orchestrator → analyst → architecture
```

### 3. CodeBurn — full cost visibility
Reads from `~/.claude/projects/` (via the `codeburn` CLI when present, native parser as fallback) and displays in the status line:

```
💰 $239.25 today / $100/d  ⚠   1185 calls   |   🤖 67% ok·63fb   |   📂 CCDEW
```

Auto-warning at 75% of `daily_budget_usd`, alert at 100%.

### 4. SAFLA — Self-Adaptive Feedback Loop
Tracks which Enneagram node worked or failed. **+0.05** per success, **−0.10** per failure (asymmetric — penalize more), clamped to [-0.5, +0.5]. State at `.claude-flow/data/safla.json`. Cross-process safe: every write is wrapped in a file-lock so two parallel Claude sessions cannot corrupt the data.

### 5. Red Hat Evaluator — prevents over-engineering
Before any architecture task, `red-hat-evaluator.cjs` injects 2-3 critical questions:
- *"What tacit assumptions does this solution contain?"*
- *"Is there a simpler approach with ≤ 50% of the complexity?"*

### 6. Instincts — learns from your usage
`lib/instincts.cjs` records `(prompt biometric, routed node, success)` tuples. After ≥3 occurrences with success rate ≥ 50%, suggests automatically: `[INSTINCT] you usually route this to node N (X% confidence over M similar prompts)`.

### 7. Secret-scan — pre-edit hard-block
`lib/secret-scan.cjs` detects 11 secret patterns (AWS, Anthropic, OpenAI, GitHub, Stripe, RSA, Slack, Bearer, JWT, etc.) plus 8 sensitive paths (`.env`, `id_rsa`, `*.pfx`, etc.). Wired into the `pre-edit` hook — **blocks the edit** if a leak is detected.

### 8. Skills auto-activation
`lib/skills-activator.cjs` scans `.claude/skills/<name>/SKILL.md` frontmatter and matches triggers / description against the current prompt. Suggests up to 3 most relevant skills per prompt; tracks usage in `.claude-flow/data/skill-usage.jsonl` for `deadSkills()` detection.

### 9. 5-zoom audit (Maha → Nano)
`/infer` runs at 5 levels of detail:

| Zoom | Scope | Example findings |
|---|---|---|
| **MAHA** | Whole-system | LOC > soft cap, tests < minimum, audit history empty |
| **MACRO** | Cross-module | files > 500 lines (HIGH), > 300 (WARN), excessive coupling |
| **MEZZO** | Per-module | modules with > 12 exports |
| **MICRO** | Per-function | functions > 75 lines or > 5 args |
| **NANO** | Per-line/char | trailing whitespace, mixed tabs+spaces, real TODO/FIXME |

`/optimize nano` applies safe NANO transforms automatically (with backup); higher zooms return proposals only.

### 10. Skills-propose — search GitHub maturi, scaffold without code copy
`/skills-propose <keyword>` queries GitHub Search API with 4 query variants, filters strictly (≥10 stars, allowed licenses MIT/Apache/ISC/BSD/MPL, push within 365 days, !archived, !disabled, license-known by default). Returns top mature candidates. With `--scaffold <local-name>`, generates `.claude/skills/<local-name>/SKILL.md` with frontmatter (`inspired_by`, `inspired_url`, `inspired_stars`, `inspired_license`, `triggers`) — **no code copied**, just metadata + license attribution.

### 11. Cross-process safety (`lib/file-lock.cjs`)
Every SAFLA write is wrapped in an O_EXCL file-lock. Tested live with 2 parallel `fork()` processes writing 100 outcomes each — **200/200 survive, no orphans, no corrupt keys**. Stale lock auto-cleanup at >30s.

### 12. Performance baseline + regression detection
`lib/perf-baseline.cjs` records rolling 30-sample p95 for hot paths (e.g. `ssa.filterContext`, `safla.recordOutcome`). At SessionEnd, auto-runs benchmarks; if current run > baseline p95 × 1.5 → `[PERF] 🚨 regression`.

### 13. Auto-archiving sessions
At every `/exit` or SessionEnd, `lib/session-snapshot.cjs` writes a snapshot in **two formats**:
- `.claude-flow/sessions/session-<localISO>-<pid>.json` — machine-readable (cost, SAFLA, instincts, skills, perf, audit, errors, workspace)
- `_MEMORY/sessions/session-<localISO>-<pid>.md` — Obsidian Markdown with frontmatter and tagged sections (auto-tagged `audit-fail`, `errors-high` when applicable)

`/sessions-compare 5` returns a diff table across the last N snapshots.

### 14. PII redaction in logs
All `error-log.cjs` writes pass through `lib/redact.cjs`: emails, phones, JWT, AWS/Anthropic/OpenAI keys, hex >40 chars, home paths → `~`. Logs are safe to share for support.

### 15. Multi-platform detection
`lib/platform-detect.cjs` detects Claude Code / Cursor / Codex / Gemini / OpenCode and reports capabilities (hooks, slashCommands, mcpServers, subAgents). `/platform` warns when a feature isn't supported by the current host.

---

## Quick start

### Requirements
- Node.js ≥ 18
- Python 3.x (optional — used by Obsidian helpers)
- Claude Code CLI

### Install
```bash
git clone <CCDEW-repo> CCDEW
cd CCDEW

# Optional but recommended (canonical cost data):
npm install -g codeburn

# Optional reproducibility:
npm install --package-lock-only
```

### Run
```bash
claude
```

On first prompt, hooks auto-initialize. Verify:
```bash
npm run audit            # /evaluate-setup
node .claude/helpers/hook-handler.cjs flags
```

---

## Workspace structure

```
CCDEW/
├── .claude/
│   ├── settings.json          ← 13 active hook events
│   ├── helpers/
│   │   ├── lib/               ← 21 reusable libraries (atomic-write, platform, flags, validate, ...)
│   │   ├── tests/             ← 22 regression test suites
│   │   ├── hook-handler.cjs   ← lazy-require dispatcher (19 commands)
│   │   ├── ssa.cjs            ← context filtering
│   │   ├── safla.cjs          ← adaptive feedback (cross-process locked)
│   │   ├── codeburn.cjs       ← real cost tracking + native fallback
│   │   ├── intelligence.cjs   ← memory graph + PageRank
│   │   ├── graphify.cjs       ← session reports
│   │   ├── secret-scan.cjs    ← 11 patterns + 8 sensitive paths
│   │   ├── skills-activator.cjs
│   │   ├── instincts.cjs
│   │   ├── platform-detect.cjs
│   │   ├── statusline.cjs
│   │   ├── verify.cjs / review.cjs / quality-gate.cjs / diff-explain.cjs
│   │   ├── evaluate-setup.cjs
│   │   ├── enneagram_router.py / enneagram_compose.py
│   │   ├── obs.py / obsidian-session-context.py
│   │   ├── auto_learn.py / auto_learn_consolidate.py / auto_learn_rotate.py
│   │   └── (more...)
│   └── commands/              ← 10 slash command definitions
├── _MEMORY/                   ← Obsidian vault
│   ├── _DASHBOARD.md          ← live evolution table
│   ├── decisions/             ← 11 architectural decisions documented
│   └── sessions/              ← Obsidian MD per /exit (auto-generated)
├── PROJECTS/                  ← your active projects
├── repositories/              ← Red Hat–style meta-workspace for external repos
├── _BEST_PRACTICES/           ← wisdom, referenced not copied
├── _TEMPLATES/                ← scaffolding for new projects
├── _SETTINGS/                 ← workspace rules + protocols
├── _ARCHIVE/                  ← rollback snapshots + optimize backups
└── package.json
```

---

## CLI commands (npm scripts)

```bash
npm test                      # Run all 22 test suites (147 tests)
npm run audit                 # /evaluate-setup full health-check (38 checks)
npm run audit:fix             # /evaluate-setup with --fix flag
npm run burn                  # Real-time cost tracking
npm run verify                # Quick pre-commit sweep
npm run review                # 3-agent code review brief
npm run quality-gate          # Strict pass/fail (incl. npm audit)
npm run diff-explain          # Plain-English git diff summary
npm run mcp-health            # Verify ~/.claude.json MCP servers
npm run infer                 # 5-zoom audit (Maha → Nano)
npm run optimize -- nano      # Auto-fix NANO drift (apply)
npm run optimize -- nano --dry-run
npm run optimize -- micro     # Proposal-only
npm run optimize -- mezzo|macro|maha
npm run skills-propose -- "keyword"
npm run skills-propose -- "keyword" --scaffold local-skill-name
npm run exit                  # Save full session snapshot
npm run sessions-compare -- 5
npm run bench                 # Benchmark hot paths + record to perf-baseline
```

---

## Slash commands in Claude Code

```
/evaluate-setup    /verify     /review        /quality-gate   /diff-explain
/research          /cost       /infer         /optimize       /exit
/sessions-compare  /skills-propose            /bench          /mcp-health
/safla-clean       /instincts  /errors        /platform       /skills-active
```

---

## Auto-triggers (no manual call needed)

| Trigger | Action |
|---|---|
| `git commit*` in Bash | Auto-runs `/verify` (block on fail; bypass: `HOOKS_SKIP=1`) |
| `git push*` in Bash | Auto-runs `/quality-gate` (block on fail; bypass: `HOOKS_SKIP=1`) |
| SessionStart | Auto-runs `/evaluate-setup` once per 24h, alerts only on FAIL or > 2 WARN |
| SessionEnd | Auto-saves snapshot (JSON + Obsidian MD) + auto-runs benchmark for `ssa.filterContext` |
| pre-edit | Auto-runs `secret-scan.check()` — blocks edit if leak detected |
| UserPromptSubmit | `inject-workflow` (with SSA, Skills, Instincts hints) + `route` |

---

## Permissions deny list (security baseline)

35+ patterns blocking sensitive reads:
- `**/.env*`, `**/credentials.{json,yml}`, `**/secrets.{json,yml}`
- `**/id_rsa`, `**/id_ed25519`, `**/*.pem`, `**/*.pfx`, `**/*.key`
- `**/.aws/credentials`, `**/.ssh/id_*`, `**/.kube/config`, `**/.netrc`
- `**/.gnupg/`, `**/.docker/config.json`, `**/.npmrc`, `**/.pypirc`
- `/etc/passwd`, `/etc/shadow`, `/etc/sudoers`, `/etc/ssh/`, `/proc/`
- `C:\Windows\System32\config\`, `C:\Windows\System32\drivers\`

Plus dangerous Bash blocks (`rm -rf /*`, `format c:`, fork bomb, `dd if=* of=/dev/sd*`, `mkfs.*`).

---

## Performance (overhead per hook, hot path)

| Hook | Median |
|---|---|
| `inject-workflow` | ~100ms |
| `route` | ~100ms |
| `pre-edit` (incl. secret-scan) | ~30ms |
| `session-end` (incl. snapshot + bench) | ~150ms |
| `ssa.filterContext(50)` | 0.31ms p50 |
| `safla.recordOutcome` | 0.85ms p50 (with cross-process lock) |
| `evaluate-setup` full audit | <1s |

Global hook timeout: 5s force-exit (hooks can never hang Claude Code).

---

## Stability guarantees (verified live)

| Aspect | Status |
|---|---|
| Cross-process atomic writes | ✅ 200 outcomes from 2 parallel `fork()` survive (no data loss) |
| 50 concurrent in-process atomic writes | ✅ no orphans, final iter correct |
| 1000 SAFLA outcomes serial | ✅ 0 corrupt keys (`[1-9]` regex enforced) |
| Fuzz inputs to all `lib/` functions | ✅ 30+ malformed inputs rejected consistently |
| Encoding edge cases (BOM, CRLF, RTL, emoji) | ✅ handled correctly |
| Disk full / read-only FS / corrupt JSON | ✅ graceful degradation (8/8 tests) |
| Cross-platform (Linux + macOS + Windows) | ✅ paths via `lib/platform.cjs` |

---

## Documentation map

| File | Purpose |
|---|---|
| [`README.md`](README.md) | This file (English) |
| [`README.ro.md`](README.ro.md) | Romanian translation |
| [`CHANGELOG.md`](CHANGELOG.md) | Version-by-version evolution (v3.0 → v3.8) |
| [`CREDITS.md`](CREDITS.md) | Full attribution: direct deps, ancestry, inspired layers, original work |
| [`MIGRATION.md`](MIGRATION.md) | Upgrade guide v2.0 → v3.x |
| [`_MEMORY/_DASHBOARD.md`](_MEMORY/_DASHBOARD.md) | Live workspace state |
| [`_MEMORY/decisions/INDEX.md`](_MEMORY/decisions/INDEX.md) | 10 architectural decisions documented |
| `.claude/commands/` | Slash command specs |

---

## License

MIT — see [`LICENSE`](LICENSE). All upstream sources (codeburn, ECC, Red Hat setup-evaluator, ruflo) use compatible permissive licenses; CCDEW does not introduce any new restrictions.

---

## Contributing & forking

Fork freely under MIT. If your fork keeps a meaningful chunk of CCDEW, a link back to this repo and the upstreams listed in [`CREDITS.md`](CREDITS.md) is appreciated but not legally required.

If you publish derivative academic / blog work using **SSA / SAFLA / Enneagram-routing / 5-zoom auto-infer** as primary techniques, citing the workspace + the upstream Enneagram methodology authors is the courteous path.
