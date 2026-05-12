---
name: CCDEW Memory Dashboard
description: Live overview of CCDEW evolution, decisions, sessions, and pending items
type: reference
tags: [dashboard, session-start, ccdew, evolution]
project: ccdew
priority: high
_version: 3
_created: 2026-05-10
_modified: 2026-05-12
_modified_by: claude
related: [_INBOX.md, _PROTOCOL.md, _USER_NOTES.md, decisions/INDEX.md, sessions/]
---

# CCDEW Memory Dashboard

> CCDEW Obsidian vault. Indexes the full workspace evolution + architectural decisions + session snapshots. Auto-updated at `/exit` and SessionEnd.

## Current version

**CCDEW v3.9.2** · 22 test suites · **37/37 PASS** · enneagram_topology.md + Template Sync Audit

## Quick evolution (v3.0 → v3.9.1)

| v | Date | Tests | LOC | Modules | Features |
|---|---|---|---|---|---|
| 3.0 | 2026-05-10 | 24 | ~3500 | 4 | Rebuild from scratch |
| 3.1 | 2026-05-10 | 35 | ~4200 | 5 | Instincts + auto-fix |
| 3.2 | 2026-05-10 | 70 | ~5300 | 9 | TZ + i18n + shell-safe |
| 3.3 | 2026-05-10 | 86 | ~5800 | 11 | perf-baseline + PII redact |
| 3.4 | 2026-05-10 | 98 | ~6400 | 13 | 5-zoom audit + auto-infer |
| 3.5 | 2026-05-10 | 114 | ~6700 | 17 | auto-learn + stability |
| 3.6 | 2026-05-10 | 133 | ~7200 | 19 | skills-propose + snapshots |
| 3.7 | 2026-05-10 | 140 | ~7250 | 19 | Python detect + NANO fix |
| 3.8 | 2026-05-10 | 147 | ~7500 | 21 | file-lock + race fix |
| **3.9** | **2026-05-12** | **147** | **~8000** | **23** | **v6.1 SLIM: SSA 5D + Ruflo + Profiles** |
| **3.9.2** | **2026-05-12** | **147** | **~8200** | **25** | **enneagram_topology.md + Template Sync Audit** |
| **3.9.1** | **2026-05-12** | **147** | **~8100** | **24** | **SOP Engine + Auto-Profile + MetaGPT** |

## v6.1 SLIM Components

| Component | Status | Description |
|---|---|---|
| Enneagram | ✅ | 9-node routing + workflow selection |
| SSA Layer | ✅ | 5-dimensional scoring (semantic, enneagram, holographic, recency, pinned) |
| SAFLA | ✅ | Self-Adaptive Feedback Loop (30 sessions, 23 feedbacks) |
| CodeBurn | ✅ | $764/lună, 9759 apeluri |
| Ruflo | ✅ | MCP tools: swarmInit, agentSpawn, memoryStore, federation |
| SOP Engine | ✅ | 5 SOPs: refactor, audit, multi-file-refactor, research, security-audit |
| Auto-Profile | ✅ | Budget-based auto-switch (lite/full/ssa-max) |
| Red Hat Evaluator | ✅ | 37/37 PASS |

## Obsidian indexes

- [Decisions Index](decisions/INDEX.md) — architectural decisions
- `sessions/` — Obsidian MD per `/exit` (auto-generated)
- [Inbox](_INBOX.md) — manual user→Claude drop zone
- [User Notes](_USER_NOTES.md) — user-only space
- [Protocol](_PROTOCOL.md) — bidirectional vault rules

## Recent Changes (auto-updated)

- 2026-05-12: v3.9.1 → SOP Engine (MetaGPT-style) + Auto-Profile + profile command
- 2026-05-12: v3.9.0 → v6.1 SLIM complete: SSA 5D + Ruflo + Profiles
- 2026-05-10: v3.8.0 → cross-process file-lock + race fix
- 2026-05-10: v3.7.0 → Python detection real path + skills fallback
- 2026-05-10: v3.6.0 → skills-propose GitHub + /exit snapshot + /sessions-compare
- 2026-05-10: v3.5.0 → 7/10 round-4 zones repaired + stability 5-zoom
- 2026-05-10: v3.4.0 → 5-zoom audit + auto-infer + auto-optimize
- 2026-05-10: v3.3.0 → perf-baseline + PII redact + auto-triggers

## Memory Stats

- **Total memory files**: auto-updated
- **Critical**: decisions in `decisions/`
- **Session snapshots**: see `sessions/` (auto-grows on every `/exit`)
- **Last updated**: 2026-05-12
- **Vault size**: ~35KB (decisions + dashboard + sessions cumulative)