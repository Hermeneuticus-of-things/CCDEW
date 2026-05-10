---
name: Structural DEBT — do NOT split intelligence + hook-handler
severity: HIGH
version: v3.5+
date: 2026-05-10
status: deferred (debt documented, not yet executed)
tags: [debt, refactor, split, architecture, decision-not-to-act]
---

# Structural DEBT — do NOT split intelligence.cjs + hook-handler.cjs

## Context
`auto-infer` (5-zoom audit) consistently flags 2 files as **HIGH** (>500 lines hard cap):

```
intelligence.cjs   979 lines
hook-handler.cjs  1024 lines
```

Automatic recommendation: "Split into 3 modules by responsibility".

## Options

**A. Immediate split (follow recommendation)**
- intelligence.cjs → `intel-graph.cjs` + `intel-init.cjs` + `intel-consolidate.cjs`
- hook-handler.cjs → `lib/handlers/{lifecycle,audit,tools}.cjs`
- Estimated effort: 2-3 hours
- Risk: HIGH regression (changes across 30+ handler commands, init/consolidate with complex logic)

**B. Defer as documented DEBT**
- Maintain status quo
- Risk: 0 (nothing changes)
- Cost: audit will continue to flag as HIGH (cosmetic, not functional)

**C. Minimal extract (move 1-2 functions to submodules)**
- 30-50% LOC reduction without major refactor
- Risk: LOW
- Benefit: partial — still over 500 lines

## Decision
**B — defer as documented DEBT.**

## Rationale
1. **HIGH regression risk** — massive refactor = high chance of bug in commands that work today
2. **0 user-visible benefit** — user doesn't see LOC, only behavior
3. **No active functional request** that triggers the split (when we integrate another project that uses graph functions, we'll do an extract)
4. **Best practice "stable + performant final"** — split added now brings instability
5. **Audit warning ≠ bug** — it's a signal for the future, not a blocker for now

## Trigger for re-evaluation
We re-evaluate the split when:
- A specific bug appears in zones not covered by tests in `intelligence.cjs::consolidate()` (most complex)
- We want to share `intelligence` with another project (then we extract as a separate lib)
- LOC exceeds 1500 (then it's impractical to navigate)

## Consequences
- /infer will continue to show 2 HIGH findings → that's expected, must not be ignored but INTERPRETED
- /optimize macro report: "proposal-only, human decision"
- DEBT visible in `_MEMORY/_DASHBOARD.md::Pending Corrections`
