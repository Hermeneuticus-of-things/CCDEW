# CHANGELOG — CCDEW (Claude Code Development Efficient Workspace)

> Format reference: [`_SETTINGS/CHANGELOG-FORMAT.md`](_SETTINGS/CHANGELOG-FORMAT.md)
> Folder renamed in v3.1: `claude-code-eficient-workspace` → `CCEW` → `CCDEW`.
> See [`CREDITS.md`](CREDITS.md) for full source attribution.

---

## [4.2.0] — 2026-06-05 — betterbird-ccdew: msgview.html popup pentru message_display_action

### Request
Creare `betterbird-ccdew/msgview.html` — popup inline în toolbar-ul de citire email BetterBird.

### Decizii
- Vanilla JS, fără ES6+ module syntax (compatibilitate MV2/Thunderbird)
- Auto-detect dark/light theme via `prefers-color-scheme`
- Threat score bar (1-4 nivele cu culori distincte)
- Urgency badge, nature, life_domain, severity, specifics (max 2), action_hint
- Snooze 24h + Dismiss salvate în `browser.storage.local` (aceeași schemă ca sidebar.html)
- "Open Full Dashboard" → `browser.tabs.create({url: 'http://127.0.0.1:8766'})`
- Loading spinner pe durata fetch-ului

### Fișiere modificate
- `betterbird-ccdew/msgview.html` — creat

---

## [4.1.0] — 2026-06-05 — CCDEW v3.1.0: messageDisplayAction + context menu

### Request
Better BB symbiosis — CCDEW integrat în UI-ul nativ BB.

### Implementat
1. `message_display_action` — buton în toolbar-ul de citire email, popup msgview.html
2. `matchAlert` handler în background.js
3. Context menu pe lista de mesaje
4. `msgview.html` — mini-card cu threat score, snooze/dismiss inline

### Fișiere modificate
- betterbird-ccdew/manifest.json — v3.1.0
- betterbird-ccdew/background.js — matchAlert + context menu
- betterbird-ccdew/msgview.html — NOU

---

## [4.0.2] — 2026-06-05 — BetterBird fix configurare extensie: popup + descriptor + status

### Probleme rezolvate
1. **`browser_action` fără `default_popup`** — click pe butonul din toolbar nu deschidea nimic
   - Fix: adăugat `"default_popup": "sidebar.html"` în manifest.json
2. **`status: null` și `descriptor: null`** în extensions.json — BB nu știa calea extensiei
   - Fix: setat `status=4`, `descriptor=<cale reală>` în extensions.json
3. Versiune incrementată → `3.0.3`

### NU schimba fără testare
- `manifest.json` → `browser_action.default_popup` trebuie să rămână `"sidebar.html"`
- `extensions.json` → `status=4`, `descriptor` cu calea absolută, `active=true`
- `user.js` → cele 3 pref-uri pentru extensii nesemnate trebuie să existe

### Fișiere modificate
- `betterbird-ccdew/manifest.json` — adăugat `default_popup`, versiune 3.0.3
- `.thunderbird/.../extensions.json` — descriptor + status reparate

---

## [4.0.1] — 2026-06-05 — BB Email Dashboard: Rezolvare conturi + Documentare stare stabilă

### Request
Salvare stare stabilă a proiectului BB Email Dashboard pentru a nu se strica pe viitor.
Rezolvare: câmpul `account` afișa "Gmail N" în loc de adresa reală.

### Stare curentă — STABILĂ ✅
- `http://localhost:8766/` — Dashboard dark UI complet funcțional
- `http://localhost:8766/api/impact-alerts` — 50 alerte live cu câmpuri complete
- `ccdew-email-dashboard.service` — enabled + running, restart automat
- Extensie BetterBird `ccdew-email-intelligence@ccdew` v3.0.2 — activă
- Autostart la login: BetterBird + Dashboard (`.config/autostart/`)
- Smoke tests: 5/5 ✅

### Ce NU trebuie schimbat fără testare
- `email-dashboard-server.py` — `resolve_account()` + `_build_account_map()` (mapare conturi)
- `email-dashboard.html` — UI complet cu modal, search, stats, sort
- `betterbird-ccdew/sidebar.html` — aceleași câmpuri ca dashboard-ul web
- `ccdew-email-dashboard.service` + wrapper `ccdew-email-dashboard-start.sh`
- `email-accounts-registry.json` — sursa mapărilor cont → adresă email

### Rezolvare account "Gmail N"
- Problemă: `account` = "Gmail 1", "Gmail 2" etc. (nume intern BetterBird)
- Cauză: `betterbird-cache-reader.py` stochează numele IMAP dir, nu adresa
- Soluție: `_build_account_map()` în server citește `email-accounts-registry.json`
  și construiește maparea `"Gmail N" → adresă reală` per provider (Gmail/GMX/Proton/etc.)
- Funcționează pentru orice provider — primul cont = fără număr, al doilea = 1, etc.

### Proton Mail — statusul integrării
- Proton Bridge NU e instalat → emailurile Proton nu sunt indexate
- Codul suportă deja Proton în mapare — când se instalează Bridge și se adaugă în BB,
  va apărea automat ca `matei@protonmail.com` (sau adresa reală)
- Pași instalare: vezi mesajul din sesiunea 2026-06-05

### Fișiere modificate
- `CCDEW/.claude/helpers/email-dashboard-server.py` — `_build_account_map()` + `resolve_account()`
- `CCDEW/.claude/helpers/email-dashboard.html` — UI v4.0: search, stats clickabile, modal, sort, prev/next, clipboard
- `CCDEW/betterbird-ccdew/sidebar.html` — UI v4.0: carduri compacte + modal popup

---

## [4.0.0] — 2026-06-05 — BB Email Dashboard: Modal popup interactiv per email

### Request
UI interactiv — clic pe card deschide popup cu toate detaliile emailului.

### Decizii
- Carduri compacte în listă: icon, urgency, nature badge, subiect, expeditor, action hint
- Clic pe card → modal overlay animat cu detalii complete
- Modalul conține: urgency+severity+nature badges, subiect, label, expeditor+dată+cont, specifics (bullet list complet), action hint, butoane
- Butoane modal: Deschide BB / Arhivează / Amână (condițional) / Închide
- Închidere: buton ✕, clic pe overlay, tasta ESC
- Focus management: focus pe butonul ✕ la deschidere, ESC global
- `alertsIndex[]` — array local cu obiectele alerte pentru acces rapid din modal
- CSS complet pentru modal, carduri compacte, animații, focus-visible, reducedMotion

### Fișiere modificate
- `betterbird-ccdew/sidebar.html` — rewrite complet cu modal popup

## [3.9.9] — 2026-06-05 — BB Email Dashboard: Redesign carduri email cu câmpuri reale API

### Request
UI sidebar.html — fiecare card de alertă să afișeze mult mai multe informații: expeditor, natură, deadline-uri/limite, specifice.

### Decizii
- Cardurile foloseau câmpuri inexistente (`phishing_risk`, `priority_score`, `time_sensitive`, `entities.amounts`) — înlocuite cu câmpurile reale ale API-ului
- Câmpuri noi afișate: `from` (expeditor), `label` (descriere), `specifics[]` (bullet list), `action_hint` (acțiune recomandată), `nature_label`+`family` (badges), `date`, `account`+`severity` (meta)
- Filtrul `phishing` reparat: verifică `a.nature==='phishing'` în loc de `a.phishing_risk==='HIGH'`
- Butoane: `snooze` apare la urgency immediate/today (nu `time_sensitive==='yes'`)
- CSS nou: `.label-desc`, `.from-row`, `.from-addr`, `.date-val`, `.specifics-list`, `.action-hint`, `.nature-badge`, `.family-badge`, `.phishing-badge`
- CSS vechi eliminat: `.ts-badge`, `.entity-tag`, `.phish-warn`, `.priority`, `.specific`
- Sync automat în BetterBird via `ccdew-bb-sync-ext.sh`

### Fișiere modificate
- `betterbird-ccdew/sidebar.html` — rewrite complet `renderAlerts()` + CSS carduri

### [3.9.8] — 2026-06-05 — BB Email Dashboard: Audit complet + 26 fix-uri + Suite teste + Autostart

### Request
Audit complet UX/UI + cod + teste multi-nivel + pornire automată Zorin OS pentru proiectul betterbird-ccdew.

### Decizii
- Serviciu canonic `ccdew-email-dashboard.service` cu wrapper anti-conflict-port
- Extensie BetterBird sincronizată automat via `ccdew-bb-sync-ext.sh`
- Suită de teste 3-tier: unit (34) + frontend static + integration HTTP (38 total, 100%)
- Script master `ccdew-bb-start` (start / --fix / --status)

### Fișiere modificate/create
- `betterbird-ccdew/sidebar.html` — 13 fix-uri UX/JS/CSS/accesibilitate
- `betterbird-ccdew/manifest.json` — eliminat messagesUpdate, adăugat CSP
- `betterbird-ccdew/background.js` — recursie subfoldere, skip spam/junk/trash
- `betterbird-ccdew/install-addon.sh` — eliminat messagesUpdate din userPermissions
- `.claude/helpers/email-dashboard-server.py` — thread safety, CORS OPTIONS, path traversal, throttle
- `~/.config/systemd/user/ccdew-email-dashboard.service` — Conflicts, StartLimitBurst
- `~/.local/bin/ccdew-email-dashboard-start.sh` — wrapper anti-conflict port
- `~/.local/bin/ccdew-bb-sync-ext.sh` — sync sursă → extensie + extensions.json
- `~/.local/bin/ccdew-bb-start` — script master start/fix/status
- `~/.config/autostart/ccdew-betterbird.desktop` — autostart BB la login
- `betterbird-ccdew/tests/` — 3 fișiere test Python + runner bash

### Versiune
3.9.8

---

## [3.9.4] — 2026-06-05 — Dashboard v6: Tiered Cache + App Mode + Systemd + Auto-restart

### CCDEW Dashboard v6 — Refactorizare completă performanță + UX

#### Performanță — Tiered Cache Architecture
- **4 tier-uri de refresh independente** via subprocese separate (non-blocking):
  - `rt` 5s — cost, SSA, SAFLA, session, memory (file reads)
  - `sys` 8s — htop CPU per-core, procese, temperaturi, swap (Python subprocess)
  - `svc` 30s — proxy health, servicii up/down, disk/RAM, intelligence (curl + net)
  - `proj` 90s — git log, obsidian scan, CHANGELOG/TODO, hermes version
- **Toate request-urile < 100ms** (față de 3-13s anterior)
- Subprocese `child_process.spawn` — event loop Node.js nu mai e blocat niciodată
- Cache pre-warmat la startup staggered (1s/3s/5s) pentru first-load instant

#### Carduri noi adăugate în Dashboard
- 🔴 **ALERTS** — critical/warn/info automate (Swap%, Disk%, Temp, Hermes behind, TODO)
- 💻 **LAPTOP** — htop-style: CPU cores bars, top 12 procese, swap, temp, agenți, servicii
- 📋 **PROJECT STATUS** — CHANGELOG versiuni recente + TODO pending/done
- 🔌 **INFRA/PROXY** — Anthropic Proxy :8082, Claude-Mem MCP :37700, Hermes skills/memories
- 🌿 **GIT ACTIVITY** — CCDEW + Open-Cload: ultimele 5 commit-uri, uncommitted changes
- 🧠 **OBSIDIAN** — scan `_MEMORY/`: 31 fișiere .md, user-profile preview

#### Mod aplicație nativă
- `brave-browser --app=http://localhost:8765/dashboard` — fereastră fără UI browser
- `.desktop` entry: `~/.local/share/applications/ccdew-dashboard.desktop`
- Icon SVG custom: dark theme, CPU bars, cost curve, litera C Claude
- Shortcut pe Desktop + apare în meniu Zorin ca "CCDEW Dashboard"
- Script `~/.local/bin/ccdew-dashboard` cu auto-start server dacă nu rulează

#### Auto-start + Auto-restart
- **systemd user service** `ccdew-dashboard.service` — pornire la boot
- `loginctl enable-linger think` — pornește chiar fără login grafic
- **File watcher** integrat în server — detectează modificări `dashboard-server.cjs` / `dashboard.html`, `process.exit(0)` → systemd `Restart=on-failure` repornește automat
- Interval watcher: 2s

#### Fix-uri anterioare (din sesiunea precedentă)
- `process.chdir(CCDEW_ROOT)` — fix SAFLA/SSA care citeau din directorul greșit
- `getSSAStats()` cu fallback la `ssa-stats.json` pe disk (date persistente între restart-uri)
- `getIntelligenceDirect()` — citire directă `graph-state.json` (310 noduri / 24525 edges)
- `budget_pct: NaN` → fix `(data.daily_budget || 100)` ca fallback
- Modal system complet — click orice card → popup cu date reale detaliate
- Toate componentele (Red Hat, Graphify, Project Scope, etc.) au modal cu date reale
- Indicator `⚡ Xms · rt:Xs sys:Xs svc:Xs proj:Xs` în topbar pentru transparență cache

### Fișiere modificate
- `Open-Cload/.opencode/dashboard-server.cjs` — refactorizare majoră
- `Open-Cload/.opencode/dashboard.html` — carduri noi + modal system + cache hint
- `.claude/helpers/agent-harness.cjs` — NOU: OODA loop + benchmarking + observation contract
- `~/.local/share/applications/ccdew-dashboard.desktop` — NOU
- `~/.local/share/icons/hicolor/256x256/apps/ccdew-dashboard.svg` — NOU
- `~/.local/bin/ccdew-dashboard` — NOU
- `~/.config/systemd/user/ccdew-dashboard.service` — NOU

### Comenzi utile
```bash
systemctl --user status ccdew-dashboard   # stare
systemctl --user restart ccdew-dashboard  # restart manual
journalctl --user -u ccdew-dashboard -f   # log live
ccdew-dashboard                           # lansează fereastra app
```

---

## [3.9.5] — 2026-06-05 — Email Dashboard BB Integration Fix

### Email Dashboard (:8766) — Fix complet integrare Betterbird

#### `/bb` endpoint — rescris complet
- **Butoane „✉ Deschide în Betterbird"** per rând (doar emailurile cu email_ref)
- JS minim inline — `fetch('/api/bb-open?q=KEY')` cu feedback vizual (#status)
- Feedback: „Se deschide..." → „Deschis în Betterbird ✓" (verde) sau „Nu s-a găsit .eml" (roșu)
- Până la 50 rânduri (față de 20 anterior)
- **Fix fallback subject/from** — același lanț de fallback ca `load_index()`:
  `raw.subject → entry.subject → raw.summary → entry.summary → '(fără subiect)'`

#### `/api/bb-open` — fix critic
- **Eliminat fallback la ultimul .eml modificat** (deschidea emailul greșit)
- Returnează acum **JSON** în loc de text plain
  - `{"ok": true, "eml": "/path/to/file.eml"}` la succes
  - `{"ok": false, "error": "no .eml found", "hint": "rulează ccdew-email-refresh"}` la lipsă
- Căutare în 2 pași: ref exact (`{ref}-*.eml`) → suffix key (`*{suffix}*.eml`) → eroare clară
- `hint` în răspuns explică ce trebuie făcut

#### `/` (pagina principală) — fix subject/from
- Același lanț de fallback consistent aplicat în `light[]` pentru JSON dat front-end-ului

### Fișiere modificate
- `.claude/helpers/email-dashboard-server.py` — `/bb`, `/api/bb-open`, `light[]` fallback

---

## [3.9.6] — 2026-06-05 — Pending items: metrics/tier + Hermes update + mbox daemon

### Dashboard `/api/metrics/:tier`
- **Nou endpoint** `GET /api/metrics/{rt|sys|svc|proj}` — returnează doar tier-ul cerut
- **`?refresh=1`** — forțează refresh imediat, așteaptă max 6s și returnează datele proaspete
- Răspuns: `{tier, age, data, timestamp}` — util pentru refresh selectiv din browser sau scripturi
- `global._ccdewRefresh` expune funcțiile `runSys/runSvc/runProj` pentru trigger extern

### Hermes Agent update
- **v0.13.0 → v0.15.1** (617 commits instalați cu `git pull --rebase origin main`)
- pip absent din venv: reparat cu `ensurepip` + reinstalare pachet
- 158 skills disponibile (față de un număr mai mic anterior)

### mbox daemon — email live sync
- **`~/.local/bin/ccdew-mbox-daemon.py`** — NOU
  - Polling 30s pe 16 mbox-uri Betterbird (`ImapMail/`)
  - Detectează modificări mtime → rulează `ccdew-email-watch.py` → notifică `:8766/api/webhook`
  - Log: `~/.local/state/ccdew-mbox-daemon.log`
- **`~/.config/systemd/user/ccdew-mbox-watcher.service`** — NOU, enabled + active
- Email-urile noi apar în dashboard în < 30s după ce Betterbird le descarcă din IMAP

### Fișiere create/modificate
- `Open-Cload/.opencode/dashboard-server.cjs` — `/api/metrics/:tier` + `global._ccdewRefresh`
- `~/.local/bin/ccdew-mbox-daemon.py` — NOU
- `~/.config/systemd/user/ccdew-mbox-watcher.service` — NOU

---

## [3.9.7] — 2026-06-05 — Email Dashboard: 4 fix-uri calitate UI + date

### A) `ccdew-email-watch.py` — câmpul `date` în L3
- `batch` entries primesc `date` din header-ul email real (Date:), normalizat la `YYYY-MM-DD`
- `store_memory()` acceptă `dates=` și scrie `date`, `subject`, `from`, `account` în `val`
- `email_ref` scris în JSON de nivel superior (nu doar în `value`)
- Emailuri noi indexate vor apărea corect în statisticile „azi / săptămâna / luna"

### B) `email-dashboard.html` — `bb()` cu `fetch()` și feedback vizual
- Înlocuit `window.open()` cu `fetch('/api/bb-open?q=...')`
- Buton „Deschide în Betterbird" feedback: verde ✓ la succes, roșu ✗ cu mesaj la eroare
- Fallback timeout 3-4s și resetare automată a butonului

### C) Decay temporal — emailuri vechi nu mai apar ca „immediate"
- `_age_days()` extinde fallback la `createdAt` (timestamp indexare) când câmpul `date` lipsește
- Reguli decay: >365 zile → `no_deadline`, >90 zile → `this_week`, >30 zile (non-critical) → `today`
- `is_actionable()` folosește `eff_urgency` (cu decay) în loc de `urgency` brut
- **Rezultat verificat**: emailuri 2022 → 0 actionable (toate 193 degradate corect)

### D) Auto-refresh selectiv — fără `location.reload()`
- `setInterval(90s)` face `fetch('/api/actionable?limit=200')` și re-renderizează lista
- Păstrează: scroll, filtre active, text căutat, panel detalii deschis
- Live dot clipire verde la fiecare refresh reușit
- Nu întrerupe dacă user scrie în search sau are panel deschis

### Fișiere modificate
- `~/.local/bin/ccdew-email-watch.py` — date + email_ref în L3
- `.claude/helpers/email-dashboard.html` — `bb()` fetch + auto-refresh selectiv
- `.claude/helpers/email-dashboard-server.py` — `_age_days()`, `effective_urgency()`, `is_actionable()`

---

## [3.9.3] — 2026-05-12 — SSA Token Metrics + Devcontainer + GitHub Actions + Scheduled Tasks + Dashboard v5

### SSA Efficiency Fix
- **Token metrics added:** entries, chars, tokens (all three measured)
- **New API:** `resetStats()`, `getRawStats()`, detailed `getSSAEfficiency()`
- **Per-call metrics:** avg_entries_per_call, avg_tokens_saved_per_call
- **Real-world expectation:** 25-35% token reduction (diverse content), 60-80% (homogeneous)

### Dashboard v5
- **Complete rewrite** — all 12 sections explicit: Audit, Metrics, Modules, Hooks, Commands, Feature Flags, SOP Engine, Enneagram, MCP, Templates, Obsidian, Tests, Security
- **Quick Reference** — all commands in one place
- **5-Zoom Canon** — audit levels documented
- **Template sync** — all 7 templates with status

### Scheduled Tasks Support
- Added `ScheduledTask` hook → `hook-handler scheduled-task`
- Added `LoopTask` hook → `hook-handler loop-task`
- Both show SAFLA/SSA/CodeBurn status

### Files Added
- `_TEMPLATES/devcontainer/devcontainer.json`
- `_TEMPLATES/devcontainer/README.md`
- `_TEMPLATES/github-workflows/ccdew-quality-gate.yml`
- `_TEMPLATES/github-workflows/README.md`
- `_TEMPLATES/opencode-desktop/APP.md` — OpenCode Desktop mobile dashboard (ASCII UI)
- `_TEMPLATES/opencode-desktop/README.md` — OpenCode Desktop integration guide
- `.opencode.json` — OpenCode Desktop config for CCDEW

### Files Modified
- `.claude/helpers/ssa.cjs` — weights tuned for better efficiency
- `.claude/helpers/feature-flags.json` — top_k reduced per profile
- `.claude/helpers/hook-handler.cjs` — +scheduled-task, +loop-task handlers
- `.claude/settings.json` — +ScheduledTask +LoopTask hook events

---

## [3.9.2] — 2026-05-12 — enneagram_topology.md + Template Sync Audit + GitHub Comparison

### Highlights
- **Template Audit Complete** — All 5 templates verified byte-for-byte identical with Hermeneuticus upstream
- **enneagram_topology.md** — documented CCDEW's enneagram adaptive topology system
- **_DASHBOARD.md v4** — enhanced with live audit results, SOP commands, auto-profile rules, benchmark table, template sync status
- **GitHub Comparison Audit** — compared CCDEW with shanraisshan (52k stars), cretiq, language-specific workspaces. CCDEW is the only self-hosting workspace with: Enneagram 9-node routing, SAFLA cost-aware feedback, 5D SSA, Auto-Profile, SOP Engine, 22 test suites, 38-check Red Hat evaluator

### Files Added
- `_MEMORY/enneagram_topology.md` — full documentation: types, stress/growth arrows, arc topology, SSA scoring, SAFLA integration, JSON format
- `_MEMORY/AUDIT-GITHUB-COMPARISON.md` — comprehensive audit + GitHub comparison (CCDEW vs 3 repos)

---

## [3.9.1] — 2026-05-12 — SOP Engine + Auto-Profile + MetaGPT patterns

### Highlights
- **SOP Engine** (`sop-engine.cjs`) — MetaGPT-style Standard Operating Procedures with 5 pre-built SOPs: refactor, audit, multi-file-refactor, research, security-audit
- **Auto-Profile Switching** — Automatic profile switch based on daily budget usage (>90% → ssa-max, >75% → lite)
- **SOP Commands** — `sop list`, `sop <name>`, `sop-execute <name>`
- **Enhanced inject-workflow** — Auto-profile check + Ruflo swarm init + SOP suggestion

### Files Added
- `.claude/helpers/sop-engine.cjs` — SOP engine with 5 default workflows
- `.claude/helpers/ruflo.cjs` — Updated with federation functions

### Tests
- `sop list`: 5 SOPs available
- `sop-execute audit`: 4 phases completed
- `evaluate-setup`: **37/37 PASS**

---

## [3.9.0] — 2026-05-12 — v6.1 SLIM Implementation Complete

### Highlights
- **SSA Layer Enhanced** — 5-dimensional scoring (semantic, enneagram, holographic, recency, pinned) replaces simple Jaccard
- **Ruflo Integration** — Complete MCP wrapper with `swarmInit()`, `agentSpawn()`, `memoryStore()`, `federation*()` functions
- **Feature Profiles** — 3 modes: Lite (3/13 components), Full (13/13), SSA-Max (9/13 with aggressive filtering)
- **Auto-swarm in inject-workflow** — Complex tasks (3+ agents) auto-trigger `ruflo.swarmInit()`
- **Profile switch command** — `/profile lite|full|ssa-max` for instant mode switching

### Components Added/Modified
| File | Change |
|---|---|
| `.claude/helpers/ssa.cjs` | Enhanced 5D scoring + `getSSAEfficiency()` |
| `.claude/helpers/feature-flags.json` | Added profiles + ruflo component |
| `.claude/helpers/ruflo.cjs` | New — 10 Ruflo MCP functions |
| `.claude/helpers/hook-handler.cjs` | +ruflo integration, +profile, +ruflo-status |
| `.claude/commands/profile.md` | New — `/profile` command docs |

### Metrics
- `evaluate-setup`: **37/37 PASS**
- `bench`: SSA 1.31ms, SAFLA 0.77ms
- SSA Efficiency: **~40%** (tokens_saved/total, target <25%)
- Profile modes: 3 available (lite/full/ssa-max)

### Tests
- 22 suites · **147/147 PASS** · 0 FAIL

---

## [3.8.1] — 2026-05-10 — System audit + AgentDB sync + honor bridge patch

### Highlights
- **WASM fix** — `sql-wasm.wasm` lipsea din cache `2ed56890` → copiat din `09002f`; AgentDB operațional
- **AgentDB sync** — 25 fișiere memorie (Obsidian + auto-memory) → 26 entries în AgentDB
- **bridge agent patch** — 2 buguri rezolvate: `h_status` crash pe `str.get()` + `[HEALTH]`/`[SECURITY:]` false-dispatch
- **Status audit** — raport complet toate prioritățile → `_MEMORY/sessions/` + GitHub

### Fișiere modificate
- `.npm/_npx/2ed56890c96f58f7/node_modules/sql.js/dist/sql-wasm.wasm` (copiat)
- `~/.claude/bridge/coop_agent.py` (patch aplicat)
- `_MEMORY/consiliu_qnapgx_proiect.md` (creat)
- `memory/project_consiliu_qnapgx.md` (creat)
- `_MEMORY/sessions/audit-2026-05-10.md` (creat)

---

## [3.8.0] — 2026-05-10 — Round 5 zone netouched: cross-process file-lock + bench + i18n

### Highlights
- **Cross-process race condition fix** — 2 parallel `fork()` processes writing SAFLA used to lose 50% of writes. New `lib/file-lock.cjs` with O_EXCL + retry-with-backoff guarantees 200/200 outcomes survive.
- **`/bench` command + auto-record at SessionEnd** — measures hot-path timings, alerts on regression > baseline p95 × 1.5.
- **i18n hot-path** — `t()` integrated for `codeburn.unavailable` message; `CCDEW_LANG=ro` partially propagated.

### Decisions
- Zones 1+2 (split `intelligence.cjs` 979L and `hook-handler.cjs` 1024L) deferred as **DEBT** — HIGH risk regression, 0 user-visible benefit. Documented in `_MEMORY/decisions/008-debt-structural-split.md`.

### Tests
- 22 suites · **147/147 PASS** · 0 FAIL
- New: `tests/file-lock.test.cjs` (6/6), `tests/cross-claude-race.test.cjs` (1/1)

---

## [3.7.0] — 2026-05-10 — Python detection + skills description fallback + NANO false-pos

### Highlights
- **Python `findPython()` real-path probe** — Windows Store alias `python3.exe` was triggering "Python was not found" promo and exit non-zero. Fix: probe with `-V`, return resolved path only on `Python X.Y` output.
- **Skills description-overlap fallback** — when SKILL.md has no `triggers` field, fall back to ≥2 word overlap with `description`. 33 skills now activatable.
- **NANO false-positive eliminated** — auto-infer no longer flags TODO/FIXME inside `/* */` block comments or string literals.
- **`tests/python-smoke.test.cjs`** — `ast.parse()` syntax check on all 7 Python helpers.

### Tests
- 20 suites · **140/140 PASS**

---

## [3.6.0] — 2026-05-10 — Skills-propose (GitHub mature search) + /exit session snapshot + /sessions-compare

### New modules
- `lib/skills-propose.cjs` — GitHub Search API + strict mature filter (≥10 stars, allowed licenses, push <365d, !archived) + scaffold generator (frontmatter only, no code copy).
- `lib/session-snapshot.cjs` — full session capture (cost+SAFLA+instincts+skills+perf+audit+errors+workspace) → JSON.

### New commands
- `/skills-propose <keyword>` — list mature candidates from GitHub
- `/skills-propose <keyword> --scaffold <local-name>` — generate `.claude/skills/<name>/SKILL.md` with attribution
- `/exit` — manual snapshot
- `/sessions-compare N` — diff across last N sessions

### Auto-trigger
- `session-end` hook now auto-saves snapshot on every Claude Code session close.

### Tests
- 19 suites · **133/133 PASS**

---

## [3.5.0] — 2026-05-10 — Stability 5-zoom + auto-learn + 7/10 round 4 zones repaired

### Repairs
| # | Zone | Solution |
|---|---|---|
| 1 | JSDoc absent | `lib/jsdoc-validator.cjs` |
| 2 | npm audit not wrapped | added in `quality-gate.cjs` |
| 3 | `_ARCHIVE/` local-only | `lib/remote-backup.cjs` warns on missing remote |
| 4 | i18n EN-only | `lib/strings.cjs` with RO+EN dict + env switch |
| 5 | Dead skill detection | `usageStats()` + `deadSkills()` + auto-track |
| 8 | No reproducibility | `package-lock.json` generated |
| 10 | Skill execution feedback | tracking auto on every `activateForPrompt()` |

Zones 6, 7, 9 skipped with documented rationale.

### New modules
- `lib/auto-learn.cjs` — dynamic threshold learning from audit history
- 5-zoom stability test suite (concurrency MACRO, stress MEZZO, fuzz MICRO, encoding NANO)

### Tests
- 17 suites · **114/114 PASS**

---

## [3.4.0] — 2026-05-10 — 5-zoom audit (Maha→Nano) + auto-infer + auto-optimize

### New modules
- `lib/auto-infer.cjs` — scans workspace at 5 zoom levels, deduces gaps without explicit user request
- `lib/auto-optimize.cjs` — applies safe NANO transforms automatically (BOM strip, CRLF→LF, trim trailing); MICRO/MEZZO/MACRO/MAHA proposal-only

### 5-zoom canon established
| Zoom | Scope |
|---|---|
| MAHA | Whole-system goal alignment |
| MACRO | Cross-module structure |
| MEZZO | Per-module cohesion |
| MICRO | Per-function complexity |
| NANO | Per-line/char hygiene |

See `_MEMORY/decisions/007-5-zoom-canon.md`.

### Tests
- 15 suites · **98/98 PASS**

---

## [3.3.0] — 2026-05-10 — perf-baseline + PII redact + auto-triggers + meta-workspace + RO docs

### Highlights
- `lib/perf-baseline.cjs` — rolling 30-sample p95 with regression detection
- `lib/redact.cjs` — automatic PII scrubbing in `error-log.cjs` (emails, JWT, API keys, home paths)
- `migrate()` framework wired into `safla.cjs::load()` — version chain v1.0→v2.0
- `repositories/` — Red Hat–style meta-workspace folder pattern
- `.claude/commands/research.md` — ECC research-first dev mode
- Auto-triggers: `git commit` → `/verify`; `git push` → `/quality-gate`; SessionStart → audit at 24h cadence

### Tests
- 13 suites · **86/86 PASS**

---

## [3.2.0] — 2026-05-10 — Adversarial round 2: TZ + i18n + shell-safe + budget + tools

### New `lib/` modules
| Module | Purpose |
|---|---|
| `lib/local-date.cjs` | TZ-aware `todayLocal()` / `monthLocal()` — non-UTC users no longer lose 2-4h "today" |
| `lib/pricing.cjs` | Centralized model pricing (PRICING_VERSION='2026.05'), single source of truth |
| `lib/migrate.cjs` | JSON migration framework with version chain + safety limit (32 steps) |
| `lib/i18n.cjs` | RO + EN routing keywords with diacritics-stripping |
| `lib/path-safe.cjs` | Shell injection mitigation: rejects `& ; \| $ ( ) ' " ! * ? \r \n` |

### Refactors
- `codeburn-engine.cjs` uses `lib/pricing` + `lib/local-date`, removed 17 hardcoded lines
- `codeburn.cjs::fetchRealStatus()` validates path with `isSafeBinaryPath()` before exec
- `hook-handler.cjs::selectWorkflow()` uses `lib/i18n` with diacritics stripping
- `metrics-update.cjs` no longer calls top-level `execSync` — uses `lib/platform.findExecutable()` lazy

### Config v3.2
- `feature-flags.json::codeburn.daily_budget_usd` (100 default), `warn_at_pct` (0.75), `alert_at_pct` (1.0)
- `settings.json::permissions.deny` +14 patterns (`.gnupg/`, `.docker/config.json`, `.npmrc`, `.pypirc`, `/etc/passwd`, `/etc/shadow`, `/etc/sudoers`, `/etc/ssh/`, `/proc/`, `C:\Windows\System32\config\`, `C:\Windows\System32\drivers\`) + dangerous Bash blocks (`mkfs.*`, fork bomb, `dd if=* of=/dev/sd*`, `rm -rf /`)
- Hook timeouts cut: `inject-workflow` 8s → 5s, `route` 10s → 5s

### Tools
- `package.json` with `engines.node >= 18` + 8 npm scripts
- `run-tests.cjs` — runner iterating `tests/*.test.cjs`
- `mcp-health` command — verifies `~/.claude.json::mcpServers` for misconfigurations
- Statusline budget alert: `💰 $X/$Y/d` with `🚨@100%` and `⚠@75%`

### Tests
- 11 suites · **70/70 PASS**

---

## [3.1.0] — 2026-05-10 — Blind-spot fixes + state restore + Instincts + auto-fix + folder rename CCEW→CCDEW

### Repairs from earlier audit blind spots
| Blind spot | Fix |
|---|---|
| SAFLA learned state lost in rebuild | Restored from `_ARCHIVE/pre-rebuild-2026-05-10/` with key validation: 8 valid nodes kept, 1 corrupt key (`[object Object]`) dropped, 45 real feedbacks recovered |
| Statusline broken | Rebuilt with lazy-require, live cost visible (`💰 $X.XX/d · Nc │ 🤖 X% ok·Nfb │ 📂 project │ 🖥 platform`) |
| Silent catches everywhere | `lib/error-log.cjs` with rotation (5k lines) at `.claude-flow/logs/errors.jsonl`; `/errors` command shows last 20 |
| Permissions deny weak | +21 patterns: `.env*`, `credentials.{json,yml}`, `secrets.*`, `id_rsa`, `id_ed25519`, `*.pem`, `*.pfx`, `.aws/credentials`, `.ssh/id_*`, `.kube/config`, `.netrc`, plus 4 `Bash` deny |
| Slash commands as dead code | Wired in `hook-handler.cjs`: `verify`, `review`, `quality-gate`, `diff-explain`, `evaluate-setup`, `platform`, `instincts`, `errors`, `safla-clean`, `skills-active` |
| Multi-platform stub unused | Wired in `/platform` with explicit capability report |
| Test isolation race | `safla-validation.test.cjs` uses `mkdtempSync` with pid + clear `require.cache` |
| Auto-fix missing | `/evaluate-setup --fix` resolves: invalid SAFLA keys, .tmp orphans, missing logs/, missing reports/ |
| v2 docs stale | `README.md` rewrite + `MIGRATION.md` complete for v2 → v3 upgrade |

### New ECC layer: Instincts
- `instincts.cjs` — pattern recognition from real usage
- Records `(prompt fingerprint, node, success)` in `.claude-flow/data/instincts.jsonl`
- Detects repeated patterns (≥3 occurrences, success_rate ≥ 50%)
- Suggests in `inject-workflow`: `[INSTINCT] you usually route this to node N (X% confidence over M similar prompts)`
- Auto-wired in `post-task` (records without explicit user request)

### Folder renamed
`claude-code-eficient-workspace/` → `CCEW/` → `CCDEW/` (final).

### Tests
- 6 suites · **35/35 PASS**

---

## [3.0.1] — 2026-05-10 — Native codeburn engine (CLI-independent fallback)

### Added
- `lib/codeburn-engine.cjs` — pure-Node parser for `~/.claude/projects/**/*.jsonl`
  - Computes cost directly from `usage.{input,output,cache_creation,cache_read}_tokens` × per-model pricing (opus/sonnet/haiku)
  - Latency: ~2.7s on 79 files (acceptable with 60s TTL cache)
  - Disclaimer: pricing is an estimate; CLI is canonical when present
- `tests/codeburn-engine.test.cjs` — 8 checks (modelTier mapping, cost computation, cache costs, totals shape)

### Changed
- `codeburn.cjs::totals()` — prefers CLI when available, falls back to native engine otherwise
- `evaluate-setup.cjs` — verifies CLI and engine separately, reports which source produces the data

### Result
System works **without `npm install -g codeburn`** (less precise on pricing).

### Tests
- 5 suites · **32/32 PASS**

---

## [3.0.0] — 2026-05-10 — Rebuild from scratch: lib/ utilities + ECC + Red Hat setup-evaluator integration

### Audit fixes (all applied)
| # | Bug | Fix |
|---|---|---|
| 1 | SAFLA silent state corruption (`[object Object]` keys) | `lib/validate.cjs` regex `^[1-9]$`; invalid silent skip |
| 2 | Codeburn Windows ENOENT (no `.cmd` ext) | `lib/platform.cjs::findExecutable` filters `.cmd|.exe|.bat` |
| 3 | Atomic rename EPERM under concurrency | `lib/atomic-write.cjs` retry-with-backoff 50/100/200ms + tmp cleanup |
| 4 | hook-handler eager-require 12 modules (~146ms cold) | Lazy `lazy(name)` cache, on-demand per command |
| 5 | Node 22 refuses `.cmd` at `execFileSync` (CVE-2024-27980) | `shell: true` only for `.cmd|.bat`, fixed args |

### New architecture under `.claude/helpers/`
```
helpers/
├── lib/                          ← reusable utilities
├── tests/                        ← regression test suites
├── hook-handler.cjs              ← LAZY-REQUIRE dispatcher
├── safla.cjs                     ← validation + atomic write + clamp
├── codeburn.cjs                  ← Win-aware `.cmd` + shell:true execFileSync
├── secret-scan.cjs               ← NEW: 11 secret patterns + 8 sensitive paths (ECC-style)
├── evaluate-setup.cjs            ← NEW: 38-check audit (Red Hat–style)
├── platform-detect.cjs           ← NEW: Claude/Cursor/Codex/Gemini/OpenCode detection
└── skills-activator.cjs          ← NEW: scans .claude/skills/*/SKILL.md
```

### ECC layer (everything-claude-code)
- `secret-scan.cjs` integrated in `pre-edit` hook (blocks AWS/Anthropic/OpenAI/GitHub/Stripe/RSA keys + sensitive paths)
- `skills-activator.cjs` scans `.claude/skills/<name>/SKILL.md` frontmatter and suggests active skills per prompt
- `platform-detect.cjs` — multi-platform stub: Cursor / Codex / Gemini / OpenCode / Claude Code

### Red Hat setup-evaluator layer
- `/evaluate-setup` — comprehensive audit (38 checks across config, modules, performance, state, cost, security, platform)
- `/verify` — quick sanity sweep (typecheck/test/lint/secret/dead-code)
- `/review` — 3-agent review swarm (reviewer + analyst + tester)
- `/quality-gate` — strict pass/fail before merge/deploy
- `/diff-explain` — plain-English summary of git diff

### Live audit (2026-05-10)
- 4 test suites: 24/24 PASS
- evaluate-setup: 38/38 PASS
- codeburn live: $5.98/d ~~(estimated reproducible — actually varies per machine)~~
- ssa.filterContext(50): 0.83ms median
- safla.recordOutcome: 1.22ms median

### Backup safety
Pre-rebuild snapshot at `_ARCHIVE/pre-rebuild-2026-05-10/.claude/` (2.9MB) and `.claude-flow/` (66KB) — instant rollback available.

---

## [2.0.0] — 2026-05-08 — v6.1 Micro: SSA + CodeBurn + SAFLA + Graphify + LangGraph Micro

**Request:** Complete token-efficiency optimization system + cost observability + adaptive feedback loop for Claude Code Desktop.

### Architecture (9 new modules, zero external deps except codeburn)

| Module | Role | LOC |
|---|---|---|
| `feature-flags.json` | Toggle on/off per component (lite/full) | — |
| `codeburn.cjs` | Real `codeburn` CLI integration (npm v0.9.7) | 107 |
| `red-hat-evaluator.cjs` | Inject critical questions before architecture tasks | 79 |
| `ssa.cjs` | Sparse/Selective Attention — Jaccard trigram filter, 76% context reduction | 140 |
| `auto-optimize.cjs` | Verbose-prompt detection → estimated token savings | 92 |
| `safla.cjs` | Self-Adaptive Feedback Loop — track success/failure per Enneagram node + sync with CodeBurn | 175 |
| `graphify.cjs` | ASCII + Markdown session reports (CodeBurn + SAFLA + Obsidian + AutoOpt) | 220 |
| `langgraph-micro.cjs` | CJS state machine workflow (standard/architecture/quick_fix), no Python | 255 |
| `metrics-update.cjs` | Auto-update `_DASHBOARD.md` + `_METRICS/` at SessionEnd (background non-blocking export) | 185 |

### Hook-handler.cjs — extended with all wirings

**UserPromptSubmit (route):**
- SSA filters intelligence context + Obsidian entries (top-3 relevant)
- AutoOptimize detects verbose prompts
- RedHat injects critical questions (architecture ≥12 words + verb+noun)
- LangGraph starts matching workflow (standard/architecture/quick_fix)
- SAFLA shows adaptive hint per node
- Enneagram routes to optimal agent

**inject-workflow:** extended with SSA zoom level (NANO/MICRO/MAHA) + SAFLA weight adjustment

**SessionStart:** SAFLA.sessionStart() + obsidian-session-context.py → populates index

**SessionEnd:**
- CodeBurn.totals() (cache-first, 117ms vs 8500ms previously)
- SAFLA.syncWithCodeBurn() — penalizes high-cost nodes
- Graphify.generateReport() → `.claude-flow/reports/session-*.md`
- MetricsUpdate → `_DASHBOARD.md` + `_METRICS/codeburn-optimize-latest.md`
- LangGraph.clearActive()

### New commands

| CLI command | Action |
|---|---|
| `node hook-handler.cjs flags` | Status of all components |
| `node hook-handler.cjs burn` | Real cost today + month (codeburn CLI) |
| `node hook-handler.cjs safla` | Performance history per Enneagram node |
| `node hook-handler.cjs graphify` | ASCII summary + save MD report |
| `node hook-handler.cjs lg` | Active LangGraph workflow |

### New slash command
- `.claude/commands/cost.md` → `/cost`, `/cost today`, `/cost month`, `/cost optimize`, `/cost report`

### New workspace files
- `_DASHBOARD.md` — auto-updated at SessionEnd with CodeBurn metrics
- `_METRICS/` — JSON snapshot + `codeburn-optimize-latest.md`

### Benchmark results
- `session-end` overhead: **8500ms → 117ms** (−98.6%)
- SSA context reduction: **76%** (50 entries → 12)
- All hooks: **93–185ms**

### External dependencies added
- `codeburn@0.9.7` (npm global) — sole external package

### Architectural decisions
- SAFLA, Graphify, LangGraph: custom CJS implementations (no npm/pip equivalents)
- SSA: Jaccard trigram (not Python sparse attention — complexity not justified)
- CrewAI: permanently disabled (redundant with Ruflo)
- Codeburn export: `spawn detached` (non-blocking) at SessionEnd

---

## [1.1.0] — 2026-05-04 — META-017 Auto-Learn Hook (silent background learning)

**Request:** Continuous reactive auto-learning system that captures lessons from conversations without explicit prompting; holographic, semantic-filtered, batch-consolidated to Obsidian-compatible memory.

### Architecture (3-component pipeline)
- `auto_learn.py` (Stop hook, ~1ms) — QUEUE-ONLY: heuristic detector + project router + Karma editorial guard + atomic file-locked queue append with idempotency (md5 dedupe)
- `auto_learn_consolidate.py` (SessionEnd hook + manual `--force`) — Single LLM call (judge+distill+merge in one Anthropic API request, optional with `ANTHROPIC_API_KEY`); fallback to template-based merge; integration with semantic UPDATE-vs-NEW logic; respects Obsidian Memory v1 protocol (`## [Claude]` + `## [User]` sections); auto-creates per-project `MEMORY.md` indexes
- `auto_learn_rotate.py` (manual/cron) — monthly archival of low-confidence (`_version=1`, age >60 days) auto-learned files to `_ARCHIVE/auto_learned/<YYYY-MM>/`; cleanup MEMORY.md indexes

### Key features
- Crash recovery: spawn detached consolidate when queue ≥8 (Windows DETACHED_PROCESS / Unix start_new_session) with sentinel anti-double-spawn
- Race-free queue: dedicated lock-file (`learn_queue.lock`) serializes load+dedupe+write
- Dynamic project detection: scans `PROJECTS/` folder (no hardcoded names)
- Tag normalization: spaces → dashes, alphanumeric+dash only (Obsidian-safe)
- Split MEMORY.md routing: per-project lessons indexed in `PROJECTS/<N>/_MEMORY/MEMORY.md`, global lessons in root `memory/MEMORY.md`
- Karma Book editorial guard: skips when paths match `.scriv|_NANO/|_MAP/|Cap.|_BLOG|illustration|alogen` (avoids polluting memory with text-edit corrections)
- 7-node holographic audit applied (5 lenses + 2 zoom levels): all 12 critical/high/medium issues fixed before release

### Files added
- `.claude/helpers/auto_learn.py` (~280 LOC)
- `.claude/helpers/auto_learn_consolidate.py` (~520 LOC)
- `.claude/helpers/auto_learn_rotate.py` (~190 LOC)

### Hook config
- `Stop` hook timeout 5s (queue-light)
- `SessionEnd` adds consolidate `--force` (timeout 30s)

### Optional dependencies
- `pyyaml` (already required), `ANTHROPIC_API_KEY` env (for LLM-quality consolidation; falls back to template if missing)

---

## [1.0.0] — 2026-05-01 — Initial template release

**Request:** Create complete GitHub template repo for Claude Code workspace with Enneagram optimizations.

### What was done
- `.claude/` — full hook system (hook-handler.cjs, router.js, enneagram_router.py, intelligence.cjs, obs.py, etc.)
- `.claude/settings.json` — all hooks wired (UserPromptSubmit, SessionStart, SessionEnd, SubagentStart, SubagentStop, etc.)
- `CLAUDE.md` — workspace rules (sanitized, no personal data)
- `BEST_PRACTICES.md` — universal patterns
- `_SETTINGS/RULES/` — all operational rules (11 files)
- `_TEMPLATES/` — scaffolding for android/book/generic/research/preview-live-server
- `_BEST_PRACTICES/GROWTH_LOG.md`
- `memory/MEMORY.md` — template index
- `_MEMORY/` — protocol + inbox + dashboard + user notes templates
- `README.md` — full English documentation
- `.gitignore` — excludes personal data, runtime, node_modules

### Files created
50+
