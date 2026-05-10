---
name: Folder rename CCEW → CCDEW
severity: LOW
version: v3.1
date: 2026-05-10
status: applied
tags: [naming, branding]
---

# Folder rename CCEW → CCDEW

## Context
The original name `claude-code-eficient-workspace` (typo "eficient" instead of "efficient") was long and contained a typo. The user initially proposed `CCEW` (Claude Code Efficient Workspace), then `CCDEW` (Claude Code Development Efficient Workspace).

## Decision
Final: **CCDEW**. Covers the "development workspace" scope more precisely than CCEW (which sounded like a generic tool).

## Consequences
- Folder rename: `claude-code-eficient-workspace/` → `CCEW/` → `CCDEW/`
- 4 internal references updated: README.md, MIGRATION.md, CHANGELOG.md, statusline.cjs
- Windows-only paths preserved; relative paths required no modification
- npm package name: `ccdew`

## External references NOT modified (intentional)
- Root `<workspace>/CHANGELOG.md` keeps the historical name `claude-code-eficient-workspace` in commit-SHA mentions (these are historical references, not local paths)
- GitHub upstream repo remains `Hermeneuticus-of-things/claude-code-eficient-workspace` (no CCDEW control)
