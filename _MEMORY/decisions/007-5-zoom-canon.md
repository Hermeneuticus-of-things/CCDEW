---
name: 5-zoom audit (Maha→Nano) as CCDEW canon
severity: MED
version: v3.4
date: 2026-05-10
status: applied
tags: [audit, methodology, zoom, observability]
---

# 5-zoom audit (Maha→Nano) as CCDEW canon

## Context
The standard audit was flat: a list of findings without hierarchy. You couldn't distinguish "structural problem" from "cosmetic typo".

## Decision
**5 canonical zoom levels:**
| Zoom | Scope | Example findings |
|---|---|---|
| MAHA | Whole-system | LOC > soft cap, tests < minimum, audit history empty |
| MACRO | Cross-module | files > 500 lines, helpers↔helpers excessive coupling |
| MEZZO | Per-module | modules with > 12 exports (multiple responsibilities) |
| MICRO | Per-function | functions > 75 lines or > 5 args |
| NANO | Per-line/char | trailing whitespace, mixed tabs+spaces, real TODO/FIXME |

## Implementation
- `lib/auto-infer.cjs` — 5 functions (`inferMaha`, `inferMacro`, `inferMezzo`, `inferMicro`, `inferNano`) + `summary()`
- `lib/auto-optimize.cjs` — NANO automatic (trim/normalize), MICRO+ proposal-only (human decisions)
- `/infer` and `/optimize` slash commands

## Rationale
- Each zoom has a distinct fix type (NANO=auto-trim, MEZZO+=human review)
- Auto-optimize is safe only at NANO (no semantic change); the rest is proposal-only
- User sees prioritized: HIGH at MACRO/MAHA, WARN at MICRO, INFO at NANO

## Consequences
- 7 + 5 = 12 regression tests for auto-infer + auto-optimize
- Bug fixed later (v3.7): NANO false-positive (regex matching its own keyword in comments)
- Bug fixed later (v3.4): perf-baseline auto-rebaselined spikes (snapshot before push)

## Adoption
- `/evaluate-setup` extended report with zoom-grouped findings
- SessionStart auto-audit uses summary
