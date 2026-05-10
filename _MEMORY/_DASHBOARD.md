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

> Vault Obsidian al CCDEW. Indexează toată evoluția workspace-ului + deciziile arhitecturale + snapshot-urile sesiunilor. Auto-updated la `/exit` și SessionEnd.

## Versiune curentă

**CCDEW v3.8.0** · 22 test suites · **147/147 PASS** · 38/38 audit · 0 FAIL · 0 WARN

## Evoluție rapidă (v3.0 → v3.8)

| v | Data | Test suites | Tests | LOC | Module lib/ | Slash cmd | Trigger / focus |
|---|---|---|---|---|---|---|---|
| 3.0 | 2026-05-10 | 4 | 24 | ~3500 | 4 | 5 | Rebuild from scratch · `claude-code-eficient-workspace` → CCEW |
| 3.0.1 | 2026-05-10 | 5 | 32 | ~3700 | 5 | 5 | Native codeburn engine (CLI-independent fallback) |
| 3.1 | 2026-05-10 | 6 | 35 | ~4200 | 5 | 9 | Blind-spot fixes + state restore + Instincts + auto-fix |
| 3.2 | 2026-05-10 | 11 | 70 | ~5300 | 9 | 9 | TZ + i18n + shell-safe + budget + tools |
| 3.3 | 2026-05-10 | 13 | 86 | ~5800 | 11 | 11 | perf-baseline + PII redact + auto-triggers + RO docs |
| 3.4 | 2026-05-10 | 15 | 98 | ~6400 | 13 | 13 | 5-zoom audit + auto-infer + auto-optimize |
| 3.5 | 2026-05-10 | 17 | 114 | ~6700 | 17 | 13 | Stability 5-zoom + auto-learn + 7 zone oarbe round 4 |
| 3.6 | 2026-05-10 | 19 | 133 | ~7200 | 19 | 15 | skills-propose GitHub + /exit snapshot + /sessions-compare |
| 3.7 | 2026-05-10 | 20 | 140 | ~7250 | 19 | 15 | Python detect + skills fallback + NANO false-pos |
| **3.8** | **2026-05-10** | **22** | **147** | **~7400** | **21** | **16** | **file-lock cross-process + bench + race fix** |

## Indici Obsidian

- [Decisions Index](decisions/INDEX.md) — 10 decizii arhitecturale documentate
- `sessions/` — Obsidian MD per /exit (auto-generated, frontmatter cu metrici)
- [Inbox](_INBOX.md) — drop-zone manuale user→Claude
- [User Notes](_USER_NOTES.md) — note libere user (Claude doar citește)
- [Protocol](_PROTOCOL.md) — regulile vault-ului bidirecțional

## Recent Changes (auto-updated)

- 2026-05-10: v3.8.0 → cross-process file-lock + race fix (200/200 outcomes survive)
- 2026-05-10: v3.7.0 → Python detection real path + skills description fallback
- 2026-05-10: v3.6.0 → skills-propose GitHub + /exit snapshot + /sessions-compare
- 2026-05-10: v3.5.0 → 7/10 zone oarbe round 4 reparate + stability 5-zoom
- 2026-05-10: v3.4.0 → 5-zoom audit + auto-infer + auto-optimize la Maha→Nano
- 2026-05-10: v3.3.0 → perf-baseline + PII redact + auto-triggers (git commit→verify)
- 2026-05-10: v3.2.0 → TZ-local fix + RO/EN i18n + shell injection mitigation
- 2026-05-10: v3.1.0 → blind-spot fixes + folder rename CCEW→CCDEW
- 2026-05-10: v3.0.0 → rebuild de la zero + lib/ utilities + lazy require dispatcher

## Pending Corrections

- [ ] DEBT structural: `intelligence.cjs` 979L + `hook-handler.cjs` 1024L peste hard cap 500 — split deferred (motiv: HIGH risk regression, 0 user-visible benefit) — vezi [decisions/008](decisions/008-debt-structural-split.md)
- [ ] Ruflo MCP nu activ în sesiunea curentă — necesită repornire Claude Code pentru ca `~/.claude.json::claude-flow.args` cu `mcp start` să fie consume — vezi [decisions/003](decisions/003-mcp-claude-flow-fix.md)
- [ ] ONNX onnxruntime-node lipsește din `D:/Cloude Code/ruflo/` — vector embeddings local disabled — vezi [decisions/003](decisions/003-mcp-claude-flow-fix.md)
- [ ] 33 skills under `.claude/skills/`, niciuna activată în sesiunea de development (skills-activator are fallback description-overlap din v3.7, dar skills-le fixate sunt agentdb-* etc., nu match cu prompts CCDEW)

## Memory Stats

- **Total memory files**: depinde de runs — auto-updated
- **Critical**: 10 decizii în `decisions/`
- **Sessions snapshots**: vezi `sessions/` (auto-grow la fiecare /exit)
- **Last updated**: 2026-05-10
- **Vault size**: ~25KB (decisions + dashboard + sessions cumulate)
