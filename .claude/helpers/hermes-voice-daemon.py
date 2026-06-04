#!/usr/bin/env python3
"""
Hermes Agent Zero Voice Daemon v3.0
Vorbire corectă în română, fără suprapuneri, cu coadă de procesare.

Usage:
  python3 hermes-voice-daemon.py --start    # Start daemon (background)
  python3 hermes-voice-daemon.py --stop     # Stop daemon
  python3 hermes-voice-daemon.py --status   # Check status
  python3 hermes-voice-daemon.py --test     # Test voice
  python3 hermes-voice-daemon.py            # Run foreground
"""

import os, sys, json, time, glob, subprocess, hashlib, threading
from datetime import datetime
from pathlib import Path

# ── Configuration ──
HOME = os.path.expanduser("~")
SEMANTIC_DIR = os.path.join(HOME, "CCDEW/_MEMORY/semantic")
CONFIG_FILE = "/tmp/hermes-agent-zero-config.json"
ALERTS_FILE = "/tmp/hermes-agent-zero-alerts.json"
PID_FILE = os.path.expanduser("~/.local/state/hermes-voice-daemon.pid")
SEEN_DB = os.path.expanduser("~/.local/state/hermes-voice-seen.json")

DEFAULT_CONFIG = {
    "enabled": True,
    "voice_enabled": True,
    "min_priority": 7,
    "cooldown_minutes": 30,
    "language": "ro",
    "voice_type": "female3",
    "speech_rate": -20,
    "speech_volume": 50,
    "speak_template": True
}

# ── Attention Types with Romanian Voice Messages ──
ATTENTION_MESSAGES = {
    "URGENT_RESPONSE": {
        "ro": "Atenție maximă! Email urgent de la {sender}. Subiect: {subject}. Necesită răspuns imediat!",
        "priority": 10,
        "emoji": "🔴"
    },
    "PAYMENT": {
        "ro": "Atenție! Email cu plată de la {sender}. Subiect: {subject}. Verifică factura și confirmă plata.",
        "priority": 9,
        "emoji": "💰"
    },
    "SCHEDULE": {
        "ro": "Email cu programare de la {sender}. Subiect: {subject}. Confirmă dacă poți participa.",
        "priority": 8,
        "emoji": "📅"
    },
    "SECURITY": {
        "ro": "Alertă de securitate de la {sender}. Subiect: {subject}. Verifică contul imediat.",
        "priority": 8,
        "emoji": "🔒"
    },
    "DELIVERY": {
        "ro": "Update livrare de la {sender}. Subiect: {subject}. Coletul tău este în drum sau a sosit.",
        "priority": 7,
        "emoji": "📦"
    },
    "REVIEW": {
        "ro": "Email important de la {sender}. Subiect: {subject}. Citește când ai timp, necesită atenție.",
        "priority": 7,
        "emoji": "👁️"
    }
}

# ── Keyword Classification ──
KEYWORDS = {
    "URGENT_RESPONSE": ["urgent", "asap", "imediat", "important", "răspunde", "reply needed", "action required", "attention"],
    "PAYMENT": ["plată", "payment", "factură", "invoice", "bill", "sumă", "amount", "card", "tranzacție", "pay"],
    "SCHEDULE": ["programare", "appointment", "meeting", "întâlnire", "calendar", "event", "invitație", "schedule"],
    "SECURITY": ["security", "securitate", "alert", "suspicious", "login", "password", "parolă", "autentificare", "unauthorized"],
    "DELIVERY": ["livrare", "delivery", "colet", "package", "tracking", "expediere", "shipped", "arrives", "temu"],
    "REVIEW": ["review", "confirm", "verification", "verify", "update", "notificare", "notification"]
}

# ═══════════════════════════════════════════════════════════════
# VOICE QUEUE SYSTEM (No Overlap)
# ═══════════════════════════════════════════════════════════════

class VoiceQueue:
    """Speech queue that processes messages one by one without overlap."""
    
    def __init__(self):
        self.queue = []
        self.lock = threading.Lock()
        self.speaking = False
        self.thread = threading.Thread(target=self._process_loop, daemon=True)
        self.thread.start()
    
    def enqueue(self, text, lang="ro", voice="female3", rate=-20, volume=50):
        """Add message to speech queue."""
        with self.lock:
            self.queue.append({
                "text": text,
                "lang": lang,
                "voice": voice,
                "rate": rate,
                "volume": volume
            })
        print(f"📝 Added to speech queue ({len(self.queue)} pending)")
    
    def _process_loop(self):
        """Process speech queue in background thread."""
        while True:
            message = None
            with self.lock:
                if self.queue:
                    message = self.queue.pop(0)
            
            if message:
                self.speaking = True
                self._speak(message)
                self.speaking = False
                time.sleep(1)  # Brief pause between messages
            else:
                time.sleep(0.5)
    
    def _speak(self, msg):
        """Speak a single message using spd-say with Romanian config."""
        text = msg["text"]
        lang = msg["lang"]
        voice = msg["voice"]
        rate = msg["rate"]
        volume = msg["volume"]
        
        print(f"🗣️  SPEAKING [{lang}][{voice}][r={rate}]: {text[:80]}...")
        
        try:
            # Use Popen for non-blocking execution, then wait for completion
            proc = subprocess.Popen(
                ["spd-say", "-l", lang, "-t", voice, "-r", str(rate), "-i", str(volume), text],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Wait for speech to complete (timeout 60s max)
            proc.wait(timeout=60)
            print(f"✅ Speech completed")
            return True
            
        except subprocess.TimeoutExpired:
            print("⚠️ Speech timeout, killing")
            proc.kill()
            return False
        except Exception as e:
            print(f"❌ Speech error: {e}")
            return False
    
    def is_speaking(self):
        return self.speaking
    
    def pending_count(self):
        with self.lock:
            return len(self.queue)

# Global voice queue
voice_queue = VoiceQueue()

# ═══════════════════════════════════════════════════════════════
# VOICE INTERFACE
# ═══════════════════════════════════════════════════════════════

def speak(text, lang="ro", voice="female3", rate=-20, volume=50):
    """Add text to speech queue (non-blocking)."""
    if not text:
        return False
    voice_queue.enqueue(text, lang, voice, rate, volume)
    return True

def speak_sync(text, lang="ro", voice="female3", rate=-20, volume=50):
    """Speak synchronously (blocking, for testing)."""
    print(f"🗣️  SYNC SPEAK: {text[:80]}...")
    try:
        proc = subprocess.Popen(
            ["spd-say", "-l", lang, "-t", voice, "-r", str(rate), "-i", str(volume), text],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        proc.wait(timeout=60)
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_voice():
    """Test voice system with all attention types."""
    print("🎤 Testing Romanian voice system...")
    
    test_messages = [
        "Hermes Agent Zero verificat. Sistemul de voce în limba română funcționează corect.",
        "Atenție maximă! Email urgent. Necesită răspuns imediat!",
        "Alertă de securitate. Verifică contul imediat.",
        "Update livrare. Coletul tău este în drum.",
        "Email cu programare. Confirmă dacă poți participa."
    ]
    
    for i, msg in enumerate(test_messages, 1):
        print(f"\n🧪 Test {i}/{len(test_messages)}")
        speak_sync(msg, "ro", "female3", -20, 50)
        time.sleep(1)
    
    print("\n✅ Voice test complete")
    print(f"📊 Speech queue pending: {voice_queue.pending_count()}")

# ═══════════════════════════════════════════════════════════════
# AGENT ZERO CORE
# ═══════════════════════════════════════════════════════════════

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        except:
            pass
    return DEFAULT_CONFIG.copy()

def load_seen():
    if os.path.exists(SEEN_DB):
        try:
            with open(SEEN_DB) as f:
                return json.load(f)
        except:
            pass
    return {}

def save_seen(seen):
    os.makedirs(os.path.dirname(SEEN_DB), exist_ok=True)
    with open(SEEN_DB, 'w') as f:
        json.dump(seen, f, indent=2)

def classify_email(data):
    subject = (data.get('subject', '') + ' ' + data.get('body', '')).lower()
    sender = data.get('account', 'unknown').lower()
    
    best_type = "REVIEW"
    best_score = 0
    
    for att_type, keywords in KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in subject)
        if score > best_score:
            best_score = score
            best_type = att_type
    
    # Overrides
    if "temu" in sender or "temu" in subject:
        best_type = "DELIVERY"
        best_score = max(best_score, 3)
    
    if "google" in sender and ("security" in subject or "alert" in subject):
        best_type = "SECURITY"
        best_score = max(best_score, 3)
    
    return best_type, best_score

def get_email_hash(data):
    content = f"{data.get('subject','')}{data.get('account','')}{data.get('date','')}"
    return hashlib.md5(content.encode()).hexdigest()[:16]

def process_email(filepath, config, seen):
    try:
        with open(filepath) as f:
            data = json.load(f)
    except:
        return None
    
    att_type, score = classify_email(data)
    att_config = ATTENTION_MESSAGES.get(att_type, ATTENTION_MESSAGES["REVIEW"])
    
    if att_config["priority"] < config["min_priority"]:
        return None
    
    email_hash = get_email_hash(data)
    if email_hash in seen:
        return None
    
    sender = data.get('account', 'unknown')
    now = time.time()
    last_seen = seen.get(f"_sender_{sender}", 0)
    cooldown = config["cooldown_minutes"] * 60
    
    if now - last_seen < cooldown:
        return None
    
    lang = config.get("language", "ro")
    message_template = att_config.get(lang, att_config["ro"])
    
    subject = data.get('subject', 'fără subiect')[:60]
    sender_name = sender.split('@')[0] if '@' in sender else sender
    
    message = message_template.format(sender=sender_name, subject=subject)
    
    return {
        "hash": email_hash,
        "timestamp": datetime.now().isoformat(),
        "sender": sender,
        "subject": subject,
        "type": att_type,
        "priority": att_config["priority"],
        "emoji": att_config["emoji"],
        "message": message,
        "spoken": False
    }

def save_alerts(alerts):
    with open(ALERTS_FILE, 'w') as f:
        json.dump(alerts, f, indent=2)

# ═══════════════════════════════════════════════════════════════
# MAIN DAEMON LOOP
# ═══════════════════════════════════════════════════════════════

def daemon_loop():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  HERMES AGENT ZERO - Voice Daemon v3.0                    ║")
    print("║  Vorbire automată română, fără suprapuneri, cu coadă        ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print("")
    
    config = load_config()
    
    # Startup speech
    speak_sync(
        config.get("startup_message", "Hermes Agent Zero pornit. Monitorizez emailurile tale. Vorbesc în limba română."),
        config.get("language", "ro"),
        config.get("voice_type", "female3"),
        config.get("speech_rate", -20),
        config.get("speech_volume", 50)
    )
    
    seen = load_seen()
    cycle = 0
    
    print(f"📁 Monitorizez: {SEMANTIC_DIR}")
    print(f"⏱️  Interval: 60 secunde")
    print(f"🔊 Voce: {config.get('voice_type', 'female3')}, Limba: {config.get('language', 'ro')}")
    print(f"📝 Coadă de vorbire: Activă (fără suprapuneri)")
    print("")
    print("Apasă Ctrl+C pentru a opri")
    print("")
    
    while True:
        try:
            cycle += 1
            config = load_config()
            
            if not config.get("enabled", True):
                time.sleep(60)
                continue
            
            files = glob.glob(os.path.join(SEMANTIC_DIR, "email-*.json"))
            files.sort(key=os.path.getmtime, reverse=True)
            
            new_alerts = []
            checked = 0
            
            for filepath in files[:100]:
                alert = process_email(filepath, config, seen)
                if alert:
                    new_alerts.append(alert)
                    
                    seen[alert["hash"]] = {
                        "timestamp": alert["timestamp"],
                        "type": alert["type"],
                        "subject": alert["subject"]
                    }
                    seen[f"_sender_{alert['sender']}"] = time.time()
                    
                    if config.get("voice_enabled", True):
                        speak(
                            alert["message"],
                            config.get("language", "ro"),
                            config.get("voice_type", "female3"),
                            config.get("speech_rate", -20),
                            config.get("speech_volume", 50)
                        )
                        alert["spoken"] = True
                
                checked += 1
            
            if new_alerts:
                save_seen(seen)
                save_alerts(new_alerts)
                print(f"[{datetime.now():%H:%M:%S}] 🔔 {len(new_alerts)} alerte noi! Ciclu: {cycle} | Coadă: {voice_queue.pending_count()}")
            else:
                if cycle % 10 == 0:
                    print(f"[{datetime.now():%H:%M:%S}] ✓ Ciclu {cycle}: {checked} emailuri verificate, 0 alerte | Coadă: {voice_queue.pending_count()}")
            
            time.sleep(60)
            
        except KeyboardInterrupt:
            speak_sync("Hermes Agent Zero oprit. La revedere.", "ro", "female3", -20, 50)
            print("\n✅ Daemon oprit de utilizator.")
            save_seen(seen)
            break
        except Exception as e:
            print(f"[{datetime.now():%H:%M:%S}] ❌ Eroare: {e}")
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
        print(f"✅ Voice daemon started (PID: {pid})")
        return
    
    os.setsid()
    daemon_loop()

def stop_daemon():
    if not os.path.exists(PID_FILE):
        print("Daemon not running")
        return
    
    with open(PID_FILE) as f:
        pid = f.read().strip()
    
    try:
        os.kill(int(pid), 15)
        os.remove(PID_FILE)
        print("✅ Voice daemon stopped")
    except:
        os.remove(PID_FILE)
        print("Daemon stopped")

def status_daemon():
    if os.path.exists(PID_FILE):
        with open(PID_FILE) as f:
            pid = f.read().strip()
        if os.path.exists(f"/proc/{pid}"):
            print(f"✅ Voice daemon running (PID: {pid})")
            print(f"📊 Pending in queue: {voice_queue.pending_count()}")
            if os.path.exists(ALERTS_FILE):
                with open(ALERTS_FILE) as f:
                    alerts = json.load(f)
                print(f"📧 Recent alerts: {len(alerts)}")
        else:
            print("❌ Stale PID file")
    else:
        print("❌ Daemon not running")

# ═══════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    if '--stop' in sys.argv:
        stop_daemon()
    elif '--status' in sys.argv:
        status_daemon()
    elif '--test' in sys.argv:
        test_voice()
    elif '--start' in sys.argv:
        start_daemon()
    else:
        daemon_loop()
