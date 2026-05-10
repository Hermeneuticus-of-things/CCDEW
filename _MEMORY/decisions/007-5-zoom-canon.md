---
name: 5-zoom audit (Maha→Nano) ca canon CCDEW
severity: MED
version: v3.4
date: 2026-05-10
status: applied
tags: [audit, methodology, zoom, observability]
---

# 5-zoom audit (Maha→Nano) ca canon CCDEW

## Context
Auditul standard era plat: o listă de findings fără ierarhie. Nu reușeai să distingi "structural problem" de "cosmetic typo".

## Decizie
**5 zoom levels canon:**
| Zoom | Scope | Exemple findings |
|---|---|---|
| MAHA | Whole-system | LOC > soft cap, tests < minimum, audit history vid |
| MACRO | Cross-module | files > 500 lines, helpers↔helpers excessive coupling |
| MEZZO | Per-module | modules cu > 12 exports (responsabilități multiple) |
| MICRO | Per-function | funcții > 75 linii sau > 5 args |
| NANO | Per-line/char | trailing whitespace, mixed tabs+spaces, real TODO/FIXME |

## Implementare
- `lib/auto-infer.cjs` — 5 funcții (`inferMaha`, `inferMacro`, `inferMezzo`, `inferMicro`, `inferNano`) + `summary()`
- `lib/auto-optimize.cjs` — NANO automat (trim/normalize), MICRO+ proposal-only (decizii umane)
- `/infer` și `/optimize` slash commands

## Motiv
- Fiecare zoom are tip distinct de fix (NANO=auto-trim, MEZZO+=human review)
- Auto-optimize e safe doar la NANO (no semantic change); restul e proposal-only
- Userul vede prioritizat: HIGH la MACRO/MAHA, WARN la MICRO, INFO la NANO

## Consecințe
- 7 + 5 = 12 teste regression pentru auto-infer + auto-optimize
- Bug fixat ulterior (v3.7): NANO false-positive (regex match keyword propriu în comments)
- Bug fixat ulterior (v3.4): perf-baseline auto-rebaselina spike-uri (snapshot înainte de push)

## Adoption
- `/evaluate-setup` raport extins cu zoom-grouped findings
- SessionStart auto-audit folosește summary
