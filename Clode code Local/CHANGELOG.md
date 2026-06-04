# CHANGELOG — Clode code Local

> Config local Claude Code + Hermes Hub pentru mașina think@zorin.
> Repo: https://github.com/Hermeneuticus-of-things/claude-code-eficient-workspace

---

## [1.0.0] — 2026-06-05 — Inițializare proiect

### Cerință
Creare proiect `Clode code Local` ca hub de configurare Claude Code locală + Hermes (Opțiunea C).

### Ce s-a făcut
- `CLAUDE.md` — instrucțiuni locale mașina think@zorin, reguli + documentație Hermes
- `.claude/settings.json` — hooks absolute spre `/home/think/CCDEW/.claude/helpers/`
- `.claude/system-prompt-hermes.txt` — identitate Hermes
- `.claude/agents/hermes/` — agenți `hermes-autonomous` + `agent-zero-learning`
- `.claude/commands/` — 6 comenzi custom (`/hermes-autonomous`, `/review`, `/verify`, `/cost`, `/research`, `/evaluate-setup`)
- `.claude/helpers/` — 12 scripturi Python Hermes + bridge `hermes-a0/`
- `README.md`, `CHANGELOG.md`, `TODO.md`, `.gitignore` — fișiere meta
- `Clode .md` — index rapid sesiune

### Fișiere create
- `CLAUDE.md`, `README.md`, `CHANGELOG.md`, `TODO.md`, `.gitignore`, `Clode .md`
- `.claude/settings.json`, `.claude/system-prompt-hermes.txt`
- `.claude/agents/hermes/hermes-autonomous.md`
- `.claude/agents/hermes/agent-zero-learning.md`
- `.claude/commands/` × 6
- `.claude/helpers/hermes-*.py` × 12 + `hermes-a0/` × 3

### Decizii
- Hooks folosesc path-uri absolute (nu `${CLAUDE_PROJECT_DIR}`) pentru stabilitate
- Scripturi Hermes sunt copii locale — sursa de adevăr rămâne `/home/think/CCDEW/.claude/helpers/`
- `Open-Cload` și `hermes-workspace` excluse din commit (au propriul `.git`)
