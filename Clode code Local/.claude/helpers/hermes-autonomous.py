#!/usr/bin/env python3
"""
Hermes Autonomous Email Analyzer v1.0
Agent Zero Style: THINK → ACT → OBSERVE → REFLECT → CORRECT

Pipeline:
  1. SCAN:    Citește email-uri din cache BB (read-only /tmp copy)
  2. PARSE:   Extrage header, body, attachments
  3. CLASSIFY: Tag-uri inteligente (Urgent, Vehicul, Legal, Business, etc.)
  4. EXTRACT:  Entități (telefon, bani, date, locații)
  5. RISK:     Scor spam/phishing (0-100)
  6. ACTION:   Recomandare (Răspunde/Plătește/Programare/Ignoră)
  7. MEMORY:   Salvează în _MEMORY/{identity,semantic,alerts}
  8. SERVE:    Dashboard web la localhost:8767

Usage:
  python3 hermes-autonomous.py --scan       # Scan + clasificare
  python3 hermes-autonomous.py --analyze    # Full analysis + memory
  python3 hermes-autonomous.py --dashboard  # Porneste web dashboard
  python3 hermes-autonomous.py --all        # Pipeline complet
"""

import os, sys, json, re, time, hashlib, html
from datetime import datetime
from pathlib import Path
from collections import Counter

# ── Setup ────────────────────────────────────────────────────────────────────
HOME = os.path.expanduser("~")
CCDEW = os.path.join(HOME, "CCDEW")
MEMORY = os.path.join(CCDEWEW := CCDEW, "_MEMORY")
STATE = os.path.join(HOME, ".local", "state")

sys.path.insert(0, os.path.join(CCDEW, ".claude", "helpers", "lib"))

# Safe read-only profile
def get_ro_profile():
    """Returnează calea către copia read-only /tmp a profilului BB."""
    import tempfile, shutil
    bb = os.path.expanduser("~/.var/app/eu.betterbird.Betterbird/.thunderbird/b8e98ik1.default-default")
    tmp = tempfile.mkdtemp(prefix="hermes_ro_")
    for sub in ["ImapMail"]:
        src, dst = os.path.join(bb, sub), os.path.join(tmp, sub)
        if os.path.exists(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
    for f in ["prefs.js", "logins.json"]:
        src = os.path.join(bb, f)
        if os.path.exists(src):
            shutil.copy2(src, tmp)
    return tmp

# ── CONFIG ───────────────────────────────────────────────────────────────────
CATEGORIES = {
    "urgent":    {"keywords": ["urgent", "imediat", "asap", "deadline", "ultima zi", "expira", "știință", "alert"], "color": "#ff4444", "priority": 10},
    "vehicul":   {"keywords": ["mașină", "auto", "véhicule", "car", "voiture", "carte grise", "contrôle technique", "assurance auto", "permis"], "color": "#ff8800", "priority": 8},
    "legal":     {"keywords": ["notar", "avocat", "tribunal", "juridic", "legal", "drept", "contract", "proces", "cedează", "succesie", "testament"], "color": "#8800ff", "priority": 9},
    "financial": {"keywords": ["bancă", "bani", "plată", "factură", "fiscal", "impozit", "revenu", "salaire", "virement", "prélèvement", "remboursement"], "color": "#00aa44", "priority": 7},
    "business":  {"keywords": ["client", "proiect", "ofertă", "devis", "facture proforma", "meeting", "rendez-vous", "collaboration"], "color": "#0088ff", "priority": 6},
    "commercial":{"keywords": ["promo", "reducere", "soldes", "ofertă specială", "bon plan", "réduction", "code promo", "livraison gratuite"], "color": "#aaaaaa", "priority": 3},
    "medical":   {"keywords": ["doctor", "medic", "spital", "consultație", "ordonanță", "analyses", "rendez-vous médical"], "color": "#ff88cc", "priority": 7},
    "travel":    {"keywords": ["zbor", "bilet", "hotel", "vacanță", "rezervare", "voyage", "réservation", "avion", "train"], "color": "#00cccc", "priority": 5},
    "administratif":{"keywords": ["admin", "prefectură", "mairie", "impôts", "déclaration", "dossier", "carte d'identité"], "color": "#cc88ff", "priority": 6},
}

# Patterns extragere
PHONE_RE = re.compile(r'(?:(?:\+33|0)\s*[1-9](?:[\s\.-]?\d{2}){4})|(?:(?:\+40|0)\s*7\d{8})')
MONEY_RE = re.compile(r'(?i)(\d+[\s\.,]?\d*)\s*(€|EUR|euro|lei|RON|\$|USD)')
DATE_RE = re.compile(r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b')
EMAIL_RE = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
URL_RE = re.compile(r'https?://[^\s<>"\']+|www\.[^\s<>"\']+')

SPAM_INDICATORS = [
    ("urgency_pressure", ["click now", "act fast", "limited time", "exclusive deal", "you won", "congratulations", "urgent action required"], 15),
    ("suspicious_sender", ["no-reply", "noreply", "donotreply", "marketing", "newsletter"], 5),
    ("phishing", ["verify your account", "suspend", "unusual activity", "login attempt", "password expired", "confirm identity"], 25),
    ("too_good", ["100% free", "guaranteed", "risk free", "no obligation", " Act now"], 10),
    ("money_request", ["wire transfer", "send money", "western union", "gift card", "bitcoin", "crypto"], 20),
]

# ── CORE ENGINE ──────────────────────────────────────────────────────────────

class HermesEmailAnalyzer:
    def __init__(self, profile_path):
        self.profile = profile_path
        self.emails = []
        self.alerts = []
        self.stats = Counter()
        
    def parse_mbox_file(self, filepath, account_name):
        """Parse a single mbox file."""
        results = []
        if not os.path.exists(filepath):
            return results
        
        with open(filepath, 'rb') as f:
            content = f.read()
        
        # Simple mbox parser
        emails_raw = content.split(b'\nFrom ')
        
        for raw in emails_raw:
            if not raw.strip():
                continue
            try:
                # Try different encodings
                text = None
                for enc in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
                    try:
                        text = raw.decode(enc, errors='ignore')
                        break
                    except:
                        continue
                
                if not text:
                    continue
                
                email_data = self._parse_email(text, account_name)
                if email_data:
                    results.append(email_data)
            except Exception as e:
                continue
        
        return results
    
    def _parse_email(self, text, account):
        """Parse individual email text."""
        lines = text.split('\n')
        
        headers = {}
        body_lines = []
        in_body = False
        
        for line in lines:
            if not in_body:
                if line.strip() == '' or line.startswith(' '):
                    if any(h in headers for h in ['from', 'subject', 'date']):
                        in_body = True
                        if line.strip() == '':
                            continue
                else:
                    if ':' in line and not line.startswith(' '):
                        key, val = line.split(':', 1)
                        headers[key.lower().strip()] = val.strip()
            else:
                body_lines.append(line)
        
        body = '\n'.join(body_lines)
        
        # Skip if not enough data
        if not headers.get('subject') and not body.strip():
            return None
        
        return {
            'account': account,
            'from': headers.get('from', 'Unknown'),
            'subject': headers.get('subject', '(no subject)'),
            'date': headers.get('date', ''),
            'body': body[:5000],  # Limit body size
            'body_preview': body[:500].replace('\n', ' '),
            'raw_hash': hashlib.md5(text.encode('utf-8', errors='ignore')).hexdigest()[:16],
        }
    
    def classify_email(self, email):
        """Classify a single email into categories."""
        text = f"{email['subject']} {email['body']}".lower()
        
        scores = {}
        for cat, data in CATEGORIES.items():
            score = sum(1 for kw in data['keywords'] if kw.lower() in text)
            if score > 0:
                scores[cat] = score
        
        # Get top category
        if scores:
            top_cat = max(scores, key=scores.get)
            email['category'] = top_cat
            email['category_score'] = scores[top_cat]
            email['category_color'] = CATEGORIES[top_cat]['color']
            email['priority'] = CATEGORIES[top_cat]['priority']
        else:
            email['category'] = 'other'
            email['category_score'] = 0
            email['category_color'] = '#888888'
            email['priority'] = 1
        
        return email
    
    def extract_entities(self, email):
        """Extract phone numbers, money amounts, dates, urls."""
        text = f"{email['subject']} {email['body']}"
        
        email['entities'] = {
            'phones': list(set(PHONE_RE.findall(text))),
            'money': list(set(MONEY_RE.findall(text))),
            'dates': list(set(DATE_RE.findall(text))),
            'emails': list(set(EMAIL_RE.findall(text))),
            'urls': list(set(URL_RE.findall(text))),
        }
        
        return email
    
    def calculate_risk(self, email):
        """Calculate spam/phishing risk score (0-100)."""
        text = f"{email['subject']} {email['body']}".lower()
        score = 0
        reasons = []
        
        for rule_name, keywords, weight in SPAM_INDICATORS:
            matches = sum(1 for kw in keywords if kw.lower() in text)
            if matches > 0:
                score += weight * matches
                reasons.append(f"{rule_name}: {matches}x")
        
        # Additional checks
        sender = email['from'].lower()
        if any(s in sender for s in ['no-reply', 'noreply', 'marketing', 'newsletter']):
            score += 5
            reasons.append("generic_sender")
        
        # URL analysis
        urls = email['entities'].get('urls', [])
        suspicious_urls = [u for u in urls if any(s in u.lower() for s in ['bit.ly', 'tinyurl', 't.co', 'short.link'])]
        if suspicious_urls:
            score += 10 * len(suspicious_urls)
            reasons.append(f"short_url: {len(suspicious_urls)}")
        
        email['risk_score'] = min(100, score)
        email['risk_reasons'] = reasons
        
        if score >= 50:
            email['risk_level'] = 'HIGH'
        elif score >= 25:
            email['risk_level'] = 'MEDIUM'
        elif score > 0:
            email['risk_level'] = 'LOW'
        else:
            email['risk_level'] = 'SAFE'
        
        return email
    
    def recommend_action(self, email):
        """Recommend next action."""
        cat = email['category']
        risk = email['risk_level']
        
        if risk in ['HIGH', 'MEDIUM']:
            email['action'] = { 'type': 'REVIEW', 'text': 'Verifică manual - posibil spam/phishing', 'urgency': 10 }
        elif cat == 'urgent':
            email['action'] = { 'type': 'ACT_NOW', 'text': 'Acțiune urgentă necesară!', 'urgency': 10 }
        elif cat == 'vehicul':
            email['action'] = { 'type': 'SCHEDULE', 'text': 'Verifică documente/CT/programare', 'urgency': 8 }
        elif cat == 'legal':
            email['action'] = { 'type': 'CONSULT', 'text': 'Consultă avocatul/notarul', 'urgency': 9 }
        elif cat == 'financial':
            email['action'] = { 'type': 'PAY', 'text': 'Verifică plată/factură', 'urgency': 7 }
        elif cat == 'medical':
            email['action'] = { 'type': 'SCHEDULE', 'text': 'Programează consultație', 'urgency': 7 }
        elif cat == 'business':
            email['action'] = { 'type': 'REPLY', 'text': 'Răspunde clientului', 'urgency': 6 }
        elif cat == 'travel':
            email['action'] = { 'type': 'CONFIRM', 'text': 'Confirmă rezervarea', 'urgency': 5 }
        elif cat == 'commercial':
            email['action'] = { 'type': 'IGNORE', 'text': 'Poți ignora sau șterge', 'urgency': 1 }
        else:
            email['action'] = { 'type': 'READ', 'text': 'Citește când ai timp', 'urgency': 2 }
        
        return email
    
    def scan_all_accounts(self):
        """Scan all inbox files from all accounts."""
        imap_dir = os.path.join(self.profile, 'ImapMail')
        
        if not os.path.exists(imap_dir):
            print(f"✗ ImapMail not found: {imap_dir}")
            return 0
        
        total = 0
        for subdir in os.listdir(imap_dir):
            inbox_path = os.path.join(imap_dir, subdir, 'INBOX')
            if not os.path.exists(inbox_path):
                continue
            
            # Map directory to email
            account_map = {
                'imap.gmail.com': 'savorvegetarien@gmail.com',
                'imap.gmail-1.com': 'ombundetotdetot@gmail.com',
                'imap.gmail-2.com': 'Matei.Ionut.Catalin.Dominic@gmail.com',
                'imap.gmail-3.com': 'forsunriseverify@gmail.com',
                'imap.gmail-4.com': 'thingsofinternet2018@gmail.com',
                'imap.gmail-5.com': 'themateiionutcatalin@gmail.com',
                'imap.gmx.com': 'matei2020@gmx.fr',
            }
            account = account_map.get(subdir, subdir)
            
            emails = self.parse_mbox_file(inbox_path, account)
            self.emails.extend(emails)
            total += len(emails)
            print(f"  📧 {account:45} | {len(emails):5} emails")
        
        print(f"\n  Total raw emails parsed: {total}")
        return total
    
    def analyze_all(self):
        """Run full analysis on all emails."""
        print("\n🔬 HERMES: Analyzing emails...")
        
        analyzed = []
        for email in self.emails:
            email = self.classify_email(email)
            email = self.extract_entities(email)
            email = self.calculate_risk(email)
            email = self.recommend_action(email)
            analyzed.append(email)
        
        self.emails = analyzed
        
        # Stats
        cat_counts = Counter(e['category'] for e in analyzed)
        risk_counts = Counter(e['risk_level'] for e in analyzed)
        action_counts = Counter(e['action']['type'] for e in analyzed)
        
        print(f"\n📊 CLASSIFICATION:")
        for cat, count in cat_counts.most_common():
            print(f"  {CATEGORIES.get(cat, {}).get('color', '#888')} {cat:15} | {count:5}")
        
        print(f"\n⚠️  RISK ANALYSIS:")
        for risk, count in risk_counts.most_common():
            emoji = {'HIGH':'🔴','MEDIUM':'🟡','LOW':'🟢','SAFE':'✅'}.get(risk, '⚪')
            print(f"  {emoji} {risk:10} | {count:5}")
        
        print(f"\n🎯 RECOMMENDED ACTIONS:")
        for act, count in action_counts.most_common():
            print(f"  {act:15} | {count:5}")
        
        return analyzed
    
    def generate_alerts(self):
        """Generate high-priority alerts."""
        alerts = []
        
        urgent_emails = [e for e in self.emails if e['priority'] >= 8]
        high_risk = [e for e in self.emails if e['risk_level'] == 'HIGH']
        
        for e in urgent_emails[:10]:
            alerts.append({
                'level': 'URGENT',
                'account': e['account'],
                'subject': e['subject'][:80],
                'action': e['action']['text'],
                'entities': e['entities'],
            })
        
        for e in high_risk[:10]:
            alerts.append({
                'level': 'RISK',
                'account': e['account'],
                'subject': e['subject'][:80],
                'risk_score': e['risk_score'],
                'reasons': e['risk_reasons'],
            })
        
        self.alerts = alerts
        print(f"\n🚨 ALERTS GENERATED: {len(alerts)} (Urgent: {len(urgent_emails)}, High Risk: {len(high_risk)})")
        return alerts
    
    def save_to_memory(self):
        """Save results to CCDEW memory layers."""
        ensure_dir = lambda p: os.makedirs(p, exist_ok=True)
        
        # L3 Semantic - email topics
        semantic_dir = os.path.join(MEMORY, "semantic")
        ensure_dir(semantic_dir)
        
        for e in self.emails[:100]:  # Only save top 100
            key = f"email-{e['category']}-{e['raw_hash']}"
            filepath = os.path.join(semantic_dir, f"{key}.json")
            with open(filepath, 'w') as f:
                json.dump({
                    'key': key,
                    'timestamp': datetime.now().isoformat(),
                    'account': e['account'],
                    'subject': e['subject'],
                    'category': e['category'],
                    'priority': e['priority'],
                    'risk': e['risk_level'],
                    'action': e['action'],
                    'entities': e['entities'],
                    'body_preview': e['body_preview'],
                }, f, indent=2, ensure_ascii=False)
        
        # L4 Identity - consolidated summary
        identity_dir = os.path.join(MEMORY, "identity")
        ensure_dir(identity_dir)
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_emails': len(self.emails),
            'categories': dict(Counter(e['category'] for e in self.emails)),
            'risk_distribution': dict(Counter(e['risk_level'] for e in self.emails)),
            'top_senders': Counter(e['from'] for e in self.emails).most_common(10),
            'urgent_count': sum(1 for e in self.emails if e['priority'] >= 8),
            'high_risk_count': sum(1 for e in self.emails if e['risk_level'] == 'HIGH'),
        }
        
        with open(os.path.join(identity_dir, f"hermes-email-summary-{datetime.now():%Y%m%d}.json"), 'w') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        # State file
        state_file = os.path.join(STATE, "hermes-email-analysis.json")
        ensure_dir(STATE)
        with open(state_file, 'w') as f:
            json.dump({
                'last_run': datetime.now().isoformat(),
                'total_analyzed': len(self.emails),
                'alerts': len(self.alerts),
                'accounts': list(set(e['account'] for e in self.emails)),
            }, f, indent=2)
        
        print(f"\n💾 Memory saved:")
        print(f"  Semantic layer (L3): {semantic_dir}")
        print(f"  Identity layer (L4): {identity_dir}")
        print(f"  State: {state_file}")

# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    import argparse
    parser = argparse.ArgumentParser(description='Hermes Autonomous Email Analyzer')
    parser.add_argument('--scan', action='store_true', help='Scan emails from BB')
    parser.add_argument('--analyze', action='store_true', help='Full analysis + memory')
    parser.add_argument('--all', action='store_true', help='Complete pipeline')
    args = parser.parse_args()
    
    if not any([args.scan, args.analyze, args.all]):
        parser.print_help()
        return
    
    print("="*70)
    print("  HERMES AUTONOMOUS EMAIL ANALYZER v1.0")
    print("  Agent Zero Style: THINK → ACT → OBSERVE → REFLECT → CORRECT")
    print("="*70)
    
    # Get safe read-only copy
    print("\n📦 Preparing read-only profile copy...")
    ro_profile = get_ro_profile()
    print(f"  ✓ Copy: {ro_profile}")
    
    hermes = HermesEmailAnalyzer(ro_profile)
    
    # Phase 1: SCAN
    if args.scan or args.all:
        print("\n🔍 PHASE 1: SCANNING ALL ACCOUNTS")
        print("-"*70)
        count = hermes.scan_all_accounts()
        if count == 0:
            print("✗ No emails found!")
            return
    
    # Phase 2: ANALYZE
    if args.analyze or args.all:
        print("\n🧠 PHASE 2: ANALYZING")
        print("-"*70)
        hermes.analyze_all()
        
        # Phase 3: ALERTS
        print("\n🚨 PHASE 3: GENERATING ALERTS")
        print("-"*70)
        hermes.generate_alerts()
        
        # Phase 4: MEMORY
        print("\n💾 PHASE 4: SAVING TO MEMORY")
        print("-"*70)
        hermes.save_to_memory()
    
    print("\n" + "="*70)
    print("  ✅ HERMES ANALYSIS COMPLETE")
    print("="*70)
    
    # Cleanup
    import shutil
    shutil.rmtree(ro_profile, ignore_errors=True)
    print(f"\n🧹 Cleaned temporary copy")

if __name__ == '__main__':
    main()
