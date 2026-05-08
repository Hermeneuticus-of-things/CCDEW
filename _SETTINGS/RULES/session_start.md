# _SETTINGS/RULES/session_start.md — 3 Reguli Necondiționate

> **Citit:** La inceputul FIECAREI sesiuni noi Claude.
> **Durata:** ~1 min, pana cand devin reflex.
> **Context lookup:** `obsidian_global_search("session-start critical")` — inlocuieste citirea manuala a fisierelor la session start. Detalii: `obsidian_context_protocol.md`.

## ⛔ REGULA 1/3 — CHANGELOG INAINTE DE COD

La ORICE cerinta sau sub-cerinta primita de la user → scrie in `PROJECTS/<Proiect>/CHANGELOG.md` **INAINTE de prima linie de cod scris**.

### Ce scriu
- Header cerinta (data, titlu scurt, versiune viitoare)
- Citat exact user (intre ghilimele)
- Decizii cheie + interpretare
- Fisiere ce urmeaza a fi modificate (scope planificat)

### Ce NU fac
- Nu incep cod inainte sa scriu in CHANGELOG
- Nu amanez "pana la sfarsit" — se uita, se pierde
- Nu scriu vag ("minor fixes", "refactor") — format detaliat per `changelog.md`

**Daca ai inceput codul fara sa scrii → STOP, completeaza CHANGELOG, apoi continui.**

Detalii format: citeste `changelog.md`.

---

## ⛔ REGULA 2/3 — TODO PERSISTENT (ANTI-CRASH)

INAINTE de a incepe lucrul la orice task multi-pas → scrie task-urile in `PROJECTS/<Proiect>/TODO.md`.

### Format
```markdown
## Sesiune [data]
### Cerinta: [text]
- [ ] task neinceput
- [~] task in curs
- [x] task complet
```

### De ce
Daca sesiunea Claude crapa → urmatoarea sesiune citeste TODO.md si continua de unde am ramas. Fara TODO.md, munca se pierde.

Regula `TodoWrite` (in memorie) **NU inlocuieste** TODO.md fizic. `TodoWrite` e ephemeral. `TODO.md` persista.

### Cand updatez
- Actualizez checkbox-urile **pe masura ce termin** (nu la sfarsit)
- Marchez `[~]` cand incep un task
- Marchez `[x]` imediat dupa ce termin

---

## ⛔ REGULA 3/3 — EPILOG (ACTUALIZARE LA COMPLETARE)

La fiecare **ducere la capat a unei cerinte** → actualizeaza IMEDIAT:

1. **CHANGELOG.md** cu rezultatul complet:
   - Ce s-a facut (concret, fisiere + linii)
   - Fisiere modificate (lista)
   - Decizii luate
   - Note neasteptate
   - Versiune finala

2. **TODO.md** cu:
   - Checkbox `[x]` pe task-ul complet
   - Sumar scurt al modificarilor

### Scop
Sa nu se piarda istoric. Daca user zice _"lucruri care au fost cerute si implementate au disparut"_ → inseamna ca nu am actualizat la timp.

Aceasta regula previne exact asa ceva. **Niciodata nu inchei o cerinta fara actualizare** — chiar daca e typo sau fix de 1 linie.

---

---

## ⛔ REGULA 4/4 — MEMORY CHECK LA COMPLETARE (META-006)

La fiecare **cerinta dusa la capat** → INAINTE de a raporta "done":

1. Intreaba-te: *"Am descoperit ceva nou in aceasta sesiune care nu e inca in memorie?"*
2. Daca DA (bug pattern, preferinta user, decizie tehnica, lectie invatata) → scrie IMEDIAT in `memory/` cu frontmatter complet.
3. Obsidian se va deschide automat la nota noua (hook B activ).

### Ce merita salvat
- Preferinte user confirmate explicit
- Decizii tehnice cu motivatia lor
- Pattern-uri de bug descoperite si rezolvate
- Workflow-uri validate in aceasta sesiune

### Ce NU salvez
- Detalii cod (sunt in fisiere)
- Task-uri temporare (merg in TODO.md)
- Lucruri deja in memory/ (verifica MEMORY.md inainte)

**Daca nu e pe disc, nu exista la sesiunea urmatoare.**

---

## Aplica pe TOATE proiectele

Regulile astea sunt universal valabile — orice proiect, orice tip, orice dimensiune. **Fara exceptii.**

La task-uri workspace-level (ex: restructurare holografica), foloseste `_SETTINGS/CHANGELOG-FORMAT.md` in loc de `PROJECTS/<Nume>/CHANGELOG.md`.
