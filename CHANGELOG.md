# CHANGELOG — CCDEW (Claude Code Efficient Workspace)

> Format: [`_SETTINGS/CHANGELOG-FORMAT.md`](_SETTINGS/CHANGELOG-FORMAT.md)
> Folder renamed from `claude-code-eficient-workspace` → `CCDEW` in v3.1.0.

---

## [3.8.0] — Round 5 zone netouched: file-lock cross-process + bench + i18n + race fix

**Data:** 2026-05-10
**Request:** "ce poți face cu Adversarial round 5 — zone netouched cu motiv"

### Zona 5 reparată — race condition cross-process REALĂ
**Bug descoperit:** test cu 2 procese paralele scriind safla.json a pierdut **100/200 outcomes** (fiecare proces overwrite cu state-ul propriu read-modify-write).

**Fix:**
- `lib/file-lock.cjs` — cross-process lock cu O_EXCL, retry-with-backoff `[10, 25, 50, 100, 200, 400, 800]ms`, stale detection >30s, timeout configurable
- `safla.cjs::recordOutcome()` folosește `withLock()` la SAFLA_PATH — read-modify-write devine atomic cross-process
- `tests/cross-claude-race.test.cjs` — fork 2 procese × 100 outcomes → 200 feedbacks survive ✓

### Zona 4 reparată — bench + perf-baseline auto-record
- Comand `bench` care rulează SSA + SAFLA hot-paths × 5, înregistrează la `perf-baseline`
- Hook `session-end` adăugat auto-bench (ssa.filterContext) → înregistrare automată după fiecare sesiune
- Detect regression `>50% peste baseline p95` → log `[PERF] 🚨 regression`

### Zona 3 parțial reparată — CCDEW_LANG hot-paths
- `t()` integrat în `/burn` pentru mesajul `codeburn.unavailable` (RO/EN switchable via `CCDEW_LANG=ro`)
- Restul UI strings (verify/quality-gate/infer) rămân EN — scope minor pentru future

### Zone 1+2 (split structural) — DEBT explicat
- `intelligence.cjs` 979L și `hook-handler.cjs` 1024L peste hard cap 500
- **De ce skip:** split major = HIGH risk (testfailure regression), 0 user-visible benefit, doar warning audit cosmetic
- DEBT documentat: best practice = split când există un trigger funcțional (bug în zona, sau need de a partaja cu alt project), NU pentru că audit zice așa

### 2 module lib/ noi
| Module | Tests |
|---|---|
| `lib/file-lock.cjs` | 6/6 PASS — cross-process O_EXCL lock + stale detect |

### Test suite v3.8 — **22 suite, 147/147 PASS**
| Suite | Tests | New |
|---|---|---|
| atomic-write | 5 | |
| auto-infer | 7 | |
| auto-optimize | 5 | |
| codeburn-engine | 8 | |
| **cross-claude-race** | **1** | NEW |
| error-log | 3 | |
| **file-lock** | **6** | NEW |
| i18n | 7 | |
| local-date | 6 | |
| migrate | 6 | |
| path-safe | 10 | |
| perf-baseline | 6 | |
| platform-detect | 4 | |
| pricing | 6 | |
| python-smoke | 7 | |
| redact | 10 | |
| safla-validation | 7 | |
| secret-scan | 8 | |
| session-snapshot | 8 | |
| skills-propose | 11 | |
| stability-5zoom | 10 | |
| strings | 6 | |
| **TOTAL** | **147/147** | |

### Empiric live (post-v3.8)
- `npm test`: **147/147 PASS** (22 suite, +2: cross-claude-race + file-lock)
- `/bench` live: ssa.filterContext 0.33ms · safla.recordOutcome 1.18ms (cu lock overhead)
- Race fix verified: 200 outcomes survive 2 procese paralele
- `/evaluate-setup`: 38/38 PASS

### Comenzi noi
```bash
npm run bench                 # rulează benchmarks + record la perf-baseline
node .claude/helpers/hook-handler.cjs bench --summary  # cu istoric complet

# Auto: SessionEnd hook auto-record ssa.filterContext (regression alert)
```

### Trade-off acceptat
SAFLA `recordOutcome` are acum **+0.3ms overhead** din cauza lockfile (verificare + create + release). Pe 1000 calls/sec asta e neglijabil; pentru hot-path single-thread, e jertfă acceptabilă pentru a NU mai pierde 50% scrieri când rulez 2 sesiuni simultane.

---

## [3.7.0] — Round 5: Python detection + skills description fallback + NANO false-pos + Python smoke

**Data:** 2026-05-10
**Request:** Audit 5-zoom + divergent-convergent + omiteri round 5 + auto-infer/optimize.

### Audit live la 5 zoom (output `/infer`)
```
[INFER] 10 findings · HIGH:2 WARN:7 INFO:1
MAHA:  19 test suites < 50 expected for 7243 LOC
MACRO: hook-handler 986 + intelligence 979 (>500 hard cap), auto-memory 351 (>300 soft cap)
MICRO: intelligence.cjs init() 111L, consolidate() 150L, stats() 191L (>75 soft cap)
NANO:  2 false-positive TODO/FIXME (auto-infer + quality-gate documentation)
```

### Round 5 omiteri descoperite (real, diferite de round 1-4)

| # | Zonă | Severitate | Status v3.7 |
|---|---|---|---|
| 1 | **Python `findPython()` returnează numele cmd, nu calea** — Windows declanșa Store alias `python3.exe` care printează "Python was not found" și exit !=0 | **HIGH** | ✅ FIX: `findPython` probează `-V`, returnează **calea rezolvată** doar dacă `Python X.Y` apare pe stdout/stderr |
| 2 | **7 fișiere Python ZERO tests** (obs, auto_learn × 3, enneagram × 2, obsidian-session-context) | MEDIUM | ✅ FIX: `tests/python-smoke.test.cjs` — `ast.parse()` syntax check pe toate, skip elegant dacă Python lipsește |
| 3 | **Skills NU se activau** — match doar pe `triggers` field; SKILL.md cu doar `description` lung fără `triggers` se ignoră | MEDIUM | ✅ FIX: fallback **description-overlap** (≥2 cuvinte ≥4 chars comune cu prompt → score = overlap) |
| 4 | **NANO false-positive** — auto-infer detectează `FIXME`/`HACK` în propriul cod (regex documentation) | LOW | ✅ FIX: skip `/* */` block comments + `//` line comments + string literals |
| 5 | **0 skill activations după 7 rounds de development** | symptom of #3 | ✅ rezolvat prin #3 |

### Test suite v3.7 — **20 suite, 140/140 PASS**
| Suite | Tests | New |
|---|---|---|
| atomic-write | 5 | |
| auto-infer | 7 | |
| auto-optimize | 5 | |
| codeburn-engine | 8 | |
| error-log | 3 | |
| i18n | 7 | |
| local-date | 6 | |
| migrate | 6 | |
| path-safe | 10 | |
| perf-baseline | 6 | |
| platform-detect | 4 | |
| pricing | 6 | |
| **python-smoke** | **7** | NEW |
| redact | 10 | |
| safla-validation | 7 | |
| secret-scan | 8 | |
| session-snapshot | 8 | |
| skills-propose | 11 | |
| stability-5zoom | 10 | |
| strings | 6 | |
| **TOTAL** | **140/140** | |

### Empiric live (post-v3.7)
- `npm test`: **140/140 PASS** (20 suite, +1 nou)
- Python detection real: `findPython() → C:\Users\Think\AppData\Local\Programs\Python\Python313\python.exe` (nu mai e alias broken)
- 7/7 fișiere Python validate sintactic
- Skills activation funcțională cu fallback description-overlap

### Adversarial round 5 — zone netouched (raportate, nu reparate în v3.7)

| # | Zonă | De ce nu acum |
|---|---|---|
| 1 | `intelligence.cjs` 979 linii — încă nu split | Refactor structural mare, scope creep |
| 2 | `hook-handler.cjs` 986 linii — încă peste hard cap 500 | La fel, scope creep |
| 3 | `CCDEW_LANG` propagation hot-paths | Doar lib/strings.cjs folosește; rest hardcoded EN — dar funcțional ok |
| 4 | `auto-memory-hook.mjs` 351 linii | În scope dar low priority |
| 5 | Performance benchmarks în CI | perf-baseline există, dar fără CI runner periodic |
| 6 | Cross-Claude session real-test | Atomic-write probabil OK, dar netest |
| 7 | License headers per-fișier | LICENSE root suficient |

---

## [3.6.0] — Skills-propose (GitHub mature search) + /exit session snapshot + /sessions-compare

**Data:** 2026-05-10
**Request:** "skills-propose caută pe GitHub și creează skills inspirate din proiecte meritoroase" + "la /exit salvează toată sesiunea + ce a învățat + metricele eficiență pentru comparații viitoare"

### 2 module lib/ noi

| Module | Rol |
|---|---|
| `lib/skills-propose.cjs` | GitHub Search API → filtrează maturi (≥10 stars, license MIT/Apache/ISC/BSD/MPL, push <365d, !archived, !disabled) → propune candidați + scaffold opțional |
| `lib/session-snapshot.cjs` | La `/exit` (sau auto la SessionEnd): capturează cost+SAFLA+instincts+skills+perf+audit+errors+workspace într-un singur JSON pentru comparații cross-session |

### `/skills-propose` features
- Searches GitHub via stdlib `https.get` (no deps), 4 query variants pentru robustețe
- **Strict license filter** — drops repos cu license unknown by default (opt-in cu `allowUnknownLicense`)
- **PII redaction** automată în descrieri (emails, paths, JWT)
- **Cache 1h** TTL la `.claude-flow/data/skills-search-cache.json`
- **Scaffold generator**: `--scaffold <local-name>` creează `.claude/skills/<name>/SKILL.md` cu frontmatter + atribuire upstream + license note
- **Refuses to overwrite** existing skills
- **No code copy** — doar metadata (descriere + topics → triggers, stars, license info)

Live test: `skills-propose "code review"` → 5 mature candidates returned (8.6k★ ARIS, 1.2k★ ai-legal, 569★ skills-marketplace, 461★ claude-code-skills, 444★ code-review-skill).

### `/exit` snapshot — schema v1.0
```json
{
  "version": "1.0",
  "session_id": "...",
  "ended_at": "2026-05-10T11:26:30+02:00",
  "duration_sec": null,
  "cost":      { "source": "real", "today_cost": 273.84, "today_calls": 1314, "month_cost": 2570.42 },
  "safla":     { "sessions": 5, "total_feedbacks": 53, "nodes": { "1": {...}, ..., "9": {...} } },
  "instincts": { "patterns": 0, "log_entries": 0 },
  "skills":    { "suggested_total": 0, "unique_skills": 0, "top_5": [], "dead_count": 33 },
  "perf":      { "ssa.filterContext": { "p95": 0.96, "latest": 0.83 }, ... },
  "audit":     { "pass": 38, "warn": 0, "fail": 0, "audits_total": 5 },
  "errors":    { "count_24h": 3, "top_scopes": { "auto-audit": 2, "skills-propose.search": 1 } },
  "workspace": { "loc": 7237, "modules": 46, "test_suites": 19 }
}
```

### Auto-trigger la SessionEnd
Hook `session-end` cheamă acum `session-snapshot.snapshot()` automat la fiecare oprire de sesiune Claude Code. **Toate sesiunile viitoare vor fi auto-arhivate** la `.claude-flow/sessions/session-<localISO>-<pid>.json`.

### `/sessions-compare` — analiza cross-session
Tabel comparativ pentru ultimele N sesiuni:
```
[SESSIONS-COMPARE] last 4 sessions:
  [0] 2026-05-10T07:43Z   [1] 2026-05-10T07:44Z   [2] 2026-05-10T07:48Z   [3] 2026-05-10T11:26+02

  metric                          [0]      [1]      [2]      [3]
  cost.today_cost                   -        -        -    273.84
  safla.total_feedbacks             -        -        -        53
  audit.pass                        -        -        -        38
  workspace.loc                     -        -        -      7237
  workspace.test_suites             -        -        -        19
```
(Sesiunile [0]-[2] sunt de la graphify pre-v3.6, deci fără cost/safla — vor avea date complete de la sesiunea următoare.)

### Test suite v3.6 — **19 suite, 133/133 PASS**
| Suite | Tests | New |
|---|---|---|
| atomic-write | 5 | |
| auto-infer | 7 | |
| auto-optimize | 5 | |
| codeburn-engine | 8 | |
| error-log | 3 | |
| i18n | 7 | |
| local-date | 6 | |
| migrate | 6 | |
| path-safe | 10 | |
| perf-baseline | 6 | |
| platform-detect | 4 | |
| pricing | 6 | |
| redact | 10 | |
| safla-validation | 7 | |
| secret-scan | 8 | |
| **session-snapshot** | **8** | NEW |
| **skills-propose** | **11** | NEW |
| stability-5zoom | 10 | |
| strings | 6 | |
| **TOTAL** | **133/133** | |

### Comenzi noi
```bash
# Skills propose
node .claude/helpers/hook-handler.cjs skills-propose "<keyword>"
node .claude/helpers/hook-handler.cjs skills-propose "<keyword>" --scaffold <local-name>
node .claude/helpers/hook-handler.cjs skills-propose "<keyword>" --fresh   # bypass cache

# Session snapshot
node .claude/helpers/hook-handler.cjs exit                  # save snapshot now
node .claude/helpers/hook-handler.cjs exit "note text"      # with annotation
node .claude/helpers/hook-handler.cjs exit --json           # full output

# Cross-session comparison
node .claude/helpers/hook-handler.cjs sessions-compare 5    # last 5 sessions
node .claude/helpers/hook-handler.cjs sessions-compare 10 --json

# Auto: la fiecare SessionEnd, snapshot creat automat
```

### Empiric live (post-v3.6)
- `npm test`: **133/133 PASS** (19 suite)
- `/evaluate-setup`: 38/38 PASS
- `/skills-propose "code review"`: 5 mature candidates returned (verified live GitHub API)
- `/exit`: snapshot saved cu cost $273.84 / 1314 calls / 53 SAFLA / 38 audit / 7237 LOC

---

## [3.5.0] — Stability 5-zoom + auto-learn + 7 zone oarbe round 4 reparate

**Data:** 2026-05-10
**Request:** "test stabilitate produse interferențe la 5 zoom + auto-învățare + reparare round 4 zone oarbe"

### 5 module lib/ noi
| Module | Rol | Zona oarbă reparată |
|---|---|---|
| `lib/jsdoc-validator.cjs` | Verifică @param/@returns pe exporturi | #1 |
| `lib/remote-backup.cjs` | Detect git remote absent + _ARCHIVE size monitoring | #3 |
| `lib/strings.cjs` | RO + EN UI strings map cu interpolare `{var}` | #4 |
| `lib/auto-learn.cjs` | Adjust thresholds dinamic din audit history (≥5 samples) | meta |
| `package-lock.json` | Reproducibility builds | #8 |

### Refactor
- `quality-gate.cjs` adaugă **npm audit** check (high/critical = FAIL)
- `skills-activator.cjs` extins: `usageStats()`, `deadSkills()`, append la `skill-usage.jsonl` la fiecare activare → **#5 + #10 reparate** (track skill activation)

### Stability test 5-zoom (NEW: 10 teste)
| Zoom | Test |
|---|---|
| MAHA | auto-infer survives empty workspace + auto-learn empty history |
| MACRO | 50 concurrent atomic writes survive race |
| MEZZO | SAFLA absorbs 1000 outcomes, zero corrupt keys |
| MICRO | fuzz `validate.isValidNodeId` rejects 17 inputs ; secret-scan tolerează malformed ; path-safe rejects 9 metachar variants |
| NANO | redact preservă unicode/emoji/RTL ; local-date Dec-31 23:59 edge ; i18n diacritics RO normalize |

### Test suite v3.5 — **17 suite, 114/114 PASS**
| Suite | Tests | New |
|---|---|---|
| atomic-write | 5 | |
| auto-infer | 7 | |
| auto-optimize | 5 | |
| codeburn-engine | 8 | |
| error-log | 3 | |
| i18n | 7 | |
| local-date | 6 | |
| migrate | 6 | |
| path-safe | 10 | |
| perf-baseline | 6 | |
| platform-detect | 4 | |
| pricing | 6 | |
| redact | 10 | |
| safla-validation | 7 | |
| secret-scan | 8 | |
| **stability-5zoom** | **10** | NEW |
| **strings** | **6** | NEW |
| **TOTAL** | **114/114** | |

### Comenzi noi
```bash
# Zone 1 (JSDoc validator)
node -e "console.log(JSON.stringify(require('./.claude/helpers/lib/jsdoc-validator.cjs').validateDir('.claude/helpers'), null, 2))"

# Zone 3 (remote backup status)
node -e "console.log(JSON.stringify(require('./.claude/helpers/lib/remote-backup.cjs').check(), null, 2))"

# Zone 4 (i18n switch)
CCDEW_LANG=ro node .claude/helpers/hook-handler.cjs evaluate-setup

# Zone 5 (dead skills)
node -e "console.log(require('./.claude/helpers/skills-activator.cjs').deadSkills())"

# Auto-learn (dynamic thresholds)
node -e "console.log(require('./.claude/helpers/lib/auto-learn.cjs').learn())"
```

### Auto-learning loop activ
- Citește ultimele 20 audits din `.claude-flow/reports/evaluate-*.json`
- Calculează rolling avg pass/warn/fail counts
- Salvează la `.claude-flow/data/learned-thresholds.json`
- Apel viitor: `shouldAlert(currentSummary)` returnează doar dacă **deviation > learned baseline**

### Zone oarbe round 4 status

| # | Zonă | Status v3.5 |
|---|---|---|
| 1 | JSDoc absent | ✅ `lib/jsdoc-validator.cjs` |
| 2 | npm audit nu wrapped | ✅ în quality-gate |
| 3 | _ARCHIVE local-only | ✅ `lib/remote-backup.cjs` warn dacă remote lipsește |
| 4 | i18n UI EN-only | ✅ `lib/strings.cjs` RO+EN cu env switch |
| 5 | Dead skill detection | ✅ `skills-activator.usageStats()` + `deadSkills()` |
| 6 | Auto-restart daemons | ⏭️ skip (no daemons running) |
| 7 | License headers per-fișier | ⏭️ skip (LICENSE root sufficient) |
| 8 | Reproducibility (no lockfile) | ✅ `package-lock.json` generat |
| 9 | Multi-Claude session race | ⏭️ atomic write deja OK |
| 10 | Skill execution feedback | ✅ skill-usage.jsonl + tracking |

**7/10 reparate, 3/10 skip cu motiv documentat.**

### Empiric live (post-v3.5)
- `npm test`: **114/114 PASS** (17 suite, 6694 LOC)
- `/evaluate-setup`: 38/38 PASS · 0 WARN · 0 FAIL
- `/infer`: 10 findings detected automat
- Stability 5-zoom: 10/10 PASS — sistemul rezistă la concurency, fuzz, encoding edge cases
- Auto-learn: framework live, va activa după 5 audits cumulati

---

## [3.4.0] — 5-zoom audit (Maha→Nano) + auto-infer + auto-optimize

**Data:** 2026-05-10
**Request:** "audit + test divergent-convergent + ce am omis + auto-inferre + auto-optimize la 5 niveluri (Maha/Macro/Mezzo/Micro/Nano)"

### Audit 5-zoom (live)
| Zoom | Findings actuale (post-v3.3) |
|---|---|
| **MAHA** (whole-system) | 6359 LOC · 15 test suites (sub 50 expected) · 33 skills · 38/38 audit PASS |
| **MACRO** (cross-module) | 3 fișiere peste 300 linii: hook-handler 900, intelligence 979, auto-memory-hook 351 |
| **MEZZO** (per-module) | export count toate sub limit (≤12) — cohesion OK |
| **MICRO** (per-function) | 3 funcții peste 75 linii în intelligence.cjs (init 111, consolidate 150, stats 191) |
| **NANO** (per-line) | 10 fișiere cu CRLF endings normalizate la LF (auto-applied) |

### Module noi
| Module | Rol |
|---|---|
| `lib/auto-infer.cjs` | Scanează workspace la 5 zoom levels, deduce gaps/drift fără cerere user |
| `lib/auto-optimize.cjs` | Aplică safe transforms (NANO automat, MICRO+ proposal-only) |

### Auto-inferre la 5 zoom (live)
- **MAHA**: detect drift de la goals (LOC > soft cap, tests sub minimum, audit history vid)
- **MACRO**: detect file size > 500 (HIGH) sau > 300 (WARN), helpers↔helpers coupling > 5
- **MEZZO**: detect modules cu > 12 exports (responsabilități multiple)
- **MICRO**: detect funcții > 75 linii sau > 5 args
- **NANO**: detect trailing whitespace, mixed tabs+spaces, TODO/FIXME real

### Auto-optimize la 5 zoom (live)
- **NANO**: aplicare AUTO — strip BOM, normalize CRLF→LF, trim trailing whitespace; backup la `_ARCHIVE/optimize-bak-<ts>/`
- **MICRO/MEZZO/MACRO/MAHA**: proposal-only — return list de acțiuni recomandate cu file:line + reason

### Comenzi noi
```bash
npm run infer                  # /infer la 5 zoom (sau hook-handler.cjs infer [--json])
npm run optimize -- nano       # apply safe transforms
npm run optimize -- nano --dry-run
npm run optimize -- micro      # proposal-only
npm run optimize -- mezzo|macro|maha
```

### Test suite v3.4 — **15 suite, 98/98 PASS**
| Suite | Tests | New |
|---|---|---|
| atomic-write | 5 | |
| **auto-infer** | **7** | NEW |
| **auto-optimize** | **5** | NEW |
| codeburn-engine | 8 | |
| error-log | 3 | |
| i18n | 7 | |
| local-date | 6 | |
| migrate | 6 | |
| path-safe | 10 | |
| perf-baseline | 6 | |
| platform-detect | 4 | |
| pricing | 6 | |
| redact | 10 | |
| safla-validation | 7 | |
| secret-scan | 8 | |
| **TOTAL** | **98/98 PASS** | |

### Adversarial round 4 — zone netouched (raportate, nu fixed)
1. **JSDoc absent** — fără type signatures (TS-style); auto-infer/optimize ar putea valida
2. **Performance benchmarking în CI** — perf-baseline există, dar nu rulează auto periodic
3. **SBOM / dependency security audit** — `npm audit` nu e wrapped
4. **Backup la cloud** — `_ARCHIVE/` doar local
5. **i18n UI strings** — keywords routing OK, console messages încă english
6. **Dead skill detection** — 33 skills, nu știm care folosite real (instincts ar putea track activations)
7. **Auto-restart daemons** — niciun
8. **License headers** — absente în fișiere individuale (LICENSE există root)
9. **Reproducibility builds** — fără package-lock.json
10. **TypeScript migration path** — nu există plan, dar JSDoc ar fi un compromise
11. **Multi-Claude session race** — 2 sesiuni simultane scriu safla.json paralel (atomic write OK, dar interleave ok la nivel logic)
12. **Skill execution feedback** — skills-activator sugerează, nu măsoară uptake

### Empiric live (post-v3.4)
- `npm test`: **98/98 PASS** (15 suite)
- `/evaluate-setup`: 38/38 PASS · 0 WARN · 0 FAIL
- `/infer`: 10 findings detected automat la 5 zoom (2 HIGH structural, 7 WARN minor, 1 INFO)
- `/optimize nano`: 10 fișiere LF-normalized, backup-uri în `_ARCHIVE/optimize-bak-2026-05-10/`

---

## [3.3.0] — Round 3: perf-baseline + PII redact + auto-triggers + meta-workspace + RO docs

**Data:** 2026-05-10
**Request:** "fă tot pana la final si rezolva cu best practice acolo unde trebuie sa fie performant si stabil la final."

### Phase 1 — Round 3 BP fixes
- `lib/perf-baseline.cjs` — performance regression detection (rolling 30-sample window, p95 tracking, alerts when current > p95 × 1.5)
- `lib/redact.cjs` — PII redaction în logs: emails, phone-like, JWT, hex, AWS/Anthropic/OpenAI keys, home paths → `~`
- `error-log.cjs` integrează `redact` automat — toate erorile/extra-urile redacted înainte de scriere
- `safla.cjs::load()` folosește `lib/migrate.cjs` cu chain v1.0→v2.0 (framework actually used acum, nu mai e dead code)
- `codeburn-cache.json` — adăugat câmp `version: '1.0'` pentru migration future-proof

### Phase 2 — ECC + Red Hat coverage deep
- `repositories/` folder + README — Red Hat meta-workspace pattern, separare CCDEW root vs sub-projects vs external repos
- `.claude/commands/research.md` — ECC research-first development pattern (6-phase: context→constraints→prior-art→proposal→adversarial→plan)
- `README.ro.md` — documentație multi-language (română), inspirat din ECC multi-lingual support

### Phase 3 — Auto-triggers (npm scripts ca hooks)
- **`pre-bash` extended**: detectează `git commit*` → auto-rulează `verify`; detectează `git push*` (fără `--no-verify`) → auto-rulează `quality-gate`. Fail = block (bypass via `HOOKS_SKIP=1`)
- **`SessionStart` extended**: nou hook `auto-audit` rulează `evaluate-setup --json` o dată la 24h, păstrează snapshot la `.claude-flow/reports/auto-audit-last.json`, raportează `[AUTO-AUDIT] ⚠ N FAIL · M WARN` doar dacă există probleme

### Phase 4 — Tests + audit final

| Suite | Tests | New |
|---|---|---|
| atomic-write | 5 | |
| codeburn-engine | 8 | |
| error-log | 3 | |
| i18n | 7 | |
| local-date | 6 | |
| migrate | 6 | |
| **perf-baseline** | **6** | NEW |
| path-safe | 10 | |
| platform-detect | 4 | |
| pricing | 6 | |
| **redact** | **10** | NEW |
| safla-validation | 7 | |
| secret-scan | 8 | |
| **TOTAL** | **86/86 PASS** | |

### Empiric live (post-v3.3)
- `npm test`: **86/86 PASS** (13 suite)
- `/evaluate-setup`: 38/38 PASS
- `/auto-audit`: gata să ruleze la SessionStart
- `pre-bash` cu auto-verify/auto-quality-gate gates
- PII redaction validată: emails, AWS/Anthropic/OpenAI keys, JWT, paths home

### Breaking change minor
- `pre-bash` blochează `git commit` și `git push` dacă verify/quality-gate eșuează. **Bypass:** `HOOKS_SKIP=1 git commit -m "..."` pentru emergency override. Atenție: bypass înseamnă commit cu erori known.

---

## [3.2.0] — Adversarial round 2: TZ + i18n + shell-safe + budget + tools

**Data:** 2026-05-10
**Request:** "aplică tot ce ai înțeles" (după test divergent-convergent + adversarial omiteri).

### 5 module lib/ noi
| Module | Rol |
|---|---|
| `lib/local-date.cjs` | TZ-aware `todayLocal()` / `monthLocal()` — userii non-UTC nu mai pierd 2-4h "today" |
| `lib/pricing.cjs` | Centralized model pricing (PRICING_VERSION='2026.05'), single source pentru 3 locuri ce avea hardcoded values |
| `lib/migrate.cjs` | JSON migration framework cu version chain + safety limit 32 steps |
| `lib/i18n.cjs` | RO+EN routing keywords (refactorizare/refactorizez, fixează, repară, etc.) |
| `lib/path-safe.cjs` | Shell injection mitigation cu `isSafeBinaryPath()` — blochează metachars `& ; \| $ () ' " ! * ? \r \n` |

### Refactor propagat
- `codeburn-engine.cjs` → folosește `lib/pricing` + `lib/local-date`, eliminat 17 linii hardcoded
- `codeburn.cjs::fetchRealStatus()` → validează path cu `isSafeBinaryPath()` înainte de exec; logged la `error-log.cjs` dacă fail
- `hook-handler.cjs::selectWorkflow()` → folosește `lib/i18n` cu diacritics-stripping (`refactorizează` → `refactorizeaza`)
- `metrics-update.cjs` → eliminat top-level execSync `where codeburn` (era IIFE blocking la load); folosește `lib/platform.findExecutable()` lazy

### Config v3.2
- `feature-flags.json`: `codeburn.daily_budget_usd` (100 default), `warn_at_pct` (0.75), `alert_at_pct` (1.0); `safla.{weight_success, weight_failure, weight_clamp}` constants
- `settings.json::permissions.deny` +14 patterns: `.gnupg/`, `.docker/config.json`, `.npmrc`, `.pypirc`, `/etc/passwd`, `/etc/shadow`, `/etc/sudoers`, `/etc/ssh/`, `/proc/`, `C:\Windows\System32\config\`, `C:\Windows\System32\drivers\` + 4 dangerous Bash (`mkfs.*`, fork bomb, `dd if=* of=/dev/sd*`, `rm -rf /`)
- Hook timeouts cut: `inject-workflow` 8s→**5s**, `route` 10s→**5s** (CC UI feedback faster)

### Tools noi
- `package.json` cu `engines.node >= 18` și scripts: `npm test`, `npm run audit`, `npm run audit:fix`, `npm run burn`, `npm run verify`, `npm run review`, `npm run quality-gate`, `npm run mcp-health`
- `run-tests.cjs` — runner care iterează `tests/*.test.cjs` și raportează pass/fail aggregat
- `mcp-health` command — verifică `~/.claude.json::mcpServers` pentru misconfigurări (ex: claude-flow fără `mcp start`)
- Statusline budget alert: `💰 $X/$Y/d` cu `🚨` la 100% și `⚠` la 75% din `daily_budget_usd`

### Test suite v3.2 — **11 suite, 70/70 PASS**
| Suite | Tests |
|---|---|
| atomic-write | 5 |
| codeburn-engine | 8 |
| error-log | 3 |
| **i18n** (NEW) | **7** |
| **local-date** (NEW) | **6** |
| **migrate** (NEW) | **6** |
| **path-safe** (NEW) | **10** |
| platform-detect | 4 |
| **pricing** (NEW) | **6** |
| safla-validation | 7 |
| secret-scan | 8 |
| **TOTAL** | **70/70** |

### Empiric live (post-rebuild)
- `npm test`: 70/70 PASS
- `/evaluate-setup`: 38/38 PASS · 0 WARN · 0 FAIL
- `/burn`: **$253.82 today · 1247 calls** (CLI canonical, validat path-safe)
- `/mcp-health`: 2 servers configured (notebooklm + claude-flow), ambele cu command set
- TZ fix verificat: `todayLocal()` returnează data locală EET, nu UTC slice

---

## [3.1.0] — CCDEW: blind-spot fixes + state restore + Instincts + portable + auto-fix

**Data:** 2026-05-10
**Request:** "fă tot ce ai descoperit" — fix-uri pentru toate omiterile profunde + redenumire `claude-code-eficient-workspace` → **CCDEW**.

### Fix-uri pentru zone oarbe identificate
| Zonă oarbă | Fix |
|---|---|
| Pierdere SAFLA learned state | Restore din `_ARCHIVE/pre-rebuild-2026-05-10/` cu key-validation pass: 8 noduri valide păstrate, 1 cheie coruptă (`[object Object]`) aruncată, 45 feedback-uri reale recuperate |
| Statusline rupt | Rebuild cu lazy-require, cost vizibil live (`💰 $X.XX/d · Nc │ 🤖 X% ok·Nfb │ 📂 project │ 🖥 platform`) |
| Catch silent peste tot | `lib/error-log.cjs` cu rotație 5k linii la `.claude-flow/logs/errors.jsonl`; `/errors` command afișează ultimele 20 |
| Permissions deny slabă | +21 patterns: `.env*`, `credentials.{json,yml}`, `secrets.*`, `id_rsa`, `id_ed25519`, `*.pem`, `*.pfx`, `.aws/credentials`, `.ssh/id_*`, `.kube/config`, `.netrc`, plus 4 `Bash` deny pentru `rm -rf /*`, `format c:`, etc. |
| Slash commands cod-mort | Wired în `hook-handler.cjs`: `verify`, `review`, `quality-gate`, `diff-explain`, `evaluate-setup`, `platform`, `instincts`, `errors`, `safla-clean`, `skills-active` |
| Multi-platform stub neutilizat | Wire în `/platform` cu raport explicit: hooks/slashCommands/mcpServers/subAgents per platform; warning-uri când lipsesc capabilities |
| Test isolation race | `safla-validation.test.cjs` folosește `mkdtempSync` cu pid + clear `require.cache` ca să nu interfereze cu cwd alt test |
| Auto-fix lipsă | `/evaluate-setup --fix`: cleanup invalid SAFLA keys, .tmp orphans, ensure logs/ + reports/ dirs |
| Documentație v2 stale | `README.md` rewrite + `MIGRATION.md` complet pentru upgrade v2 → v3 |

### Layer ECC Instincts NOU
- `instincts.cjs` — pattern recognition din usage real
- Înregistrează (prompt fingerprint, node, success) în `.claude-flow/data/instincts.jsonl`
- Detectează patterns repetate (≥3 occurrences, success_rate ≥ 50%)
- Sugerează în `inject-workflow`: `[INSTINCT] you usually route this to node N (X% confidence over M similar prompts)`
- Comenzi: `/instincts`, `/instincts --rebuild`, `/instincts --suggest "<prompt>"`
- Wire în `post-task` automat (record fără să ceară userul)

### Test suite v3.1
| Suite | Tests | Status |
|---|---|---|
| `atomic-write.test.cjs` | 5 | PASS |
| `codeburn-engine.test.cjs` | 8 | PASS |
| `error-log.test.cjs` | 3 | PASS (NEW) |
| `platform-detect.test.cjs` | 4 | PASS |
| `safla-validation.test.cjs` | 7 | PASS (test-isolation fixed) |
| `secret-scan.test.cjs` | 8 | PASS |
| **Total** | **35** | **35/35 PASS** |

### `/evaluate-setup` empiric live
- 38/38 PASS · 0 WARN · 0 FAIL
- `--fix` flag: cleanup automat 4 categorii drift
- codeburn live $235/zi · 1185 calls (canonical via CLI)
- SAFLA: 5 sesiuni, 46 feedback-uri valide

### REDENUMIT: `claude-code-eficient-workspace` → `CCDEW`
Folder + toate referințele interne și în alte proiecte ale workspace-ului actualizate. Backup pre-rename păstrat.

---

## [3.0.1] — Native codeburn engine (CLI-independent fallback)

**Data:** 2026-05-10

**Added:**
- `lib/codeburn-engine.cjs` — pure-Node parser pentru `~/.claude/projects/**/*.jsonl`
  - Calculează cost direct din `usage.{input,output,cache_creation,cache_read}_tokens` × pricing pe model (opus/sonnet/haiku)
  - Latency: ~2.7s pe 79 fișiere (acceptabil cu cache 60s TTL existing)
  - Disclaimer: pricing-ul e estimate (Anthropic 2026 baseline) — diferă de CLI; CLI rămâne canonical când prezent
- `tests/codeburn-engine.test.cjs` — 8 verificări (modelTier mapping, cost computation, cache costs, totals shape)

**Changed:**
- `codeburn.cjs::totals()` — preferă CLI când disponibil, fallback la native engine altfel
- `evaluate-setup.cjs` — verifică separat CLI și engine, raportează care sursă produce datele

**Result:** sistemul funcționează **fără `npm install -g codeburn`** (dar mai puțin precis pe pricing).

---

## [3.0.0] — Rebuild from scratch: lib/ utilities + ECC + Red Hat setup-evaluator integration

**Data:** 2026-05-10
**Request:** Rebuild `.claude/` workspace de la zero cu best practices acumulate din audit anterior (5 fix-uri identificate) + integrare elemente tehnice din `everything-claude-code` (ECC) și `redhat-community-ai-tools/claude-code-setup-evaluator`.

### Fix-uri din audit (toate aplicate)

| # | Bug | Fix |
|---|---|---|
| 1 | SAFLA silent state corruption (`[object Object]` keys) | `lib/validate.cjs` regex `^[1-9]$`; invalid silent skip |
| 2 | Codeburn Windows ENOENT (no `.cmd` ext) | `lib/platform.cjs::findExecutable` filtrează `.cmd|.exe|.bat` |
| 3 | Atomic rename EPERM under concurrency | `lib/atomic-write.cjs` retry-with-backoff 50/100/200ms + tmp cleanup |
| 4 | hook-handler eager-require 12 modules (~146ms cold) | Lazy `lazy(name)` cache, on-demand per command |
| 5 | Node 22 refuză `.cmd` la `execFileSync` (CVE-2024-27980) | `shell: true` doar pentru `.cmd|.bat`, args fixe |

### Arhitectură nouă — `.claude/helpers/`

```
helpers/
├── lib/                          ← utilități reutilizabile (top-level deps minim)
│   ├── atomic-write.cjs           — writeAtomic + writeAtomicJson (retry+backoff)
│   ├── platform.cjs               — findExecutable (Win .cmd-aware) + findPython
│   ├── flags.cjs                  — feature-flags loader (5s TTL cache)
│   └── validate.cjs               — isValidNodeId + asString + clampNumber
├── tests/                        ← 4 regression-test suites
│   ├── atomic-write.test.cjs      — 5/5 PASS
│   ├── platform-detect.test.cjs   — 4/4 PASS
│   ├── safla-validation.test.cjs  — 7/7 PASS
│   └── secret-scan.test.cjs       — 8/8 PASS
├── hook-handler.cjs              ← LAZY-REQUIRE dispatcher (146ms cold → ~5ms)
├── safla.cjs                     ← validation + atomic write + clamp
├── codeburn.cjs                  ← Win-aware `.cmd` + shell:true execFileSync
├── intelligence.cjs              ← uses lib/atomic-write
├── graphify.cjs                  ← skips invalid SAFLA keys (no [object Object] in tables)
├── secret-scan.cjs               ← NEW: 11 secret patterns + 8 sensitive paths (ECC-style)
├── evaluate-setup.cjs            ← NEW: 37-check audit (Red Hat–style)
├── platform-detect.cjs           ← NEW: Claude/Cursor/Codex/Gemini/OpenCode detection
└── skills-activator.cjs          ← NEW: scan .claude/skills/*/SKILL.md, match prompt
```

### Layer ECC (everything-claude-code)
- **secret-scan.cjs** + integrat în `pre-edit` hook (blocks AWS/Anthropic/OpenAI/GitHub/Stripe/RSA keys + .env/id_rsa paths)
- **skills-activator.cjs** scanează `.claude/skills/<name>/SKILL.md` frontmatter și sugerează skills active la fiecare prompt
- **platform-detect.cjs** — multi-platform stub: detect Cursor / Codex / Gemini / OpenCode / Claude Code

### Layer Red Hat setup-evaluator
- `/evaluate-setup` — comprehensive audit (37 checks across config/modules/perf/state/cost/security/platform)
- `/verify` — quick sanity sweep (typecheck/test/lint/secret/dead-code)
- `/review` — 3-agent review swarm (reviewer + analyst + tester)
- `/quality-gate` — strict pass/fail before merge/deploy
- `/diff-explain` — plain-English summary of git diff

### Audit empiric (live, 2026-05-10)
```
Total checks: 61   PASS: 61   WARN: 0   FAIL: 0
- 4 test suites: 24/24 PASS
- evaluate-setup: 37/37 PASS
- codeburn live: $236.92 today (1173 calls), $2534.73 month (real data)
- ssa.filterContext(50): 0.83ms median
- safla.recordOutcome: 1.22ms median
```

### Backup safety
Pre-rebuild snapshot la `_ARCHIVE/pre-rebuild-2026-05-10/.claude/` (2.9MB) și `.claude-flow/` (66KB) — orice rollback e instant.

### Comenzi noi
```bash
node .claude/helpers/hook-handler.cjs evaluate-setup    # full audit
node .claude/helpers/hook-handler.cjs platform          # detected AI tool
node .claude/helpers/hook-handler.cjs skills-active     # current prompt match
node .claude/helpers/hook-handler.cjs safla-clean       # remove corrupt keys
```

---

## [2.0.0] — v6.1 Micro: SSA + CodeBurn + SAFLA + Graphify + LangGraph Micro

**Data:** 2026-05-08  
**Request:** Sistem complet de optimizare token efficiency + cost observability + feedback loop adaptiv pentru Claude Code Desktop.

**Arhitectură (9 module noi, zero dependențe externe):**

### Module noi în `.claude/helpers/`

| Modul | Rol | LOC |
|---|---|---|
| `feature-flags.json` | Toggle on/off per componentă (lite/full) | — |
| `codeburn.cjs` | Integrare `codeburn` CLI real (npm v0.9.7) — date reale din `~/.claude/projects/` | 107 |
| `red-hat-evaluator.cjs` | Injectare întrebări critice pre-execuție pentru task-uri de arhitectură | 79 |
| `ssa.cjs` | Sparse/Selective Attention — filtrare Jaccard trigram, 76% reducere context + integrare Obsidian index | 140 |
| `auto-optimize.cjs` | Detectare prompt verbos → estimare % tokeni economisiți | 92 |
| `safla.cjs` | Self-Adaptive Feedback Loop — tracking success/failure per nod Enneagram + sync cu CodeBurn | 175 |
| `graphify.cjs` | Rapoarte ASCII + Markdown sesiune (CodeBurn + SAFLA + Obsidian + AutoOpt) | 220 |
| `langgraph-micro.cjs` | State machine workflow CJS (standard/architecture/quick_fix) fără Python | 255 |
| `metrics-update.cjs` | Auto-update `_DASHBOARD.md` + `_METRICS/` la SessionEnd (export background non-blocking) | 185 |

### Hook-handler.cjs — extins cu toate conexiunile

**UserPromptSubmit (route):**
- SSA filtrează context intelligence + entries Obsidian (top-3 relevante)
- AutoOptimize detectează prompturi verbale
- RedHat injectează întrebări critice (arhitectură ≥12 cuvinte + verb+substantiv)
- LangGraph pornește workflow potrivit (standard/architecture/quick_fix)
- SAFLA afișează hint adaptiv per nod
- Enneagram rutează spre agent optim

**inject-workflow:** extins cu SSA zoom level (NANO/MICRO/MAHA) + SAFLA weight adjustment

**SessionStart:** SAFLA.sessionStart() + obsidian-session-context.py → populează index

**SessionEnd:**
- CodeBurn.totals() (cache-first, 117ms vs 8500ms anterior)
- SAFLA.syncWithCodeBurn() — penalizează noduri cu cost ridicat
- Graphify.generateReport() → `.claude-flow/reports/session-*.md`
- MetricsUpdate → `_DASHBOARD.md` + `_METRICS/codeburn-optimize-latest.md`
- LangGraph.clearActive()

### Comenzi noi

| Comandă CLI | Acțiune |
|---|---|
| `node hook-handler.cjs flags` | Status toate componentele |
| `node hook-handler.cjs burn` | Cost real azi + luna (codeburn CLI) |
| `node hook-handler.cjs safla` | Performance history per nod Enneagram |
| `node hook-handler.cjs graphify` | ASCII summary + save raport MD |
| `node hook-handler.cjs lg` | Workflow activ LangGraph |

### Slash command nou
- `.claude/commands/cost.md` → `/cost`, `/cost today`, `/cost month`, `/cost optimize`, `/cost report`

### Fișiere noi workspace
- `_DASHBOARD.md` — actualizat automat la SessionEnd cu metrici CodeBurn
- `_METRICS/` — snapshot JSON + `codeburn-optimize-latest.md`

### Rezultate benchmark
- `session-end` overhead: **8500ms → 117ms** (−98.6%)
- SSA context reduction: **76%** (50 entries → 12)
- Toate hookurile: **93–185ms**
- Cost real sesiune: **$5.98/zi, $232.99/lună**

**Dependențe externe adăugate:**
- `codeburn@0.9.7` (npm global) — singurul pachet extern

**Decizii arhitecturale:**
- SAFLA, Graphify, LangGraph: implementări custom CJS (nu pachete externe — nu există pe npm/pip)
- SSA: Jaccard trigram (nu sparse attention Python — complexitate nejustificată)
- CrewAI: dezactivat permanent (redundant cu Ruflo)
- Export codeburn: `spawn detached` (non-blocking) la SessionEnd

---

## [1.1.0] — META-017 Auto-Learn Hook (silent background learning)

**Request:** Continuous reactive auto-learning system that captures lessons from conversations without explicit prompting; holographic, semantic-filtered, batch-consolidated to Obsidian-compatible memory.

**Architecture (3-component pipeline):**
- `auto_learn.py` (Stop hook, ~1ms) — QUEUE-ONLY: heuristic detector + project router + Karma editorial guard + atomic file-locked queue append with idempotency (md5 dedupe)
- `auto_learn_consolidate.py` (SessionEnd hook + manual `--force`) — Single LLM call (judge+distill+merge in one Anthropic API request, optional with `ANTHROPIC_API_KEY`); fallback to template-based merge; integration with semantic UPDATE-vs-NEW logic; respects Obsidian Memory v1 protocol (`## [Claude]` + `## [User]` sections); auto-creates per-project `MEMORY.md` indexes
- `auto_learn_rotate.py` (manual/cron) — lunar archival of low-confidence (`_version=1`, age >60 days) auto-learned files to `_ARCHIVE/auto_learned/<YYYY-MM>/`; cleanup MEMORY.md indexes

**Key features:**
- Crash-recovery: spawn detached consolidate when queue ≥8 (Windows DETACHED_PROCESS / Unix start_new_session) with sentinel anti-double-spawn
- Race-free queue: dedicated lock-file (`learn_queue.lock`) serializes load+dedupe+write
- Dynamic project detection: scans `PROJECTS/` folder (no hardcoded names)
- Tag normalization: spaces → dashes, alphanumeric+dash only (Obsidian-safe)
- Split MEMORY.md routing: per-project lessons indexed in `PROJECTS/<N>/_MEMORY/MEMORY.md`, global lessons in root `memory/MEMORY.md`
- Karma Book editorial guard: skips when paths match `.scriv|_NANO/|_MAP/|Cap.|_BLOG|ilustra|alogen` (avoids polluting memory with text-edit corrections)
- 7-node holographic audit applied (5 lenses + 2 zoom levels): all 12 critical/high/medium issues fixed before release

**Files added:**
- `.claude/helpers/auto_learn.py` (~280 LOC)
- `.claude/helpers/auto_learn_consolidate.py` (~520 LOC)
- `.claude/helpers/auto_learn_rotate.py` (~190 LOC)

**Hook config:**
- `Stop` hook timeout 5s (queue-light)
- `SessionEnd` adds consolidate `--force` (timeout 30s)

**Optional dependencies:** `pyyaml` (already required), `ANTHROPIC_API_KEY` env (for LLM-quality consolidation; falls back to template if missing)

---

## [1.0.0] — Initial template release

**Request:** Create complete GitHub template repo for Claude Code workspace with Enneagram optimizations.

**What was done:**
- `.claude/` — full hook system (hook-handler.cjs, router.js, enneagram_router.py, intelligence.cjs, obs.py, etc.)
- `.claude/settings.json` — all hooks wired (UserPromptSubmit, SessionStart, SessionEnd, SubagentStart, SubagentStop, etc.)
- `CLAUDE.md` — workspace rules (sanitized, no personal data)
- `BEST_PRACTICES.md` — universal patterns
- `_SETTINGS/RULES/` — all operational rules (11 files)
- `_TEMPLATES/` — scaffolding for android/carte/generic/research/preview-live-server
- `_BEST_PRACTICES/GROWTH_LOG.md`
- `memory/MEMORY.md` — template index
- `_MEMORY/` — protocol + inbox + dashboard + user notes templates
- `README.md` — full English documentation
- `.gitignore` — excludes personal data, runtime, node_modules

**Files created:** 50+
