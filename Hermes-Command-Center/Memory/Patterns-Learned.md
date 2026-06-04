---
tags: [patterns, learning, memory, email-analysis]
date: 2026-05-23
---

# 🧩 Patterns Learned

> **Pattern-uri și insight-uri extrase din analiza a 17,475 emailuri**
> *Aceste pattern-uri reprezintă "cunoștințele" acumulate de Hermes*

---

## 🔴 Pattern-uri Urgente (Recurente)

### Security Alerts
- **Frecvență**: ~15% din emailurile urgente
- **Sursă**: Conturi Gmail (în special [[savorvegetarien]])
- **Pattern**: Google trimite alerte de securitate la fiecare 2-3 săptămâni
- **Acțiune**: Verificare periodică a https://myaccount.google.com/security
- **Risc**: LOW (alerte preventive, nu incidente reale)

### Comenzi Online (Temu)
- **Frecvență**: ~65% din categoria Vehicul
- **Sursă**: [[savorvegetarien]]
- **Pattern**: Comenzi frecvente pe Temu, tracking livrări
- **Acțiune**: Monitorizare livrări, verificare colete
- **Insight**: Utilizatorul folosește intens Temu pentru cumpărături online

---

## 📧 Pattern-uri pe Conturi

### Conturi Gmail (6)
- **Pattern**: Toate conturile Gmail folosesc OAuth2
- **Pattern**: Conturile sunt folosite pentru scopuri diferite (personal, tech, verificare)
- **Pattern**: Gmail filtrează automat spam-ul agresiv
- **Insight**: Utilizatorul are o strategie de "compartimentalizare" a identităților online

### Cont GMX (1)
- **Pattern**: Singurul cont european (FR)
- **Pattern**: Folosește autentificare cu parolă (nu OAuth)
- **Insight**: Posibil utilizat pentru servicii EU-specific sau ca backup

---

## 🏷️ Pattern-uri Categorii

| Categorie | % din Total | Pattern Principal |
|-----------|-------------|-------------------|
| Urgent | 0.1% | Alerte securitate Google |
| Vehicul | 0.25% | Comenzi Temu, tracking |
| Legal | 0.03% | Documente sporadice |
| Financial | 0.006% | Foarte rar |
| Business | 0.07% | Tech/IoT related |
| Other | 0.1% | Newslettere, diverse |

---

## 🧠 Insight-uri Abstracte

### Comportament Email
1. **Volum**: ~2,184 emailuri/an (17,475 / 8 ani)
2. **Distribuție**: ~6 emailuri/zi în medie
3. **Peak**: Conturile Gmail primesc majoritatea volumului
4. **GMX**: Volum mult mai scăzut, posibil cont secundar

### Securitate
- Toate conturile Gmail au 2FA activ (bazat pe alertele de securitate)
- GMX folosește parolă directă (posibil fără 2FA)
- Nicio încercare de phishing detectată în analiză

### Preferințe
- Platformă preferată: Gmail (6/7 conturi)
- Client email: BetterBird (Thunderbird fork)
- Shopping: Temu (frecvent)
- Interese: Tech, IoT, vegetarianism (după nume conturi)

---

## 🔄 Pattern-uri de Învățare

### Ce am învățat despre utilizator
- [x] Are multiple identități online (compartimentalizare)
- [x] Folosește conturi Gmail pentru servicii Google
- [x] Folosește GMX pentru servicii EU
- [x] Cumpără frecvent de pe Temu
- [x] Monitorizează securitatea conturilor
- [ ] Încă nu am identificat pattern-uri de călătorie
- [ ] Încă nu am identificat pattern-uri medicale clare

### Ce ar trebui să învăț
- [ ] Pattern-uri temporale (când sunt cele mai multe emailuri)
- [ ] Relații între expeditori și conturi
- [ ] Evoluția volumului de email în timp
- [ ] Identificarea automată a emailurilor importante vs. noise

---

## 🔗 Legături

- [[Long-Term-Memory]] - Hub memorie
- [[Decisions-Log]] - Decizii bazate pe pattern-uri
- [[00-Dashboard]] - Dashboard principal
- [[Learning/Concepts]] - Concepte abstracte derivate

---

*Ultima actualizare: 2026-05-23*
*Sursă: Analiza Hermes a 17,475 emailuri*
