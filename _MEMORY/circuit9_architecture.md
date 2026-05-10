---
tags: [consiliu, qnapgx, circuit9, architecture, memory-layers, adaptive-routing]
created: 2026-05-10
project: Consiliu
---

# Circuit 9 — Arhitectura cu 9 Straturi + Rutare Adaptivă

## Principii

- **Sincretism**: teoria grafurilor + control cibernetic + optimizare runtime + homeostazie biologică
- **Conexiune**: lungime sarcină ↔ complexitate semantică ↔ resurse disponibile ↔ calitate vs viteză
- **Sinergie**: scurtarea produce salt calitativ — viteză fără pierdere critică de calitate

## Cele 9 Noduri / Straturi

| Nod | Strat | Rol |
|-----|-------|-----|
| 1 | Working Memory | Context imediat, input curent |
| 2 | Episodic Buffer | Istoric recent (ultima sesiune) |
| 3 | Procedural Memory | Skills, proceduri anterioare |
| 4 | Semantic Memory | Fapte, cunoaștere generală |
| 5 | Decision Layer | Rutare, planificare, decizie |
| 6 | Priority / Affect | Urgență, importanță, emoție |
| 7 | Skill Execution | Execuție tool-uri, acțiuni |
| 8 | Output Formation | Formulare răspuns |
| 9 | Consolidation | Învățare, pruning, entropie |

## Căi de Execuție

| Lungime | Noduri | Când | Motiv |
|---------|--------|------|-------|
| 3 | 1 → 5 → 9 | task < 60 chars, resurse > 85%, chat casual | Viteză maximă |
| 5 | 1 → 3 → 5 → 7 → 9 | context mediu, recall, skills anterioare | Balanță calitate-viteză |
| 9 | 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 | complex, nou, critic, calitate maximă | Calitate prioritară |

## Logica de Decizie

```python
if resource_load > 85 or len(task) < 60:
    return 3   # ultra-rapid
elif complexity < 45 or needs_recall:
    return 5   # balansat
else:
    return 9   # calitate maxima
```

## Scoring complexitate

```python
score = min(40, len(task) // 4)           # greutate lungime (//4 nu //5)
score += sum(10 for kw in KEYWORDS_COMPLEX if kw in task.lower())
score += min(20, "." * 5 + "?" * 3 + "," * 2)  # punctuatie
score += 5 if re.search(r"\d{4,}", task) else 0
score += 10 if re.search(r"```|def |class |import ", task) else 0
# Threshold: score >= 45 → 9 noduri | score < 45 → 5 noduri
```

## Cuvinte cheie complexitate

```python
KEYWORDS_COMPLEX = ["analiz", "strateg", "planific", "diagnos", "calcul",
                    "rezolv", "creativ", "plan ", "arhitectur", "decizi", "critic",
                    "migrare", "implementa", "proiecteaz", "urgent", "repara", "imediat",
                    "sincroniz", "holografic", "coreleaz", "integra", "configur", "optimiz",
                    "refactor", "propun", "reproiecteaz", "consolid", "migrar"]
# Test suite: 9/9 PASS (2026-05-10 v2 — spec-faithful)
```

## Entropia per Lungime

- **3 noduri**: entropie locală — curățare imediată după răspuns
- **5 noduri**: entropie procedurală — verifică + actualizează skill-urile (Strat 7)
- **9 noduri**: entropie globală — consolidare profundă + pruning memorie

## Implementare

- Modul Python: `/share/CACHEDEV1_DATA/agent_skills/circuit9.py`
- Trigger din QnapGX: `python3 -c "import urllib.request,json; print(urllib.request.urlopen('http://127.0.0.1:9879/skills/circuit9_run/run', data=json.dumps({'args':['TASK_TEXT']}).encode()).read().decode())"`
- Obsidian sync: `_MEMORY/circuit9_architecture.md` (acest fișier)
