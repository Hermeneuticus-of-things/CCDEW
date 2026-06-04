#!/usr/bin/env python3
"""
Hermes Deep Link Generator
Extrage Message-ID din fiecare email pentru link-uri directe în BetterBird.
Generează mapare hash → message_id și adaugă în raport HTML.
"""
import os, json, glob, hashlib
from collections import Counter

PROFILE = os.path.expanduser("~/.var/app/eu.betterbird.Betterbird/.thunderbird/b8e98ik1.default-default")
OUTPUT_JSON = os.path.expanduser("~/CCDEW/_MEMORY/hermes-message-ids.json")

def extract_message_ids(inbox_path):
    """Extrage Message-ID pentru fiecare email din INBOX mbox."""
    results = {}
    
    if not os.path.exists(inbox_path):
        return results
    
    with open(inbox_path, 'rb') as f:
        content = f.read()
    
    # Split mbox entries
    raw_emails = content.split(b'\nFrom ')
    
    for raw in raw_emails:
        if not raw.strip():
            continue
        
        try:
            text = raw.decode('utf-8', errors='ignore')
        except:
            continue
        
        # Generate hash (same as analyzer)
        raw_hash = hashlib.md5(raw).hexdigest()[:16]
        
        # Extract Message-ID
        message_id = None
        subject = None
        lines = text.split('\n')
        
        for line in lines[:50]:  # Headers only
            l = line.lower()
            if l.startswith('message-id:'):
                message_id = line.split(':', 1)[1].strip().strip('<>').strip()
            elif l.startswith('subject:'):
                subject = line.split(':', 1)[1].strip()
        
        if message_id:
            results[raw_hash] = {
                'message_id': message_id,
                'subject': subject or '(no subject)',
            }
    
    return results

def scan_all_accounts():
    """Scan all INBOXes and build complete message-id database."""
    print("🔍 Scanning all accounts for Message-IDs...")
    
    imap_dir = os.path.join(PROFILE, 'ImapMail')
    if not os.path.exists(imap_dir):
        print("✗ ImapMail not found!")
        return {}
    
    account_map = {
        'imap.gmail.com': 'savorvegetarien@gmail.com',
        'imap.gmail-1.com': 'ombundetotdetot@gmail.com',
        'imap.gmail-2.com': 'Matei.Ionut.Catalin.Dominic@gmail.com',
        'imap.gmail-3.com': 'forsunriseverify@gmail.com',
        'imap.gmail-4.com': 'thingsofinternet2018@gmail.com',
        'imap.gmail-5.com': 'themateiionutcatalin@gmail.com',
        'imap.gmx.com': 'matei2020@gmx.fr',
    }
    
    all_ids = {}
    
    for subdir in os.listdir(imap_dir):
        inbox_path = os.path.join(imap_dir, subdir, 'INBOX')
        if not os.path.exists(inbox_path):
            continue
        
        account = account_map.get(subdir, subdir)
        ids = extract_message_ids(inbox_path)
        
        for h, data in ids.items():
            all_ids[h] = {
                **data,
                'account': account,
                'folder': 'INBOX',
            }
        
        print(f"  📧 {account:45} | {len(ids):5} Message-IDs extracted")
    
    # Save
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(all_ids, f, indent=2)
    
    print(f"\n✓ Total Message-IDs: {len(all_ids)}")
    print(f"  Saved: {OUTPUT_JSON}")
    
    return all_ids

if __name__ == '__main__':
    scan_all_accounts()
