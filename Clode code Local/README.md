# Clode code Local

Config local Claude Code + Hermes Hub pentru mașina **think@zorin**.

Parte din workspace-ul [CCDEW](https://github.com/Hermeneuticus-of-things/claude-code-eficient-workspace).

## Conținut

```
.claude/
├── settings.json          ← hooks + permisiuni (paths absolute spre CCDEW)
├── system-prompt-hermes.txt
├── agents/hermes/         ← agenți Hermes (autonomous, agent-zero-learning)
├── commands/              ← comenzi custom Claude Code
│   ├── hermes-autonomous.md
│   ├── evaluate-setup.md
│   ├── review.md / verify.md
│   └── cost.md / research.md
└── helpers/               ← scripturi Python Hermes
    ├── hermes-autonomous.py
    ├── hermes-dashboard.py
    ├── hermes-memory-sync.py
    ├── hermes-notifier-v3.py
    ├── hermes-zorin-symbiote.py
    └── hermes-a0/         ← bridge Agent Zero
```

## Comenzi disponibile

| Comandă | Descriere |
|---|---|
| `/hermes-autonomous` | Lansează Hermes în mod autonom (loop OODA) |
| `/evaluate-setup` | Audit 38 puncte Red Hat-style |
| `/review` | Code review |
| `/verify` | Verificare comportament real |
| `/cost` | Raport costuri sesiune |
| `/research` | Research aprofundat |

## Note

- Hooks pointează la `/home/think/CCDEW/.claude/helpers/` (sursa de adevăr)
- Scripturi Hermes din `helpers/` sunt copii locale — actualizează manual după modificări în CCDEW
