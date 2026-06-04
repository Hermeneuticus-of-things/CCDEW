#!/usr/bin/env python3
"""
Hermes Memory Sync v1.0
Sincronizează datele din analiza Hermes în vault-ul Obsidian.

Usage:
  python3 hermes-memory-sync.py --daily      # Generează daily note
  python3 hermes-memory-sync.py --weekly     # Generează weekly review
  python3 hermes-memory-sync.py --extract    # Extrage insight-uri noi
  python3 hermes-memory-sync.py --all        # Rulează tot
"""

import os, sys, json, glob
from datetime import datetime

HOME = os.path.expanduser("~")
VAULT = os.path.join(HOME, "CCDEW/Hermes-Command-Center")
MEMORY_DIR = os.path.join(VAULT, "Memory")
LEARNING_DIR = os.path.join(VAULT, "Learning")
EXTRACTS_DIR = os.path.join(VAULT, "Extracts")
DAILY_DIR = os.path.join(VAULT, "02-Daily-Notes")
SEMANTIC_DIR = os.path.join(HOME, "CCDEW/_MEMORY/semantic")

def ensure_dirs():
    for d in [EXTRACTS_DIR, DAILY_DIR]:
        os.makedirs(d, exist_ok=True)

def generate_daily_note():
    """Generează nota zilnică."""
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    weekday = today.strftime("%A")
    
    # Count emails analyzed
    semantic_files = glob.glob(os.path.join(SEMANTIC_DIR, "email-*.json"))
    urgent = sum(1 for f in semantic_files if _is_urgent(f))
    
    content = f"""---
tags: [daily, journal, {today.strftime('%Y-%m')}]
date: {date_str}
---

# 📅 {date_str} - {weekday}

### 🌅 Dimineața
- **Stare**: 
- **Prioritatea zilei**: 
- **Emailuri noi**: {len(semantic_files):,} total analizate

### 📧 Emailuri Procesate
- [ ] Inbox curățat
- [ ] Urgente tratate ({urgent} urgente detectate)
- [ ] Newslettere scanate

### 🧠 Insight-ul Zilei
> *Cel mai important lucru învățat azi:*

### ✅ Acțiuni Completate
- [ ] 
- [ ] 
- [ ] 

### 📝 Note și Idei
- 
- 
- 

### 🔗 Legături
- [[01-Inbox/Capture]] - Iteme noi capturate
- [[Memory/Patterns-Learned]] - Pattern-uri observate
- [[Learning/Learning-Queue]] - Progres învățare

### 🌆 Seara
- **Stare finală**: 
- **Mâine prioritizat**: 
- **Gratitudine**: 

---

*Generat automat de Hermes Memory Sync*
"""
    
    filepath = os.path.join(DAILY_DIR, f"{date_str}.md")
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"✅ Daily note creat: {filepath}")
    return filepath

def _is_urgent(filepath):
    try:
        with open(filepath) as f:
            data = json.load(f)
        return data.get('priority', 0) >= 8 or data.get('risk') == 'HIGH'
    except:
        return False

def extract_insights():
    """Extrage insight-uri din fișierele semantice."""
    files = glob.glob(os.path.join(SEMANTIC_DIR, "email-*.json"))
    insights = []
    
    for f in files[:50]:  # Sample 50
        try:
            with open(f) as fh:
                data = json.load(fh)
            
            cat = data.get('category', 'unknown')
            subj = data.get('subject', 'no subject')[:60]
            
            if cat != 'unknown' and cat != 'other':
                insights.append({
                    'category': cat,
                    'subject': subj,
                    'priority': data.get('priority', 0),
                    'risk': data.get('risk', 'SAFE')
                })
        except:
            pass
    
    # Group by category
    from collections import defaultdict
    by_cat = defaultdict(list)
    for i in insights:
        by_cat[i['category']].append(i)
    
    # Generate extract file
    today = datetime.now().strftime("%Y-%m-%d")
    content = f"""---
tags: [extracts, insights, {today}]
date: {today}
---

# 🔍 Extracte Emailuri - {today}

> **Insight-uri extrase automat din analiza semantică**

---

## 📊 Rezumat

- **Total emailuri analizate**: {len(files):,}
- **Insight-uri extrase**: {len(insights)}
- **Categorii identificate**: {len(by_cat)}

---

## 🏷️ Distribuție pe Categorii

"""
    
    for cat, items in sorted(by_cat.items(), key=lambda x: -len(x[1])):
        content += f"\n### {cat.upper()} ({len(items)} emailuri)\n\n"
        for item in items[:5]:
            content += f"- {item['subject']}\n"
        if len(items) > 5:
            content += f"- ... și încă {len(items) - 5}\n"
    
    content += """
---

*Generat automat de Hermes Memory Sync*
"""
    
    filepath = os.path.join(EXTRACTS_DIR, f"extract-{today}.md")
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"✅ Extracte create: {filepath}")
    return filepath

def generate_weekly_review():
    """Generează template pentru review săptămânal."""
    today = datetime.now()
    week = today.strftime("%Y-W%U")
    
    content = f"""---
tags: [weekly-review, review, {today.strftime('%Y-%m')}]
date: {today.strftime('%Y-%m-%d')}
---

# 📊 Weekly Review - {week}

> **Review săptămânal al sistemului Hermes**

---

## 📧 Emailuri Săptămâna Aceasta

- **Total primite**: 
- **Urgente**: 
- **Procesate**: 
- **Arhivate**: 

---

## 🧠 Pattern-uri Noi Observate

- 
- 
- 

---

## ✅ Acțiuni Completate

- [ ] 
- [ ] 
- [ ] 

---

## ❌ Ce nu a mers

- 
- 

---

## 🎯 Obiective Săptămâna Viitoare

- [ ] 
- [ ] 
- [ ] 

---

## 📚 Învățare

- **Ce am învățat**: 
- **Ce vreau să învăț**: 
- **Resurse descoperite**: 

---

## 🔗 Legături

- [[Memory/Patterns-Learned]] - Pattern-uri actualizate
- [[Decisions-Log]] - Decizii noi
- [[Learning/Learning-Queue]] - Progres

---

*„Review-ul regulat este cheia îmbunătățirii continue."*
"""
    
    filepath = os.path.join(MEMORY_DIR, f"Review-{week}.md")
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"✅ Weekly review creat: {filepath}")
    return filepath

def main():
    ensure_dirs()
    
    if '--daily' in sys.argv or '--all' in sys.argv:
        generate_daily_note()
    
    if '--extract' in sys.argv or '--all' in sys.argv:
        extract_insights()
    
    if '--weekly' in sys.argv or '--all' in sys.argv:
        generate_weekly_review()
    
    if len(sys.argv) == 1:
        print("Usage: python3 hermes-memory-sync.py [--daily|--weekly|--extract|--all]")
        print("\n✅ Rulare implicită (--all)...")
        generate_daily_note()
        extract_insights()
        generate_weekly_review()
    
    print("\n🧠 Sincronizare memorie completată!")

if __name__ == '__main__':
    main()
