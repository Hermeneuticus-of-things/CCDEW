#!/usr/bin/env python3
"""
Hermes Auto-Refresh Daemon
Monitorizează emailurile în timp real și re-generează dashboard-ul
la fiecare email nou detectat.

Funcționalități:
  1. Watch INBOX files pentru modificări (mtime/size)
  2. Diferențiere emailuri noi vs. existente
  3. Analiză rapidă doar pentru emailurile noi
  4. Regenerare dashboard HTML + notificare desktop
  5. Cronometru: verificare la fiecare 60 secunde

Usage:
  python3 hermes-auto-refresh.py --start      # Pornește daemon
  python3 hermes-auto-refresh.py --stop       # Oprește daemon
  python3 hermes-auto-refresh.py --status     # Status
"""
import os, sys, json, time, hashlib, subprocess
import glob
from datetime import datetime
from pathlib import Path

PID_FILE = os.path.expanduser("~/.local/state/hermes-daemon.pid")
INBOX_DIR = os.path.expanduser("~/.var/app/eu.betterbird.Betterbird/.thunderbird/b8e98ik1.default-default/ImapMail")
DASHBOARD = os.path.expanduser("~/CCDEW/_MEMORY/hermes-dashboard.html")
NOTIFIER = os.path.expanduser("~/CCDEW/.claude/helpers/hermes-notifier-v3.py")
ANALYZER = os.path.expanduser("~/CCDEW/.claude/helpers/hermes-autonomous.py")
STATE = os.path.expanduser("~/.local/state/hermes-daemon-state.json")

# Track known emails by hash
KNOWN_HASHES = set()

def save_state():
    with open(STATE, 'w') as f:
        json.dump({
            'last_check': datetime.now().isoformat(),
            'known_hashes': list(KNOWN_HASHES),
            'total_seen': len(KNOWN_HASHES)
        }, f)

def load_state():
    global KNOWN_HASHES
    if os.path.exists(STATE):
        try:
            with open(STATE) as f:
                data = json.load(f)
            KNOWN_HASHES = set(data.get('known_hashes', []))
        except:
            pass

def get_email_hash(filepath, offset=0):
    """Calculează hash bazat pe conținutul fișierului (last 5KB pentru rapid)."""
    try:
        size = os.path.getsize(filepath)
        with open(filepath, 'rb') as f:
            f.seek(max(0, size - 5120))  # Ultimii 5KB
            content = f.read()
        return hashlib.md5(content).hexdigest()[:16]
    except:
        return None

def scan_inboxes():
    """Scanează toate INBOX-urile și returnează hash-uri noi."""
    new_hashes = []
    all_hashes = []
    
    for root, dirs, files in os.walk(INBOX_DIR):
        for f in files:
            if f == 'INBOX':
                filepath = os.path.join(root, f)
                h = get_email_hash(filepath)
                if h:
                    all_hashes.append(h)
                    if h not in KNOWN_HASHES:
                        new_hashes.append(h)
    
    return new_hashes, all_hashes

def rebuild_dashboard():
    """Re-generează raportul Hermes HTML complet."""
    try:
        subprocess.run([sys.executable, ANALYZER, '--all'], 
                      capture_output=True, timeout=120)
        
        # Copy for easy access
        if os.path.exists(NS := os.path.expanduser("~/CCDEW/_MEMORY/hermes-command-center.html")):
            os.replace(NS, DASHBOARD)
        
        return True
    except Exception as e:
        print(f"Error rebuilding dashboard: {e}")
        return False

def send_new_email_notification(count, urgent_count=0):
    """Notificare desktop pentru emailuri noi."""
    try:
        urgency = "critical" if urgent_count > 0 else "normal"
        icon = "dialog-warning" if urgent_count > 0 else "mail-unread"
        
        msg = f"📧 {count} emailuri noi detectate"
        if urgent_count > 0:
            msg += f"\n🔴 {urgent_count} necesită atenție URGENTĂ!"
        
        subprocess.run([
            "notify-send", "-u", urgency, "-i", icon, "-t", "8000",
            "🧠 Hermes: Emailuri Noi", msg
        ], capture_output=True)
    except:
        pass

def daemon_main():
    """Loop principal daemon."""
    print("🔔 Hermes Auto-Refresh Daemon started")
    print(f"   Monitoring: {INBOX_DIR}")
    print(f"   Check interval: 60 seconds")
    print("   Press Ctrl+C to stop")
    
    load_state()
    
    # Initial scan
    new_hashes, all_hashes = scan_inboxes()
    if new_hashes:
        print(f"   Initial: {len(new_hashes)} new emails found")
        KNOWN_HASHES.update(new_hashes)
        rebuild_dashboard()
    
    save_state()
    
    cycle = 0
    while True:
        try:
            time.sleep(60)
            cycle += 1
            
            new_hashes, all_hashes = scan_inboxes()
            
            if new_hashes:
                print(f"[{datetime.now():%H:%M:%S}] {len(new_hashes)} NEW EMAILS!")
                
                # Rebuild dashboard
                rebuild_dashboard()
                
                # Check for urgent notifications using v3
                try:
                    subprocess.run([sys.executable, NOTIFIER], timeout=30)
                except:
                    pass
                
                # Update known
                KNOWN_HASHES.update(new_hashes)
                save_state()
            
            # Periodic full rebuild + notify check every 5 cycles (~5 min)
            if cycle % 5 == 0:
                print(f"[{datetime.now():%H:%M:%S}] Periodic rebuild...")
                rebuild_dashboard()
                # Also check for urgent notifications
                try:
                    subprocess.run([sys.executable, NOTIFIER], timeout=30)
                except:
                    pass
                
        except KeyboardInterrupt:
            print("\n✅ Daemon stopped")
            save_state()
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)

def start_daemon():
    if os.path.exists(PID_FILE):
        with open(PID_FILE) as f:
            old_pid = f.read().strip()
        if os.path.exists(f"/proc/{old_pid}"):
            print(f"Daemon already running (PID: {old_pid})")
            return
    
    pid = os.fork()
    if pid > 0:
        with open(PID_FILE, 'w') as f:
            f.write(str(pid))
        print(f"✅ Daemon started (PID: {pid})")
        return
    
    # Child process
    os.setsid()
    daemon_main()

def stop_daemon():
    if not os.path.exists(PID_FILE):
        print("Daemon not running")
        return
    
    with open(PID_FILE) as f:
        pid = f.read().strip()
    
    try:
        os.kill(int(pid), 15)  # SIGTERM
        os.remove(PID_FILE)
        print("✅ Daemon stopped")
    except ProcessLookupError:
        os.remove(PID_FILE)
        print("Daemon was not running, removed stale PID")
    except Exception as e:
        print(f"Error stopping daemon: {e}")

def status_daemon():
    if os.path.exists(PID_FILE):
        with open(PID_FILE) as f:
            pid = f.read().strip()
        if os.path.exists(f"/proc/{pid}"):
            print(f"✅ Daemon running (PID: {pid})")
            if os.path.exists(STATE):
                with open(STATE) as f:
                    data = json.load(f)
                print(f"   Last check: {data.get('last_check', 'N/A')}")
                print(f"   Total seen: {data.get('total_seen', 0)}")
        else:
            print("❌ Stale PID file")
    else:
        print("❌ Daemon not running")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Hermes Auto-Refresh Daemon')
    parser.add_argument('--start', action='store_true', help='Start daemon')
    parser.add_argument('--stop', action='store_true', help='Stop daemon')
    parser.add_argument('--status', action='store_true', help='Show status')
    args = parser.parse_args()
    
    if args.stop:
        stop_daemon()
    elif args.status:
        status_daemon()
    else:
        start_daemon()
