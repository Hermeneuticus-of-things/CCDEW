#!/usr/bin/env python3
"""
CCDEW Email Intelligence Module
Extinde hermes-email-orchestrator cu:
  - Thread tracking / deduplicare inteligentă
  - Entity extraction (date, sume, termene)
  - Phishing detection
  - Sentiment / priority scoring
  - Calendar event extraction
  - SAFLA feedback loop
"""

import re, json, os, hashlib
from datetime import datetime, timedelta
from collections import defaultdict
from email.header import decode_header

# ── Deduplication ───────────────────────────────────────────────────────────
def normalize_subject(subject):
    """Normalize subject for thread grouping."""
    try:
        parts = decode_header(subject)
        decoded = ""
        for part, charset in parts:
            if isinstance(part, bytes):
                decoded += part.decode(charset or "utf-8", errors="replace")
            else:
                decoded += part
        s = decoded
    except:
        s = subject
    # Remove Re:/Fwd:/FW: prefixes, lowercase, strip punctuation
    s = re.sub(r'^(Re:|Fwd:|FW:|转发：|答复：)\s*', '', s, flags=re.I)
    s = s.lower().strip()
    s = re.sub(r'[^\w\s]', '', s)
    s = re.sub(r'\s+', ' ', s)
    return s[:80]

def thread_key(subject, from_addr):
    """Generate a thread key for deduplication."""
    norm = normalize_subject(subject)
    # Extract domain from from_addr
    domain = ""
    m = re.search(r'@([^>\s]+)', from_addr)
    if m:
        domain = m.group(1).lower()
    return hashlib.md5(f"{norm}|{domain}".encode()).hexdigest()[:16]

# ── Entity Extraction ───────────────────────────────────────────────────────
def extract_entities(subject, from_addr):
    """Extract money amounts, dates, deadlines from subject."""
    text = f"{subject} {from_addr}"
    entities = {
        "amounts": [],
        "dates": [],
        "deadlines": [],
        "urls": [],
        "codes": [],
    }
    # Money amounts: €123.45, $100, 123 EUR, etc.
    for m in re.finditer(r'[€$£¥]\s*([\d.,]+(?:\s*[KkMmBb])?)\s*(?:USD|EUR|GBP)?', text):
        entities["amounts"].append(m.group(0).strip())
    for m in re.finditer(r'([\d.,]+)\s*(?:EUR|USD|GBP|lei|ron)', text, re.I):
        entities["amounts"].append(m.group(0).strip())

    # Dates: 2025-03-17, 17/03/2025, March 17, etc.
    date_patterns = [
        r'\b(\d{4}-\d{2}-\d{2})\b',
        r'\b(\d{2}/\d{2}/\d{4})\b',
        r'\b(\d{2}\.\d{2}\.\d{4})\b',
    ]
    for pat in date_patterns:
        for m in re.finditer(pat, text):
            entities["dates"].append(m.group(1))

    # Deadlines: "in 7 days", "by March 17", "termenul 31 martie"
    deadline_keywords = [
        r'(?:in|within)\s+(\d+)\s+(?:days?|hours?|zile?)',
        r'(?:by|before|până la|pana la|termenul|deadline)\s+(.{0,30})',
        r'(?:expires?|expiră|expira)\s+(.{0,25})',
    ]
    for pat in deadline_keywords:
        for m in re.finditer(pat, text, re.I):
            entities["deadlines"].append(m.group(0).strip())

    # URLs
    for m in re.finditer(r'https?://[^\s<>"{}|\\^`\[\]]+', text):
        entities["urls"].append(m.group(0))

    # Codes / verification codes
    for m in re.finditer(r'\b(?:code|cod|verification|verify|token)\s*[:#]?\s*(\d{4,8})\b', text, re.I):
        entities["codes"].append(m.group(1))

    return entities

# ── Phishing Detection ──────────────────────────────────────────────────────
PHISHING_PATTERNS = [
    ("suspicious_sender", r'no-?reply@.*\.(tk|ml|ga|cf|gq|top|xyz|click|link|work)$'),
    ("impersonation", r'(security|support|verify|confirm|update|account)@.*\.(com|net|org|co\.\w{2})$'),
    ("urgency_scam", r'\b(verify (?:your|immediately)|suspend|disable|locked|unusual activity|confirm now)\b'),
    ("link_mismatch", None),  # would need HTML body for full check
]

def detect_phishing(subject, from_addr, body_hint=""):
    """Simple phishing score 0-100."""
    text = f"{subject} {from_addr} {body_hint}".lower()
    score = 0
    reasons = []

    # Check sender domain vs display name
    display = re.search(r'^"?([^"<]+)"?\s*<', from_addr)
    if display:
        disp_name = display.group(1).lower()
        domain_match = re.search(r'@([^>\s]+)', from_addr)
        if domain_match:
            domain = domain_match.group(1).lower()
            # If display name contains "google", "amazon", "paypal" but domain doesn't match
            brand_domains = {
                'google': ['google.com', 'accounts.google.com'],
                'amazon': ['amazon.com', 'amazon.co.uk', 'amazon.fr', 'amazon.de'],
                'paypal': ['paypal.com'],
                'apple': ['apple.com', 'icloud.com'],
                'microsoft': ['microsoft.com', 'outlook.com', 'live.com'],
                'facebook': ['facebook.com', 'fb.com', 'meta.com'],
                'instagram': ['instagram.com'],
                'netflix': ['netflix.com'],
            }
            for brand, legit_domains in brand_domains.items():
                if brand in disp_name and not any(d in domain for d in legit_domains):
                    score += 40
                    reasons.append(f"Possible impersonation of {brand} from {domain}")

    # Check patterns in text
    if re.search(r'\b(verify your account|confirm your identity|update your information)\b', text):
        score += 15
        reasons.append("Urgent verification language")
    if re.search(r'\b(suspended|locked|unauthorized access|breach)\b', text):
        score += 15
        reasons.append("Fear-based language")
    if re.search(r'\b(won|winner|lottery|prize|gift card)\b', text):
        score += 20
        reasons.append("Reward scam language")
    if len(re.findall(r'http', text)) > 2:
        score += 10
        reasons.append("Multiple links")

    return {
        "phishing_score": min(score, 100),
        "phishing_risk": "HIGH" if score >= 60 else "MEDIUM" if score >= 30 else "LOW",
        "phishing_reasons": reasons,
    }

# ── Sentiment & Priority Scoring ───────────────────────────────────────────
def compute_priority_score(classification, entities, phishing):
    """Compute a priority score 0-100 for inbox ordering."""
    score = 0
    # Base from urgency
    urgency_scores = {"immediate": 40, "today": 30, "this_week": 20, "no_deadline": 5}
    score += urgency_scores.get(classification.get("urgency", "no_deadline"), 0)

    # Severity
    severity_scores = {"critical": 30, "high": 20, "medium": 10, "low": 0}
    score += severity_scores.get(classification.get("severity", "low"), 0)

    # Nature boost
    nature_boost = {"security": 10, "financial": 10, "legal": 8, "medical": 8, "account": 5}
    score += nature_boost.get(classification.get("nature", ""), 0)

    # Amount boost
    if entities.get("amounts"):
        score += 5

    # Phishing penalty (inverse: phishing emails get lower priority unless security)
    if phishing.get("phishing_risk") == "HIGH" and classification.get("nature") != "security":
        score -= 20

    return max(0, min(100, score))

# ── Calendar Event Extraction ───────────────────────────────────────────────
def extract_calendar_events(subject, from_addr, date_str):
    """Extract potential calendar events from email metadata."""
    events = []
    text = f"{subject} {from_addr}".lower()

    # Meeting patterns
    meeting_patterns = [
        r'\b(meeting|meet|call|interview|appointment|rendez-vous|întâlnire)\b',
        r'\b(webinar|webina[rz]|atelier|workshop|curs)\b',
        r'\b(scheduled for|on \w+day|\d{1,2}:\d{2})\b',
    ]
    is_meeting = any(re.search(p, text) for p in meeting_patterns)

    # Flight / travel
    travel_patterns = [
        r'\b(flight|boarding pass|check-?in|booking reference|zbor)\b',
        r'\b(hotel reservation|check-?in|check-?out)\b',
    ]
    is_travel = any(re.search(p, text) for p in travel_patterns)

    if is_meeting:
        events.append({"type": "meeting", "source": "subject", "date_hint": date_str})
    if is_travel:
        events.append({"type": "travel", "source": "subject", "date_hint": date_str})

    # Try to extract exact date from subject
    exact_date = None
    for m in re.finditer(r'(\d{4}-\d{2}-\d{2})', subject):
        try:
            datetime.strptime(m.group(1), "%Y-%m-%d")
            exact_date = m.group(1)
            break
        except:
            pass
    if exact_date:
        events.append({"type": "deadline", "date": exact_date, "source": "subject_date"})

    return events

# ── SAFLA Feedback Loop ─────────────────────────────────────────────────────
SAFLA_STATE = os.path.expanduser("~/.local/state/ccdew-safla-email.json")

def load_safla():
    if os.path.exists(SAFLA_STATE):
        with open(SAFLA_STATE) as f:
            return json.load(f)
    return {"actions": [], "patterns": {}}

def save_safla(data):
    os.makedirs(os.path.dirname(SAFLA_STATE), exist_ok=True)
    with open(SAFLA_STATE, "w") as f:
        json.dump(data, f, indent=2)

def record_action(email_ref, action_type, classification):
    """Record user action for SAFLA learning."""
    safla = load_safla()
    safla["actions"].append({
        "email_ref": email_ref,
        "action": action_type,
        "nature": classification.get("nature"),
        "urgency": classification.get("urgency"),
        "severity": classification.get("severity"),
        "time": datetime.now().isoformat(),
    })
    # Update pattern weights
    key = f"{classification.get('nature')}:{classification.get('urgency')}:{classification.get('severity')}"
    if key not in safla["patterns"]:
        safla["patterns"][key] = {"archive": 0, "reply": 0, "flag": 0, "read": 0, "total": 0}
    safla["patterns"][key][action_type] = safla["patterns"][key].get(action_type, 0) + 1
    safla["patterns"][key]["total"] += 1
    save_safla(safla)

def suggest_action(classification):
    """Suggest action based on SAFLA learned patterns."""
    safla = load_safla()
    key = f"{classification.get('nature')}:{classification.get('urgency')}:{classification.get('severity')}"
    pat = safla["patterns"].get(key, {})
    if not pat or pat.get("total", 0) < 3:
        return classification.get("action", "Nimic")  # fallback to rule-based
    # Most common action for this pattern
    actions = {k: v for k, v in pat.items() if k != "total"}
    if actions:
        best = max(actions, key=actions.get)
        return best
    return classification.get("action", "Nimic")

# ── Rich Classification ─────────────────────────────────────────────────────
def enrich_classification(subject, from_addr, date_str, base_classification):
    """Add all intelligence layers to a base classification."""
    entities = extract_entities(subject, from_addr)
    phishing = detect_phishing(subject, from_addr)
    priority = compute_priority_score(base_classification, entities, phishing)
    events = extract_calendar_events(subject, from_addr, date_str)
    thread = thread_key(subject, from_addr)
    suggested = suggest_action(base_classification)

    enriched = dict(base_classification)
    enriched.update({
        "time_sensitive": "yes" if base_classification.get("urgency") in ("immediate", "today") else "no",
        "entities": entities,
        "phishing_score": phishing["phishing_score"],
        "phishing_risk": phishing["phishing_risk"],
        "phishing_reasons": phishing["phishing_reasons"],
        "priority_score": priority,
        "calendar_events": events,
        "thread_key": thread,
        "suggested_action": suggested,
    })
    return enriched

# ── Batch Deduplication ─────────────────────────────────────────────────────
def deduplicate_emails(email_list):
    """Deduplicate emails by thread key, keeping the newest."""
    threads = defaultdict(list)
    for e in email_list:
        tk = thread_key(e.get("subject", ""), e.get("from", ""))
        threads[tk].append(e)

    deduped = []
    for tk, items in threads.items():
        # Keep the one with the most recent date, or the one with highest priority
        # For simplicity, keep the newest by date string
        items.sort(key=lambda x: x.get("date", ""), reverse=True)
        deduped.append(items[0])
    return deduped

if __name__ == "__main__":
    # Quick test
    test = {
        "subject": "Action required: Account deletion in 7 days",
        "from": "Mozilla <accounts@firefox.com>",
        "date": "2026-05-18",
    }
    base = {
        "nature": "account",
        "urgency": "immediate",
        "severity": "critical",
        "action": "Răspunde în termenul specificat",
    }
    enriched = enrich_classification(test["subject"], test["from"], test["date"], base)
    print(json.dumps(enriched, indent=2, ensure_ascii=False))
