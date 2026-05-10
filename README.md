# CCDEW — Claude Code Development Efficient Workspace

[![tests](https://img.shields.io/badge/tests-147%2F147%20PASS-brightgreen)]() [![audit](https://img.shields.io/badge/audit-38%2F38%20PASS-brightgreen)]() [![coverage](https://img.shields.io/badge/suites-22-blue)]() [![version](https://img.shields.io/badge/version-3.8.0-blue)]() [![license](https://img.shields.io/badge/license-MIT-green)]()

```
22 test suites · 147/147 PASS · 0 FAIL
38 audit checks · 0 WARN · 0 FAIL
~7500 LOC · 47 helpers (21 lib/ + 26 top-level)
19 slash commands · 13 hook events
1 external runtime dep (codeburn — optional)
```

---

## What it does

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

## Quick start

```bash
git clone https://github.com/Hermeneuticus-of-things/claude-code-eficient-workspace.git CCDEW
cd CCDEW
npm install -g codeburn        # optional, canonical cost data
npm test                       # 147/147 PASS expected
npm run audit                  # 38/38 PASS expected
claude                         # start using
```

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

## Performance overhead

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

## License

MIT — see [LICENSE](LICENSE).

CCDEW builds on permissive upstreams (codeburn MIT, ECC, Red Hat setup-evaluator, ruflo). Full attribution in [CREDITS.md](CREDITS.md).
