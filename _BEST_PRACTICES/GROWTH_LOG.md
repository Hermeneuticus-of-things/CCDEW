# _BEST_PRACTICES/GROWTH_LOG.md — Meta: Navigare, Reguli Creștere, Growth Log
## Citit: DOAR la audit, promovare/demovare pattern, sau decizie arhitecturală. NICIODATĂ la task normal.

---

## 🌳 Cross-links (fractal navigation)

### In jos (root → intermediat → proiect)

| Tip | Intermediat | Proiecte |
|---|---|---|
| **Android** | `_BEST_PRACTICES/android/BEST_PRACTICES.md` | MyAndroidApp |
| **Carte** | `_BEST_PRACTICES/carte/BEST_PRACTICES.md` | MyBook |
| **Generic** | `_BEST_PRACTICES/generic/BEST_PRACTICES.md` | MyResearch |

### In sus (proiect → root)

- **1 tip** → promovez la `_BEST_PRACTICES/<tip>/`
- **≥2 tipuri** → promovez la root `BEST_PRACTICES.md`
- Fiecare promovare = entry in acest growth log

### Lateral (intermediat ↔ intermediat)

Pattern in 2 intermediate = candidat clar pentru root.

---

## 🌱 Growth rules

### Cand ADAUG in root
- Evidenta la ≥2 tipuri diferite de proiect
- NU deja in intermediat sau proiect
- Independenta de stack/domeniu

### Cand DEMOVEZ din root
- Era specifica unui tip → mut la `_BEST_PRACTICES/<tip>/` cu nota `Demoted din root`
- Adaug entry in Growth log

### Cand PROMOVEZ spre root
- Evidenta in ≥2 tipuri
- Las referinta la intermediat
- Adaug entry in Growth log cu sursa

---

## 📈 Growth log (cronologic)

<!-- Add your optimization history here -->

---

## 📝 Cum adaug o lectie noua

1. Identific nivelul: proiect → intermediat → root (specificity-first)
2. Categorie: PATTERN sau ANTI-PATTERN
3. Format: `ID-NNN — Titlu` cu: Cand / Ce fac / De ce / Refs
4. Adaug entry în Growth log cu data + sursa
5. Cross-ref dacă se leagă de alt pattern

**Autorizare:** Nu trebuie confirmare user pentru adăugare lecții noi în BEST_PRACTICES.md — dar menționez explicit (ID + nivel) în răspuns.
