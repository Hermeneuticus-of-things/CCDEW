# _SETTINGS/RULES/cerinta_noua.md — Cerinta Noua Mid-Task

> **Citit:** Cand user trimite o cerinta noua **in timp ce lucrez la alt task** (build, rebuild, fix, implementation in curs).
> **Scop:** Sa nu se piarda cerinta daca sesiunea crapa inainte sa ajung la ea.

## Regula centrala

Daca user trimite o **cerinta noua** in timp ce sunt mijloc de alt task, **IMEDIAT**:

1. **Opreste-te din task-ul curent** — nu termina operatia in progres, doar nu incepe una noua (ex: daca gradle build ruleaza, il las sa termine, dar nu pornesc alt build)

2. **Deschide `PROJECTS/<Proiect>/TODO.md`**

3. **Adauga o sectiune noua:**
```markdown
## 📌 CERINTA NOUA USER YYYY-MM-DD HH:MM

### Citat exact user:
> "textul exact"

### Interpretare:
- **Fisier tinta estimat:** [path]
- **Strategie:** [cum abordez]
- **Complexitate estimata:** [small / medium / large]

### Integrare:
[ ] amanata pentru V beta X.Y.Z
[ ] inclus in sesiunea curenta (dupa task-ul in progres)
[ ] prioritate imediata — pauzez task-ul curent
```

4. **ABIA APOI continui task-ul curent** (sau pauzez daca user a zis explicit "urgent")

## De ce fizic in TODO.md si nu doar TodoWrite

**TodoWrite** e in memorie Claude — **dispare la restart sesiune**.
**TODO.md** e fisier pe disk — **persista** intre sesiuni.

Daca sesiunea crapa / restart / inchis chat → cerinta dispare din TodoWrite dar ramane in TODO.md.

## NU ACCEPTA excuse

- ❌ "o sa retin pana termin" → nu, salvare fizica imediata
- ❌ "TodoWrite e suficient" → nu, TodoWrite e ephemeral
- ❌ "e o cerinta mica" → nu, indiferent cat de mica
- ❌ "sunt la mijloc de build" → nu, doar nu incepi operatie noua, dar TODO.md se actualizeaza

## Cand se pauzeaza task-ul curent (decizie rapida)

- Cerinta noua e **bug critical live** raportat de user → pauzez
- Cerinta noua e **clarificare la task-ul curent** → integrez, nu pauzez
- Cerinta noua e **feature separat** → salvez in TODO si continui task-ul curent
- User zice explicit **"urgent"** / **"opreste-te"** → pauzez imediat

Cand pauzez: marchez task-ul curent `[~] paused at step N` in TODO.md, continui cu cerinta noua.

## Integrare cu CHANGELOG

Cand ajung sa lucrez la cerinta noua → aplic session_start REGULA 1 (scrie in CHANGELOG INAINTE de cod). Cerinta e deja in TODO; CHANGELOG inregistreaza oficial inceperea lucrului.
