# CCDEW + Open-Cload

**Open-Cload** = **OpenCode** + **CCDEW** integration.

## Quick Start

```bash
# Start OpenCode (auto-opens dashboard)
opencode

# Direct commands
opencode status          # Cost tracking
opencode safla stats     # Learning stats
opencode dashboard       # Web dashboard
opencode audit           # 5-zoom audit
```

## What You Get

| Feature | Description |
|---------|-------------|
| **Dashboard** | Real-time metrics at http://localhost:8765/dashboard |
| **Cost Tracking** | Daily/monthly API costs with budget alerts |
| **Enneagram Routing** | Task routing to specialized agents |
| **5-Zoom Audit** | Architecture review at 5 levels |
| **Learning System** | Feedback-driven improvement |
| **Custom Commands** | `/audit`, `/status`, `/route`, `/safla`, etc. |

## Dashboard

Opens automatically when you run `opencode`. Shows:
- Today's cost vs $100/day budget
- Month-to-date totals
- SAFLA learning feedback
- Intelligence graph stats
- Efficiency metrics

## Custom Commands in OpenCode

Type `/` in OpenCode to see CCDEW commands:
- `/audit` — 5-zoom architecture audit
- `/status` — CCDEW metrics
- `/route` — Task routing recommendation
- `/snapshot` — Save session state
- `/secret-scan` — Secret detection
- `/compact` — Context token reduction
- `/dashboard` — Launch web dashboard

## Files

```
CCDEW/
├── AGENTS.md              # Project context
├── .claude/
│   ├── helpers/          # CCDEW systems (codeburn, safla, etc.)
│   └── skills/           # Agent skills
└── .opencode/
    └── ccdew-wrapper.cjs # OpenCode bridge

Open-Cload/               # Integration repo (also on GitHub)
├── .opencode/
│   ├── commands/         # Custom OpenCode commands
│   ├── plugins/          # CCDEW plugin
│   └── dashboard.*       # Web dashboard
├── .claude/skills/       # CCDEW agent skills
├── AGENTS.md             # Open-Cload context
└── README.md             # This file
```

## Links

- **Dashboard**: http://localhost:8765/dashboard
- **Open-Cload Repo**: https://github.com/Hermeneuticus-of-things/Open-Cload
- **CCDEW Helpers**: `/home/think/CCDEW/.claude/helpers/`