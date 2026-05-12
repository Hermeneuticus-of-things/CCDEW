# OpenCode Desktop — Mobile Dashboard for CCDEW

> Optimizat pentru OpenCode Desktop App Mode. Vizualizare rapida status CCDEW v6.1 SLIM.

---

## Status Bar

```
00:00:00 ⟳ App Mode | CCDEW v3.9.3 | 37/37 OK | SSA OK | SAFLA OK
```

---

## Navigare

| Icon | Section | Status | Badge |
|---|---|---|---|
| 🏠 Acasa | Dashboard | OK | — |
| 🤖 MCP Servere | 3 servere | 1/3 | 7 |
| 🧠 Modele | LLM-uri | OK | 11 |
| 📚 Notebooks | Sesiuni | OK | 11 |
| 🎵 Audio | Feedback | Reserved | 8 |
| ⚡ Comenzi | Comenzi | OK | 19 |
| 🔔 Alerte | Notifications | 2 pending | 2 |

---

## Actiuni Rapide

```
[+ Adauga MCP]    → Adauga server MCP nou
[+ Cost Detaliat] → Vizualizare cost CodeBurn
[+ SAFLA]         → Statistici SAFLA
[+ Instincts]     → Raport pattern-uri invatate
[+ Securitate]    → Scanare secrete
[+ LLM Status]    → Status model LLM
```

---

## Cost Detaliat

| Perioada | Cost | Tinta | Status |
|---|---|---|---|
| Astazi | live | <$100/zi | OK |
| Luna aceasta | $764 | <$3000/luna | OK |
| Per apel | avg | <$0.05 | OK |

---

## SAFLA

| Metric | Valoare |
|---|---|
| Sesiuni | 30 |
| Feedback-uri | 23 |
| Eficienta | ~40% (tinta <25%) |
| Status | Learning activ |

---

## Instincts

| Metric | Valoare |
|---|---|
| Pattern-uri | >=3 aparitii |
| Rata succes | >=50% |
| Status | Activ |

---

## Securitate

| Verificare | Status |
|---|---|
| Permisiuni deny | 40 pattern-uri |
| Secret scan | 11 pattern-uri |
| Shell injection | Mitigat |
| PII redaction | Activ |

---

## MCP Servers

| # | Server | Status | Comanda |
|---|---|---|---|
| 1 | claude-flow | Activ | `npx -y ruflo@latest mcp start` |
| 2 | ruv-swarm | Optional | `npx -y ruv-swarm mcp start` |
| 3 | flow-nexus | Optional | `npx -y flow-nexus@latest mcp start` |

---

## Modele

| Model | Provider | Status |
|---|---|---|
| claude-opus-4-7 | Anthropic | Activ |
| claude-sonnet-4-7 | Anthropic | Activ |
| claude-haiku-4-5 | Anthropic | Default |
| gemini-2.0-flash-exp | OpenRouter | Free |
| deepseek-chat-v3 | OpenRouter | Free |

---

## LLM Status

| Verificare | Status |
|---|---|
| Provider | Anthropic |
| Model default | claude-haiku-4-5 |
| Conexiune | OK |

---

## Comenzi Rapide

```bash
/opencode init      # Initializeaza workspace
/connect anthropic   # Conecteaza Claude
/share              # Impartaseste sesiune
/undo               # Anuleaza modificari
/redo               # Refa modificari
/plan               # Plan mode
```

---

## Updated

2026-05-12 by Claude Code