---
tags: [consiliu, circuit9, spec, sincretism, adaptive-routing, decision-rules]
created: 2026-05-11
project: Consiliu
type: specification
---

# Circuit 9 — Specificație Completă

## Principiul Sincretismului

Reunim: Teoria grafurilor (noduri și căi), controlul adaptiv din sistemele cibernetice, optimizarea runtime din programare și homeostazia biologică. Rezultatul: un Circuit 9 viu, care se comportă ca un sistem nervos ce alege automat cea mai bună cale.

## Principiul Conexiunii

Fiecare decizie de scurtare creează legături explicite între:
- Lungimea sarcinii
- Complexitatea semantică
- Resurse disponibile (RAM, CPU, timp)
- Necesitatea de calitate vs. viteză

## Principiul Sinergiei

Scurtarea produce un salt calitativ: viteză mare fără pierdere critică de calitate, prin activarea doar a nodurilor esențiale.

---

## Reguli Concrete de Scurtare (Noduri = Straturi)

**Circuit 9 complet (9 noduri):**
Traversarea completă Strat 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 + feedback.
Se folosește când calitatea maximă este prioritară.

**Circuit 9 scurtat la 5 noduri:**
Calea optimă: Strat 1 → 3 → 5 → 7 → 9

**Circuit 9 scurtat la 3 noduri:**
Calea ultra-rapidă: Strat 1 → 5 → 9

---

## Reguli de Decizie — Când se scurtează?

| Situație / Context | Lungime | Noduri | Motiv | Exemple |
|---|---|---|---|---|
| Task simplu, clar, factual | 3 noduri | 1 → 5 → 9 | Viteză maximă + calitate suficientă | "Ce oră este?", "Adaugă 2+2" |
| Query scurt (< 60 caractere) | 3 noduri | 1 → 5 → 9 | Eficiență + viteză | Întrebări directe, comenzi simple |
| Task mediu, necesită context | 5 noduri | 1 → 3 → 5 → 7 → 9 | Balanță calitate-viteză | "Cum am rezolvat task-ul similar ieri?" |
| Necesită skills / proceduri anterioare | 5 noduri | 1 → 3 → 5 → 7 → 9 | Calitate procedurală + eficiență | "Folosește tool-ul X cum ai făcut data trecută" |
| Task complex, analiză profundă | 9 noduri | Toate 9 | Calitate maximă | Plan strategic, rezolvare problemă nouă |
| Resurse limitate (RAM/CPU înalt) | 3 sau 5 | Scurtat automat | Eficiență + supraviețuire sistem | QNAP încărcat cu alte containere |
| Necesitate critică de acuratețe | 9 noduri | Toate 9 | Calitate prioritară | Calcul financiar, diagnostic tehnic |
| Sesiune rapidă / conversație casual | 3 noduri | 1 → 5 → 9 | Viteză + fluiditate | Chat relaxat, întrebări frecvente |
| Prima apariție a unui concept nou | 9 noduri | Toate 9 | Calitate (învățare profundă) | Subiect complet nou |

---

## Reguli Formale de Decizie (Logica Programatorului)

```python
def decide_circuit9_length(task: str, context) -> int:
    score_complexity = calculate_complexity(task)   # lungime + cuvinte cheie + entități
    resource_load = get_system_load()               # RAM, CPU pe QNAP

    if resource_load > 85 or len(task) < 60:
        return 3      # ultra-rapid

    elif score_complexity < 45 or "recall" in task.lower():
        return 5      # balansat

    else:
        return 9      # calitate maximă
```

---

## Entropia per Lungime

- **3 noduri:** Rezoluție rapidă (1→5→9) + Entropie locală — curățare imediată după răspuns
- **5 noduri:** Rezoluție medie + Entropie procedurală — verifică skill-urile din Strat 7
- **9 noduri:** Rezoluție completă + Entropie globală — consolidare + pruning profund

Această logică asigură că Circuitul 9 devine nucleul adaptiv al sistemului.

---

## Referințe implementare

- Spec completă: `_MEMORY/circuit9_spec.md` (acest fișier)
- Arhitectură + implementare: `_MEMORY/circuit9_architecture.md`
- Cod pe QNAP: `/share/CACHEDEV1_DATA/agent_skills/circuit9.py`
- Test suite: 9/9 PASS (2026-05-11)
