# OpenCode Root Access - CCDEW

## Permisiuni

OpenCode în CCDEW poate scrie în:
- `/home/think/CCDEW/` - workspace root
- `/home/think/CCDEW/_MEMORY/` - memorie persistentă
- `/home/think/CCDEW/.claude/` - configurații și helpers
- `/tmp/opencode/` - directoare temporare

## Reguli Scriere

1. **DA**: Fișiere în workspace-ul CCDEW
2. **DA**: Actualizare memoria în `_MEMORY/`
3. **DA**: Modificare helpers în `.claude/helpers/`
4. **NU**: Fișiere sistem din afara workspace-ului
5. **NU**: Comenzi destructive (dd, mkfs, etc)

## Utilizator

- User: **think**
- Hermes: helper activ, fără platforme specifice