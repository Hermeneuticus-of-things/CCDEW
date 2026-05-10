---
name: CCDEW Decisions Index
description: Catalog cronologic + tematic al deciziilor arhitecturale CCDEW v3.x
type: index
tags: [decisions, architecture, ccdew, history]
project: ccdew
priority: critical
_version: 1
_created: 2026-05-10
_modified: 2026-05-10
---

# Decisions Index

10 decizii arhitecturale documentate. Fiecare are: context, opțiuni considerate, decizia luată, motiv, consecințe.

## Cronologic (v3.0 → v3.8)

| # | Decizie | Versiune | Severitate |
|---|---|---|---|
| 001 | [Rebuild from scratch (vs incremental fixes)](001-rebuild-from-scratch.md) | v3.0 | HIGH |
| 002 | [Native codeburn engine (CLI-independent fallback)](002-native-codeburn-engine.md) | v3.0.1 | MED |
| 003 | [MCP claude-flow `mcp start` arg fix](003-mcp-claude-flow-fix.md) | v3.1 | HIGH |
| 004 | [Folder rename CCEW → CCDEW](004-rename-ccew-ccdew.md) | v3.1 | LOW |
| 005 | [Shell injection mitigation cu lib/path-safe](005-shell-injection-mitigation.md) | v3.2 | HIGH |
| 006 | [PII redaction obligatorie în logs](006-pii-redaction-mandatory.md) | v3.3 | MED |
| 007 | [5-zoom audit (Maha→Nano) ca canon CCDEW](007-5-zoom-canon.md) | v3.4 | MED |
| 008 | [DEBT structural: NU split intelligence + hook-handler](008-debt-structural-split.md) | v3.5 | HIGH |
| 009 | [Skills-propose: search GitHub maturi, NU import cod](009-skills-propose-no-code-copy.md) | v3.6 | HIGH |
| 010 | [Cross-process lock pentru SAFLA (race fix)](010-cross-process-lock.md) | v3.8 | HIGH |

## Per categorie

### Securitate
- 005 — shell injection
- 006 — PII redaction

### Arhitectură
- 001 — rebuild strategy
- 008 — debt structural

### Concurență & stabilitate
- 010 — cross-process lock

### Multi-platform & portabilitate
- 002 — codeburn fallback
- 003 — MCP wiring
- 004 — folder name

### Audit & observabilitate
- 007 — 5-zoom canon

### Ecosystem & integrare
- 009 — skills-propose

## Reguli de update

1. Fiecare decizie nouă majoră primește un fișier `<NNN>-<slug>.md`
2. INDEX.md se actualizează manual sau prin `node hook-handler.cjs decisions-add`
3. Frontmatter must include: `name`, `description`, `severity`, `version`, `tags`, `outcome`
4. NU șterge decisions existente — dacă o reverso-i, scrie nouă (`<NNN>-revert-of-<MMM>.md`)
