# TODO — CCDEW (Claude Code Development Efficient Workspace)

## Session 2026-06-05 — betterbird msgview.html

### Request: Popup message_display_action pentru BetterBird CCDEW

- [x] Creat `betterbird-ccdew/msgview.html` — popup compact 320px
- [x] Auto-detect dark/light theme
- [x] Threat score bar + urgency badge + nature + domain + severity + specifics + action_hint
- [x] Snooze 24h / Dismiss → browser.storage.local (cheie subject|from|date)
- [x] Open Full Dashboard → http://127.0.0.1:8766
- [x] Loading spinner + empty state + error state
- [x] CHANGELOG + TODO actualizate

---

## Session 2026-06-05 — Dashboard v6 + App Mode + Systemd

### Request: Performanță dashboard + aplicație nativă + auto-start

- [x] Tiered cache architecture (rt/sys/svc/proj) — toate request-urile < 100ms
- [x] Subprocese separate pentru operații blocking (curl, git, Python)
- [x] 5 carduri noi: ALERTS, LAPTOP/htop, PROJECT STATUS, INFRA/PROXY, GIT, OBSIDIAN
- [x] Modal system — click orice → popup cu date reale
- [x] `brave-browser --app` mode — dashboard ca fereastră nativă fără UI browser
- [x] `.desktop` entry + icon SVG custom în meniu Zorin
- [x] Shortcut pe Desktop
- [x] `systemd --user` service `ccdew-dashboard.service` — auto-start la boot
- [x] `loginctl enable-linger` — pornire fără login grafic
- [x] File watcher integrat — restart automat la modificări cod/HTML
- [x] Script `~/.local/bin/ccdew-dashboard` cu fallback inteligent
- [x] Documentat în CHANGELOG v3.9.4
- [x] Email Dashboard BB: `/bb` cu butoane deschide + JS feedback (v3.9.5)
- [x] Email Dashboard BB: `/api/bb-open` returnează JSON, fără fallback greșit
- [x] Email Dashboard BB: subject/from fallback consistent în toate endpoint-urile
- [x] `/api/metrics/:tier` cu `?refresh=1` în dashboard-server (v3.9.6)
- [x] Hermes update v0.13.0 → v0.15.1 (617 commits, git pull + pip reinstall)
- [x] mbox daemon — email live sync la 30s polling pe 16 mbox-uri Betterbird
- [x] Email watch: câmpul date în L3, email_ref, subject/from în value (v3.9.7)
- [x] Email dashboard bb(): fetch() cu feedback verde/roșu în loc de window.open()
- [x] Decay temporal: emailuri >365d→no_deadline, >90d→this_week; 2022 emails=0 actionable
- [x] Auto-refresh selectiv 90s: fetch('/api/actionable') în loc de location.reload()
- [ ] Router port-forward (manual): TCP 443→9443, UDP 53→51820 la 192.168.99.1
- [ ] Swap reset: `sudo swapoff /dev/zram0 && sudo swapon /dev/zram0` (necesită terminal)

### Pending (viitor)
- [ ] Router port-forward `:443→9443` și `:53→51820` la Orange Smart 192.168.99.1
- [ ] Hermes update — 617 commits behind (`hermes update`)
- [ ] Swap 100% persistent — consideră mărire zram sau RAM upgrade
- [ ] Dashboard: endpoint `/api/metrics/<tier>` pentru refresh selectiv din browser

---

## Session 2026-05-12 — CCDEW v6.1 SLIM Finalization

### Request: Complete v6.1 SLIM implementation + verify Hermeneuticus compatibility

**Hermeneuticus rules adoption**
- [x] Evaluated: CHANGELOG/ TODO/ EPILOG — CCDEW has superset
- [x] Rules confirmed: 4 rules (CCDEW) vs 3 (Hermeneuticus) + 1 extra MEMORY CHECK

**Template sync audit**
- [x] android: CLAUDE.md IDENTICAL, BEST_PRACTICES.md IDENTICAL
- [x] generic: CLAUDE.md IDENTICAL, BEST_PRACTICES.md IDENTICAL
- [x] research: CLAUDE.md IDENTICAL, BEST_PRACTICES.md IDENTICAL
- [x] carte: CLAUDE.md IDENTICAL
- [x] preview-live-server: CLAUDE.md IDENTICAL, serve_md.py IDENTICAL

**enneagram_topology.md documentation**
- [x] Created `_MEMORY/enneagram_topology.md` — 9 types, arc weights, SSA scoring, SAFLA feedback

**Workspace sync**
- [x] CLAUDE.md: Updated date to 2026-05-12, added v6.1 SLIM + Enneagram Topology to workspace map
- [x] _DASHBOARD.md: Updated to v3.9.2

**Git push + tag**
- [x] git pull --rebase origin main
- [x] git push origin main
- [x] git tag v6.1-slim-baseline
- [x] git push origin v6.1-slim-baseline

**Remaining (optional)**
- [ ] .claude/helpers/feature-flags.json — commit v6.1 SLIM feature flags
- [ ] .claude/helpers/hook-handler.cjs — commit Ruflo + SOP integration
- [ ] .claude/helpers/ssa.cjs — commit 5D scoring
- [ ] .claude/helpers/ruflo.cjs — commit (new file)
- [ ] .claude/helpers/sop-engine.cjs — commit (new file)
- [ ] .claude/commands/profile.md — commit (new file)

---

## Session 2026-05-10

### Request: Full rebuild with best-practices + ECC + Red Hat setup-evaluator integration (v3.0 → v3.8 in single session)

**v3.0 — Rebuild from scratch**
- [x] Backup `.claude/` + `.claude-flow/` to `_ARCHIVE/pre-rebuild-2026-05-10/`
- [x] `lib/atomic-write.cjs` — retry-with-backoff (50/100/200ms) + tmp cleanup on final fail
- [x] `lib/platform.cjs` — findExecutable Win-aware (`.cmd|.exe|.bat` filter)
- [x] `lib/flags.cjs` — 5s TTL cache loader
- [x] `lib/validate.cjs` — isValidNodeId, asString, clampNumber
- [x] Rewrite `safla.cjs` — validation regex + atomic write + clamp
- [x] Rewrite `codeburn.cjs` — Win .cmd detection + shell:true (Node 22 CVE-2024-27980)
- [x] Patch `intelligence.cjs` — uses `lib/atomic-write`
- [x] Rewrite `graphify.cjs` — filters invalid SAFLA keys (no [object Object])
- [x] Rewrite `hook-handler.cjs` — LAZY require (146ms cold → ~5ms)
- [x] Add `secret-scan.cjs` — 11 patterns + 8 paths, integrated in pre-edit
- [x] Add `evaluate-setup.cjs` — 38-check Red Hat-style audit
- [x] Add `platform-detect.cjs` — Claude/Cursor/Codex/Gemini/OpenCode
- [x] Add `skills-activator.cjs` — scan SKILL.md, match prompt
- [x] 4 test suites: atomic-write (5/5), platform-detect (4/4), safla-validation (7/7), secret-scan (8/8) = 24/24 PASS

**v3.0.1 — Native codeburn fallback**
- [x] `lib/codeburn-engine.cjs` — pure-Node parser for `~/.claude/projects/**/*.jsonl`
- [x] codeburn.cjs prefers CLI when available, falls back to native engine
- [x] codeburn-engine.test.cjs (8/8 PASS)

**v3.1 — Blind-spot fixes + Instincts + folder rename**
- [x] Restore SAFLA learned state from backup (45 valid feedbacks recovered)
- [x] Statusline rebuild with lazy require + live cost visibility
- [x] `lib/error-log.cjs` — JSONL log with rotation (5k lines)
- [x] Permissions deny extended (+21 patterns)
- [x] Wire backend slash commands in hook-handler
- [x] `instincts.cjs` — pattern recognition (ECC layer)
- [x] `/evaluate-setup --fix` flag
- [x] Folder renamed `claude-code-eficient-workspace` → `CCEW` → `CCDEW`

**v3.2 — TZ + i18n + shell-safe + budget + tools**
- [x] `lib/local-date.cjs` — TZ-aware todayLocal/monthLocal
- [x] `lib/pricing.cjs` — centralized model pricing
- [x] `lib/migrate.cjs` — JSON migration framework
- [x] `lib/i18n.cjs` — RO+EN routing keywords
- [x] `lib/path-safe.cjs` — shell injection mitigation
- [x] Hook timeouts cut (route 10s→5s, inject 8s→5s)
- [x] feature-flags v3.2 + permissions +14 patterns
- [x] Tools: package.json, run-tests.cjs, mcp-health, statusline budget alert

**v3.3 — perf + redact + auto-triggers + meta-workspace + RO docs**
- [x] `lib/perf-baseline.cjs` — rolling 30-sample p95 + regression detect
- [x] `lib/redact.cjs` — PII scrubbing in error-log
- [x] `repositories/` Red Hat meta-workspace folder
- [x] `.claude/commands/research.md` — ECC research-first
- [x] Auto-triggers: git commit→/verify, git push→/quality-gate
- [x] SessionStart auto-audit (24h cadence)

**v3.4 — 5-zoom audit + auto-infer + auto-optimize**
- [x] `lib/auto-infer.cjs` — 5-zoom (Maha→Nano) workspace audit
- [x] `lib/auto-optimize.cjs` — safe NANO transforms + proposals for higher zooms
- [x] `/infer` and `/optimize` slash commands

**v3.5 — Stability 5-zoom + auto-learn + 7/10 round-4 zones**
- [x] `lib/jsdoc-validator.cjs` (zone 1)
- [x] npm audit in quality-gate (zone 2)
- [x] `lib/remote-backup.cjs` (zone 3)
- [x] `lib/strings.cjs` RO+EN UI dict (zone 4)
- [x] skills-usage tracking + deadSkills (zones 5+10)
- [x] `package-lock.json` (zone 8)
- [x] `lib/auto-learn.cjs` — dynamic threshold learning
- [x] `tests/stability-5zoom.test.cjs` — 10 cross-zoom interference tests

**v3.6 — skills-propose + /exit snapshot + /sessions-compare**
- [x] `lib/skills-propose.cjs` — GitHub Search API + strict mature filter + scaffold (no code copy)
- [x] `lib/session-snapshot.cjs` — full session capture
- [x] `/exit`, `/sessions-compare`, `/skills-propose` commands
- [x] SessionEnd auto-snapshot

**v3.7 — Python detection + skills fallback + NANO false-pos**
- [x] `findPython()` real-path probe (Windows Store alias bypass)
- [x] Skills description-overlap fallback when no triggers field
- [x] NANO false-positive eliminated (block-comment-aware regex)
- [x] `tests/python-smoke.test.cjs` — 7 .py files validated

**v3.8 — Round 5 zones netouched: file-lock + bench + i18n hot-paths**
- [x] `lib/file-lock.cjs` — cross-process O_EXCL lock with stale detection
- [x] `tests/cross-claude-race.test.cjs` — 200/200 outcomes survive 2 fork() processes
- [x] `tests/file-lock.test.cjs` — 6/6 PASS
- [x] `/bench` command + auto-record at SessionEnd
- [x] `t()` integrated for `codeburn.unavailable` hot-path
- [x] DEBT documented: zones 1+2 (split intelligence + hook-handler) deferred

**Documentation refresh**
- [x] CHANGELOG.md rewritten in clean English
- [x] README.md with live v3.8.0 metrics, English-only
- [x] CREDITS.md — comprehensive attribution per source
- [x] MIGRATION.md — v2.0 → v3.x upgrade guide in English
- [x] ARCHITECTURE.md — 5-zoom architecture map in English
- [x] _MEMORY/_DASHBOARD.md — evolution table v3.0 → v3.8
- [x] _MEMORY/decisions/INDEX.md + 10 decisions in English
- [x] _MEMORY/sessions/ — Obsidian MD auto-generated at /exit + SessionEnd

**GitHub push**
- [x] Stage all changes (96 files, +8621/-2801)
- [x] Commit v3.8.0 with detailed message + Co-Authored-By
- [x] Push origin/main (auto-redirected to Hermeneuticus-of-things)
- [x] Update remote URL to new location
- [x] Cleanup: remove README.ro.md, rewrite all RO content in EN

### Optional (remaining)
- [ ] Claude Code restart to activate MCP claude-flow (post-v3.1 fix)
- [ ] Install onnxruntime-node in `<workspace>/ruflo/` for vector embeddings
- [ ] Eventual split of intelligence.cjs + hook-handler.cjs (DEBT — see decisions/008)
- [ ] CCDEW_LANG full propagation (currently only codeburn.unavailable uses t())

---

## Session 2026-05-08 — predecessor v2.0 (claude-code-eficient-workspace)

### Request: v6.1 Micro — SSA + CodeBurn + SAFLA + Graphify + LangGraph + holographic connections
- [x] Created `feature-flags.json` — toggle per component
- [x] Created `codeburn.cjs` — real codeburn CLI integration (npm v0.9.7)
- [x] Created `red-hat-evaluator.cjs` — pre-execution critical evaluation
- [x] Created `ssa.cjs` — Jaccard context filtering + Obsidian index
- [x] Created `auto-optimize.cjs` — verbose-prompt detection
- [x] Created `safla.cjs` — adaptive feedback loop + CodeBurn sync
- [x] Created `graphify.cjs` — ASCII + Markdown session reports
- [x] Created `langgraph-micro.cjs` — CJS state machine workflow
- [x] Created `metrics-update.cjs` — `_DASHBOARD.md` + `_METRICS/` auto
- [x] Extended `hook-handler.cjs` — all modules connected
- [x] Extended `inject-workflow` — SSA zoom + SAFLA weight hint
- [x] Extended `session-restore` — SAFLA + Obsidian auto-populate
- [x] Extended `session-end` — CodeBurn + SAFLA sync + Graphify + Metrics
- [x] Fixed `session-end` performance: 8500ms → 117ms
- [x] Created `.claude/commands/cost.md` — `/cost` slash command
- [x] Created `_DASHBOARD.md` — auto-updated
- [x] Created `_METRICS/` — snapshots + optimize suggestions
- [x] Installed `codeburn@0.9.7` global (npm)
- [x] Updated `CHANGELOG.md` to v2.0.0
- [x] Created complete `README.md` for new users

### Remaining (optional)
- [x] `git init` + push to Hermeneuticus repo (done in v3.8)
- [ ] Testing on a real project (Consiliu)
- [ ] KNOWN_PROJECTS in obsidian-session-context.py (add "consiliu")

---

## Session 2026-05-01 — initial template

### Request: Create template repo
- [x] Create directory structure
- [x] Copy/adapt .claude/helpers/ files
- [x] Create settings.json (sanitized)
- [x] Create CLAUDE.md (generic)
- [x] Copy BEST_PRACTICES.md
- [x] Copy _SETTINGS/RULES/
- [x] Copy _TEMPLATES/
- [x] Create memory/MEMORY.md template
- [x] Create _MEMORY/ structure
- [x] Create README.md
- [x] Create .gitignore
- [x] Initialize git + initial commit
