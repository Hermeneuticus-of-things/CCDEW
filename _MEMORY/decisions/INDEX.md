---
name: CCDEW Decisions Index
description: Chronological + thematic catalog of CCDEW v3.x architectural decisions
type: index
tags: [decisions, architecture, ccdew, history]
project: ccdew
priority: critical
_version: 1
_created: 2026-05-10
_modified: 2026-05-10
---

# Decisions Index

10 architectural decisions documented. Each contains: context, options considered, decision taken, rationale, consequences.

## Chronological (v3.0 → v3.8)

| # | Decision | Version | Severity |
|---|---|---|---|
| 001 | [Rebuild from scratch (vs incremental fixes)](001-rebuild-from-scratch.md) | v3.0 | HIGH |
| 002 | [Native codeburn engine (CLI-independent fallback)](002-native-codeburn-engine.md) | v3.0.1 | MED |
| 003 | [MCP claude-flow `mcp start` arg fix](003-mcp-claude-flow-fix.md) | v3.1 | HIGH |
| 004 | [Folder rename CCEW → CCDEW](004-rename-ccew-ccdew.md) | v3.1 | LOW |
| 005 | [Shell injection mitigation via lib/path-safe](005-shell-injection-mitigation.md) | v3.2 | HIGH |
| 006 | [Mandatory PII redaction in logs](006-pii-redaction-mandatory.md) | v3.3 | MED |
| 007 | [5-zoom audit (Maha→Nano) as CCDEW canon](007-5-zoom-canon.md) | v3.4 | MED |
| 008 | [Structural DEBT: do NOT split intelligence + hook-handler](008-debt-structural-split.md) | v3.5 | HIGH |
| 009 | [Skills-propose: search GitHub mature, NO code import](009-skills-propose-no-code-copy.md) | v3.6 | HIGH |
| 010 | [Cross-process lock for SAFLA (race fix)](010-cross-process-lock.md) | v3.8 | HIGH |

## By category

### Security
- 005 — shell injection
- 006 — PII redaction

### Architecture
- 001 — rebuild strategy
- 008 — structural DEBT

### Concurrency & stability
- 010 — cross-process lock

### Multi-platform & portability
- 002 — codeburn fallback
- 003 — MCP wiring
- 004 — folder name

### Audit & observability
- 007 — 5-zoom canon

### Ecosystem & integration
- 009 — skills-propose

## Update rules

1. Every new major decision gets a file `<NNN>-<slug>.md`
2. INDEX.md is updated manually or via `node hook-handler.cjs decisions-add`
3. Frontmatter must include: `name`, `description`, `severity`, `version`, `tags`, `outcome`
4. Do NOT delete existing decisions — if reverted, write a new one (`<NNN>-revert-of-<MMM>.md`)
