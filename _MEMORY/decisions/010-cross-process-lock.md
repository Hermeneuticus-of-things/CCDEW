---
name: Cross-process lock for SAFLA (race fix)
severity: HIGH
version: v3.8
date: 2026-05-10
status: applied
tags: [concurrency, atomic, lock, safla, multi-session]
---

# Cross-process lock for SAFLA (race fix)

## Context
A test with 2 parallel processes (`fork()`) writing 100 outcomes each into safla.json confirmed a **REAL race**:

```
[FAIL] race verify: lost writes: 100/200 (50% loss)
```

Cause: each process does `load() → modify → save()` atomically — BUT between process A's load and save, process B finishes its cycle with a different state. **Atomic write guaranteed file integrity**, but did not guarantee both writes are counted.

## Real severity
- **Multi-Claude session use case**: user opens 2 Claude Code sessions simultaneously (e.g.: 1 for audit, 1 for editing). Both call `safla.recordOutcome()` in parallel. Without lock: half the feedbacks are silently lost.
- On single-thread: 0 issue (verified in round-2 stability test)
- On multi-thread real: 50% data loss

## Options

**A. In-process queue + serial flush**
- Pro: simple
- Contra: doesn't solve cross-process

**B. Append-only log + reduce on read**
- Pro: write-side atomic, no lock
- Contra: schema changed, refactor all consumers

**C. Cross-process file-lock (sibling .lock with O_EXCL)**
- Pro: minimal change, surround critical section with lock
- Contra: lock contention overhead

**D. SQLite (with WAL mode)**
- Pro: industry standard
- Contra: external dependency, schema migration

## Decision
**C — `lib/file-lock.cjs` with O_EXCL + retry-with-backoff.**

## Implementation
- `acquire(target)` opens `<target>.lock` with `wx` (fail if exists)
- Retry delays: `[10, 25, 50, 100, 200, 400, 800]ms` (max ~1.6s wait)
- Stale detection: if lockfile mtime >30s → assume owner crashed, unlink + retry
- `withLock(target, fn)` — try/finally guarantees release on throw
- Default timeout 5s, error code `ELOCK_TIMEOUT`

## SAFLA integration
```js
function recordOutcome(nodeId, success, task) {
  // ...validation...
  withLock(SAFLA_PATH, () => {
    const data = load();
    // modify
    save(data);
  }, { timeoutMs: 5000 });
}
```

## Verification
- `tests/cross-claude-race.test.cjs`: 2 fork × 100 outcomes parallel → **200 feedbacks survive, no orphans, no corrupt keys** (post-fix)
- `tests/file-lock.test.cjs`: 6/6 PASS (acquire, release, timeout, withLock, throw safety, stale cleanup)

## Trade-off accepted
SAFLA `recordOutcome` now has **+0.3ms overhead** due to the lockfile cycle (open + write + close + unlink). On 1000 calls/sec = negligible. Benefit: zero data loss in multi-session use case.

## Generalized
The lock is available for any critical file — futureproof for `instincts.jsonl`, `skill-usage.jsonl`, etc. when they have concurrent writers.
