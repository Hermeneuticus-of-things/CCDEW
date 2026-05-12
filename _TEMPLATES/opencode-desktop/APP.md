# OpenCode Desktop — CCDEW Mobile App

```
┌─────────────────────────────────────────┐
│ 00:00:00                                │
│ ⟳                                      │
│ 📱 App Mode                             │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ 🏠 Acasă                            │ │
│ ├─────────────────────────────────────┤ │
│ │ 🤖 MCP Servere              7        │ │
│ ├─────────────────────────────────────┤ │
│ │ 🧠 Modele                  11       │ │
│ ├─────────────────────────────────────┤ │
│ │ 📚 Notebooks                11       │ │
│ ├─────────────────────────────────────┤ │
│ │ 🎵 Audio                  8        │ │
│ ├─────────────────────────────────────┤ │
│ │ ⚡ Comenzi                 19       │ │
│ ├─────────────────────────────────────┤ │
│ │ 🔔 Alerte                 2        │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ Acțiuni                                 │
│                                         │
│ 💰 Cost Detaliat                  →     │
│ 🧠 SAFLA                        →     │
│ 🔮 Instincts                    →     │
│ 🛡️ Securitate                   →     │
│ ⚡ LLM Status                    →     │
│                                         │
│ + Adaugă MCP                           │
└─────────────────────────────────────────┘
```

---

## Status Grid

| Icon | Section | Status | Count |
|---|---|---|---|
| 🏠 | Acasă | OK | — |
| 🤖 | MCP Servere | 3 servere | 7 |
| 🧠 | Modele | 11 modele | 11 |
| 📚 | Notebooks | 11 sesiuni | 11 |
| 🎵 | Audio | Reserved | 8 |
| ⚡ | Comenzi | 19 | 19 |
| 🔔 | Alerte | 2 pending | 2 |

---

## Quick Actions

| Action | Route | Status |
|---|---|---|
| Cost Detaliat | → Cost | OK |
| SAFLA | → SAFLA stats | OK |
| Instincts | → Pattern report | OK |
| Securitate | → Secret scan | OK |
| LLM Status | → Model status | OK |
| Adaugă MCP | → Add MCP server | OK |

---

## OpenCode Desktop Config

```json
{
  "name": "CCDEW v6.1 SLIM",
  "provider": "anthropic",
  "model": "claude-opus-4-7",
  "mcp": {
    "claude-flow": "npx -y ruflo@latest mcp start"
  },
  "features": {
    "ssa": true,
    "safla": true,
    "codeburn": true,
    "ruflo": true,
    "sop-engine": true
  }
}
```

---

**CCDEW v3.9.3** — Mobile dashboard for OpenCode Desktop