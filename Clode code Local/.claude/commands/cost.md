# /cost — CodeBurn Dashboard

Afișează costul real de tokeni pentru sesiunea curentă și luna aceasta.

## Utilizare

```
/cost           → status compact (azi + luna)
/cost today     → detalii ziua curentă
/cost month     → detalii luna curentă  
/cost optimize  → analiză waste + sugestii reducere
/cost report    → dashboard interactiv complet
```

## Implementare

```bash
# /cost (default — status compact)
codeburn status

# /cost today
codeburn today

# /cost month
codeburn month

# /cost optimize
codeburn export --format json | node .claude/helpers/hook-handler.cjs burn --json

# /cost report (dashboard interactiv TUI)
codeburn report
```

## Output exemplu

```
Today  $3.81  112 calls    Month  $230.82  2164 calls
```

## Note

- Date citite direct din `~/.claude/projects/` de codeburn CLI
- Actualizat automat la fiecare SessionEnd via hook
- Cache 60s în `.claude-flow/data/codeburn-cache.json` pentru statusline
