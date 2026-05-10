---
description: Block-or-pass gate — checks all quality criteria before merge/deploy
allowed-tools: Bash, Read
---

# /quality-gate

A strict pass/fail gate. Designed to be run before merging to main or deploying.

## Default criteria (all must PASS)

| Check | Threshold |
|---|---|
| Typecheck | 0 errors |
| Unit tests | 100% pass |
| Coverage | ≥ 80% on changed files |
| Lint | 0 errors (warnings allowed) |
| Secret-scan | 0 matches |
| Bundle size | ≤ +5% vs main |
| Test execution time | ≤ 2× the median of last 10 runs |
| Cost-per-call (codeburn) | ≤ $0.05 average |

## How to run

```
/quality-gate
```

With overrides:

```
/quality-gate --no-bundle-check
/quality-gate --coverage 90
```

## Exit behavior

- All PASS → exit 0, prints summary green
- Any FAIL → exit 1, prints which check failed and the next step
- The hook handler refuses to run a follow-up `/release` or git push when this gate failed in the same session

## Config

Put per-project overrides in `.claude/quality-gate.json`:

```json
{
  "coverage_threshold": 75,
  "bundle_size_delta_max_pct": 10,
  "skip": ["bundle"]
}
```
