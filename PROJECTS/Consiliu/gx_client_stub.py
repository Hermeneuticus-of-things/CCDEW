#!/usr/bin/env python3
"""
gx_client_stub.py v2 — Simulator GX cu symbiotic + voice + role split.

ROL GX: VORBESTE CU IONUT (chat conversational + voice).
DELEGAȚIE: task complex → forward "exec: ..." la QnapGX prin bridge.
"""
import json
import ssl
import os
import re
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

BRIDGE = os.environ.get("BRIDGE_URL", "http://100.97.220.9:9876")
SOUL_SYNC = os.environ.get("SOUL_SYNC_URL", "http://100.97.220.9:9878")
SKILL_RUNNER = "http://100.97.220.9:9879"
OLLAMA = os.environ.get("OLLAMA_HOST", "http://100.97.220.9:11434")  # via Tailscale
TTS_URL = "http://100.97.220.9:8001/v1/audio/speech"
DATA_DIR = Path(os.environ.get("GX_DATA_DIR", os.path.expanduser("~/.gx_stub")))
DATA_DIR.mkdir(parents=True, exist_ok=True)

STATE_FILE = DATA_DIR / "gx_state.json"
QUEUE_FILE = DATA_DIR / "offline_queue.json"
LOG_FILE = DATA_DIR / "gx.log"
VOICE_OUT_DIR = DATA_DIR / "voice"
VOICE_OUT_DIR.mkdir(parents=True, exist_ok=True)

# Modele GX (warm-first, atunci capabil)
GX_MODELS = [
    "tinydolphin:latest",  # 636MB FAST warm pentru test E2E
    "gemma4-e2b-hauhaucs:latest",  # 3.1GB primary RO multilingual
    "fredrezones55/Gemma-4-Uncensored-HauhauCS-Aggressive:latest",  # 6.3GB final HQ
]

POLL_INTERVAL = 10


def log(msg):
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"last_msg_id": 0, "last_qnapgx_seq": 0, "last_gx_seq": 0}


def save_state(s):
    STATE_FILE.write_text(json.dumps(s, indent=2))




# === mTLS Configuration ===
CONSILIU_CA = os.path.expanduser("~/.consiliu/mtls/ca.crt")
CONSILIU_CERT = os.path.expanduser("~/.consiliu/mtls/think.crt")
CONSILIU_KEY = os.path.expanduser("~/.consiliu/mtls/think.key")
USE_MTLS = os.path.exists(CONSILIU_CA) and os.path.exists(CONSILIU_CERT) and os.path.exists(CONSILIU_KEY)
if USE_MTLS:
    BRIDGE = os.environ.get("BRIDGE_URL_MTLS", "https://qnap.consiliu:9877")

def make_mtls_opener():
    """Create urllib opener with mTLS client cert."""
    if not USE_MTLS:
        return urllib.request.build_opener()
    ctx = ssl.create_default_context(cafile=CONSILIU_CA)
    ctx.load_cert_chain(certfile=CONSILIU_CERT, keyfile=CONSILIU_KEY)
    ctx.check_hostname = True
    handler = urllib.request.HTTPSHandler(context=ctx)
    return urllib.request.build_opener(handler)

_OPENER = make_mtls_opener()

def http_json(url, method="GET", data=None, timeout=8):
    body = None
    headers = {}
    if data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with _OPENER.open(req, timeout=timeout) as r:
            return json.loads(r.read())
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        raise ConnectionError(f"{url}: {e}")


def bridge_send(msg, to="Think", frm="GX"):
    try:
        return http_json(f"{BRIDGE}/api/messages", method="POST",
                         data={"from": frm, "to": to, "message": msg})
    except ConnectionError:
        queue_offline("bridge_send", {"to": to, "message": msg})


def bridge_poll(state):
    try:
        msgs = http_json(f"{BRIDGE}/api/messages?for=GX&unread=false")
        new = [m for m in msgs if m.get("id", 0) > state["last_msg_id"]]
        if new:
            state["last_msg_id"] = max(m["id"] for m in new)
            save_state(state)
        return new
    except ConnectionError:
        return []


def queue_offline(action, payload):
    queue = json.loads(QUEUE_FILE.read_text()) if QUEUE_FILE.exists() else []
    queue.append({"action": action, "payload": payload, "ts": datetime.now().isoformat()})
    QUEUE_FILE.write_text(json.dumps(queue, indent=2))


def flush_offline_queue():
    if not QUEUE_FILE.exists():
        return
    queue = json.loads(QUEUE_FILE.read_text())
    if not queue:
        return
    replayed, failed = [], []
    for item in queue:
        try:
            if item["action"] == "bridge_send":
                p = item["payload"]
                bridge_send(p["message"], to=p.get("to", "Think"), frm="GX")
                replayed.append(item)
            else:
                replayed.append(item)
        except Exception:
            failed.append(item)
    QUEUE_FILE.write_text(json.dumps(failed, indent=2))
    if replayed:
        log(f"[QUEUE] flushed {len(replayed)}, failed {len(failed)}")


def get_first_available_model():
    """Return first model from GX_MODELS that responds."""
    for m in GX_MODELS:
        try:
            req = urllib.request.Request(f"{OLLAMA}/api/show",
                data=json.dumps({"name": m}).encode(),
                headers={"Content-Type": "application/json"}, method="POST")
            urllib.request.urlopen(req, timeout=3).read()
            return m
        except Exception:
            continue
    return GX_MODELS[-1]


def gx_llm_chat(user_text, history=None, max_tokens=200):
    """LLM conversational. Returnează text natural în română."""
    model = get_first_available_model()
    system = (
        "Esti GX, asistentul mobil al lui Ionut. Vorbesti ROMANA naturala. "
        "Esti inima conversatiei — interpretezi cererile lui Ionut. "
        "Daca task-ul cere COD/MATEMATICA/SISTEM (ex: 'verifica disc', 'instaleaza X', 'calculeaza Y'), "
        "raspunzi STRICT cu 'FORWARD_QNAPGX: <task>' — eu (GX runtime) il trimit la QnapGX. "
        "Pentru orice altceva (chat, salutari, intrebari simple) raspunzi conversational. "
        "Refuzi doar daca task incalca SOUL.md_GX (privacy biometric, sterge SOUL, etc.)."
    )
    body = {"model": model, "prompt": user_text, "system": system, "stream": False,
            "options": {"num_predict": max_tokens, "temperature": 0.7, "num_ctx": 4096}}
    try:
        req = urllib.request.Request(f"{OLLAMA}/api/generate",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=300) as r:
            raw = json.loads(r.read()).get("response", "").strip()
            raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
        return raw, model
    except Exception as e:
        return f"[GX-LLM-ERR: {e}]", model


def speak(text, voice="alloy"):
    """TTS via hermes-tts QNAP. Returneaza path la fisier mp3."""
    body = {"model": "tts-1", "input": text[:500], "voice": voice}
    try:
        req = urllib.request.Request(TTS_URL,
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read()
        ts = datetime.now().strftime("%H%M%S")
        out = VOICE_OUT_DIR / f"gx_speech_{ts}.mp3"
        out.write_bytes(data)
        return str(out)
    except Exception as e:
        log(f"[TTS-ERR] {e}")
        return None


def forward_to_qnapgx(task):
    """Forward exec task la QnapGX prin bridge."""
    return bridge_send(f"exec: {task}", to="QnapGX", frm="GX")


def handle_user_message(user_text):
    """Pipeline: user → LLM GX → decide local/forward → response (text + voice)."""
    log(f"[USER] {user_text}")
    response, model = gx_llm_chat(user_text)
    log(f"[GX-LLM/{model.split('/')[-1][:30]}] {response[:120]}")

    if response.startswith("FORWARD_QNAPGX:"):
        task = response[len("FORWARD_QNAPGX:"):].strip()
        log(f"[FORWARD] task='{task[:80]}' → QnapGX")
        forward_to_qnapgx(task)
        ack = f"Am trimis task-ul către QnapGX. Te anunț când răspunde."
        speak(ack)
        return ack
    else:
        # Direct response — TTS in romana
        speak(response)
        return response


def respond_to_inquiry(msg):
    text = msg.get("message", "").lower()
    if any(kw in text for kw in ["raporteaza", "raportează", "ce stai", "in ce stadiu", "cum esti"]):
        try:
            sync_status = http_json(f"{SOUL_SYNC}/sync/status")
            response = (f"[GX] {get_first_available_model().split('/')[-1][:40]} activ. "
                       f"Last bridge msg: #{load_state()['last_msg_id']}. "
                       f"CRDT entries: {sync_status.get('total_entries', '?')}. "
                       f"Voice: TTS ready.")
            bridge_send(response, to=msg.get("from", "Think"))
        except Exception as e:
            log(f"[ERR] {e}")


def handle_qnapgx_result(m):
    """Handler pentru răspuns exec: de la QnapGX → surfaced la Ionut prin GX voice."""
    txt = m.get("message", "")
    result_body = txt[len("[QNAP/"):] if txt.startswith("[QNAP/") else txt
    summary = f"QnapGX a executat task-ul. Rezultat: {result_body[:200]}"
    log(f"[QNAPGX-RESULT] {result_body[:120]}")
    bridge_send(f"[GX] {summary}", to="Ionut", frm="GX")
    speak(summary)


def main():
    log(f"[GX-stub v3] start, polling {BRIDGE} la {POLL_INTERVAL}s")
    log(f"[GX-stub v3] LLM candidates: {[m.split('/')[-1] for m in GX_MODELS]}")
    log(f"[GX-stub v3] TTS: {TTS_URL}")
    log(f"[GX-stub v3] data: {DATA_DIR}")

    flush_offline_queue()
    bridge_send("[GX/HELLO] GX v3 online — canal direct QnapGX↔GX activ. Bridge: 100.97.220.9:9876.", to="QnapGX", frm="GX")
    bridge_send("[GX/HELLO] GX v3 pornit pe x200 (100.86.169.24).", to="Ionut", frm="GX")

    state = load_state()
    iteration = 0
    while True:
        iteration += 1
        if iteration % 6 == 0:  # flush queue la fiecare minut
            flush_offline_queue()
        try:
            new_msgs = bridge_poll(state)
            for m in new_msgs:
                log(f"[MSG #{m['id']}] {m.get('from')}: {m.get('message','')[:100]}")
                frm = m.get("from", "")
                txt = m.get("message", "")
                txt_lower = txt.lower()

                # Răspuns exec: de la QnapGX → surfaceaza la Ionut
                if frm == "QnapGX" and (txt.startswith("[QNAP/") or "exec:" in txt_lower[:30]):
                    handle_qnapgx_result(m)

                elif any(k in txt_lower for k in ["raporteaza", "raportează", "ce stai", "in ce stadiu"]):
                    respond_to_inquiry(m)

                elif frm in ("Ionut", "Think", "Honor") and not txt_lower.startswith(("teach:", "exec:", "memo:", "memory:", "[")):
                    response = handle_user_message(txt)
                    bridge_send(f"[GX/RESP] {response[:300]}", to=frm)

        except KeyboardInterrupt:
            break
        except Exception as e:
            log(f"[loop err] {e}")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "chat":
        # Interactive mode pentru test
        text = " ".join(sys.argv[2:])
        result = handle_user_message(text)
        print(json.dumps({"response": result}, ensure_ascii=False, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "speak":
        path = speak(" ".join(sys.argv[2:]))
        print(f"voice file: {path}")
    elif len(sys.argv) > 1 and sys.argv[1] == "models":
        print(f"Available: {get_first_available_model()}")
    else:
        main()
