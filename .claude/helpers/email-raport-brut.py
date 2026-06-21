#!/usr/bin/env python3
"""
Raport emailuri: date brute + clasificare (Urgenta, Natura, Time Sensitive)
"""
import json, os, sys
from email.header import decode_header
from collections import defaultdict

HOME = os.path.expanduser("~")
PREFILTER = os.path.join(HOME, ".local", "state", "ccdew-email-prefilter.json")

def decode_subject(subject):
    try:
        parts = decode_header(subject)
        decoded = ""
        for part, charset in parts:
            if isinstance(part, bytes):
                decoded += part.decode(charset or "utf-8", errors="replace")
            else:
                decoded += part
        return decoded
    except:
        return subject

NATURE_RULES = [
    ("security", ["security", "unauthorized", "suspicious", "password", "2fa", "verification", "alert", "breach", "compromised"]),
    ("financial", ["payment", "invoice", "bank", "transfer", "salary", "fee", "charge", "refund", "subscription", "billing", "iban", "maintenance fee"]),
    ("legal", ["terms", "policy", "gdpr", "contract", "legal", "regulation", "declaration", "declaratie", "guvern", "dgfip", "impot", "tax"]),
    ("medical", ["medical", "health", "doctor", "clinic", "spital", "rezultat", "analize", "prescription"]),
    ("health", ["health", "insurance", "asigurare", "wellness"]),
    ("account", ["account", "login", "register", "welcome", "verify", "confirm", "activation", "maintenance"]),
    ("personal", ["family", "friend", "personal", "matei", "ionut", "catalin"]),
    ("administrative", ["admin", "settings", "preferences", "profile", "notification"]),
    ("technical", ["api", "token", "deploy", "server", "update", "upgrade", "expire", "github", "coding"]),
    ("business", ["business", "company", "client", "project", "meeting"]),
    ("commercial", ["order", "shipping", "delivery", "purchase", "shop", "store", "comanda"]),
    ("travel", ["flight", "hotel", "booking", "travel", "trip", "zbor", "hotel"]),
    ("logistics", ["shipping", "tracking", "courier", "posta", "livrare"]),
    ("vehicle", ["car", "auto", "insurance", "rovinieta", "itr"]),
    ("education", ["course", "training", "certification", "university", "school"]),
    ("professional", ["job", "career", "interview", "resume", "cv"]),
]

URGENCY_RULES = [
    ("immediate", ["delete in", "deletion in", "expire in", "expires in", "about to expire", "last chance", "final notice", "action required", "urgent", "critical", "immediate"]),
    ("today", ["today", "24 hours", "one day", "within 1", "by end of", "pana la", "azi"]),
    ("this_week", ["week", "7 days", "5 days", "3 days", "saptamana", "zile"]),
]

SEVERITY_RULES = [
    ("critical", ["account deletion", "unauthorized access", "breach", "compromised", "failed payment", "payment failed", "unsuccessful"]),
    ("high", ["expire", "expiring", "security alert", "suspicious", "verify your", "confirm your"]),
    ("medium", ["update", "new feature", "maintenance", "notification"]),
]

def classify(subject, from_addr):
    text = f"{decode_subject(subject)} {from_addr}".lower()
    nature = "other"
    nature_score = 0
    for n, keywords in NATURE_RULES:
        score = sum(1 for kw in keywords if kw in text)
        if score > nature_score:
            nature_score = score
            nature = n

    urgency = "no_deadline"
    urgency_score = 0
    for u, keywords in URGENCY_RULES:
        score = sum(1 for kw in keywords if kw in text)
        if score > urgency_score:
            urgency_score = score
            urgency = u

    severity = "low"
    severity_score = 0
    for s, keywords in SEVERITY_RULES:
        score = sum(1 for kw in keywords if kw in text)
        if score > severity_score:
            severity_score = score
            severity = s

    time_sensitive = "DA" if urgency in ("immediate", "today") else ("POATE" if urgency == "this_week" else "NU")
    return nature, urgency, severity, time_sensitive

def main():
    if not os.path.exists(PREFILTER):
        print(f"Nu am gasit prefilter: {PREFILTER}")
        sys.exit(1)

    with open(PREFILTER) as f:
        data = json.load(f)

    emails = []
    for account_name, account_data in data.get("accounts", {}).items():
        for msg in account_data.get("keep_list", []):
            subject = msg.get("subject", "")
            from_addr = msg.get("from", "")
            date = msg.get("date", "")
            nature, urgency, severity, time_sensitive = classify(subject, from_addr)
            emails.append({
                "account": account_name,
                "date": date,
                "from": from_addr,
                "subject": decode_subject(subject),
                "nature": nature,
                "urgency": urgency,
                "severity": severity,
                "time_sensitive": time_sensitive,
            })

    # Sortare: urgency, severity, nature, date desc
    urgency_order = {"immediate": 0, "today": 1, "this_week": 2, "no_deadline": 3}
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    emails.sort(key=lambda e: (
        urgency_order.get(e["urgency"], 9),
        severity_order.get(e["severity"], 9),
        e["nature"],
        e["date"],
    ))

    # Grupare
    grouped = defaultdict(lambda: defaultdict(list))
    for e in emails:
        grouped[e["urgency"]][e["nature"]].append(e)

    # Afișare
    lines = []
    lines.append("# 📧 RAPORT EMAILURI — Date brute + Clasificare")
    lines.append(f"**Total emailuri procesate:** {len(emails)}\n")

    for urgency in ["immediate", "today", "this_week", "no_deadline"]:
        if urgency not in grouped:
            continue
        ulabel = {"immediate": "🚨 URGENT (imediata)", "today": "⏰ AZI (today)", "this_week": "📅 SAPTAMANA ASTA", "no_deadline": "📁 FARA DEADLINE"}[urgency]
        lines.append(f"\n## {ulabel}")
        for nature in sorted(grouped[urgency].keys()):
            nicon = {"security": "🔒", "financial": "💰", "legal": "⚖️", "medical": "🏥", "health": "💚", "account": "👤", "personal": "🏠", "administrative": "⚙️", "technical": "🔧", "business": "💼", "commercial": "🛒", "travel": "✈️", "logistics": "📦", "vehicle": "🚗", "education": "🎓", "professional": "💼", "other": "📋"}.get(nature, "📋")
            lines.append(f"\n### {nicon} {nature.upper()}")
            lines.append("| Data | Cont | De la | Subiect | Severitate | Time Sensitive |")
            lines.append("|------|------|-------|---------|------------|----------------|")
            for e in grouped[urgency][nature]:
                subj = e['subject'].replace('|', '\\|').replace('\n', ' ').replace('\r', '')[:80]
                from_ = e['from'].replace('|', '\\|')[:40]
                lines.append(f"| {e['date']} | {e['account']} | {from_} | {subj} | {e['severity']} | {e['time_sensitive']} |")

    output = "\n".join(lines)
    print(output)

    out_path = os.path.join(HOME, ".local", "state", "ccdew-email-raport.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(output)
    print(f"\n\n✅ Raport salvat in: {out_path}")

if __name__ == "__main__":
    main()
