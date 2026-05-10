# CCDEW — Claude Code Development Efficient Workspace v3.x

**Workspace ultra-eficient pentru Claude Code** cu rutare Enneagram, optimizare automată tokeni, urmărire cost real, feedback loop adaptiv, prevenire scurgere secrete și recunoaștere pattern-uri (instincts).

> Inspirat de: [Hermeneuticus-of-things/claude-code-eficient-workspace](https://github.com/Hermeneuticus-of-things/claude-code-eficient-workspace)
> v3 integrează straturi din [everything-claude-code (ECC)](https://github.com/affaan-m/everything-claude-code) (skills auto-activate, instincts, secret-scan, multi-platform) și [claude-code-setup-evaluator (Red Hat)](https://github.com/redhat-community-ai-tools/claude-code-setup-evaluator) (`/evaluate-setup`, `/verify`, `/review`, `/quality-gate`, `/diff-explain`).
> Vezi [`MIGRATION.md`](MIGRATION.md) pentru upgrade din v2.0.

## Structură

```
CCDEW/
├── .claude/                ← config Claude Code + helpers + skills + comenzi
├── PROJECTS/               ← proiectele tale active
├── repositories/           ← repo-uri externe (pattern Red Hat meta-workspace)
├── _BEST_PRACTICES/        ← wisdom referenced
├── _TEMPLATES/             ← scaffolding copiat la proiect nou
├── _SETTINGS/              ← reguli + protocoale
├── _MEMORY/                ← Obsidian vault bidirecțional Claude ↔ User
└── _ARCHIVE/               ← snapshot-uri pentru rollback
```

## Comenzi rapide

```bash
npm test               # 70+ teste regression (11+ suite)
npm run audit          # /evaluate-setup full (38+ checks)
npm run audit:fix      # auto-rezolvă WARN-urile
npm run burn           # cost real azi+lună (codeburn CLI)
npm run verify         # typecheck+test+lint+secret-scan+dead-code
npm run review         # 3-agent swarm code review
npm run quality-gate   # strict pass/fail înainte de merge
npm run mcp-health     # verifică ~/.claude.json MCP servers
```

## Slash commands în Claude Code

| Comandă | Rol |
|---|---|
| `/evaluate-setup` | health-check complet workspace |
| `/verify` | sanity sweep pe diff curent |
| `/review` | swarm 3 agenți (reviewer + analyst + tester) |
| `/quality-gate` | pass/fail strict înainte de merge |
| `/diff-explain` | sumar plain-English git diff |
| `/research` | research-first dev (context → propunere → plan) |
| `/cost` | status codeburn + sugestii optimizare |

## Caracteristici principale

### 1. SSA — Filtrare context (−76% tokeni)
La fiecare prompt, în loc să injecteze toată memoria, SSA calculează **similaritate Jaccard trigram** între prompt și fiecare entry de memorie. Rezultat: din 50 entries, doar 12 sunt injectate.

### 2. Enneagram Routing — Agentul potrivit pentru task-ul potrivit
Sistemul clasifică automat fiecare prompt într-unul din 9 tipuri de task și selectează agentul specializat. Bug fix → `tester` (Nod 6), nu `sparc-orchestrator` (Nod 8).

### 3. CodeBurn — Vizibilitate completă cost
Citește direct din `~/.claude/projects/` și afișează în statusline: `💰 $X/$100/d · Nc 🚨@100% ⚠@75%`. Fallback la engine nativ când CLI-ul lipsește.

### 4. SAFLA — Sistem care învață din experiență
Urmărește ce agent a funcționat sau nu pentru fiecare tip de task. Penalitate `-0.10` la failure, bonus `+0.05` la success.

### 5. Red Hat Evaluator — Previne over-engineering
Înainte de orice task de arhitectură, injectează 2-3 întrebări critice: "*Ce presupuneri tacite conține această soluție?*" "*Există abordare mai simplă cu ≤50% complexitate?*"

### 6. Secret-scan — Prevenire automată scurgere secrete
Hook `pre-edit` blochează scrierea de chei AWS/Anthropic/OpenAI/GitHub/Stripe/RSA private și fișiere `.env`, `id_rsa`, `*.pfx`.

### 7. Instincts — Recunoaștere pattern-uri
Înregistrează (prompt fingerprint, agent, succes) la fiecare task. După ≥3 apariții ale aceluiași tipar, sugerează automat agentul: `[INSTINCT] you usually route this to node N (X% confidence)`.

## Multi-platform support

CCDEW funcționează cu:
- **Claude Code** (toate features) ✓
- **Cursor** (MCP-only — fără hooks/slash) ⚠
- **Codex** (rulare CLI standalone) ⚠
- **Gemini** (configurare manuală) ⚠
- **OpenCode** (hooks + slash similar Claude Code) ✓

Comanda `/platform` raportează capabilities-le pe sesiunea curentă.

## Securitate

- **secret-scan** integrat în `pre-edit` hook
- **35+ patterns deny** în `settings.json` (`/etc/passwd`, `.gnupg/`, `.aws/credentials`, `id_rsa`, `*.pfx`, `C:\Windows\System32\`...)
- **path-safe** validare împotriva shell injection în `execFileSync` cu `shell:true`
- **PII redaction** automată în `errors.jsonl` (emails, JWT, API keys, paths)

## Observabilitate

- `errors.jsonl` cu rotație 5k linii la `.claude-flow/logs/`
- `perf-baseline.json` track p95 hot-paths cu detectare regresie >50%
- `evaluate-*.json` snapshots periodice pentru diff cross-runs
- Statusline live cu cost + SAFLA success rate + project + platform

## Quick start

```bash
# 1. Clone CCDEW
git clone <CCDEW-repo> CCDEW
cd CCDEW

# 2. Instalează codeburn (singura dep externă)
npm install -g codeburn

# 3. Verifică totul
npm run audit

# 4. Pornește Claude Code
claude
```

La primul prompt, sistemul auto-inițializează. Verifică:
```bash
node .claude/helpers/hook-handler.cjs flags
```

## Documentație complementară

- [README.md](README.md) — versiunea în engleză
- [MIGRATION.md](MIGRATION.md) — upgrade v2 → v3
- [CHANGELOG.md](CHANGELOG.md) — istoric versiuni cu detalii tehnice
- `_SETTINGS/RULES/` — reguli operaționale
- `.claude/commands/` — documentație slash commands

## Licență

MIT — vezi [LICENSE](LICENSE).
