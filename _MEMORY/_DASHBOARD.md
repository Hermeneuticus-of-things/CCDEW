---
name: CCDEW Memory Dashboard
description: Live overview of CCDEW evolution, decisions, sessions, and pending items
type: reference
tags: [dashboard, session-start, ccdew, evolution]
project: ccdew
priority: high
_version: 4
_created: 2026-05-10
_modified: 2026-05-12
_modified_by: claude
related: [_INBOX.md, _PROTOCOL.md, _USER_NOTES.md, decisions/INDEX.md, sessions/]
---

# CCDEW Memory Dashboard

> CCDEW Obsidian vault. Indexes the full workspace evolution + architectural decisions + session snapshots. Auto-updated at `/exit` and SessionEnd.

## Current version

**CCDEW v3.9.2** · 22 test suites · **37/37 PASS** · enneagram_topology.md + Template Sync Audit

---

## Audit Results (live)

| Check Suite | Result | Details |
|---|---|---|
| A. CONFIGURATION | OK PASS | settings.json, feature-flags.json, permissions deny |
| B. MODULES | OK PASS | 10 helper modules, hook-handler wiring |
| C. PERFORMANCE | OK PASS | SSA 1.31ms, SAFLA 0.77ms |
| D. STATE | OK PASS | safla.json, instincts.json, decisions/ |
| E. COST | OK PASS | CodeBurn: $764/lună, 9759 apeluri |
| F. SECURITY | OK PASS | 40 deny patterns, secret-scan 11 patterns |
| G. CROSS-PLATFORM | OK PASS | linux, Python /usr/bin/python3, Node /usr/bin/node |

**Total: 37/37 PASS · 0 WARN · 0 FAIL**

---

## Quick evolution (v3.0 → v3.9.2)

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
| 3.9 | 2026-05-12 | 147 | ~8000 | 23 | v6.1 SLIM: SSA 5D + Ruflo + Profiles |
| 3.9.1 | 2026-05-12 | 147 | ~8100 | 24 | SOP Engine + Auto-Profile + MetaGPT |
| **3.9.2** | **2026-05-12** | **147** | **~8200** | **25** | **enneagram_topology.md + Template Sync Audit** |

---

## v6.1 SLIM Components

| Component | Status | Version | Description |
|---|---|---|---|
| Enneagram | OK | 9 types | 9-node routing + stress/growth arcs + adaptive topology |
| SSA Layer | OK | 5D | semantic + enneagram + holographic + recency + pinned scoring |
| SAFLA | OK | v3 | 30 sessions, 23 feedbacks, efficiency ~40% (target <25%) |
| CodeBurn | OK | CLI+native | $764/lună, 9759 apeluri, cache-first 117ms |
| Ruflo | OK | MCP | swarmInit, agentSpawn, memoryStore, federation, hooks_route |
| SOP Engine | OK | MetaGPT-style | 5 SOPs: refactor, audit, multi-file-refactor, research, security-audit |
| Auto-Profile | OK | budget-based | lite (3/13) / full (13/13) / ssa-max (9/13) auto-switch |
| Red Hat Evaluator | OK | 38-check | 37/37 PASS |

---

## SOP Engine Commands

| Command | Action |
|---|---|
| `sop list` | List all available SOPs |
| `sop <name>` | Show SOP details (phases, tools, agents) |
| `sop-execute <name>` | Execute SOP workflow |

**Available SOPs:** refactor · audit · multi-file-refactor · research · security-audit

---

## Auto-Profile Switch Rules

| Budget Used | Profile | Components Active |
|---|---|---|
| >90% daily | `ssa-max` | 9/13 (aggressive filtering) |
| >75% daily | `lite` | 3/13 (minimal) |
| <75% daily | `full` | 13/13 (all features) |

---

## Enneagram Topology

**9 Types:** Reformer, Helper, Achiever, Individualist, Investigator, Loyalist, Enthusiast, Challenger, Peacemaker

**Default weights:** All types start at 1.0. Achiever (type 3) has weight 3.0 by default.

**Arc topology:** 72 arcs (9×8 source→target). Stress/growth lines get 1.5x weight.

**Documentation:** See [_MEMORY/enneagram_topology.md](enneagram_topology.md) — types, arcs, SSA scoring, SAFLA integration.

---

## Template Sync Status (vs Hermeneuticus upstream)

| Template | CLAUDE.md | BEST_PRACTICES.md | serve_md.py | Status |
|---|---|---|---|---|
| android | IDENTICAL | IDENTICAL | — | OK synced |
| generic | IDENTICAL | IDENTICAL | — | OK synced |
| research | IDENTICAL | IDENTICAL | — | OK synced |
| carte | IDENTICAL | — | — | OK synced |
| preview-live-server | IDENTICAL | — | IDENTICAL | OK synced |

**CCDEW-unique directories:** `_MEMORY/` · `_BEST_PRACTICES/` · `_SETTINGS/`

---

## Benchmark Summary

| Metric | Value | Target | Status |
|---|---|---|---|
| SSA filter latency | 1.31ms | <5ms | OK |
| SAFLA feedback latency | 0.77ms | <2ms | OK |
| SSA Efficiency | ~40% | <25% | WARN |
| evaluate-setup | 37/37 | 37/37 | OK |
| Test suites | 147/147 | 147/147 | OK |

---

## Obsidian indexes

- [Decisions Index](decisions/INDEX.md) — architectural decisions
- [Enneagram Topology](enneagram_topology.md) — 9 types + arc weights + SSA integration
- `sessions/` — Obsidian MD per `/exit` (auto-generated)
- [Inbox](_INBOX.md) — manual user→Claude drop zone
- [User Notes](_USER_NOTES.md) — user-only space
- [Protocol](_PROTOCOL.md) — bidirectional vault rules

---

## Recent Changes (auto-updated)

- 2026-05-12: v3.9.2 → enneagram_topology.md + Template Sync Audit (all 5 templates IDENTICAL)
- 2026-05-12: v3.9.2 → CLAUDE.md sync + _DASHBOARD.md v4 + TODO.md session log
- 2026-05-12: v3.9.1 → SOP Engine (MetaGPT-style) + Auto-Profile + profile command
- 2026-05-12: v3.9.0 → v6.1 SLIM complete: SSA 5D + Ruflo + Profiles
- 2026-05-10: v3.8.0 → cross-process file-lock + race fix
- 2026-05-10: v3.7.0 → Python detection real path + skills fallback
- 2026-05-10: v3.6.0 → skills-propose GitHub + /exit snapshot + /sessions-compare
- 2026-05-10: v3.5.0 → 7/10 round-4 zones repaired + stability 5-zoom

---

## Memory Stats

- **Total memory files**: auto-updated
- **Critical**: decisions in `decisions/`
- **Session snapshots**: see `sessions/` (auto-grows on every `/exit`)
- **Last updated**: 2026-05-12
- **Vault size**: ~35KB (decisions + dashboard + sessions cumulative)