# CCDEW Workspace Dashboard

**Version:** v3.9.3 — 2026-05-12
**Status:** 37/37 PASS — SSA OK — 147/147 tests

---

## Quick Status

| System | Status | Metric |
|---|---|---|
| Audit | OK | 37/37 checks |
| Tests | OK | 147/147 |
| SSA | OK | efficiency target <25% |
| Cost | OK | $764/luna |
| Templates | OK | 7 synced |

---

## Commands

```bash
# Audit + tests
npm test
node .claude/helpers/evaluate-setup.cjs

# Cost
node .claude/helpers/hook-handler.cjs burn

# SSA stats
node -e "console.log(JSON.stringify(require('./.claude/helpers/ssa.cjs').getSSAEfficiency(), null, 2))"

# SOP
node .claude/helpers/hook-handler.cjs sop list
node .claude/helpers/hook-handler.cjs sop-execute <name>

# Profile
node .claude/helpers/hook-handler.cjs profile lite|full|ssa-max
```

---

## Components (v6.1 SLIM)

| Component | Status | File |
|---|---|---|
| Enneagram 9-node | OK | enneagram_router.py |
| SSA 5D | OK | ssa.cjs |
| SAFLA | OK | safla.cjs |
| CodeBurn | OK | codeburn.cjs |
| Ruflo MCP | OK | ruflo.cjs |
| SOP Engine | OK | sop-engine.cjs |
| Auto-Profile | OK | feature-flags.json |
| Instincts | OK | instincts.cjs |
| Secret Scan | OK | secret-scan.cjs |
| Auto-Audit | OK | evaluate-setup.cjs |

---

## Hooks (13 events)

UserPromptSubmit, PreToolUse, PostToolUse, SessionStart, SessionEnd, Stop, PreCompact, SubagentStart, SubagentStop, Notification, ScheduledTask, LoopTask

---

## Files

| File | Purpose |
|---|---|
| CLAUDE.md | Workspace root rules |
| CHANGELOG.md | Version history |
| TODO.md | Task tracking |
| BEST_PRACTICES.md | Universal patterns |
| _MEMORY/_DASHBOARD.md | Obsidian vault dashboard |
| _MEMORY/enneagram_topology.md | Enneagram docs |
| _MEMORY/AUDIT-GITHUB-COMPARISON.md | GitHub comparison |

---

## Updated

2026-05-12 by Claude Code