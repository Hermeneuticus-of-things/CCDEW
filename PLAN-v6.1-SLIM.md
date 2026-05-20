# ✅ Plan Complet de Implementare – v6.1 SLIM
**Realist & Anti-Overengineering**

> Rezolvă criticile majore: supracomplexitate, SSA vag, redundanță de orchestratori, estimări nerealiste de timp.

---

## 1. Repositories Utilizate (Surse Oficiale)

| Repository | Rol | Link |
|---|---|---|
| claude-code-eficient-workspace | Nucleu (Enneagram + Holographic Memory + Hooks) | [CCDEW](https://github.com/Hermeneuticus-of-things/claude-code-eficient-workspace) |
| SAFLA | Hybrid Memory + Self-Aware Feedback Loop | [SAFLA](https://github.com/ruvnet/SAFLA) |
| Ruflo | Orchestrator principal de swarms | [Ruflo](https://github.com/ruvnet/ruflo) |
| claude-code-setup-evaluator | Structură + Evaluator automat | [Evaluator](https://github.com/redhat-community-ai-tools/claude-code-setup-evaluator) |
| CodeBurn | Token & Cost Observability + Optimize | [CodeBurn](https://github.com/getagentseal/codeburn) |
| Obsidian | Graf vizual bidirectional (opțional) | (folosit deja în workspace) |

**Eliminate intenționat:** CrewAI, LangGraph, Graphify (prea multă redundanță).

---

## 2. Principii Fundamentale (Anti-Complexitate)

- **Enneagram (9 noduri)** = nucleu intangibil
- **SSA (Subquadratic Sparse Attention)** = modul concret și măsurabil
- Modularitate strictă cu **Feature Flags** (Lite / Full / SSA-Max)
- **Hook Dispatcher Central** = un singur punct de control
- Evaluare continuă obligatorie cu **CodeBurn + Red Hat evaluator**
- **"Less is More"** — scopul este să folosești sistemul, nu să-l întreții

---

## 3. Arhitectura Finală SLIM (6 componente)

| Componentă | Rol | Prioritate |
|---|---|---|
| Enneagram | Routing + Topologie swarm | Core |
| SSA Layer | Atenție inteligentă + Context Zoom | Core |
| Ruflo | Orchestrator principal + parallel agents | Orchestrare |
| SAFLA | Memorie hibridă + Feedback Loop | Memorie & Learning |
| Red Hat Evaluator + CodeBurn | Disciplină + Cost Control | Observability |
| Obsidian | Vizualizare (opțional) | Opțional |

---

## 4. SSA – Definiție Concretă & Implementare

### Definiție
**SSA = mecanism de selecție inteligentă a contextului** înainte ca orice agent să primească promptul.

### Implementare tehnică

```python
# ssa-attention.py
Calculează scor de relevanță pentru fiecare fișier/memorie/skill folosind:
- Semantic similarity (embeddings via SAFLA/Ruflo)
- Enneagram distance (cât de aproape e de nodul curent)
- Holographic related: links
- Istoric recent (episodic memory)

Selectează sparse context (Top-K + bonus related).
```

### Context Zoom Adaptiv
| Level | Context |
|---|---|
| **Maha** | Overview workspace |
| **Mega** | Proiect activ |
| **Mezzo** | Subdirector principal |
| **Micro** | Fișiere cheie |
| **Nano** | Secțiuni relevante din fișiere |

### Metrică obligatorie
```
SSA Efficiency Ratio = (tokens folosiți / tokens potențiali) → țintă < 25%
```

**Acest layer va fi obligatoriu testat cu CodeBurn înainte/după.**

---

## 5. Plan de Implementare pe Faze

### Faza 0: Pregătire & Baseline (4-6 ore)
- [ ] Clonează workspace-ul nou (eficient-synergy-v6.1)
- [ ] Adaugă submodules: SAFLA, Ruflo, Red Hat evaluator, CodeBurn
- [ ] Instalează codeburn + ruflo via MCP
- [ ] Rulează evaluarea inițială completă (Red Hat + CodeBurn)
- [ ] Git tag: `baseline-v6.1`

### Faza 1: Fundație Solidă (1-2 zile)
- [ ] Structură Red Hat (skills/, commands/, agent-docs/)
- [ ] Migrează conținutul vechi + adaugă frontmatter SSA
- [ ] Integrează Hook Dispatcher Central (`hook-dispatcher.cjs`)
- [ ] Implementează SSA Layer complet (`ssa-attention.py`)
- [ ] Integrează CodeBurn hooks (SessionEnd + optimize automat)

### Faza 2: Memorie + Learning (2-3 zile)
- [ ] SAFLA Memory Bridge (holographic ↔ SAFLA)
- [ ] Conectare META-017 Auto-Learn Hook cu SAFLA
- [ ] Safety layer + rollback
- [ ] Testare SSA + CodeBurn pe proiect pilot

### Faza 3: Ruflo Orchestration + Consolidare (3-4 zile)
- [x] Ruflo ca orchestrator principal
- [x] Extinde inject-workflow:
  - Enneagram routing
  - SSA Context Selection
  - Ruflo swarm_init + parallel agents (fiecare cu mini-SSA)
- [x] Template-uri hibride
- [x] Dashboard complet cu metrici CodeBurn + SSA Efficiency

### Faza 4: Optimizare & Team (opțional, 2-3 zile)
- [x] Team Sharing (anonimizat)
- [x] Obsidian Deep (opțional)
- [x] Moduri Lite/Full/SSA-Max

**Timp total realist pentru versiunea stabilă: 8-14 zile (nu ore!)**

---

## 6. Măsuri Anti-Riscuri (obligatorii)

- [ ] **Feature Flags** puternice în `settings.json` (poți dezactiva Ruflo, SAFLA, SSA)
- [ ] **Evaluator agresiv** rulează la fiecare SessionStart și flaghează orice creștere de tokeni
- [ ] **Hook Dispatcher central** → evită conflicte
- [ ] **Fallback automatic**: dacă Ruflo/SAFLA eșuează → revine la Enneagram pur
- [ ] **CodeBurn monitorizează continuu** token creep
- [ ] **Proiect pilot obligatoriu** înainte de aplicare pe toate proiectele

---

## 7. Flux Tipic (Simplu)

```
Task utilizator → inject-workflow
  ↓
Enneagram determină ruta
  ↓
SSA selectează context optim (Maha→Nano)
  ↓
Ruflo pornește swarm (parallel)
  ↓
La final → SAFLA învață + CodeBurn înregistrează + optimize
  ↓
Evaluator verifică
```

---

## 8. Dashboard Open-Cload v6.1

Dashboard-ul actual (`http://localhost:8765`) trebuie să afișeze:

| Metrică | Sursă | Display |
|---|---|---|
| SSA Efficiency | ssa-attention.py | % (verde < 25%, roșu > 40%) |
| Tokeni folosiți | CodeBurn | $/zi, total |
| Enneagram nod activ | inject-workflow | Badge cu emoji nod |
| SAFLA feedback | safla.json | Count + ultimul pattern |
| Swarm status | Ruflo | Active/inactive |
| LLM model | OpenRouter API | Badge + latență |

---

## 9. Feature Flags (settings.json)

```json
{
  "v6_1": {
    "enabled": true,
    "enneagram": true,
    "ssa_layer": true,
    "ruflo_orchestrator": false,
    "safla_learning": true,
    "codeburn_monitoring": true,
    "obsidian_viz": false,
    "mode": "full"
  },
  "ssa": {
    "efficiency_target": 0.25,
    "context_zoom": "auto",
    "top_k": 10
  }
}
```

---

## 10. MCP Integration

```bash
# MCP servers necesare
opencode mcp add claude-code-evaluator  # Red Hat Evaluator
opencode mcp add codeburn              # Cost monitoring
opencode mcp add ruflo                 # Swarm orchestration
opencode mcp add safla                 # Memory & Learning
opencode mcp add ssa-layer             # SSA Attention
```

---

*Plan generat: 2026-05-12 | Versiune: v6.1 SLIM*