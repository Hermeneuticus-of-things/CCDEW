---
description: Explain what changed in the current diff — what + why + risk
allowed-tools: Bash, Read
---

# /diff-explain

Plain-English summary of `git diff` for humans + reviewers + commit messages.

## Output structure

```
## Summary
2 sentences — what overall outcome this diff achieves.

## Files changed (5)
- src/auth.ts (+42 -8) — moved JWT validation into a helper, added refresh-token branch
- src/auth.test.ts (+30) — covers the new branch
- ...

## Risk
- LOW: new code is well-tested, no public API changes
- ⚠ MEDIUM: removes the synchronous `validate()` export — if any external caller depends on it, build will break

## Suggested commit message
feat(auth): add refresh-token branch with isolated validation helper
```

## How to run

```
/diff-explain                  # current uncommitted diff
/diff-explain HEAD~3..HEAD     # last 3 commits
/diff-explain main..HEAD       # branch vs main
/diff-explain <file>           # single file
```

## When to use

- Writing a PR description from a messy WIP branch
- Reviewing your own diff before pushing
- Onboarding a teammate to recent changes
- Generating a changelog entry
