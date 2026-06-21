#!/usr/bin/env python3
"""Watchdog tokenuri premium — alerteaza daca un canal premium
ramane fara token valid mai mult de 30 de minute.
Ruleaza la fiecare 15 min din cron."""
import json, os, time, subprocess

TOKEN_CACHE = os.path.expanduser("~/.hermes/skills/zorin-romania-tv/.token_cache.json")
SKILL = os.path.expanduser("~/.hermes/skills/zorin-romania-tv/SKILL.md")
STATE_FILE = os.path.expanduser("~/.hermes/skills/zorin-romania-tv/.watchdog-state.json")

PREMIUM_KEYWORDS = ["hbo", "cinemax", "axn", "warner", "skyshowtime", "filmbox",
                    "amc", "comedycentral", "procinema", "filmnow", "filmcafe",
                    "cinemaraton", "filmmania", "diva", "epicdrama"]

def get_premium_channels():
    channels = []
    with open(SKILL) as f:
        name, url = None, None
        for line in f:
            if line.startswith("#EXTINF:"):
                name = line.split(",", 1)[1].strip() if "," in line else None
            elif line.startswith("http") and name:
                url = line.strip()
                if any(kw in url.lower() or kw in name.lower().replace(" ","") for kw in PREMIUM_KEYWORDS):
                    channels.append((name, url.split("?")[0]))
                name = None
    return channels

def check_tokens():
    try:
        with open(TOKEN_CACHE) as f:
            cache = json.load(f)
    except:
        return []

    now = time.time()
    premium = get_premium_channels()
    results = []
    for name, src in premium:
        tokenized = cache.get(src)
        if tokenized and "token=" in tokenized:
            m = __import__("re").search(r"token=[0-9a-f]+\.(\d+)", tokenized)
            if m and int(m.group(1)) > now:
                remaining = int(m.group(1)) - now
                results.append({"name": name, "ok": True, "remaining_m": remaining // 60})
            else:
                results.append({"name": name, "ok": False, "remaining_m": 0})
        else:
            results.append({"name": name, "ok": False, "remaining_m": 0})
    return results

results = check_tokens()
ok = sum(1 for r in results if r["ok"])
dead = sum(1 for r in results if not r["ok"])

# Load previous state for alerting
try:
    with open(STATE_FILE) as f:
        prev = json.load(f)
    prev_dead = prev.get("dead_channels", {})
except:
    prev_dead = {}

now = time.time()
alerts = []
current_dead = {}

for r in results:
    if not r["ok"]:
        current_dead[r["name"]] = now
        if r["name"] in prev_dead:
            dead_since = now - prev_dead[r["name"]]
            if dead_since > 1800:  # 30 min
                alerts.append(f"{r['name']} fara token de {int(dead_since // 60)}min")
        else:
            alerts.append(f"{r['name']} a pierdut tokenul (proaspat)")

# Log status
log_line = f"{time.ctime()}: {ok} premium OK, {dead} premium DEAD"
with open(STATE_FILE.replace(".json", ".log"), "a") as f:
    f.write(log_line + "\n")

# Save state
with open(STATE_FILE, "w") as f:
    json.dump({"dead_channels": current_dead, "last_check": now}, f)

print(log_line)
if alerts:
    for a in alerts:
        print(f"  ALERT: {a}")
    # If any channel has been dead >30min, also write to a persistent alert file
    critical = [a for a in alerts if "min" in a]
    if critical:
        with open(STATE_FILE.replace(".json", ".critical"), "a") as f:
            f.write(f"{time.ctime()}: {'; '.join(critical)}\n")
