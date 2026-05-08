# Obsidian Context Protocol
## Updated: see template version

> **Purpose:** Replaces manual reads with structured vault searches. **Connections live in Obsidian, not in prompt — token savings.**
> **Workspace vault:** `<WORKSPACE_DIR>` (general memory + `_MEMORY/` junction)
> **Project vaults:** `PROJECTS/<Name>/` with own `.obsidian/` + `_WORKSPACE` junction back
> **Registry:** `_SETTINGS/vaults.json`
> **Savings:** ~75-80% token context reduction per complex session

---

## Why `obs.py` and not MCP

The Obsidian MCP server can be unreliable on Windows + Node 22 + npx.
Stable solution: **local Python CLI** at `.claude/helpers/obs.py` — clean process per call,
zero handshake, zero network dependencies.

| Operation | Before (MCP, unstable) | Now (CLI, stable) |
|---|---|---|
| Search content + frontmatter | `obsidian_global_search` | `python .claude/helpers/obs.py search "..."` |
| List notes | `obsidian_list_notes` | `obs.py list [--tag X] [--folder Y] [--recent N]` |
| Read with frontmatter | `obsidian_read_note` | `obs.py read <path>` |
| Manage frontmatter | `obsidian_manage_frontmatter` | `obs.py fm <path> get\|set\|del <key> [val]` |
| Manage tags | `obsidian_manage_tags` | `obs.py tags <path> add\|del\|list <tag>` |
| Search-replace | `obsidian_search_replace` | `obs.py replace <path> <old> <new>` |
| Backlinks | (not in MCP) | `obs.py backlinks <note>` |
| Outgoing links | (not in MCP) | `obs.py links <path>` |

**Note:** The MCP remains passively available; if it fails, `obs.py` continues undisturbed.

---

## Base rule

**First action = `obs.py search`, not direct `Read`.**

`Read` remains fallback — only after search finds nothing, or when we know the exact path.

## Multi-vault routing

| Search in... | Flag |
|---|---|
| General workspace (default) | `obs.py search "..."` |
| A specific project | `obs.py --project MyProject search "..."` |
| All (workspace + all projects) | `obs.py --all search "..."` |
| Explicit path | `obs.py --vault "/path/to/vault" search "..."` |

`obs.py vaults list` shows the registry. `obs.py vaults status` shows config_version + features per project.

---

## Protocol per situation

### Session start
```bash
python .claude/helpers/obs.py search "session-start" --tag feedback --max-files 10
```
Replaces blind reading of `MEMORY.md` index.

### Task on specific project
```bash
python .claude/helpers/obs.py list --tag myproject --recent 15
python .claude/helpers/obs.py search "my feature" --in PROJECTS/MyProject
```

### Search past decision/rule
```bash
python .claude/helpers/obs.py search "swarm preset" -i
```

### Memory lookup (cross-session)
```bash
python .claude/helpers/obs.py list --folder _MEMORY --tag workflow
python .claude/helpers/obs.py read _MEMORY/feedback_xxx.md
```

---

## Frontmatter schema in memory files

All files in `_MEMORY/` should have:

```yaml
---
name: ...
description: ...
type: feedback | reference | project | user
tags: [session-start, code, workflow, swarm, ...]
project: MyProject | workspace
priority: critical | high | medium
---
```

### Main tags
| Tag | When used |
|---|---|
| `session-start` | CRITICAL rules applied at any session |
| `code` | Code-related memories |
| `workflow` | Workflow patterns |
| `swarm` | Parallel agent rules, mesh preset |
| `feedback` | Behavior corrections |
| `reference` | Technical reference information |

### Priority: critical
Files with `priority: critical` must be found at ANY session, regardless of project.

```bash
python .claude/helpers/obs.py search "priority: critical" --in _MEMORY
```

---

## Vault structure (summary)

```
<WORKSPACE_DIR>/
  _MEMORY/          <- memory files with frontmatter (junction optional)
  PROJECTS/         <- active projects (CLAUDE.md, CHANGELOG, TODO per project)
  _BEST_PRACTICES/  <- android/, carte/, generic/ (on-demand)
  _SETTINGS/RULES/  <- workflow rules (this rule is here)
  BEST_PRACTICES.md <- tier 1 universal
  CLAUDE.md         <- workspace root rules
  .claude/helpers/obs.py  <- vault CLI (zero-MCP)
```

---

## Quick reference (cheat-sheet)

```bash
# Full help
python .claude/helpers/obs.py --help
python .claude/helpers/obs.py <cmd> --help

# Setup multi-vault
obs.py setup --auto          # configure/upgrade all projects
obs.py vaults list           # show registry
obs.py vaults status         # config_version + features per project
obs.py audit                 # token cost auto-loaded + redundancies

# Searches (with vault routing)
obs.py search "query" [--tag TAG] [--in folder/] [-i] [--max-files N]
obs.py --project MyProject search "..."
obs.py --all search "..."    # all vaults
obs.py list [--tag TAG] [--folder PATH] [--recent N] [--json]

# Reading
obs.py read <path>           # frontmatter + body
obs.py read <path> --fm-only    # frontmatter only (JSON)
obs.py read <path> --body-only  # body markdown only

# Mutations
obs.py fm <path> get [key]   # display frontmatter (or one key)
obs.py fm <path> set <key> <value>
obs.py fm <path> del <key>
obs.py tags <path> add|del|list [tag]
obs.py replace <path> <old> <new> [--regex] [-i] [--dry-run]

# Links (Obsidian graph view uses these)
obs.py backlinks <note>      # who links to note (multi-vault)
obs.py links <path>          # what note links to
obs.py link <a> <b>          # bidirectional wikilink between 2 notes
```
