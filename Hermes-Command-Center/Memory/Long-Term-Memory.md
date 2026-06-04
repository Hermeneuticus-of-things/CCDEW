---
tags: [memory, system, long-term, hermes]
date: 2026-05-23
---

# 🧠 Long-Term Memory System

> **Sistemul de memorie persistentă al lui Hermes**
> *"Creierul digital care nu uită niciodată"*

---

## 🏗️ Arhitectura Memoriei

```
┌─────────────────────────────────────────┐
│         INPUT (Emailuri, Date)          │
└─────────────────┬───────────────────────┘
                  ▼
┌─────────────────────────────────────────┐
│      01-Inbox (Captură Rapidă)          │
│      - Emailuri importante              │
│      - Idei, task-uri, remindere        │
└─────────────────┬───────────────────────┘
                  ▼
┌─────────────────────────────────────────┐
│      02-Daily-Notes (Jurnal Zilnic)     │
│      - Context zilnic                   │
│      - Decizii luate                    │
│      - Pattern-uri observate            │
└─────────────────┬───────────────────────┘
                  ▼
┌─────────────────────────────────────────┐
│      PROCESARE (PARA Method)            │
│  03-Projects  → Acțiuni concrete        │
│  04-Areas     → Domenii de responsabilitate│
│  05-Resources → Cunoștințe de referință │
└─────────────────┬───────────────────────┘
                  ▼
┌─────────────────────────────────────────┐
│      MEMORY (Memorie pe Termen Lung)    │
│      - Patterns învățate                │
│      - Decizii și consecințe            │
│      - Concepte abstracte               │
└─────────────────┬───────────────────────┘
                  ▼
┌─────────────────────────────────────────┐
│      LEARNING (Învățare Continuă)       │
│      - Queue de învățare                │
│      - Review-uri periodice             │
│      - Conexiuni noi                    │
└─────────────────────────────────────────┘
```

---

## 📊 Starea Memoriei

| Tip | Count | Ultima Actualizare |
|-----|-------|-------------------|
| **Emailuri Indexate** | 17,475 | 2026-05-23 |
| **Pattern-uri Detectate** | [[Patterns-Learned\|Vezi lista]] | - |
| **Decizii Înregistrate** | [[Decisions-Log\|Vezi log]] | - |
| **Concepte Învățate** | [[Learning/Concepts\|Vezi concepte]] | - |
| **Extrase din Emailuri** | [[Extracts\|Vezi extrase]] | - |

---

## 🔗 Hub-uri de Memorie

### 🎯 Procesare Activă
- [[01-Inbox/Capture]] - Captură rapidă (GTD Inbox)
- [[02-Daily-Notes]] - Jurnal zilnic
- [[03-Projects]] - Proiecte active
- [[04-Areas]] - Zone de responsabilitate

### 🧠 Memorie Pe Termen Lung
- [[Memory/Patterns-Learned]] - Pattern-uri învățate din emailuri
- [[Memory/Decisions-Log]] - Jurnal decizii
- [[Memory/Review-Weekly]] - Review săptămânal
- [[Memory/People-Index]] - Index persoane/contacte

### 📚 Sistem de Învățare
- [[Learning/Learning-Queue]] - Coadă de învățare
- [[Learning/Concepts]] - Concepte abstracte
- [[Learning/Reviews]] - Review-uri periodice
- [[Learning/Spaced-Repetition]] - Repetiție spațiată

---

## 🔄 Ciclu de Viață al Informației

```
CAPTURE → PROCESS → DISTILL → EXPRESS → REVIEW
   ↓         ↓         ↓         ↓         ↓
 Inbox    Projects   Memory    Output   Learning
```

1. **CAPTURE** - Orice idee/email/task intră în [[01-Inbox/Capture]]
2. **PROCESS** - Procesat zilnic, mutat în proiecte sau arhivat
3. **DISTILL** - Extrase insight-uri, salvate în [[Memory]]
4. **EXPRESS** - Folosit pentru decizii, acțiuni, output
5. **REVIEW** - Revizuit periodic în [[Learning/Reviews]]

---

## 🛠️ Instrumente

### Template-uri Rapide
- `Ctrl + T` → [[Templates/Email-Analysis]] - Analiză email
- `Ctrl + D` → [[Templates/Daily-Note]] - Notă zilnică
- `Ctrl + C` → [[Templates/Concept]] - Notă concept

### Comenzi Hermes
```bash
# Sincronizează memoria cu emailurile noi
hermes-monitor sync

# Generează review săptămânal
python3 ~/CCDEW/.claude/helpers/hermes-memory-sync.py --weekly

# Extrage concepte noi
python3 ~/CCDEW/.claude/helpers/hermes-memory-sync.py --extract
```

---

*Sistem de memorie Hermes v2.0*
*"What you don't write down, you don't remember. What you don't review, you don't learn."*
