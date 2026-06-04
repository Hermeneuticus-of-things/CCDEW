#!/usr/bin/env python3
"""
Hermes Notifier v3 - Final
Folosește Message-ID stabil + filtrează doar emailurile URGENTE (priority >= 8 sau risk=HIGH).

Flow:
1. Încarcă hermes-message-ids.json (stabil, generat o singură dată)
2. Încarcă analiza semantică din _MEMORY/semantic/*.json
3. Notifică DOAR emailurile cu priority >= 8 sau risk == 'HIGH'
4. Marchează ca văzute permanent în ~/.local/state/hermes-v3-seen.json
"""
import os, sys, json, subprocess, glob
from datetime import datetime

HOME = os.path.expanduser("~")
MSG_FILE = os.path.join(HOME, "CCDEW/_MEMORY/hermes-message-ids.json")
SEMANTIC_DIR = os.path.join(HOME, "CCDEW/_MEMORY/semantic")
DB_FILE = os.path.join(HOME, ".local/state/hermes-v3-seen.json")

def load_json(path, default=None):
    if os.path.exists(path):
        try:
            with open(path) as f:
                return json.load(f)
        except:
            pass
    return default or {}

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def notify(title, message, urgency="normal", icon="dialog-information"):
    try:
        subprocess.run(["notify-send", "-u", urgency, "-i", icon, "-t", "10000", title, message],
                      check=False, capture_output=True)
        return True
    except:
        return False

def msgid_from_key(key):
    """Extract Message-ID from a message-id registry key."""
    if key in MSG_IDS:
        return MSG_IDS[key].get('message_id', '')
    return ''

def find_urgent_alerts():
    """Scan semantic files and return list of (stable_id, analysis_data) for urgent emails."""
    alerts = []
    files = glob.glob(os.path.join(SEMANTIC_DIR, "email-*.json"))
    
    for f in files:
        try:
            data = load_json(f)
            priority = data.get('priority', 0)
            risk = data.get('risk', 'SAFE')
            
            if priority >= 8 or risk == 'HIGH':
                # Use Message-ID if available, otherwise use filename as stable ID
                mid = data.get('message_id', '')
                if not mid:
                    # Use filename without extension as stable identifier
                    mid = os.path.basename(f).replace('.json', '')
                
                if mid:
                    alerts.append((mid, data))
        except:
            pass
    
    # Sort by priority desc
    alerts.sort(key=lambda x: x[1].get('priority', 0), reverse=True)
    return alerts

def main():
    global MSG_IDS
    MSG_IDS = load_json(MSG_FILE, {})
    seen = load_json(DB_FILE, {})
    
    alerts = find_urgent_alerts()
    new_alerts = []
    
    for mid, data in alerts:
        if mid not in seen:
            new_alerts.append((mid, data))
    
    if not new_alerts:
        print(f"[{datetime.now():%H:%M:%S}] ✓ Nu sunt emailuri urgente noi.")
        print(f"         Total văzute: {len(seen)} | Total analizat: {len(glob.glob(os.path.join(SEMANTIC_DIR, 'email-*.json')))}")
        return 0
    
    print(f"[{datetime.now():%H:%M:%S}] 🔔 {len(new_alerts)} alerte urgente noi!")
    sent = 0
    
    for mid, data in new_alerts[:5]:  # Max 5
        cat = data.get('category', 'other')
        risk = data.get('risk', 'SAFE')
        priority = data.get('priority', 0)
        action = data.get('action', {})
        
        emoji = "🔴" if risk == 'HIGH' else "🟡"
        urgency = "critical" if risk == 'HIGH' else "normal"
        icon = "dialog-warning" if risk == 'HIGH' else "mail-unread"
        
        subject = data.get('subject', 'Fără subiect')[:60]
        account = data.get('account', 'N/A')
        action_text = action.get('text', 'Verifică')
        
        title = f"{emoji} HERMES: {cat.upper()} ({priority}/10)"
        msg = f"{subject}\n💡 {action_text}\n📧 {account}"
        
        if notify(title, msg, urgency, icon):
            seen[mid] = {
                "subject": subject,
                "account": account,
                "category": cat,
                "timestamp": datetime.now().isoformat()
            }
            sent += 1
            print(f"  ✓ {account}: {subject[:50]}")
    
    save_json(DB_FILE, seen)
    print(f"  Total dismiss: {len(seen)} | Notificat acum: {sent}")
    return sent

if __name__ == '__main__':
    main()
