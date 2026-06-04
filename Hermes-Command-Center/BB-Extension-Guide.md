# 🧠 Ghid Utilizare - Hermes Agent Zero în BetterBird

> **Cum vezi, folosești și configurezi extensia**

---

## 📍 PASUL 1: Deschide BetterBird

```bash
flatpak run eu.betterbird.Betterbird
```

---

## 📍 PASUL 2: Găsește Extensia

### Opțiunea A - Buton în Toolbar (Recomandat)

1. **Uită-te în toolbar-ul de sus** (lângă butoanele New Message, Reply, etc.)
2. **Caută iconița** 🧠 (sau un cerc albastru cu punct)
3. **Dacă NU o vezi:**
   - Apasă pe **≡** (meniu hamburger, stânga-sus)
   - **View → Toolbars → Customize Toolbar**
   - Caută "Hermes" sau 🧠 în lista de elemente
   - **Trage-o** în toolbar
   - Apasă **Done**

### Opțiunea B - Meniu Add-ons

1. **≡ → Add-ons → Extensions**
2. Caută: **"Hermes Agent Zero - Voice Alerts"**
3. Ar trebui să apară ca **activă** (verde)

---

## 📍 PASUL 3: Ce Vezi Când Apeși

### Popup-ul Extensiei:

```
┌─────────────────────────────────┐
│  🧠 Hermes Agent Zero           │
│  ─────────────────────────────  │
│  Status: 🟢 Activ               │
│  Emailuri analizate: 1,247      │
│  Alerte trimise: 3              │
│                                 │
│  CONTROALE:                     │
│  [🔊 Voce: ON]                  │
│  [📊 Nivel minim: 7]            │
│  [⏱️ Interval: 60 sec]          │
│                                 │
│  ACȚIUNI:                       │
│  [🔍 Scanează acum]             │
│  [🗣️ Test voce]                 │
│                                 │
│  TIPURI DE ATENȚIE:             │
│  🔴 RĂSPUNS URGENT              │
│  💰 PLATĂ NECESARĂ              │
│  📅 PROGRAMARE                  │
│  🔒 SECURITATE                  │
│  📦 LIVRARE                     │
│  👁️ REVIEW                      │
└─────────────────────────────────┘
```

---

## 📍 PASUL 4: Cum Funcționează

### AUTOMAT (Fără să apeși nimic)

1. **Daemonul Python** rulează în fundal
2. **Scanează** emailurile la fiecare 60 secunde
3. **Detectează** emailuri urgente
4. **VORBEȘTE** automat cu voce Supertonic AI
5. **Arată** notificare desktop

### MANUAL (Când apeși butonul)

1. **Click pe 🧠** în toolbar
2. **Vezi status** curent
3. **Ajustezi setări**:
   - Pornit/Oprit voce
   - Nivel minim de alertă
   - Interval de scanare
4. **Testezi vocea**

---

## 📍 PASUL 5: Setări Recomandate

| Setare | Valoare | Efect |
|--------|---------|-------|
| **Voce** | ON | Vorbește când e urgent |
| **Nivel minim** | 7 | Doar importantele |
| **Interval** | 60s | Verifică every minut |

### Ce înseamnă "Nivel minim":

- **5** → Vorbește la ORICE (inclusiv newslettere)
- **7** → Doar emailuri importante (recomandat)
- **8** → Doar URGENTE (foarte strict)
- **9** → Doar CRITICE (extrem de strict)

---

## 📍 PASUL 6: Testare

### Test Voce:
1. Click pe 🧠
2. Apasă **"Test voce"**
3. Ar trebui să auzi:
   > *"Hermes Agent Zero funcționează corect. Sistemul de voce în limba română funcționează corect."*

### Test Alertă Reală:
1. Așteaptă să primești un email urgent
2. Sau: Modifică nivelul minim la 5 temporar
3. Daemonul ar trebui să vorbească automat

---

## 📍 COMENZI RAPIDE (Terminal)

```bash
# Pornește toate serviciile
hermes-monitor start

# Testează vocea
hermes-monitor voice test

# Verifică status
hermes-monitor status

# Oprește tot
hermes-monitor stop
```

---

## ❌ Dacă Nu Funcționează

### Problema: Nu văd iconița 🧠
**Soluție:**
1. ≡ → View → Toolbars → Customize Toolbar
2. Caută "Hermes" în lista de elemente
3. Trage-o în toolbar

### Problema: Nu aude vocea
**Soluție:**
1. Verifică volumul sistemului
2. Rulează: `hermes-monitor voice test`
3. Verifică dacă Supertonic e instalat:
   ```bash
   ls ~/.local/share/supertonic-venv/bin/supertonic
   ```

### Problema: Extensia nu apare în Add-ons
**Soluție:**
1. Închide BetterBird complet
2. Verifică fișierul:
   ```bash
   ls ~/.var/app/eu.betterbird.Betterbird/.thunderbird/*/extensions/hermes-agent-zero*
   ```
3. Redeschide BetterBird

---

## ✅ CHECKLIST

- [ ] BetterBird deschis
- [ ] Iconița 🧠 vizibilă în toolbar
- [ ] Click pe 🧠 deschide popup
- [ ] "Test voce" funcționează
- [ ] Daemonul rulează în fundal
- [ ] Primești notificări pentru emailuri urgente

---

*Extensia este activă și funcțională!*
