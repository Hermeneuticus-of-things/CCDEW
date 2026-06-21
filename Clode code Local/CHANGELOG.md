# CHANGELOG — Clode code Local

> Config local Claude Code + Hermes Hub pentru mașina think@zorin.
> Repo: https://github.com/Hermeneuticus-of-things/claude-code-eficient-workspace

---

## [1.2.0] — 2026-06-05 — Mailspring: pachet intern ccdew-intelligence

### Cerință
Integrare nativă CCDEW Email Intelligence în Mailspring ca pachet intern (`ccdew-intelligence`): badge-uri în lista de thread-uri, banner de alertă sub header-ele mesajelor, sidebar cu toate alertele, polling la serverul local `http://127.0.0.1:8766`.

### Ce s-a făcut
- `package.json` — manifest pachet Mailspring
- `lib/main.ts` — intrare TypeScript: CCDEWStore (polling 120s, lookup rapid Map), CCDEWThreadBadge (dot colorat per threat_score), CCDEWMessageBar (banner urgenţă), CCDEWSidebar (toate alertele grupate)

### Fișiere vizate
- `PROJECTS/mailspring-ccdew/app/internal_packages/ccdew-intelligence/package.json` (NOU)
- `PROJECTS/mailspring-ccdew/app/internal_packages/ccdew-intelligence/lib/main.ts` (NOU)

---

## [1.1.0] — 2026-06-05 — Zorin TV: self-healing multi-sursă + proxy HLS

### Cerință
Server TV românesc local (`localhost:8899`): extindere căutare variante peste iptv-org (OTT/web), redare în browser pentru streamuri CORS/referer-locked, fix agent core Hermes.

### Ce s-a făcut
- **Căutare variante multi-sursă** (`find_alternative`): magicplaces token-refresh + rediscovery rdslive.tv → 3 surse M3U publice (iptv-org, Free-TV, iptv-org-lang). `norm_name` îmbunătățit (elimină simboluri ca Ⓖ).
- **Proxy HLS `/hls?u=<b64>`** — rezolvă CORS + referer-lock universal: fetch server-side cu UA/Referer, rescrie master→variante→segmente prin proxy, servește cu `Access-Control-Allow-Origin: *`.
- **UI escaladare la eroare**: redare directă → proxy (CORS) → find-alternative, cu `originalUrl` urmărit separat de URL-ul proxat.
- **Fix magicplaces „nu se vede"**: proxy-ul auto-tokenizează URL-urile magicplaces — `_mp_token_expired(url)` parsează timestamp-ul Unix din token și reîmprospătează (`refresh_token`) când e gol sau expirat; UI rutează magicplaces prin proxy din start (`needsProxy`). Sub-URL-urile păstrează tokenurile proprii (doar top-level se tokenizează).
- **Scos fallback YouTube** — fals-pozitiv în 2026 (yt-dlp vechi → 403, yt-dlp nou → fără m3u8; googlevideo fără CORS).
- **Fix Hermes agent core**: `sp.run` → `subprocess.run` ([hermes-agent-core.py:130]) — înainte verificarea TV dădea `NameError` → toate canalele fals „dead".
- **Fix**: `if __name__ == "__main__"` pe blocul de pornire server (modul importabil pentru teste).

### Fișiere modificate
- `.claude/helpers/zorin-tv-server.py` — proxy HLS, multi-sursă, guard `__main__`, scos YouTube
- `.claude/helpers/zorin-tv-ui.html` — escaladare proxy `toProxy()`/`escalate()`, `originalUrl`
- `.claude/helpers/hermes-agent-core.py` — fix `sp.run`
- `~/.hermes/skills/zorin-romania-tv/SKILL.md` — 66→101 canale (verificate ffprobe)

### Verificat
- Proxy cap-coadă cu curl: master→variante→segmente rescrise, CORS prezent, segment real `200 video/MP2T 529KB`
- base64 browser-style ↔ server `urlsafe_b64decode` — round-trip cu `?`/`&`/`=`
- Fără regresie: Pro TV recuperat prin magicplaces (`h264 1920x1080`); 101 canale intacte
- JS syntax OK (node --check); agent core compilează + rulează ciclu curat

### Decizii
- YouTube abandonat ca sursă web (HLS indisponibil în 2026, CORS absent) — proxy-ul rezolvă redarea pentru sursele M3U/IPTV reale
- Validare web prin `#EXTM3U` doar acolo unde ffprobe dă fals-negativ; proxy-ul citește segmente întregi (live ~2s, OK în memorie)

### Limitări
- Redarea video în browser + lanțul `escalate()` neverificate într-un browser real (doar server-side cu curl + sintaxă JS)

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
