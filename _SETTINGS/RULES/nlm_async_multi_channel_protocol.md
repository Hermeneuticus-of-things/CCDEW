# RULES — NLM Async + Multi-Canal Anti-Timeout/Anti-Dezlogare
## Universal cross-project (orice integrare cu NotebookLM sau RAG slow APIs)

**Data:** 2026-05-02 — extras din Karma Book session learnings, generalizat.

## Când aplici

Oricând faci queries către:
- NotebookLM (Karma BooK, Cercetare, Glosar — sau orice notebook)
- Orice RAG service cu latență variabilă (5-180s pe query)
- API-uri externe cu rate-limiting + auth-cookies persistente

## Protocol în 10 nivele (aplici în ordine, fallback dacă eșuează)

### Nivel 1 — Async pattern (PRIMAR)
- `mcp__notebooklm-mcp__notebook_query_start` cu `timeout: 180` → returnează `query_id` imediat
- `mcp__notebooklm-mcp__notebook_query_status` cu `query_id` → poll până `status: "completed"`
- Evită timeout sincron; server poate procesa lent fără eroare client-side

### Nivel 2 — Timeout mărit
- Parametru `timeout: 180` (vs 90 default) pentru queries grele
- Pentru context window mare (200+ surse), 240s e justificat

### Nivel 3 — Grouped queries
- 3-5 sub-întrebări într-un singur prompt structurat
- Consum 1 query quota în loc de 5
- NLM/Gemini procesează coerent multi-întrebare

### Nivel 4 — Multi-notebook batch (canal multiplu)
- `mcp__notebooklm-mcp__batch action=query` peste 2-3 notebook-uri
- ATENȚIE THROTTLE între notebook-uri (≥3s)

### Nivel 5 — Endpoint alternativ
- `research_start` (deep research) vs standard `notebook_query`
- Diferit pipeline backend, mai robust pentru queries lungi

### Nivel 6 — Conversation_id reuse
- Păstrează context între queries în același notebook
- Cache implicit; queries follow-up mai rapide + precise + cheaper

### Nivel 7 — Cache local
- Dacă răspunsul NLM despre concept X există local, REUTILIZEZ pentru concepte related
- Salvează în memorie (Obsidian Memory v1) pentru sesiuni viitoare

### Nivel 8 — CDP direct via Brave (BACKUP ULTIM)
- Dacă MCP cade complet, accesez NLM direct prin browser MCP / javascript_tool
- Brave dedicated profile authenticated — rezolvă auth fără re-login
- ATENȚIE: doar BACKUP, nu primary (anti-suspicion)

### Nivel 9 — Throttle obligatoriu (ANTI-SUSPICION)
- ≥3s între queries succesive
- ≥5s între queries multi-notebook
- ≥10s pauză între batches mari (>5 queries)

### Nivel 10 — Daily tier limits awareness
- Free: 50 queries/zi
- Plus: 500 queries/zi  ← TIER actual user
- Ultra: 5000 queries/zi
- Verifică `nlm` CLI sau interfață web pentru remaining quota
- Pentru workload mare, planifică în multiple zile

## Auto-login force (ÎNAINTE de orice NLM call în sesiune lungă)

```bash
python C:\Users\Think\.claude\scripts\nlm_auto_login.py --force
```

Verifică `AUTH_REFRESHED_OK` la final. Dacă auth expiră mid-session, rulează din nou (nu așteaptă 401).

**Root cause documenat:** NLM auth expiră în sesiuni lungi pentru că hooks rulează `--check` (verificare doar), NU `--force` (refresh). Cookies expiră după ~3-4h fără refresh.

## Anti-pattern (PRODUC DEZLOGARE)

- ❌ Multiple Brave instances simultan (anti-bot signature)
- ❌ Refresh-hammer (de ex. `nlm login --check` la fiecare 30s)
- ❌ Playwright headless (`pip install notebooklm-py[browser]`) — bot signature instant
- ❌ Queries fără throttle (toate la zero)
- ❌ Multiple sesiuni Claude pe același NLM concurent
- ❌ Auto-keep-alive cu interval fix (declanșează detection)

## Backbone tehnic NLM (informativ)

- **Pipeline hibrid pe Gemini 2.5:**
  - Free tier: Gemini 2.5 Flash
  - Plus tier: Gemini 2.5 Pro
  - Ultra tier: Pro + Deep Think
- RAG grounded pe surse uploaded (ex: 210 surse Karma BooK)
- Citații cu sursa originală pentru verificare factuală
- Romanian language support fluent

## Aplicabilitate cross-project

- **Karma Book:** doctrinar grounded pe 210 surse jaina/vedanta/buddhist
- **Glosar:** 30 surse termeni
- **Cercetare:** 224 surse research
- **Orice proiect viitor cu NLM:** aplică același protocol
- **Orice RAG service viitor:** adaptez Nivel 1-3 (async + timeout + grouped)

## Vezi și

- `nlm_anti_suspicion.md` — strategy completă anti-detection
- Memory: `karma_drift_session_learnings.md` — context Karma-specific care a generat această regulă
