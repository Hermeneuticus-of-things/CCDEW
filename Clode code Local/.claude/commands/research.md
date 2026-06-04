---
description: Research-first development mode — gather context before writing code (ECC pattern)
allowed-tools: Read, Grep, Glob, WebFetch, WebSearch, Agent
---

# /research

Research-first development pattern from `everything-claude-code` (ECC).

## Why
Writing code before understanding the problem produces refactor cycles. Research-first means: **understand → propose → review → write → verify**. Each phase has a deliverable; you don't move forward without it.

## How to invoke
```
/research <question or feature>
```

## What happens
1. **Phase 1 — Context gather** (Read, Grep, Glob): map the existing code that touches this feature. Output: list of relevant files with one-line summaries.
2. **Phase 2 — Constraints**: read CLAUDE.md, BEST_PRACTICES.md, PROJECTS/<name>/CLAUDE.md. Surface anything that limits the solution space.
3. **Phase 3 — Prior art**: WebSearch for similar problems / patterns. WebFetch top result. (Optional — skip if internal-only.)
4. **Phase 4 — Proposal**: 3 sentences max — what to do, what NOT to do, biggest tradeoff.
5. **Phase 5 — Adversarial review**: spawn `analyst` agent to find holes in the proposal before code is written.
6. **Phase 6 — Plan**: ordered list of files to touch, in execution order.

## When to skip
- One-line typo fix
- Trivial config change
- You already did the research yesterday for a related feature

## Output format
```
## Context
- file_a.ts:42 — owns X
- file_b.ts — invoked from file_a, validates Y

## Constraints (from CLAUDE.md)
- No M-dash in narrative (Karma rule)
- Cap0 = no illustrations

## Proposal
Add helper Z that does W. Avoid V because of past incident in <#issue>. Tradeoff: simpler API but loses Z'.

## Adversarial findings
- Edge case: when input is null, current code returns 0 silently — proposal must throw

## Plan
1. Add `lib/z.cjs` (40 lines)
2. Wire in `module-a.cjs:42`
3. Add test `tests/z.test.cjs` (5 cases)
4. Update CHANGELOG
```
