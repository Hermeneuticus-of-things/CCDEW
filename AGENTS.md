# CCDEW — Claude Code Efficient Workspace

## Overview

CCDEW este un workspace optimizat pentru dezvoltare AI-asistata cu cost tracking, invatare adaptiva, si calitate automata.

## Core Features

### Cost Tracking (CodeBurn)
- **Buget zilnic**: $100/zi
- **Urmarire**: apeluri API, cost per sesiune, tendinte lunare
- **Optimizare**: compactare automata context cand bugetul > 75%

**Verificare cost:**
```bash
node .claude/helpers/codeburn.cjs
```

### Enneagram Routing (Safla)
Sistem de routing bazat pe 9 tipuri de personalitate:

| Nod | Nume | Specialitate |
|-----|------|--------------|
| 1 | Perfectionist | Calitate, linting |
| 2 | Helper | Documentatie |
| 3 | Achiever | Testare, CI |
| 4 | Individualist | Arhitectura |
| 5 | Investigator | Debug, securitate |
| 6 | Loyalist | Error handling |
| 7 | Enthusiast | Prototyping |
| 8 | Challenger | Infrastructure |
| 9 | Peacemaker | Reviews |

**Inregistrare feedback:**
```bash
node .claude/helpers/safla.cjs feedback [nod] success|failure
node .claude/helpers/safla.cjs stats
```

### 5-Zoom Audit
Audit la 5 niveluri inainte de commit:

1. **MAHA** - Arhitectura sistem
2. **MACRO** - Responsabilitati modul
3. **MEZZO** - Design functii
4. **MICRO** - Calitate cod
5. **NANO** - Finisare

```bash
node .claude/helpers/evaluate-setup.cjs --json
```

### Invatare Adaptiva (Intelligence)
- Graph de memorie contextual
- Pattern detection
- Acces la context relevant

```bash
node .claude/helpers/intelligence.cjs stats --json
```

## Comenzi Rapide

| Comanda | Descriere |
|---------|-----------|
| `opencode status` | Afiseaza metrici cost |
| `opencode audit` | Ruleaza 5-zoom audit |
| `opencode route [task]` | Recomanda nodul optim |
| `opencode dashboard` | Deschide dashboard web |
| `opencode snapshot` | Salveaza stare sesiune |

## Workflow Recomandat

### Inainte de Commit
1. `/secret-scan` - Verifica secrete
2. `/audit` - Trece 5-zoom
3. `/status` - Verifica bugetul

### Dupa Task Major
1. `/safla [success|failure]` - Inregistreaza feedback
2. `/snapshot` - Salveaza stare
3. `/compact` - Reduce context daca e mare

### Monitorizare
- Dashboard: `http://localhost:8765/dashboard`
- Se deschide automat cu `opencode`

## Structura Proiectului

```
CCDEW/
├── .claude/
│   ├── helpers/          # Sisteme CCDEW
│   │   ├── codeburn.cjs # Cost tracking
│   │   ├── safla.cjs    # Invatare/routing
│   │   ├── hook-handler.cjs
│   │   ├── intelligence.cjs
│   │   ├── ssa.cjs     # Context filtering
│   │   └── lib/        # Librarii
│   └── skills/         # Agent skills
├── .opencode/          # OpenCode bridge
├── _METRICS/           # Snapshots cost
└── _MEMORY/            # Memorie persistenta
```

## Reguli de Calitate

- Nu expune API keys sau secrete
- Ruleaza audit inainte de commit
- Inregistreaza feedback dupa task-uri
- Compacta context cand creste
- Verifica bugetul zilnic

## Cost Management

| Utilizare | Status | Actiune |
|-----------|--------|---------|
| < 50% | 🟢 Verde | Normal |
| 50-75% | 🟡 Galben | Pregateste compact |
| 75-100% | 🟠 Portocaliu | Compacteaza |
| > 100% | 🔴 Rosu | Stop, revizuieste |

## Tips

1. **Routing**: `/route` ajuta sa alegi abordarea optima
2. **Buget**: Verifica `/status` inainte de sesiuni lungi
3. **Audit**: Ruleaza `/audit` devreme, nu cand problemele se cumuleaza
4. **Feedback**: Inregistreaza rezultate pentru imbunatatire continua