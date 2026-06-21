#!/usr/bin/env python3
"""
Zorin Agent — Agent Launcher v1.0
Pornește și înregistrează automat agenții Zorin Agent pe Memory Bus.
"""
import os, sys, json, time, threading, subprocess, requests, signal

HOME = os.path.expanduser("~")
BUS_URL = "http://127.0.0.1:8765"
HELPERS = os.path.join(HOME, "CCDEW", ".claude", "helpers")

AGENTS = {
    "zorin-agent-core": {
        "type": "orchestrator",
        "cmd": ["python3", os.path.join(HELPERS, "zorin-agent-bus.py")],
        "capabilities": ["memory_bus", "task_queue", "agent_registry", "dashboard"],
        "auto_start": True
    },
    "hermes-agent-core": {
        "type": "automation",
        "cmd": ["python3", os.path.join(HELPERS, "hermes-agent-core.py"), "--loop"],
        "capabilities": ["system_monitor", "service_guard", "disk_watch", "skill_exec"],
        "auto_start": True
    },
    "zorin-agent-voice": {
        "type": "voice",
        "cmd": [os.path.join(HOME, ".hermes", "hermes-agent", "venv", "bin", "python3"),
                os.path.join(HELPERS, "zorin-agent-voice.py")],
        "capabilities": ["text_to_speech", "speech_to_text", "supertonic3", "faster_whisper", "romanian_tts"],
        "auto_start": True
    },
    "zorin-agent-personal": {
        "type": "personal",
        "cmd": None,
        "capabilities": ["calendar", "reminders", "notes", "email_summary"],
        "auto_start": False
    },
    "zorin-agent-dev": {
        "type": "developer",
        "cmd": None,
        "capabilities": ["code_review", "auto_test", "git_ops", "deploy"],
        "auto_start": False
    },
    "zorin-agent-sysadmin": {
        "type": "sysadmin",
        "cmd": ["python3", os.path.join(HELPERS, "hermes-binary-guardian.py"), "--watch"],
        "capabilities": ["binary_watch", "kernel_monitor", "security_scan", "backup"],
        "auto_start": True
    },
    "zorin-agent-personal": {
        "type": "personal",
        "cmd": ["python3", os.path.join(HELPERS, "zorin-agent-personal.py")],
        "capabilities": ["reminders", "notes", "agenda", "email_summary", "daily_tasks"],
        "auto_start": True
    },
    "zorin-agent-dev": {
        "type": "developer",
        "cmd": ["python3", os.path.join(HELPERS, "zorin-agent-dev.py")],
        "capabilities": ["code_review", "git_ops", "test_runner", "builds", "project_scan"],
        "auto_start": True
    },
    "zorin-agent-network": {
        "type": "network",
        "cmd": ["python3", os.path.join(HELPERS, "zorin-agent-network.py")],
        "capabilities": ["ping_monitor", "qnap_access", "wireguard", "teleport", "dns_check"],
        "auto_start": True
    },
    "zorin-agent-file": {
        "type": "file",
        "cmd": ["python3", os.path.join(HELPERS, "zorin-agent-file.py")],
        "capabilities": ["disk_scan", "cleanup", "backup", "dedup", "organize"],
        "auto_start": True
    },
    "zorin-agent-browser": {
        "type": "browser",
        "cmd": ["python3", os.path.join(HELPERS, "zorin-agent-browser.py")],
        "capabilities": ["web_search", "web_fetch", "scrape", "research"],
        "auto_start": True
    },
    "zorin-agent-media": {
        "type": "media",
        "cmd": ["python3", os.path.join(HELPERS, "zorin-agent-media.py")],
        "capabilities": ["download", "convert", "metadata", "organize_media", "yt_dlp"],
        "auto_start": True
    },
    "zorin-agent-scheduler": {
        "type": "scheduler",
        "cmd": ["python3", os.path.join(HELPERS, "zorin-agent-scheduler.py")],
        "capabilities": ["cron", "scheduled_tasks", "recurring_jobs", "timers"],
        "auto_start": True
    },
    "zorin-agent-hardware": {
        "type": "hardware",
        "cmd": ["python3", os.path.join(HELPERS, "zorin-agent-hardware.py")],
        "capabilities": ["disk_health", "drivers", "kernel", "io_stats", "temperature", "hardware_scan"],
        "auto_start": True
    },
    "zorin-agent-tv": {
        "type": "tv",
        "cmd": ["python3", os.path.join(HELPERS, "zorin-agent-tv.py")],
        "capabilities": ["channel_monitor", "stream_health", "failover", "auto_repair", "token_refresh"],
        "auto_start": True
    },
    "zorin-agent-vault": {
        "type": "vault",
        "cmd": ["python3", os.path.join(HELPERS, "zorin-agent-vault.py")],
        "capabilities": ["password_store", "auth_pin", "auth_fingerprint", "sensitive_data"],
        "auto_start": True
    },
    "zorin-agent-home": {
        "type": "home",
        "cmd": ["python3", os.path.join(HELPERS, "zorin-agent-home.py")],
        "capabilities": ["bluetooth_scan", "wifi_scan", "zigbee", "philips_hue", "smart_devices", "light_control", "device_discovery"],
        "auto_start": True
    }
}

processes = {}

def register_agent(name, info):
    try:
        r = requests.post(f"{BUS_URL}/agent/register", json={
            "name": name,
            "type": info["type"],
            "capabilities": info["capabilities"]
        }, timeout=5)
        return r.json()
    except Exception as e:
        return {"status": "error", "msg": str(e)}

def heartbeat_loop(name):
    while True:
        try:
            requests.post(f"{BUS_URL}/agent/heartbeat", json={"name": name}, timeout=3)
        except:
            pass
        time.sleep(30)

def start_agent(name, info):
    if not info["cmd"]:
        print(json.dumps({"event": "agent_skipped", "name": name, "reason": "no_cmd"}))
        return False
    try:
        proc = subprocess.Popen(
            info["cmd"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        processes[name] = proc
        reg = register_agent(name, info)
        threading.Thread(target=heartbeat_loop, args=(name,), daemon=True).start()
        print(json.dumps({"event": "agent_started", "name": name, "pid": proc.pid, "register": reg}))
        return True
    except Exception as e:
        print(json.dumps({"event": "agent_failed", "name": name, "error": str(e)}))
        return False

def start_all():
    print(json.dumps({"event": "zorin_agent_launcher_start", "agents": len(AGENTS)}))
    for name, info in AGENTS.items():
        if info["auto_start"]:
            start_agent(name, info)
            time.sleep(2)

def stop_all():
    for name, proc in processes.items():
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except:
            try:
                proc.kill()
            except:
                pass
    print(json.dumps({"event": "zorin_agent_launcher_stop"}))

def status_all():
    results = {}
    for name, info in AGENTS.items():
        proc = processes.get(name)
        results[name] = {
            "type": info["type"],
            "running": proc is not None and proc.poll() is None,
            "capabilities": info["capabilities"]
        }
    return results

if __name__ == "__main__":
    import sys
    if "--start" in sys.argv:
        start_all()
        try:
            while True: time.sleep(1)
        except KeyboardInterrupt:
            stop_all()
    elif "--stop" in sys.argv:
        stop_all()
    elif "--status" in sys.argv:
        print(json.dumps(status_all(), indent=2))
    else:
        start_all()
        try:
            while True: time.sleep(1)
        except KeyboardInterrupt:
            stop_all()
