---
name: Obsidian Interactive Memory — Protocol v1
description: Rules for the bidirectional memory system Claude <-> Obsidian
type: reference
tags: [protocol, session-start, memory]
project: workspace
priority: critical
_version: 1
_created: <!-- fill in date -->
_modified: <!-- fill in date -->
_modified_by: claude
related: []
---

# Obsidian Interactive Memory v1 — Protocol

## Memory file structure

```yaml
---
name: short title
description: one line — used for search
type: feedback | user | project | reference
tags: [tag1, tag2]
project: workspace | MyProject | AnotherProject
priority: critical | high | medium | low
_version: N          <- incremented by Claude at each write
_created: YYYY-MM-DD
_modified: YYYY-MM-DD
_modified_by: claude | user
related: [file1.md, file2.md]
---

## [Claude]
Content written and managed exclusively by Claude.

---
## [User]
<!-- Write any correction or additional context. Claude picks it up at session start. -->
```

---

## Writing rules

| Who | Writes in | Does NOT write in |
|---|---|---|
| Claude | `## [Claude]` + frontmatter | `## [User]` |
| You (Obsidian) | `## [User]` + `_INBOX.md` | `## [Claude]` directly |

**Exception:** You can edit `## [Claude]` if you mark the change with `[USER CORRECTION]:` — Claude picks it up and integrates it.

---

## Session start flow (Claude)

```
1. Read _INBOX.md → ## [Pending]
   → process each item → create/update memory file
   → move item to ## [Processed]

2. Scan ## [User] in all recently modified files
   → if non-placeholder content exists → process
   → update ## [Claude] accordingly
   → increment _version + _modified

3. Load MEMORY.md index into context
```

---

## New memory write flow (Claude)

```
1. Check if similar file exists (obs.py search)
2. If yes → update ## [Claude] + _version++
3. If no → create new file with both sections
4. Update MEMORY.md → ## [Claude Index]
```

---

## _INBOX.md — quick drop zone

Write in `## [Pending]` anything you want Claude to remember:
- corrections to existing rules
- new memory you want added
- project notes
- new references

Free format — Claude understands the context and creates the correct file.

---

## Conflict protocol

- **No conflict** if each writes in their own section
- **If both write `## [Claude]`**: higher `_version` wins; older version moves to `## [User]` as `[BACKUP vN]:`
- **If you delete something from `## [Claude]`**: Claude reconstructs it at session start from context — if you want to permanently remove it, write in `## [User]`: `[DELETE]: reason`

---

## Obsidian tag conventions

```
#session-start    -> read mandatory at boot
#critical         -> critical rule
#feedback         -> Claude behavior
#project-X        -> specific to a project
#pending          -> requires action
```
