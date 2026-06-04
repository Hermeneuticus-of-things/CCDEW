#!/usr/bin/env python3
"""
Hermes Voice Engine v4.0 - Supertonic TTS Integration
Natural, human-like Romanian speech using AI TTS.

Usage:
  python3 hermes-voice-supertonic.py --install      # Install Supertonic
  python3 hermes-voice-supertonic.py --test         # Test voice
  python3 hermes-voice-supertonic.py --start        # Start daemon
  python3 hermes-voice-supertonic.py --stop         # Stop daemon
"""

import os, sys, json, time, glob, subprocess, hashlib, threading
from datetime import datetime
from pathlib import Path

# ── Configuration ──
HOME = os.path.expanduser("~")
VENV_DIR = os.path.join(HOME, ".local/share/supertonic-venv")
PYTHON_VENV = os.path.join(VENV_DIR, "bin/python")
SEMANTIC_DIR = os.path.join(HOME, "CCDEW/_MEMORY/semantic")
PID_FILE = os.path.expanduser("~/.local/state/hermes-voice-daemon.pid")
SEEN_DB = os.path.expanduser("~/.local/state/hermes-voice-seen.json")

# Priority-based thresholds: only speak if priority >= EXPRESS_THRESHOLD
EXPRESS_THRESHOLD = 8  # Only speak if priority >= 8 (URGENT, PAYMENT, SCHEDULE, SECURITY)
VISUAL_ONLY_THRESHOLD = 6  # Visual alert if priority >= 6 but < 8

DEFAULT_CONFIG = {
    "enabled": True,
    "voice_enabled": True,
    "express_mode": True,       # Only speak high-priority emails
    "min_priority": 6,
    "express_threshold": 8,     # Only speak if >= this
    "cooldown_minutes": 30,
    "language": "ro",
    "voice_gender": "female",
    "voice_speed": 1.0,
}

# ── Attention Types ──
ATTENTION_TYPES = {
    "URGENT_RESPONSE": {
        "ro": "Atenție maximă! Email urgent de la {sender}. Subiect: {subject}. Necesită răspuns imediat!",
        "priority": 10,
        "emoji": "🔴",
        "express": True
    },
    "PAYMENT": {
        "ro": "Atenție! Email cu plată de la {sender}. Subiect: {subject}. Verifică factura.",
        "priority": 9,
        "emoji": "💰",
        "express": True
    },
    "SCHEDULE": {
        "ro": "Email cu programare de la {sender}. Subiect: {subject}. Confirmă prezența.",
        "priority": 8,
        "emoji": "📅",
        "express": True
    },
    "SECURITY": {
        "ro": "Alertă de securitate de la {sender}. Subiect: {subject}. Verifică contul imediat.",
        "priority": 8,
        "emoji": "🔒",
        "express": True
    },
    "DELIVERY": {
        "ro": "Update livrare de la {sender}. Subiect: {subject}. Coletul tău este în drum.",
        "priority": 7,
        "emoji": "📦",
        "express": False  # Visual only, no voice
    },
    "REVIEW": {
        "ro": "Email important de la {sender}. Subiect: {subject}. Citește când ai timp.",
        "priority": 7,
        "emoji": "👁️",
        "express": False  # Visual only, no voice
    }
}

class VoiceEngine:
    """TTS Engine using Supertonic or fallback to spd-say."""
    
    def __init__(self):
        self.has_supertonic = False
        self.voice = None
        self._check_supertonic()
    
    def _check_supertonic(self):
        """Check if Supertonic is available."""
        if os.path.exists(PYTHON_VENV):
            try:
                result = subprocess.run(
                    [PYTHON_VENV, "-c", "import supertonic; print('OK')"],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    self.has_supertonic = True
                    print("✅ Supertonic TTS disponibil")
                    return
            except:
                pass
        
        print("ℹ️  Supertonic nu e disponibil, folosesc spd-say")
        self.has_supertonic = False
    
    def speak(self, text, lang="ro", speed=1.0):
        """Speak text using best available TTS."""
        if not text:
            return False
        
        print(f"🗣️  SPEAK: {text[:80]}...")
        
        if self.has_supertonic:
            return self._speak_supertonic(text, lang, speed)
        else:
            return self._speak_fallback(text, lang)
    
    def _speak_supertonic(self, text, lang, speed):
        """Use Supertonic for natural speech."""
        try:
            script = f'''
import sys
sys.path.insert(0, "{VENV_DIR}/lib/python3.12/site-packages")
from supertonic import TTS
import soundfile as sf
import numpy as np

try:
    tts = TTS(auto_download=True)
    voice_name = "F1"  # Female voice
    style = tts.get_voice_style(voice_name=voice_name)
    
    wav, duration = tts.synthesize(
        text="{text}",
        lang="{lang if lang == 'ro' else 'en'}",
        voice_style=style,
        total_steps=8,
        speed={speed}
    )
    
    # Save and play
    sf.write("/tmp/hermes_voice.wav", wav.squeeze(), 44100)
    print("WAV generated")
except Exception as e:
    print(f"Error: {{e}}")
'''
            # Generate audio
            result = subprocess.run(
                [PYTHON_VENV, "-c", script],
                capture_output=True, text=True, timeout=60
            )
            
            if os.path.exists("/tmp/hermes_voice.wav"):
                # Play the audio
                subprocess.run(
                    ["paplay", "/tmp/hermes_voice.wav"] if self._has_paplay() else 
                    ["aplay", "/tmp/hermes_voice.wav"],
                    capture_output=True, timeout=30
                )
                return True
            
        except Exception as e:
            print(f"Supertonic error: {e}, using fallback")
        
        return self._speak_fallback(text, lang)
    
    def _speak_fallback(self, text, lang):
        """Fallback to spd-say."""
        try:
            proc = subprocess.Popen(
                ["spd-say", "-l", lang, "-t", "female3", "-r", "-20", text],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            proc.wait(timeout=60)
            return True
        except Exception as e:
            print(f"TTS fallback error: {e}")
            return False
    
    def _has_paplay(self):
        """Check if paplay is available."""
        try:
            subprocess.run(["which", "paplay"], capture_output=True, check=True)
            return True
        except:
            return False
    
    def install_supertonic(self):
        """Install Supertonic in virtual environment."""
        print("📦 Instalare Supertonic...")
        print("   Acest proces poate dura câteva minute...")
        
        # Create venv
        os.makedirs(VENV_DIR, exist_ok=True)
        
        try:
            subprocess.run(["python3", "-m", "venv", VENV_DIR], check=True, timeout=30)
        except:
            print("❌ Nu pot crea virtual environment")
            return False
        
        # Upgrade pip
        subprocess.run([PYTHON_VENV, "-m", "pip", "install", "--upgrade", "pip"], 
                      check=False, timeout=60)
        
        # Install supertonic
        try:
            subprocess.run([PYTHON_VENV, "-m", "pip", "install", "supertonic", "soundfile", "numpy"],
                          check=True, timeout=300)
            print("✅ Supertonic instalat!")
            self.has_supertonic = True
            return True
        except:
            print("❌ Eroare la instalarea Supertonic")
            print("   Folosesc spd-say ca fallback")
            return False

# ── Voice Queue (No Overlap) ──
class VoiceQueue:
    def __init__(self):
        self.queue = []
        self.lock = threading.Lock()
        self.speaking = False
        self.engine = VoiceEngine()
        self.thread = threading.Thread(target=self._process_loop, daemon=True)
        self.thread.start()
    
    def enqueue(self, text, lang="ro", speed=1.0):
        with self.lock:
            self.queue.append({"text": text, "lang": lang, "speed": speed})
    
    def _process_loop(self):
        while True:
            message = None
            with self.lock:
                if self.queue:
                    message = self.queue.pop(0)
            
            if message:
                self.speaking = True
                self.engine.speak(message["text"], message["lang"], message["speed"])
                self.speaking = False
                time.sleep(1)
            else:
                time.sleep(0.5)

voice_queue = VoiceQueue()

# ═══════════════════════════════════════════════════════════════
# MAIN DAEMON
# ═══════════════════════════════════════════════════════════════

def process_and_alert():
    """Process emails and decide: express (voice) or visual."""
    files = glob.glob(os.path.join(SEMANTIC_DIR, "email-*.json"))
    files.sort(key=os.path.getmtime, reverse=True)
    
    express_alerts = []
    visual_alerts = []
    
    for filepath in files[:50]:
        try:
            with open(filepath) as f:
                data = json.load(f)
            
            # Determine priority
            priority = data.get('priority', 0)
            risk = data.get('risk', 'SAFE')
            
            # Check thresholds
            if priority >= EXPRESS_THRESHOLD or risk == 'HIGH':
                # EXPRESS: Voice + Visual
                express_alerts.append(data)
            elif priority >= VISUAL_ONLY_THRESHOLD:
                # VISUAL: Only notification, no voice
                visual_alerts.append(data)
                
        except:
            pass
    
    return express_alerts, visual_alerts

def speak_alerts(alerts):
    """Speak express alerts using queue."""
    for alert in alerts[:3]:  # Max 3 voice alerts
        sender = alert.get('account', 'unknown').split('@')[0]
        subject = alert.get('subject', 'fără subiect')[:50]
        
        # Determine type
        if alert.get('risk') == 'HIGH' or alert.get('priority', 0) >= 9:
            msg = f"Atenție maximă! Email urgent de la {sender}. Subiect: {subject}. Necesită acțiune imediată!"
        elif 'security' in subject.lower() or 'alert' in subject.lower():
            msg = f"Alertă de securitate de la {sender}. Subiect: {subject}. Verifică contul imediat."
        else:
            msg = f"Email important de la {sender}. Subiect: {subject}. Necesită atenția ta."
        
        voice_queue.enqueue(msg, "ro", 1.0)

def daemon_loop():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  HERMES VOICE ENGINE v4.0                                   ║")
    print("║  Express Mode: DOAR emailuri importante sunt vorbit         ║")
    print("║  Visual Mode: Restul apar doar ca notificări vizuale        ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print("")
    
    # Startup speech (only if express)
    if voice_queue.engine.has_supertonic:
        print("🎤 Voce AI (Supertonic) - Sunet natural")
    else:
        print("🎤 Voce mecanică (spd-say) - Sunet sintetic")
    
    print(f"📊 Prag vorbire: >= {EXPRESS_THRESHOLD} (doar URGENT/PLATĂ/PROGRAMARE/SECURITATE)")
    print(f"📊 Prag vizual: >= {VISUAL_ONLY_THRESHOLD} (DELIVERY/REVIEW)")
    print("")
    
    cycle = 0
    while True:
        try:
            cycle += 1
            express, visual = process_and_alert()
            
            if express:
                print(f"\n🔴🔴🔴 ALERTE EXPRESS (Vorbite): {len(express)} 🔴🔴🔴")
                for e in express:
                    print(f"   🗣️  {e.get('subject', '?')[:60]} | Priority: {e.get('priority', 0)}")
                speak_alerts(express)
            
            if visual:
                print(f"\n🟡🟡🟡 ALERTE VIZUALE (Notificări): {len(visual)} 🟡🟡🟡")
                for v in visual:
                    print(f"   👁️  {v.get('subject', '?')[:60]} | Priority: {v.get('priority', 0)}")
            
            if not express and not visual:
                if cycle % 10 == 0:
                    print(f"[{datetime.now():%H:%M:%S}] ✓ Ciclu {cycle}: Niciun email urgent nou")
            
            time.sleep(60)
            
        except KeyboardInterrupt:
            print("\n✅ Oprit")
            break
        except Exception as e:
            print(f"❌ Eroare: {e}")
            time.sleep(60)

if __name__ == '__main__':
    if '--install' in sys.argv:
        voice_queue.engine.install_supertonic()
    elif '--test' in sys.argv:
        print("🎤 Test voce...")
        voice_queue.enqueue("Atenție maximă! Email urgent de test. Necesită răspuns imediat!", "ro", 1.0)
        time.sleep(5)
    else:
        daemon_loop()
