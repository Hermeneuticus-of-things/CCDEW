# 🧠 Hermes-Command-Center

> **Vault Obsidian pentru Management Emailuri**
> Generat automat de sistemul Hermes Email Intelligence

---

## 📁 Structura Vault-ului

```
Hermes-Command-Center/
├── .obsidian/              # Configurare Obsidian
├── 00-Dashboard.md         # 🎯 Dashboard principal
├── Accounts/               # 📧 Conturi email (7 fișiere)
│   ├── savorvegetarien.md
│   ├── matei-ionut-catalin-dominic.md
│   ├── ombundetotdetot.md
│   ├── forsunriseverify.md
│   ├── thingsofinternet2018.md
│   ├── themateiionutcatalin.md
│   └── matei2020-gmx.md
├── Categories/             # 🏷️ Categorii emailuri (6 fișiere)
│   ├── Categorie-Urgent.md
│   ├── Categorie-Vehicul.md
│   ├── Categorie-Legal.md
│   ├── Categorie-Financial.md
│   ├── Categorie-Business.md
│   └── Categorie-Other.md
├── Providers/              # 📡 Provideri email (2 fișiere)
│   ├── Provider-Gmail.md
│   └── Provider-GMX.md
└── Analysis/               # 🔍 Analize și rapoarte (3 fișiere)
    ├── Analiza-Risc.md
    ├── Timeline-Emailuri.md
    └── Actiuni-Recomandate.md
```

---

## 🚀 Cum să folosești

### Deschidere în Obsidian

1. **Instalează Obsidian** (dacă nu ai deja):
   ```bash
   # Descarcă de la https://obsidian.md/download
   # Sau folosește Flatpak:
   flatpak install flathub md.obsidian.Obsidian
   ```

2. **Deschide vault-ul**:
   ```bash
   # Dacă Obsidian e instalat:
   obsidian ~/CCDEW/Hermes-Command-Center
   
   # Sau manual din Obsidian:
   # Open folder as vault → Selectează ~/CCDEW/Hermes-Command-Center
   ```

### Navigare

- **Dashboard**: Începe de la `00-Dashboard.md`
- **Graf**: Vezi conexiunile în Graph View (Ctrl+G)
- **Legături**: Folosește wiki-links `[[nume-fișier]]` pentru navigare
- **Tag-uri**: Folosește panoul de tag-uri pentru filtrare

---

## 📊 Date incluse

| Tip | Cantitate |
|-----|-----------|
| **Conturi Email** | 7 |
| **Provideri** | 2 (Gmail, GMX) |
| **Categorii** | 6 principale |
| **Emailuri Analizate** | 17,475 |
| **Emailuri Urgente** | 68 |

---

## 🔗 Conexiuni principale

### Conturi → Provideri
- Toate conturile Gmail → [[Provider-Gmail]]
- Contul GMX → [[Provider-GMX]]

### Conturi → Categorii
- Fiecare cont poate avea emailuri în multiple categorii
- Ex: [[savorvegetarien]] are emailuri în [[Categorie-Urgent]] și [[Categorie-Vehicul]]

### Dashboard → Toate
- [[00-Dashboard]] conține link-uri către toate conturile, categoriile și providerii

---

## 🛠️ Actualizare

Pentru a re-genera vault-ul cu date noi:
```bash
# Rulează analizatorul Hermes
python3 ~/CCDEW/.claude/helpers/hermes-autonomous.py --all

# Vault-ul se poate actualiza manual sau re-crea
```

---

*Generat automat pe 2026-05-23*
*Sistem: Hermes Email Intelligence v1.0*
