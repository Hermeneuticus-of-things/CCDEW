---
description: Multi-agent code review (reviewer + analyst + tester) over the current branch diff
allowed-tools: Agent, Bash, Read, Grep
---

# /review

Spawn a 3-agent review swarm over your current uncommitted/branch changes.

## How it routes

- **reviewer** (Node 1, Reformer) — code quality, naming, simplicity, anti-patterns
- **analyst** (Node 5, Analyzer) — logic bugs, edge cases, race conditions, perf
- **tester** (Node 6, Validator) — coverage gaps, missing assertions, regression risk

The 3 agents run **in parallel** on the same diff and their reports are merged into a single prioritized list (HIGH / MEDIUM / NIT).

## How to run

```
/review
/review --branch main..HEAD
/review path/to/file.ts
```

## Output structure

```
HIGH (must fix)
- src/auth.ts:42 — null pointer on missing token (analyst)
- src/auth.ts:88 — no test for the new branch (tester)

MEDIUM (should fix)
- src/auth.ts:12 — function does 3 things, split (reviewer)

NIT (optional)
- src/auth.ts — variable `tmp` could be `userToken` (reviewer)
```

## Notes

- Agents are spawned via `swarm_init` with `topology=mesh` (peer review, no leader).
- Review takes ~30–60s for typical PR-size diffs.
- The 3 agents see the **same** diff but apply different lenses — outputs are deduplicated automatically.
