#!/usr/bin/env python3
"""
Zorin Agent — Voice Module v1.0
TTS: Supertonic 3 (natural, local, 31 limbi, 99M params)
STT: Faster-Whisper (accurate, local, multilingual)
"""
import os, sys, json, time, threading, queue, tempfile, requests
import numpy as np
import sounddevice as sd
import soundfile as sf

HOME = os.path.expanduser("~")
VENV_PYTHON = os.path.join(HOME, ".hermes", "hermes-agent", "venv", "bin", "python")
BUS_URL = "http://127.0.0.1:8765"

CONFIG = {
    "stt_model": "tiny",  # tiny/base/small/medium/large-v3
    "stt_language": "ro",
    "tts_language": "ro",
    "tts_speed": 1.0,
    "sample_rate": 44100,
    "device": None,  # None = default
    "wake_word": "zorin",
    "listening": False
}

stt_model = None
tts_engine = None
audio_queue = queue.Queue()
voice_thread = None

class ZorinVoice:
    def __init__(self):
        self.bus = BUS_URL
        self.config = CONFIG
        self.running = False

    def init_stt(self):
        global stt_model
        try:
            from faster_whisper import WhisperModel
            model_size = self.config["stt_model"]
            stt_model = WhisperModel(model_size, device="cpu", compute_type="int8")
            self._bus_log("stt_loaded", {"model": model_size})
            return True
        except Exception as e:
            print(json.dumps({"event": "stt_error", "error": str(e)}))
            return False

    def init_tts(self):
        global tts_engine
        try:
            from supertonic import TTS
            tts_engine = TTS(auto_download=True)
            self.style = tts_engine.get_voice_style(voice_name="M1")
            self._bus_log("tts_loaded", {"model": "supertonic-3"})
            return True
        except Exception as e:
            print(json.dumps({"event": "tts_error", "error": str(e)}))
            return False

    def _bus_log(self, event, data=None):
        try:
            requests.post(f"{self.bus}/message/send", json={
                "from": "zorin-agent-voice",
                "to": "*",
                "type": "log",
                "payload": {"event": event, "data": data or {}}
            }, timeout=2)
        except:
            pass

    def register(self):
        try:
            requests.post(f"{self.bus}/agent/register", json={
                "name": "zorin-agent-voice",
                "type": "voice",
                "capabilities": ["text_to_speech", "speech_to_text", "supertonic3", "faster_whisper", "romanian"]
            }, timeout=3)
        except:
            pass

    def heartbeat(self):
        while self.running:
            try:
                requests.post(f"{self.bus}/agent/heartbeat", json={"name": "zorin-agent-voice"}, timeout=2)
            except:
                pass
            time.sleep(30)

    def synthesize(self, text, lang=None):
        if not tts_engine:
            return False
        try:
            lang = lang or self.config["tts_language"]
            wav, duration = tts_engine.synthesize(
                text=text, lang=lang,
                voice_style=self.style, speed=self.config["tts_speed"]
            )
            sd.play(wav.squeeze(), samplerate=44100)
            sd.wait()
            self._bus_log("tts_spoke", {"text": text[:50], "lang": lang})
            return True
        except Exception as e:
            print(json.dumps({"event": "tts_speak_error", "error": str(e)}))
            return False

    def synthesize_to_file(self, text, output_path, lang=None):
        if not tts_engine:
            return False
        try:
            lang = lang or self.config["tts_language"]
            wav, duration = tts_engine.synthesize(
                text=text, lang=lang,
                voice_style=self.style, speed=self.config["tts_speed"]
            )
            sf.write(output_path, wav.squeeze(), 44100)
            return output_path
        except Exception as e:
            print(json.dumps({"event": "tts_file_error", "error": str(e)}))
            return False

    def transcribe(self, audio_path=None, duration=5):
        if not stt_model:
            return ""
        try:
            if audio_path:
                segments, info = stt_model.transcribe(audio_path, language=self.config["stt_language"])
            else:
                fs = 16000
                recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype="float32")
                sd.wait()
                tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                sf.write(tmp.name, recording, fs)
                segments, info = stt_model.transcribe(tmp.name, language=self.config["stt_language"])
                os.unlink(tmp.name)

            text = " ".join(seg.text for seg in segments)
            self._bus_log("stt_transcribed", {"text": text[:100], "lang": info.language})
            return text.strip()
        except Exception as e:
            print(json.dumps({"event": "stt_transcribe_error", "error": str(e)}))
            return ""

    def listen_loop(self, wake=False):
        """Ascultă continuu și procesează comenzi vocale."""
        if not stt_model:
            return
        fs = 16000
        self.config["listening"] = True
        self.synthesize("Sistemul vocal Zorin Agent este activ.")

        while self.running and self.config["listening"]:
            recording = sd.rec(int(3 * fs), samplerate=fs, channels=1, dtype="float32")
            sd.wait()

            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            sf.write(tmp.name, recording, fs)
            segments, info = stt_model.transcribe(tmp.name, language=self.config["stt_language"])
            os.unlink(tmp.name)

            text = " ".join(seg.text for seg in segments).strip().lower()
            if not text:
                continue

            self._bus_log("stt_heard", {"text": text[:100]})

            if wake and self.config["wake_word"] not in text:
                continue

            # Trimite comanda pe bus
            try:
                requests.post(f"{self.bus}/task/create", json={
                    "title": f"Comandă vocală: {text[:80]}",
                    "description": text,
                    "assigned_to": "zorin-agent-core",
                    "priority": 8
                }, timeout=3)
            except:
                pass

    def say(self, text, lang=None):
        """API public: sinteză vocală."""
        return self.synthesize(text, lang)

    def hear(self, duration=5):
        """API public: ascultă și transcrie."""
        return self.transcribe(duration=duration)

    def run(self):
        self.running = True
        self.register()
        threading.Thread(target=self.heartbeat, daemon=True).start()

        if self.init_tts():
            self._bus_log("tts_ready", {"engine": "supertonic-3"})
        if self.init_stt():
            self._bus_log("stt_ready", {"engine": "faster-whisper"})

        print(json.dumps({"event": "zorin_voice_ready", "tts": "supertonic3", "stt": "faster-whisper"}))

        if "--listen" in sys.argv:
            wake = "--wake" in sys.argv
            self.listen_loop(wake=wake)
        else:
            while self.running:
                time.sleep(1)

    def stop(self):
        self.running = False
        self.config["listening"] = False


if __name__ == "__main__":
    voice = ZorinVoice()
    try:
        if "--say" in sys.argv:
            idx = sys.argv.index("--say")
            voice.init_tts()
            voice.synthesize(" ".join(sys.argv[idx+1:]))
        elif "--hear" in sys.argv:
            voice.init_stt()
            dur = int(sys.argv[sys.argv.index("--hear") + 1]) if "--hear" in sys.argv and sys.argv[sys.argv.index("--hear") + 1].isdigit() else 5
            text = voice.transcribe(duration=dur)
            print(text)
        else:
            voice.run()
    except KeyboardInterrupt:
        voice.stop()
