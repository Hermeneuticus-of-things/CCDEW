#!/usr/bin/env python3
"""
BetterBird Cache Reader v3 - Citeste email-uri direct din cache-ul BetterBird
Nu necesita BetterBird running sau conexiune IMAP
"""

import os, json, re
from datetime import datetime
from email.header import decode_header

PROFILE = os.path.expanduser("~/.var/app/eu.betterbird.Betterbird/.thunderbird/b8e98ik1.default-default")
IMAP_DIR = os.path.join(PROFILE, "ImapMail")
OUTPUT_FILE = os.path.expanduser("~/.local/state/ccdew-email-prefilter.json")

DIR_TO_EMAIL = {
    "imap.gmail.com": "savorvegetarien@gmail.com",
    "imap.gmail-1.com": "ombundetotdetot@gmail.com",
    "imap.gmail-2.com": "Matei.Ionut.Catalin.Dominic@gmail.com",
    "imap.gmail-3.com": "forsunriseverify@gmail.com",
    "imap.gmail-4.com": "thingsofinternet2018@gmail.com",
    "imap.gmail-5.com": "themateiionutcatalin@gmail.com",
    "imap.gmx.com": "matei2020@gmx.fr",
}

def decode_subject(subject):
    try:
        decoded_parts = decode_header(subject)
        decoded = ""
        for part, charset in decoded_parts:
            if isinstance(part, bytes):
                decoded += part.decode(charset or "utf-8", errors="replace")
            else:
                decoded += part
        return decoded.strip()
    except:
        return subject

def clean_subject(subject):
    """Remove trailing headers from subject."""
    subject = subject.split("List-Unsubscribe:")[0].strip()
    subject = subject.split("Content-Type:")[0].strip()
    subject = subject.split("Reply-To:")[0].strip()
    subject = subject.split("X-Campaign")[0].strip()
    subject = subject.split("X-Priority:")[0].strip()
    subject = subject.split("X-User-ID:")[0].strip()
    subject = subject.split("X-Template:")[0].strip()
    return subject.rstrip()

def parse_mbox_file(filepath, account_name):
    emails = []
    try:
        with open(filepath, 'r', errors='replace') as f:
            content = f.read()
        
        messages = re.split(r'\nFrom - ', content)
        
        for msg in messages:
            if not msg.strip():
                continue
            
            header_end = msg.find('\n\n')
            if header_end == -1:
                continue
            headers = msg[:header_end]
            
            subject_match = re.search(r'^Subject:\s*(.+?)(?:\n[A-Z][a-z-]+:|\n\n|\Z)', headers, re.MULTILINE | re.DOTALL)
            from_match = re.search(r'^From:\s*(.+?)(?:\n[A-Z][a-z-]+:|\n\n|\Z)', headers, re.MULTILINE | re.DOTALL)
            date_match = re.search(r'^Date:\s*(.+?)(?:\n[A-Z][a-z-]+:|\n\n|\Z)', headers, re.MULTILINE | re.DOTALL)
            
            subject = ""
            if subject_match:
                raw = re.sub(r'\n\s+', ' ', subject_match.group(1).strip())
                subject = clean_subject(decode_subject(raw))
            
            from_addr = ""
            if from_match:
                raw = re.sub(r'\n\s+', ' ', from_match.group(1).strip())
                from_addr = raw
            
            date_str = ""
            if date_match:
                raw = re.sub(r'\n\s+', ' ', date_match.group(1).strip())
                date_str = raw
            
            if subject and from_addr and len(subject) > 3:
                emails.append({
                    "subject": subject,
                    "from": from_addr,
                    "date": date_str,
                    "account": account_name,
                })
    except:
        pass
    
    return emails

def main():
    inbox_files = []
    for root, dirs, files in os.walk(IMAP_DIR):
        for f in files:
            if f == "INBOX":
                inbox_files.append(os.path.join(root, f))
    
    all_emails = {}
    total_emails = 0
    
    for inbox_path in sorted(inbox_files):
        imap_dir = os.path.basename(os.path.dirname(inbox_path))
        account_name = DIR_TO_EMAIL.get(imap_dir, imap_dir)
        
        emails = parse_mbox_file(inbox_path, account_name)
        
        if account_name not in all_emails:
            all_emails[account_name] = {"keep_list": [], "archive_list": []}
        
        for i, email in enumerate(emails):
            email["id"] = f"{account_name}-{i}"
            all_emails[account_name]["keep_list"].append(email)
            total_emails += 1
    
    output = {
        "accounts": all_emails,
        "total_emails": total_emails,
        "generated_at": datetime.now().isoformat(),
        "source": "betterbird-cache"
    }
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"✓ {total_emails} emails din {len(all_emails)} conturi")

if __name__ == "__main__":
    main()
