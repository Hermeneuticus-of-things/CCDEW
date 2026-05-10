---
name: CCDEW Memory Dashboard
description: Live overview of CCDEW evolution, decisions, sessions, and pending items
type: reference
tags: [dashboard, session-start, ccdew, evolution]
project: ccdew
priority: high
_version: 2
_created: 2026-05-10
_modified: 2026-05-10
_modified_by: claude
related: [_INBOX.md, _PROTOCOL.md, _USER_NOTES.md, decisions/INDEX.md, sessions/]
---

# CCDEW Memory Dashboard

> CCDEW Obsidian vault. Indexes the full workspace evolution + architectural decisions + session snapshots. Auto-updated at `/exit` and SessionEnd.

## Current version

**CCDEW v3.8.0** · 22 test suites · **147/147 PASS** · 38/38 audit · 0 FAIL · 0 WARN

## Quick evolution (v3.0 → v3.8)

| v | Date | Test suites | Tests | LOC | lib/ modules | Slash cmd | Trigger / focus |
|---|---|---|---|---|---|---|---|
| 3.0 | 2026-05-10 | 4 | 24 | ~3500 | 4 | 5 | Rebuild from scratch · `claude-code-eficient-workspace` → CCEW |
| 3.0.1 | 2026-05-10 | 5 | 32 | ~3700 | 5 | 5 | Native codeburn engine (CLI-independent fallback) |
| 3.1 | 2026-05-10 | 6 | 35 | ~4200 | 5 | 9 | Blind-spot fixes + state restore + Instincts + auto-fix |
| 3.2 | 2026-05-10 | 11 | 70 | ~5300 | 9 | 9 | TZ + i18n + shell-safe + budget + tools |
| 3.3 | 2026-05-10 | 13 | 86 | ~5800 | 11 | 11 | perf-baseline + PII redact + auto-triggers + RO docs |
| 3.4 | 2026-05-10 | 15 | 98 | ~6400 | 13 | 13 | 5-zoom audit + auto-infer + auto-optimize |
| 3.5 | 2026-05-10 | 17 | 114 | ~6700 | 17 | 13 | Stability 5-zoom + auto-learn + 7 round-4 zones repaired |
| 3.6 | 2026-05-10 | 19 | 133 | ~7200 | 19 | 15 | skills-propose GitHub + /exit snapshot + /sessions-compare |
| 3.7 | 2026-05-10 | 20 | 140 | ~7250 | 19 | 15 | Python detect + skills fallback + NANO false-pos |
| **3.8** | **2026-05-10** | **22** | **147** | **~7500** | **21** | **19** | **file-lock cross-process + bench + race fix** |

## Obsidian indexes

- [Decisions Index](decisions/INDEX.md) — 10 architectural decisions documented
- `sessions/` — Obsidian MD per `/exit` (auto-generated, frontmatter with metrics)
- [Inbox](_INBOX.md) — manual user→Claude drop zone
- [User Notes](_USER_NOTES.md) — user-only space (Claude reads, never writes)
- [Protocol](_PROTOCOL.md) — bidirectional vault rules

## Recent Changes (auto-updated)

- 2026-05-10: v3.8.0 → cross-process file-lock + race fix (200/200 outcomes survive)
- 2026-05-10: v3.7.0 → Python detection real path + skills description fallback
- 2026-05-10: v3.6.0 → skills-propose GitHub + /exit snapshot + /sessions-compare
- 2026-05-10: v3.5.0 → 7/10 round-4 zones repaired + stability 5-zoom
- 2026-05-10: v3.4.0 → 5-zoom audit + auto-infer + auto-optimize at Maha→Nano
- 2026-05-10: v3.3.0 → perf-baseline + PII redact + auto-triggers (git commit→verify)
- 2026-05-10: v3.2.0 → TZ-local fix + RO/EN i18n + shell injection mitigation
- 2026-05-10: v3.1.0 → blind-spot fixes + folder rename CCEW→CCDEW
- 2026-05-10: v3.0.0 → rebuild from scratch + lib/ utilities + lazy-require dispatcher

## Pending Corrections

- [ ] Structural DEBT: `intelligence.cjs` 979L + `hook-handler.cjs` 1024L over hard cap 500 — split deferred (reason: HIGH risk regression, 0 user-visible benefit) — see [decisions/008](decisions/008-debt-structural-split.md)
- [ ] Ruflo MCP not active in current session — requires Claude Code restart so `~/.claude.json::claude-flow.args` with `mcp start` is consumed — see [decisions/003](decisions/003-mcp-claude-flow-fix.md)
- [ ] ONNX onnxruntime-node missing in `D:/Cloude Code/ruflo/` — local vector embeddings disabled — see [decisions/003](decisions/003-mcp-claude-flow-fix.md)
- [ ] 33 skills under `.claude/skills/`, none activated during the development session (skills-activator has description-overlap fallback since v3.7, but the existing skills are agentdb-*, browser, github-* etc. — keywords don't match CCDEW prompts)

## Memory Stats

- **Total memory files**: depends on runs — auto-updated
- **Critical**: 10 decisions in `decisions/`
- **Session snapshots**: see `sessions/` (auto-grows on every `/exit`)
- **Last updated**: 2026-05-10
- **Vault size**: ~30KB (decisions + dashboard + sessions cumulative)
