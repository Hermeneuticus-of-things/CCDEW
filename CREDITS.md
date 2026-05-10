# CREDITS & Attribution

> Comprehensive list of every external source used in CCDEW v3.8.0 — what was taken directly, what was inspired, and what is original. Honest source-by-source.

---

## Direct dependencies (runtime)

### `codeburn` (npm)
- **Author:** AgentSeal (`hello@agentseal.org`)
- **License:** MIT
- **Repo:** https://github.com/getagentseal/codeburn
- **What we use:** Direct CLI invocation via `execFileSync` for live cost tracking. The CLI reads from `~/.claude/projects/**/*.jsonl` and reports per-session token usage and cost.
- **Status:** Required runtime dependency. CCDEW falls back to a built-in native parser (`lib/codeburn-engine.cjs`) if the CLI is absent — but pricing computed by the CLI is canonical; ours is an estimate.
- **Where:** `.claude/helpers/codeburn.cjs` calls the CLI; `package.json` documents installation.

### `notebooklm-mcp`
- **Used as:** Adjacent MCP server alongside `claude-flow` in user's `~/.claude.json`.
- **Status:** Not a CCDEW dependency, but mentioned because `mcp-health` command verifies its config too.

---

## Project ancestry (what CCDEW is forked / based on)

### `claude-code-eficient-workspace` (original v1.x → v2.0 base)
- **Author:** [Hermeneuticus-of-things](https://github.com/Hermeneuticus-of-things/claude-code-eficient-workspace)
- **What was taken DIRECTLY:**
  - Root folder structure (`PROJECTS/`, `_BEST_PRACTICES/`, `_TEMPLATES/`, `_SETTINGS/`, `_MEMORY/`)
  - `_TEMPLATES/<type>/` scaffolding pattern
  - `_BEST_PRACTICES/<type>/` "wisdom referenced not copied" doctrine
  - `_MEMORY/` Obsidian bidirectional memory protocol (`_DASHBOARD.md`, `_INBOX.md`, `_PROTOCOL.md`, `_USER_NOTES.md`)
  - Initial 4 helpers in `.claude/helpers/`: `enneagram_router.py`, `enneagram_compose.py`, `obs.py`, `obsidian-session-context.py` (Python helpers — preserved as-is from upstream)
  - `auto-memory-hook.mjs` (preserved)
  - `auto_learn.py`, `auto_learn_consolidate.py`, `auto_learn_rotate.py` (preserved)
  - `intelligence.cjs` partial — original was upstream, CCDEW patched `writeJSON` to use `lib/atomic-write.cjs`
  - `router.js`, `session.js` (preserved)
- **What CCDEW changed:**
  - Folder rename (`claude-code-eficient-workspace` → `CCEW` → `CCDEW`)
  - All other helpers in `.claude/helpers/` rewritten or new (see "Original to CCDEW" below)

### `ruvnet/ruflo` & `ruvnet/claude-flow`
- **Author:** ruvnet
- **What we use:**
  - MCP server `claude-flow` configured in `~/.claude.json` (stdio, points at `D:/Cloude Code/ruflo/bin/cli.js`)
  - Agent topology patterns and the `swarm_init` concept (referenced in our `inject-workflow` AUTO-SWARM DIRECTIVE output)
  - Multi-agent orchestration ideas (we expose `/swarm-route` that returns `swarm_init_hint` JSON ready for ruflo's MCP `swarm_init` tool)
- **Status:** External MCP, not part of CCDEW directly. CCDEW just emits hints compatible with ruflo's `swarm_init`. `mcp-health` command verifies the config.

---

## Inspired layers (concepts adopted, code re-written for CCDEW)

### `everything-claude-code` (ECC)
- **Author:** Afaan M. ([affaan-m](https://github.com/affaan-m/everything-claude-code))
- **License:** see upstream
- **Concepts adopted (NO code copy):**
  - **Skills auto-activation** — CCDEW's `lib/skills-activator.cjs` scans `.claude/skills/<name>/SKILL.md` frontmatter and matches triggers/description against the prompt. Algorithm and storage are original; the *idea* of declarative skills with auto-suggest is from ECC.
  - **Instincts (pattern recognition)** — CCDEW's `lib/instincts.cjs` records `(prompt fingerprint, node, success)` tuples in JSONL and detects repeated patterns. Original implementation; concept of automatic pattern recognition from usage is from ECC.
  - **Multi-platform support** — CCDEW's `lib/platform-detect.cjs` detects Claude Code / Cursor / Codex / Gemini / OpenCode and reports capabilities. Original; the multi-platform-as-feature stance comes from ECC.
  - **Research-first development** — CCDEW's `.claude/commands/research.md` slash command implements ECC's research-first pattern (context → constraints → prior art → proposal → adversarial → plan).
  - **Multi-language documentation** — CCDEW's `README.md` (English) + `README.ro.md` (Romanian) follow ECC's multi-lingual docs principle.
- **What is NOT taken:** No source code copied from ECC. No skills imported from ECC. No commands copied verbatim.

### `claude-code-setup-evaluator` (Red Hat)
- **Author:** [redhat-community-ai-tools/claude-code-setup-evaluator](https://github.com/redhat-community-ai-tools/claude-code-setup-evaluator)
- **License:** see upstream
- **Concepts adopted:**
  - **`/evaluate-setup`** — CCDEW's command in `.claude/commands/evaluate-setup.md` and backend `lib/evaluate-setup.cjs` implements an audit similar in spirit. 38 checks across config, modules, performance, state, cost, security, cross-platform.
  - **`/verify, /review, /quality-gate, /diff-explain`** — All four commands are CCDEW reimplementations of Red Hat's slash-command toolkit. Backends are original (verify.cjs, review.cjs, quality-gate.cjs, diff-explain.cjs).
  - **Meta-workspace `repositories/`** — CCDEW's `repositories/` folder + README follow the Red Hat pattern of hosting external repos under a single workspace with shared tooling but separate git history.
  - **Pre-edit secret-leak hooks** — CCDEW's `lib/secret-scan.cjs` (11 patterns + 8 sensitive paths) wired into `pre-edit` hook. Original implementation; the concept of a hard-block on secret leaks at edit time is from Red Hat.
- **What is NOT taken:** No code copied. The slash-command names are common engineering vocabulary; the implementations are independent.

### `LangGraph` (LangChain)
- **Author:** [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph)
- **What we use:** Concept of declarative workflow state machines.
- **What we built:** `lib/langgraph-micro.cjs` — pure-CJS state-machine implementation. **Original code; concept-only from LangGraph.** Not a port, not a fork.

### Enneagram methodology
- **Origin:** George Gurdjieff → Oscar Ichazo → Claudio Naranjo (contemporary systematization of personality types and dynamics)
- **What we use:** The 9-node typology and the hexad/triangle dynamics (1→4→2→8→5→7 and 3→6→9) as a **routing topology**, not as a personality framework.
- **CCDEW's adaptation:**
  - 9-node enneagram routing (`enneagram_router.py`, `enneagram_compose.py` — preserved from upstream `claude-code-eficient-workspace`)
  - 5-zoom expansion (Maha → Macro → Mezzo → Micro → Nano) is CCDEW's ORIGINAL canonical doctrine (see `_MEMORY/decisions/007-5-zoom-canon.md`)
- **Status:** Conceptual reference, not technical dependency.

---

## Original to CCDEW (built from scratch, no upstream)

The following modules and concepts are CCDEW's own work in v3.0–v3.8:

### `lib/` utilities (21 modules)

| Module | Lines | Purpose |
|---|---|---|
| `atomic-write.cjs` | ~30 | Cross-platform atomic file write with retry-with-backoff (50/100/200ms) on EPERM/EBUSY |
| `platform.cjs` | ~50 | `findExecutable` + `findPython` with Windows `.cmd/.exe/.bat` filter and Store-alias detection |
| `flags.cjs` | ~25 | feature-flags loader with 5s TTL cache |
| `validate.cjs` | ~20 | `isValidNodeId` (regex `^[1-9]$`), `asString`, `clampNumber` |
| `error-log.cjs` | ~50 | JSONL error log with rotation (5k lines) + auto PII redaction integration |
| `codeburn-engine.cjs` | ~120 | Native `~/.claude/projects/**/*.jsonl` parser when CLI is absent |
| `local-date.cjs` | ~30 | TZ-aware `todayLocal()` / `monthLocal()` (en-CA format) |
| `pricing.cjs` | ~65 | Centralized model pricing (PRICING_VERSION='2026.05'), single source of truth |
| `migrate.cjs` | ~40 | JSON migration framework with version chain + safety limit (32 steps) |
| `i18n.cjs` | ~40 | RO + EN routing keywords with diacritics-stripping (`refactorizează` → `refactorizeaza`) |
| `path-safe.cjs` | ~30 | Shell injection mitigation: rejects `& ; \| $ ( ) ' " ! * ? \r \n` |
| `redact.cjs` | ~45 | PII scrubber: emails, phones, JWT, hex, AWS/Anthropic/OpenAI keys, home paths |
| `perf-baseline.cjs` | ~75 | Rolling 30-sample p95 with regression detection (>50% delta) |
| `jsdoc-validator.cjs` | ~60 | Verifies @param/@returns on module exports |
| `remote-backup.cjs` | ~60 | Git remote check + `_ARCHIVE/` size monitor |
| `strings.cjs` | ~60 | RO+EN UI dict with `{var}` interpolation, env `CCDEW_LANG=ro` switch |
| `auto-learn.cjs` | ~75 | Dynamic threshold learning from audit history (≥5 samples) |
| `file-lock.cjs` | ~55 | Cross-process O_EXCL lock with stale detection (>30s auto-cleanup) |
| `auto-infer.cjs` | ~140 | 5-zoom workspace audit (MAHA, MACRO, MEZZO, MICRO, NANO) |
| `auto-optimize.cjs` | ~95 | Safe NANO transforms + proposal-only for higher zooms |
| `skills-propose.cjs` | ~150 | GitHub Search API + strict mature filter (license, stars, push date) + scaffold generator |
| `session-snapshot.cjs` | ~250 | Full session capture (cost+SAFLA+instincts+skills+perf+audit+errors+workspace) → JSON + Obsidian MD |

### Algorithms designed for CCDEW

- **SSA — Sparse/Selective Attention**: Jaccard trigram similarity, top-K filter, ~76% context reduction at N=50. (`.claude/helpers/ssa.cjs`)
- **SAFLA — Self-Adaptive Feedback Loop**: per-Enneagram-node weight adjustment +0.05/−0.10 with [-0.5, +0.5] clamp. (`.claude/helpers/safla.cjs`)
- **Enneagram Compose**: multi-zoom MAHA/MACRO/MEZZO/MICRO/NANO swarm composer with 5 lenses (stylistic/doctrinal/structural/regression/memory). (`enneagram_compose.py`)
- **Graphify**: ASCII + Markdown session reports. (`graphify.cjs`)
- **Auto-infer + Auto-optimize 5-zoom**: original CCDEW canon. See `_MEMORY/decisions/007-5-zoom-canon.md`.

### Slash commands (originally implemented)

`/evaluate-setup`, `/verify`, `/review`, `/quality-gate`, `/diff-explain`, `/research`, `/cost`, `/infer`, `/optimize`, `/exit`, `/sessions-compare`, `/skills-propose`, `/bench`, `/mcp-health`, `/safla-clean`, `/instincts`, `/errors`, `/platform`, `/skills-active` — all backends in `.claude/helpers/`.

### Hook handlers (wired to Claude Code lifecycle)

`route`, `inject-workflow`, `swarm-route`, `pre-bash` (with auto-verify on `git commit` + auto-quality-gate on `git push`), `pre-edit` (with secret-scan), `post-bash`, `post-edit`, `session-restore`, `session-end` (with auto-snapshot + auto-bench), `compact-save/manual/auto`, `pre-task`, `post-task`, `auto-audit` (24h cadence), `notify`, `status`.

---

## License

CCDEW itself is released under the **MIT License** (see `LICENSE`). This matches the most permissive upstream (codeburn, MIT). When you fork or adopt:

- **For direct dependencies** (codeburn): follow their MIT license; no extra obligations.
- **For inspired-by sources** (ECC, Red Hat setup-evaluator, ruflo): no legal obligation under MIT, but a link back to upstream is courteous.
- **For Enneagram conceptual reference**: cite Gurdjieff/Ichazo/Naranjo if you publish derivative academic / blog work.
- **For LangGraph concept**: cite LangGraph if you publish derivative work using state-machine workflows.

---

## How to credit when reusing CCDEW

If you fork CCDEW or adopt large portions, the following attribution is appreciated:

```
Based on CCDEW (Claude Code Development Efficient Workspace),
which builds on:
- claude-code-eficient-workspace by Hermeneuticus-of-things (root structure, Obsidian protocol)
- everything-claude-code by Afaan M. (skills, instincts, multi-platform concepts)
- claude-code-setup-evaluator by Red Hat Community AI Tools (audit slash commands)
- ruflo/claude-flow by ruvnet (agent orchestration patterns)
- codeburn by AgentSeal (cost tracking CLI)
```

---

## Acknowledgments

- The community around **Anthropic Claude Code** for building the platform CCDEW runs on (hooks, slash commands, MCP, sub-agents).
- All upstream projects above for publishing under permissive licenses that allow adaptation and concept reuse.
- The **enneagram practitioners and authors** whose contemplative work provides the routing topology metaphor.

---

**Honesty statement:** Every module, command, and concept in CCDEW that originates outside of this workspace is documented above. If you spot a missing attribution, please open an issue.
