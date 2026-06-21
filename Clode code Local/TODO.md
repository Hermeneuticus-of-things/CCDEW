# TODO — Clode code Local

## Session 2026-06-05 — Mailspring ccdew-intelligence

### Request: Pachet intern Mailspring — CCDEW Email Intelligence

- [x] `package.json` manifest Mailspring creat
- [x] `lib/main.ts` — CCDEWStore (polling 120s, Map lookup), CCDEWThreadBadge, CCDEWMessageBar, CCDEWSidebar
- [x] activate/deactivate exportate, ComponentRegistry + WorkspaceStore.Location.RightSidebar

---

## Session 2026-06-05

### Request: Zorin TV self-healing multi-sursă + proxy HLS + fix agent core

- [x] Securizare server (XSS, path traversal, delete-channel, flag injection, atomic cache)
- [x] Extindere canale 66→101 (verificate ffprobe) + grupare tematică
- [x] `find_alternative` multi-sursă: magicplaces + 3 surse M3U publice
- [x] Proxy HLS `/hls?u=` — CORS + referer-lock, rescriere manifest+segmente
- [x] UI escaladare: redare directă → proxy → find-alternative
- [x] Fix magicplaces nu se vede: auto-tokenizare în proxy (`_mp_token_expired` → `refresh_token` pe URL gol/expirat), UI rutează magicplaces prin proxy din start
- [x] Scos fallback YouTube (fals-pozitiv în 2026)
- [x] Fix `sp.run` → `subprocess.run` în `hermes-agent-core.py`
- [x] Guard `__main__` pe server (importabil pentru teste)
- [x] Epilog CHANGELOG + TODO
- [ ] Testare redare în browser real (proxy + lanț `escalate()`) — neacoperită
- [ ] Opțional: curățare canale moarte (sau lăsat la cron 6h)

### Request: Inițializare proiect Config Local + Hermes Hub

- [x] Creare `CLAUDE.md` cu instrucțiuni locale
- [x] Creare `.claude/settings.json` cu hooks absolute
- [x] Copiere scripturi Hermes în `.claude/helpers/`
- [x] Copiere agenți Hermes în `.claude/agents/hermes/`
- [x] Copiere comenzi custom în `.claude/commands/`
- [x] Adăugare `system-prompt-hermes.txt`
- [x] Creare `README.md`, `CHANGELOG.md`, `TODO.md`, `.gitignore`
- [x] Completare `Clode .md`
- [x] Commit + push la GitHub

### Următor (backlog)

- [ ] Sincronizare automată scripturi Hermes când se modifică sursa din CCDEW
- [ ] Testare hooks pe sesiune nouă Claude Code
- [ ] Adăugare comenzi SPARC (`/sparc`, `/sparc:coder`, etc.)
- [ ] Validare `hermes-autonomous.py` — testare loop OODA local
