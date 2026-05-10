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
Numele inițial `claude-code-eficient-workspace` (typo "eficient" în loc de "efficient") era lung, conținea typo. Userul a propus inițial `CCEW` (Claude Code Efficient Workspace), apoi `CCDEW` (Claude Code Development Efficient Workspace).

## Decizie
Final: **CCDEW**. Acoperă scope-ul de "development workspace" mai precis decât CCEW (care suna ca tool generic).

## Consecințe
- Folder rename: `claude-code-eficient-workspace/` → `CCEW/` → `CCDEW/`
- 4 referințe interne actualizate: README.md, MIGRATION.md, CHANGELOG.md, statusline.cjs
- Path-uri Windows-only au fost preservate; relative paths nu au necesitat modificări
- npm package name: `ccdew`

## Referințe externe NEMODIFICATE (intentional)
- Root `D:/Cloude Code/CHANGELOG.md` păstrează numele istoric `claude-code-eficient-workspace` în mențiunile de commit SHA-uri (sunt menționări istorice, nu path local)
- GitHub repo upstream rămâne `Hermeneuticus-of-things/claude-code-eficient-workspace` (nu am control)
