---
name: CCDEW Memory Dashboard
description: Live overview of CCDEW v6.1 SLIM — evaluation, state, metrics, commands, hooks, templates
type: reference
tags: [dashboard, session-start, ccdew, evolution, v6.1-slim]
project: ccdew
priority: critical
_version: 5
_created: 2026-05-10
_modified: 2026-05-12
_modified_by: claude
related: [_INBOX.md, _PROTOCOL.md, _USER_NOTES.md, enneagram_topology.md, AUDIT-GITHUB-COMPARISON.md]
---

# CCDEW v6.1 SLIM — Dashboard

> Auto-updated at `/exit` and SessionEnd. Full state of the workspace at a glance.

---

## VERSION

**CCDEW v3.9.3** — 2026-05-12 — SSA Token Metrics + Devcontainer + GitHub Actions + Scheduled Tasks

---

## AUDIT RESULTS (run: `node .claude/helpers/evaluate-setup.cjs`)

### Overall

| Metric | Value |
|---|---|
| Total checks | 37 |
| PASS | 37 |
| WARN | 0 |
| FAIL | 0 |
| Test suites | 22 |
| Tests | 147/147 PASS |
| SSA Efficiency | target <25% — see Metrics section |

### By Suite

| Suite | Checks | Result | Files Checked |
|---|---|---|---|
| A. CONFIGURATION | 8 | OK | settings.json, feature-flags.json, permissions (40 deny patterns) |
| B. MODULES | 10 | OK | hook-handler, ssa, safla, codeburn, ruflo, sop-engine, instincts, secret-scan, red-hat, graphify |
| C. PERFORMANCE | 6 | OK | SSA 1.31ms, SAFLA 0.77ms, hook overhead <200ms |
| D. STATE | 5 | OK | safla.json, instincts.json, decisions/INDEX.md, memory/ |
| E. COST | 4 | OK | CodeBurn $764/luna, 9759 apeluri, budget alerts wired |
| F. SECURITY | 4 | OK | secret-scan 11 patterns, permissions 40 deny, shell injection mitigated |
| G. CROSS-PLATFORM | 3 | OK | linux, Python /usr/bin/python3, Node /usr/bin/node |

---

## METRICS (live)

### SSA Efficiency

```
node .claude/helpers/ssa.cjs → getSSAEfficiency()
```

| Metric | Value | Target | Status |
|---|---|---|---|
| entries.total | auto | — | — |
| entries.saved | auto | — | — |
| entries.ratio | X% | — | — |
| chars.total | auto | — | — |
| chars.saved | auto | — | — |
| chars.ratio | X% | — | — |
| **tokens.ratio** | X% | **<25%** | **OK/BELOW_TARGET** |
| avg_tokens_saved_per_call | auto | — | — |
| calls | auto | — | — |

### SAFLA

```
node .claude/helpers/safla.cjs stats
```

| Metric | Value |
|---|---|
| sessions | 30 |
| feedbacks | 23 |
| efficiency | ~40% (target <25%) |
| sync with CodeBurn | active |

### CodeBurn

```
node .claude/helpers/hook-handler.cjs burn
```

| Metric | Value |
|---|---|
| daily budget | $100 (default) |
| today cost | live |
| month cost | $764/luna |
| apeluri | 9759 |
| CLI available | yes |
| native fallback | yes |
| latency | 117ms (cache-first) |

### Benchmarks

| Component | Latency | Target | Status |
|---|---|---|---|
| SSA filter | 1.31ms | <5ms | OK |
| SAFLA feedback | 0.77ms | <2ms | OK |
| session-end overhead | 117ms | <200ms | OK |
| hook-handler lazy | <5ms | <10ms | OK |

---

## MODULES (22 lib/ + 33 helpers/)

### lib/ — 22 utilities (no external deps)

| Module | Purpose |
|---|---|
| atomic-write.cjs | Retry-with-backoff JSON write |
| file-lock.cjs | O_EXCL cross-process lock |
| flags.cjs | Feature flags loader (5s TTL cache) |
| validate.cjs | Node ID validation, clamp, asString |
| migrate.cjs | JSON migration framework |
| platform.cjs | findExecutable Win-aware |
| path-safe.cjs | Shell injection mitigation |
| error-log.cjs | JSONL log with rotation 5k lines |
| redact.cjs | PII scrubbing |
| perf-baseline.cjs | Rolling 30-sample p95 |
| codeburn-engine.cjs | Native cost parser (no CLI) |
| pricing.cjs | Model pricing (PRICING_VERSION 2026.05) |
| local-date.cjs | TZ-aware today/month |
| strings.cjs | RO+EN UI dictionary |
| i18n.cjs | RO+EN routing keywords |
| auto-infer.cjs | 5-zoom workspace audit |
| auto-optimize.cjs | Safe NANO transforms |
| auto-learn.cjs | Dynamic threshold learning |
| jsdoc-validator.cjs | JSDoc presence check |
| remote-backup.cjs | Remote backup warnings |
| skills-propose.cjs | GitHub search + scaffold generator |
| session-snapshot.cjs | Full session capture (JSON + Obsidian MD) |

### helpers/ — 33 top-level modules

| Module | Category | Status |
|---|---|---|
| hook-handler.cjs | Dispatcher | 19 commands |
| ssa.cjs | Context | 5D scoring + token metrics |
| safla.cjs | Adaptive | Cost-aware feedback loop |
| codeburn.cjs | Cost | CLI + native engine |
| ruflo.cjs | MCP | swarmInit, agentSpawn, federation |
| sop-engine.cjs | Workflow | 5 MetaGPT-style SOPs |
| instincts.cjs | Learning | Pattern recognition >=3 occurrences |
| secret-scan.cjs | Security | 11 patterns + 8 paths |
| red-hat-evaluator.cjs | Quality | Critical questions for architecture |
| graphify.cjs | Reporting | ASCII + MD session reports |
| evaluate-setup.cjs | Audit | 38-check Red Hat evaluator |
| statusline.cjs | UI | Live budget + SAFLA display |
| langgraph-micro.cjs | Workflow | State machine |
| intelligence.cjs | Memory | PageRank + trigram similarity |
| obs.py | Memory | Obsidian CLI (PyYAML, zero-MCP) |
| auto_learn.py | Learning | Queue-only queue append |
| auto_learn_consolidate.py | Learning | LLM distill + merge |
| auto_learn_rotate.py | Learning | Monthly archival |
| router.js | Routing | Multi-strategy routing |
| enneagram_router.py | Routing | 9-node personality routing |
| enneagram_compose.py | Routing | Enneagram composition |
| session.js | Lifecycle | Session management |
| auto-memory-hook.mjs | Lifecycle | ESM memory sync |
| run-tests.cjs | Testing | Test runner |
| platform-detect.cjs | Platform | Claude/Cursor/Codex/Gemini/OpenCode |
| metrics-update.cjs | Reporting | Dashboard auto-update |
| skills-activator.cjs | Skills | Skill auto-suggest |
| verify.cjs | Quality | Typecheck/test/lint/secret |
| review.cjs | Quality | 3-agent review swarm |
| quality-gate.cjs | Quality | Strict pass/fail |
| diff-explain.cjs | Quality | Plain-English diff |
| obsidian-session-context.py | Memory | Session context importer |
| workspace_node_map.json | Config | Workflow templates |

---

## HOOKS (13 events)

```
cat .claude/settings.json → hooks
```

| Event | Matcher | Handler | Timeout |
|---|---|---|---|
| UserPromptSubmit | — | inject-workflow | 5s |
| UserPromptSubmit | — | route | 5s |
| PreToolUse | Bash | pre-bash | 5s |
| PreToolUse | Write/Edit/MultiEdit | pre-edit | 5s |
| PostToolUse | Write/Edit/MultiEdit | post-edit | 10s |
| PostToolUse | Bash | post-bash | 5s |
| SessionStart | — | session-restore | 15s |
| SessionStart | — | auto-memory-hook import | 8s |
| SessionStart | — | auto-audit | 10s |
| SessionEnd | — | session-end | 10s |
| Stop | — | auto-memory-hook sync | 10s |
| Stop | — | auto_learn.py | 5s |
| PreCompact | manual | compact-manual | — |
| PreCompact | manual | compact-save | 5s |
| PreCompact | auto | compact-auto | — |
| PreCompact | auto | compact-save | 5s |
| SubagentStart | — | status | 3s |
| SubagentStop | — | post-task | 5s |
| Notification | — | notify | 3s |
| ScheduledTask | — | scheduled-task | 30s |
| LoopTask | — | loop-task | 60s |

---

## COMMANDS (19 hook-handler + 7 slash + 3 npm)

### hook-handler commands

```bash
node .claude/helpers/hook-handler.cjs <command>
```

| Command | Action |
|---|---|
| inject-workflow | Enneagram routing + SOP suggestion |
| route | Intelligence context routing |
| pre-bash | Secret scan + git gates |
| pre-edit | Secret scan check |
| post-edit | Instincts + intelligence recording |
| post-bash | SAFLA outcome recording |
| post-task | SAFLA + instincts + langgraph advance |
| session-restore | Restore previous session |
| session-end | Full session archival |
| compact-save | Pre-compact save |
| compact-manual | Manual compaction |
| compact-auto | Auto compaction |
| status | Status reporting |
| notify | Notification handler |
| burn | Codeburn cost reporting |
| flags | Feature flags display |
| graphify | Generate ASCII/MD reports |
| safla | SAFLA stats |
| lg | LangGraph workflow |
| evaluate-setup | Full 38-check audit |
| verify | Typecheck/test/lint/secret |
| review | 3-agent review swarm |
| quality-gate | Strict pass/fail |
| diff-explain | Plain-English diff |
| platform | Platform capabilities |
| skills-active | Active skills list |
| safla-clean | Clean corrupted SAFLA keys |
| instincts | Instincts pattern report |
| errors | Last 20 errors from log |
| profile | Profile lite/full/ssa-max |
| ruflo-status | Ruflo MCP health |
| sop | List/load SOP |
| sop-execute | Execute SOP workflow |
| scheduled-task | Scheduled task status |
| loop-task | Loop task status |

### slash commands

```
/<command> from .claude/commands/*.md
```

| Command | Source | Action |
|---|---|---|
| /cost | cost.md | cost today/month/optimize |
| /profile | profile.md | lite/full/ssa-max switch |
| /sop | — | via hook-handler |
| /sop list | — | via hook-handler |
| /sop-execute | — | via hook-handler |
| /evaluate-setup | — | via hook-handler |
| /verify | — | via hook-handler |
| /exit | — | via hook-handler |

### npm scripts

```bash
npm run <script>
```

| Script | Action |
|---|---|
| npm test | Run all test suites |
| npm run audit | Run evaluate-setup |
| npm run verify | Run verify.cjs |
| npm run quality-gate | Run quality-gate.cjs |
| npm run burn | Run codeburn totals |

---

## FEATURE FLAGS (13 components, 3 profiles)

```
cat .claude/helpers/feature-flags.json
```

### Components

| Component | Default | Purpose |
|---|---|---|
| enneagram | true | 9-node routing |
| ssa | true | 5D context filtering |
| codeburn | true | Cost tracking |
| red_hat | true | Critical questions |
| safla | true | Adaptive feedback |
| graphify | true | ASCII reports |
| langraph | true | State machine |
| project_scope | true | Project isolation |
| intelligence | true | PageRank context |
| auto_optimize | true | NANO transforms |
| instincts | true | Pattern learning |
| secret_scan | true | Secret detection |
| ruflo | true | MCP integration |

### Profiles

| Profile | Components | SSA top_k | SSA min_score |
|---|---|---|---|
| lite | 3/13 | 3 | 0.35 |
| full | 13/13 | 8 | 0.10 |
| ssa-max | 9/13 | 6 | 0.30 |

### Auto-Profile Switch

| Budget | Profile |
|---|---|
| >90% daily | ssa-max |
| >75% daily | lite |
| <75% daily | full |

---

## SOP ENGINE (5 workflows)

```
node .claude/helpers/hook-handler.cjs sop list
node .claude/helpers/hook-handler.cjs sop-execute <name>
```

| SOP | Phases | Agents | Purpose |
|---|---|---|---|
| refactor | Analyze → Plan → Execute → Verify → Commit | reviewer, coder | Code refactoring |
| audit | Gather → Analyze → Report | auditor, analyst | Code audit |
| multi-file-refactor | Scan → Prioritize → Refactor → Validate | scanner, refactorer | Multi-file changes |
| research | Question → Search → Synthesize → Report | researcher | Research task |
| security-audit | Scan → Analyze → Prioritize → Report | security-agent | Security review |

---

## ENNEAGRAM ROUTING (9 nodes)

### Types

| # | Name | HEXAD/TRIANGLE | Stress | Growth |
|---|---|---|---|---|
| 1 | Reformer | HEXAD | 4 | 7 |
| 2 | Helper | HEXAD | 8 | 4 |
| 3 | Achiever | TRIANGLE | 9 | 6 |
| 4 | Individualist | HEXAD | 2 | 1 |
| 5 | Investigator | HEXAD | 7 | 8 |
| 6 | Loyalist | TRIANGLE | 3 | 9 |
| 7 | Enthusiast | HEXAD | 1 | 5 |
| 8 | Challenger | HEXAD | 5 | 2 |
| 9 | Peacemaker | TRIANGLE | 6 | 3 |

### Default Node Weights

All types start at 1.0. Type 3 (Achiever) has weight 3.0 by default.

### Arc Topology

72 arcs (9×8 source→target). Stress/growth lines get 1.5x weight.

**Documentation:** See [enneagram_topology.md](enneagram_topology.md)

---

## MCP SERVERS

```
cat .mcp.json
```

| Server | Command | Status | Purpose |
|---|---|---|---|
| claude-flow | `npx -y ruflo@latest mcp start` | Primary | Ruflo MCP v3, hierarchical-mesh |
| ruv-swarm | `npx -y ruv-swarm mcp start` | Optional | RUV Swarm |
| flow-nexus | `npx -y flow-nexus@latest mcp start` | Optional, auth required | Flow Nexus |

### Claude Flow Settings (.claude/settings.json → claudeFlow)

| Setting | Value |
|---|---|
| agentTeams.enabled | true |
| swarm.topology | hierarchical-mesh |
| swarm.maxAgents | 15 |
| memory.backend | hybrid |
| memory.enableHNSW | true |
| neural.enabled | true |
| daemon.autoStart | false |
| daemon.workers | map, audit, optimize |
| security.autoScan | true |

---

## TEMPLATES (7 directories)

```
ls _TEMPLATES/
```

| Template | Files | Purpose |
|---|---|---|
| android | CLAUDE.md, BEST_PRACTICES.md, doc/, app/, .claude/, screenshots/ | Android project scaffold |
| carte | CLAUDE.md, BEST_PRACTICES.md, doc/, export/, serve_md.py | Book writing scaffold |
| generic | CLAUDE.md, BEST_PRACTICES.md, doc/ | Generic project scaffold |
| preview-live-server | CLAUDE.md, serve_md.py | Live markdown preview |
| research | CLAUDE.md, BEST_PRACTICES.md, doc/ | Research project scaffold |
| devcontainer | devcontainer.json, README.md | Dev container (Node 20, Python 3) |
| github-workflows | ccdew-quality-gate.yml, README.md | CI/CD workflows |

### Sync Status (vs Hermeneuticus upstream)

| Template | CLAUDE.md | BEST_PRACTICES.md | serve_md.py | Status |
|---|---|---|---|---|
| android | IDENTICAL | IDENTICAL | — | OK synced |
| generic | IDENTICAL | IDENTICAL | — | OK synced |
| research | IDENTICAL | IDENTICAL | — | OK synced |
| carte | IDENTICAL | — | — | OK synced |
| preview-live-server | IDENTICAL | — | IDENTICAL | OK synced |

---

## OBSIDIAN VAULT (_MEMORY/)

```
ls _MEMORY/
```

| File/Dir | Purpose |
|---|---|
| _DASHBOARD.md | This file — live workspace overview |
| _INBOX.md | User → Claude drop zone |
| _PROTOCOL.md | Bidirectional vault rules |
| _USER_NOTES.md | User-only space |
| enneagram_topology.md | 9 types, arcs, SSA scoring |
| AUDIT-GITHUB-COMPARISON.md | CCDEW vs GitHub competitors |
| enneagram_adaptive_topology.json | Live arc weights |
| circuit9_spec.md | Circuit9 spec |
| circuit9_architecture.md | Circuit9 architecture |
| decisions/ | 11 architectural decisions |
| sessions/ | Obsidian MD per /exit |
| agents/ | (reserved) |

---

## TESTS (22 suites, 147 tests)

```
node .claude/helpers/run-tests.cjs
```

| Suite | Tests | Status |
|---|---|---|
| atomic-write | 5 | PASS |
| auto-infer | 8 | PASS |
| auto-optimize | 6 | PASS |
| codeburn-engine | 8 | PASS |
| cross-claude-race | 1 | PASS |
| error-log | 6 | PASS |
| file-lock | 6 | PASS |
| i18n | 6 | PASS |
| local-date | 5 | PASS |
| migrate | 8 | PASS |
| path-safe | 7 | PASS |
| perf-baseline | 6 | PASS |
| platform-detect | 4 | PASS |
| pricing | 5 | PASS |
| redact | 6 | PASS |
| safla-validation | 7 | PASS |
| secret-scan | 8 | PASS |
| session-snapshot | 6 | PASS |
| skills-propose | 6 | PASS |
| stability-5zoom | 10 | PASS |
| strings | 5 | PASS |
| python-smoke | 7 | PASS |
| **TOTAL** | **147** | **ALL PASS** |

---

## 5-ZOOM CANON (audit levels)

| Zoom | Scope | Tools |
|---|---|---|
| MAHA | System goal alignment | auto-infer, auto-optimize (proposal) |
| MACRO | Cross-module structure | 13-module audit |
| MEZZO | Per-module cohesion | lib/ module tests |
| MICRO | Function design (50-line soft cap) | code review |
| NANO | Char-level (2-space, LF, single quotes) | auto-optimize (auto-fix) |

---

## SECURITY

### Permissions (.claude/settings.json)

**Allow:** Bash(npx @claude-flow*), Bash(node .claude/*), mcp__claude-flow__:*

**Deny (40 patterns):**
- All .env files
- All credentials.{json|yml|yaml}
- All secrets.{json|yml|yaml}
- All id_rsa, id_ed25519, id_ecdsa
- All *.pem, *.pfx, *.p12, *.key
- .aws/credentials, .ssh/id_*, .kube/config, .netrc, .gnupg/**
- /etc/passwd, /etc/shadow, /etc/sudoers, /etc/ssh/**
- /proc/**
- C:\Windows\System32\config\**, C:\Windows\System32\drivers\**
- Dangerous Bash: rm -rf /*, mkfs.*, fork bomb, dd if=* of=/dev/sd*

### Secret Scan Patterns (11)

AWS keys, Anthropic keys, OpenAI keys, GitHub tokens, Stripe keys, RSA private keys, Slack tokens, Database URLs, Generic API keys, JWT tokens, Private keys

---

## QUICK REFERENCE

### Run full audit
```bash
node .claude/helpers/evaluate-setup.cjs
```

### Run tests
```bash
npm test
# or: node .claude/helpers/run-tests.cjs
```

### Check cost
```bash
node .claude/helpers/hook-handler.cjs burn
```

### Check SSA efficiency
```bash
node -e "console.log(JSON.stringify(require('./.claude/helpers/ssa.cjs').getSSAEfficiency(), null, 2))"
```

### Switch profile
```bash
node .claude/helpers/hook-handler.cjs profile lite
node .claude/helpers/hook-handler.cjs profile full
node .claude/helpers/hook-handler.cjs profile ssa-max
```

### List SOPs
```bash
node .claude/helpers/hook-handler.cjs sop list
```

### View SAFLA stats
```bash
node .claude/helpers/hook-handler.cjs safla
```

### View instincts
```bash
node .claude/helpers/hook-handler.cjs instincts
```

---

## RECENT CHANGES

- 2026-05-12: v3.9.3 → SSA token metrics (entries, chars, tokens) + Devcontainer + GitHub Actions + Scheduled Tasks
- 2026-05-12: v3.9.2 → enneagram_topology.md + Template Sync Audit + GitHub Comparison
- 2026-05-12: v3.9.1 → SOP Engine + Auto-Profile + profile command
- 2026-05-12: v3.9.0 → v6.1 SLIM: SSA 5D + Ruflo + Profiles
- 2026-05-10: v3.8.0 → cross-process file-lock + race fix
- 2026-05-10: v3.7.0 → Python detection real path + skills fallback
- 2026-05-10: v3.6.0 → skills-propose GitHub + /exit snapshot + /sessions-compare
- 2026-05-10: v3.5.0 → 7/10 round-4 zones repaired + stability 5-zoom
- 2026-05-10: v3.4.0 → 5-zoom audit + auto-infer + auto-optimize
- 2026-05-10: v3.3.0 → perf-baseline + PII redact + auto-triggers

---

## LAST UPDATED

**2026-05-12** by Claude Code session

**Next scheduled audit:** Auto via SessionEnd hook