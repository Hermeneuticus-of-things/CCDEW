---
name: Cross-process lock pentru SAFLA (race fix)
severity: HIGH
version: v3.8
date: 2026-05-10
status: applied
tags: [concurrency, atomic, lock, safla, multi-session]
---

# Cross-process lock pentru SAFLA (race fix)

## Context
Test cu 2 procese paralele (`fork()`) scriind 100 outcomes fiecare în safla.json a confirmat **race REAL**:

```
[FAIL] race verify: lost writes: 100/200 (50% pierderi)
```

Cauza: fiecare proces face `load() → modify → save()` atomic, DAR între load și save al procesului A, procesul B termină ciclul cu state diferit. **Atomic write garanta integritatea fișierului**, dar nu garanta că ambele scrieri sunt count-ate.

## Severitate reală
- **Multi-Claude session use case**: utilizatorul deschide 2 sesiuni Claude Code simultan (ex: 1 pentru audit, 1 pentru editing). Ambele apelează `safla.recordOutcome()` în paralel. Fără lock: jumătate din feedback-uri se pierd silent.
- Pe single-thread: 0 issue (verify din round 2 stability test passes)
- Pe multi-thread real: 50% data loss

## Opțiuni

**A. In-process queue + serial flush**
- Pro: simplu
- Contra: nu rezolvă cross-process

**B. Append-only log + reduce on read**
- Pro: write-side atomic, no lock
- Contra: schema schimbată, refactor toate consumers

**C. Cross-process file-lock (sibling .lock cu O_EXCL)**
- Pro: minimal change, surround critical section cu lock
- Contra: lock contention overhead

**D. SQLite (cu WAL mode)**
- Pro: industry standard
- Contra: dependency externă, schema migrare

## Decizie
**C — `lib/file-lock.cjs` cu O_EXCL + retry-with-backoff.**

## Implementare
- `acquire(target)` deschide `<target>.lock` cu `wx` (fail dacă există)
- Retry delays: `[10, 25, 50, 100, 200, 400, 800]ms` (max ~1.6s wait)
- Stale detection: dacă lockfile mtime >30s → presupun owner crashed, unlink + retry
- `withLock(target, fn)` — try/finally garantează release pe throw
- Default timeout 5s, error code `ELOCK_TIMEOUT`

## SAFLA integration
```js
function recordOutcome(nodeId, success, task) {
  // ...validare...
  withLock(SAFLA_PATH, () => {
    const data = load();
    // modify
    save(data);
  }, { timeoutMs: 5000 });
}
```

## Verificare
- `tests/cross-claude-race.test.cjs`: 2 fork × 100 outcomes paralele → **200 feedbacks survive, no orphans, no corrupt keys** (post-fix)
- `tests/file-lock.test.cjs`: 6/6 PASS (acquire, release, timeout, withLock, throw safety, stale cleanup)

## Trade-off acceptat
SAFLA `recordOutcome` are **+0.3ms overhead** din cauza lockfile cycle (open + write + close + unlink). Pe 1000 calls/sec = neglijabil. Beneficiu: zero data loss în multi-session use case.

## Generalizat
Lock-ul e disponibil pentru orice fișier critic — futureproof pentru `instincts.jsonl`, `skill-usage.jsonl` etc. când vor avea concurrent writers.
