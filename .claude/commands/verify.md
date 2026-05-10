---
description: Verify the most recent changes — typecheck, tests, lint, secret-scan, dead code
allowed-tools: Bash, Read, Grep
---

# /verify

Quick sanity sweep over uncommitted changes (or the current branch vs main).

## What it runs

1. **Typecheck** — `tsc --noEmit` (TS) or equivalent for the detected language
2. **Tests** — runs unit tests for the changed files only (`vitest related`, `jest --findRelatedTests`, or `pytest <files>`)
3. **Lint** — eslint/ruff/golangci-lint on changed files
4. **Secret-scan** — runs `.claude/helpers/secret-scan.cjs` on every staged file
5. **Dead-code** — flags exported symbols not referenced anywhere
6. **Diff stats** — lines added/removed, files touched

## How to run

```
/verify
```

Optionally with a scope:

```
/verify --staged
/verify --branch
/verify <path/to/file.ts>
```

## Output

A grouped report:
```
[TYPECHECK] ok (0.4s)
[TESTS]     12 passed, 0 failed (1.8s)
[LINT]      2 warnings, 0 errors
[SECRETS]   clean
[DEAD]      1 unused export: src/utils/legacy.ts:exportedFn
[DIFF]      +127 -34 across 5 files
```

## When to use

- Before committing
- Before requesting code review
- After a complex refactor — quick smoke before pushing
