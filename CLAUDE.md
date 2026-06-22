# Claude Workspace — Root
## Updated: 2026-05-12

> **Parent:** N/A (workspace root)
> **Cross-project rules:** [`_SETTINGS/RULES/INDEX.md`](_SETTINGS/RULES/INDEX.md)
> **Quick start config:** [`_SETTINGS/QUICK-START-CONFIG.md`](_SETTINGS/QUICK-START-CONFIG.md)
> **Patterns 3-tier (loading on-demand):**
> Root universal → [`BEST_PRACTICES.md`](BEST_PRACTICES.md) **← session start** | Per type → `_BEST_PRACTICES/<type>/BEST_PRACTICES.md` | Project → `PROJECTS/<Name>/BEST_PRACTICES.md`

---

# SESSION START — 3 UNCONDITIONAL RULES

> Details: [`_SETTINGS/RULES/session_start.md`](_SETTINGS/RULES/session_start.md)

**1/3 — CHANGELOG BEFORE CODE.** For ANY request → new entry in project `CHANGELOG.md` BEFORE the first line of code (request header + decisions + targeted files).

**2/3 — PERSISTENT TODO (anti-crash).** BEFORE work → `PROJECTS/<Project>/TODO.md`. Format `## Session [date]` → `### Request:` → `- [ ] / [~] / [x]`. Update checkboxes as you go.

**3/3 — EPILOG AT COMPLETION.** At every completed request → update IMMEDIATELY `CHANGELOG.md` (result + files + decisions + version) + `TODO.md` (`[x]` + summary).

**Applicability:** ALL projects, even 1-line fixes.

---

## Parallel agents — default behavior (portable across machines)

**Default rule:** whenever a task has 2+ independent sub-tasks, spawn ruflo agents in parallel. Single sequential work is the exception, not the norm. Goal: maximum quality + speed + credit economy on every machine that clones this repo.

**Spawn in parallel when:**
- multi-file audit, code review, refactor across ≥3 files
- documentation pass that touches independent sections
- test generation while implementation continues
- research while another agent edits
- any "check if I missed something" / gap-audit / quality sweep
- any prompt where the AUTO-SWARM DIRECTIVE hint shows HEXAD or TRIANGLE

**Sequential is correct when:**
- single small edit (1–2 lines)
- linear text editing of one document
- strict serial dependency (B reads A's output)
- explicit "one change at a time" from the user

**Swarm preset (when keyword swarm/mesh/holographic appears or refactor ≥5 files):** apply AUTO `hierarchical-mesh, maxAgents=1000 symbolic, strategy=specialized, exclusive scope per agent`.

Details: [`_SETTINGS/RULES/swarm_preset.md`](_SETTINGS/RULES/swarm_preset.md)

## Obsidian context

Rule: **`python .claude/helpers/obs.py search` BEFORE direct `Read`.** Vault = `<WORKSPACE_DIR>` + `_MEMORY/` (memory files with frontmatter tags). `obs.py` = PRIMARY (CLI stdlib + PyYAML, clean process per call, zero-MCP).
Details: [`_SETTINGS/RULES/obsidian_context_protocol.md`](_SETTINGS/RULES/obsidian_context_protocol.md)

## Long-term memory

`<WORKSPACE_DIR>` = active memory. When you don't know something:
- **Past decisions** → `CHANGELOG.md` project | **Pending tasks** → `TODO.md` project
- **Cross-project rules** → `_SETTINGS/RULES/INDEX.md` | **Project rules** → `PROJECTS/<Name>/CLAUDE.md`

## BEST_PRACTICES loading policy

**Boot:** ONLY `BEST_PRACTICES.md` root + `MEMORY.md`. **Escalation on-demand:**
1. Task on type → read `_BEST_PRACTICES/<type>/BEST_PRACTICES.md` slim + `PROJECTS/<N>/CLAUDE.md`
2. Specific pattern → `_BEST_PRACTICES/<type>/details.md` (section `## AND-/KRT-/GEN-NNN`)
3. Verbose mode ONLY for architecture review or explicit request.

---

## Workspace map

| Task | File |
|---|---|
| Cross-project rules | `_SETTINGS/RULES/INDEX.md` |
| Universal patterns | `BEST_PRACTICES.md` (session start) |
| Per-type patterns | `_BEST_PRACTICES/<type>/BEST_PRACTICES.md` (on-demand) |
| Quick start config (naming/workflow) | `_SETTINGS/QUICK-START-CONFIG.md` |
| Standard technical requirements | `_SETTINGS/CERINTE_TEHNICE_STANDARD.md` |
| CHANGELOG format guide | `_SETTINGS/CHANGELOG-FORMAT.md` |
| Root CHANGELOG/TODO (META) | `CHANGELOG.md` / `TODO.md` |
| CCDEW v6.1 SLIM | Enneagram, SSA Layer, SAFLA, CodeBurn, Ruflo, SOP Engine, Auto-Profile |
| Enneagram Topology | [`_MEMORY/enneagram_topology.md`](_MEMORY/enneagram_topology.md) | 9 types, arc weights, SSA scoring, SAFLA feedback |

## Active projects

<!-- Add your projects here -->

| Project | Type | Status |
|---|---|---|
| Consiliu | distributed AI | active |

Add project details → `PROJECTS/<Name>/CLAUDE.md` + `BEST_PRACTICES.md` + `doc/INDEX.md`.

## Templates and structure

`_TEMPLATES/<type>/` (scaffolding **copied** for new project: android/carte/generic/research/preview-live-server) vs `_BEST_PRACTICES/<type>/` (wisdom **referenced**, not copied).

```
<WORKSPACE_DIR>/
  CLAUDE.md  BEST_PRACTICES.md  CHANGELOG.md  TODO.md     <- root meta
  PROJECTS/                                               <- active projects
  _BEST_PRACTICES/<type>/    <- BP slim + details + growth_log + skills (on-demand)
  _TEMPLATES/<type>/         <- scaffolding (do not modify directly)
  _SETTINGS/                 <- QUICK-START + RULES/ + CHANGELOG-FORMAT + CERINTE
  _MEMORY/                   <- Obsidian memory vault (bidirectional Claude <-> User)
  memory/                    <- Claude Code auto-memory (MEMORY.md index)
```

---

## Operational rules

**Auto-create project:** determine type → copy `_TEMPLATES/<type>/` into `PROJECTS/<Name>/` → fill `CLAUDE.md` + `doc/` + `BEST_PRACTICES.md`.

**Do not modify without confirmation:** propose first, execute after.

**Preview servers:** copy `_TEMPLATES/preview-live-server/serve_md.py` into project; `.claude/launch.json` in workspace; DO NOT start servers from another project.

**Scope routing:** task on project → work in `PROJECTS/<N>/`; meta task → root or `_SETTINGS/`/`_BEST_PRACTICES/`/`_TEMPLATES/`. "Remember for the future" → write in physical `.md` files (if not on disk, it's lost).

## Anthropic → OpenRouter proxy (automatic credit fallback)

When Anthropic runs out of credits, the local proxy takes over automatically with free OpenRouter models:

```bash
# Terminal 1 — start proxy (runs in background)
python3 PROJECTS/Consiliu/anthropic_proxy.py &

# Terminal 2 — tell Claude Code to use the proxy
export ANTHROPIC_BASE_URL=http://localhost:8082
claude  # starts Claude Code normally, but with automatic fallback
```

The proxy listens on `:8082`. When Anthropic returns 402 (credit exhausted) → automatic OpenRouter waterfall. Claude Code doesn't know the difference — it receives an identical Anthropic-format response.
Log: `/tmp/anthropic_proxy.log` | Status: `curl http://localhost:8082/health`

---

## OpenRouter CLI (Think local)

Automatic fallback: **Anthropic → OpenRouter** (when Anthropic is unavailable):

```bash
# Recommended: try Anthropic first, automatic fallback to OpenRouter
python3 PROJECTS/Consiliu/think_ai.py "any question"
python3 PROJECTS/Consiliu/think_ai.py --verbose "code: ..."   # shows which backend is used
python3 PROJECTS/Consiliu/think_ai.py --force-or "skip directly to OpenRouter"

# OpenRouter only (no Anthropic)
python3 PROJECTS/Consiliu/think_openrouter.py "calc: ..."
python3 PROJECTS/Consiliu/think_openrouter.py --list          # available models
```

Logic: Anthropic (claude-haiku) → if it fails (429/down/no key) → OpenRouter waterfall:
`qwen3-coder:free` → `glm-4.5-air:free` → `gpt-oss-120b:free` → `nemotron-120b:free` → `llama-3.3-70b:free` → `hermes-405b:free` → `gemma-4-31b:free` → `qwen3-80b:free` → `gpt-4o-mini`.
Keys: `ANTHROPIC_API_KEY` env var (optional) + `OPENROUTER_KEY` hardcoded in script.

---

## What Claude does NOT do at workspace root

- Does not create files at root (only in `PROJECTS/` or `_TEMPLATES/`)
- Does not modify `_TEMPLATES/` without confirmation (only copies)
- Does not delete from `_ARCHIVE/` without explicit confirmation
- Does not modify content without confirmation — proposes first
