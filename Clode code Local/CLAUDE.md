# Claude Code — Config Local + Hermes Hub
## Actualizat: 2026-06-05

> **Scop:** Configurare Claude Code locală + hub Hermes pentru mașina think@zorin.
> **Workspace root:** `/home/think/CCDEW/`
> **Parent CLAUDE.md:** `/home/think/CCDEW/CLAUDE.md`
> **Repo GitHub:** https://github.com/Hermeneuticus-of-things/claude-code-eficient-workspace

---

## Identitate mașină

- **User:** think
- **OS:** Zorin OS (Linux)
- **Shell:** bash
- **Node:** v22+

## Reguli locale

1. **Limbă:** Română în toate răspunsurile
2. **Workspace activ:** `/home/think/CCDEW/` — toate proiectele sunt aici
3. **Hermes:** asistent activ, helpers în `.claude/helpers/`
4. **Nu crea fișiere la root** fără confirmare

## Permisiuni active

- `/home/think/CCDEW/` — read/write complet
- `/home/think/CCDEW/_MEMORY/` — memorie Obsidian
- `/home/think/CCDEW/.claude/` — helpers, hooks, agenți
- `/tmp/opencode/` — temp

## Hooks active (din CCDEW/.claude/settings.json)

- `PreToolUse[Bash]` → `hook-handler.cjs pre-bash`
- `PreToolUse[Write|Edit]` → `hook-handler.cjs pre-edit`
- `PostToolUse[Write|Edit]` → `hook-handler.cjs post-edit`
- `PostToolUse[Bash]` → `hook-handler.cjs post-bash`

## Hermes — Scripturi locale

| Script | Scop |
|---|---|
| `hermes-autonomous.py` | Loop autonom OODA (think→act→observe→reflect) |
| `hermes-agent-core.py` | Core agent, tool-uri de bază |
| `hermes-dashboard.py` | Dashboard status Hermes |
| `hermes-memory-sync.py` | Sincronizare memorie bidirecțională |
| `hermes-notifier-v3.py` | Notificări desktop (Zorin) |
| `hermes-zorin-symbiote.py` | Integrare OS Zorin |
| `hermes-voice-daemon.py` | Voice input daemon |
| `hermes-deep-links.py` | Deep links handler |
| `hermes-binary-guardian.py` | Protecție fișiere binare |
| `hermes-auto-refresh.py` | Auto-refresh sesiune |
| `hermes-a0/` | Bridge Agent Zero (coordinator, memory_sync) |

**System prompt:** `.claude/system-prompt-hermes.txt`

## Agenți disponibili

- `hermes-autonomous` — agent autonom Hermes (`.claude/agents/hermes/hermes-autonomous.md`)
- `agent-zero-learning` — pattern learning Agent Zero style
- Toți agenții din `/home/think/CCDEW/.claude/agents/`

## Comenzi custom

| Comandă | Fișier |
|---|---|
| `/hermes-autonomous` | `.claude/commands/hermes-autonomous.md` |
| `/evaluate-setup` | `.claude/commands/evaluate-setup.md` |
| `/review` | `.claude/commands/review.md` |
| `/verify` | `.claude/commands/verify.md` |

## Memorie & context

- **Past decisions:** `/home/think/CCDEW/CHANGELOG.md`
- **Pending tasks:** `/home/think/CCDEW/TODO.md`
- **Cross-project rules:** `/home/think/CCDEW/_SETTINGS/RULES/INDEX.md`
- **Memory vault:** `/home/think/CCDEW/_MEMORY/`
