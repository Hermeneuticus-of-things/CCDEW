#!/usr/bin/env python3
"""Refresh tokens for ALL magicplaces channels from SKILL.md.
Extracts exact URLs from the playlist so cache keys match what the server uses.
Uses curl + mobile UA to avoid Cloudflare TLS fingerprinting.
"""
import json, urllib.parse, subprocess, os, sys, time

TOKEN_API = "https://rdslive.tv/token_proxy_test.php"
SKILL = os.path.expanduser("~/.hermes/skills/zorin-romania-tv/SKILL.md")
TOKEN_CACHE = os.path.expanduser("~/.hermes/skills/zorin-romania-tv/.token_cache.json")
STATE_FILE = os.path.expanduser("~/.hermes/skills/zorin-romania-tv/.refresh-state.txt")
LOG_FILE = os.path.expanduser("~/.hermes/skills/zorin-romania-tv/.token-refresh.log")

PRIORITY_KEYWORDS = ["hbo", "cinemax", "axn", "warner", "skyshowtime", "filmbox",
                     "amc", "comedycentral", "procinema", "filmnow", "filmcafe",
                     "cinemaraton", "filmmania", "diva", "epicdrama", "tv1000"]

HEADERS = [
    '-H', 'User-Agent: Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36',
    '-H', 'Referer: https://rdslive.tv/',
    '-H', 'Accept: application/json, text/plain, */*',
    '-H', 'Accept-Language: ro-RO,ro;q=0.9,en;q=0.8',
    '-H', 'Origin: https://rdslive.tv',
    '-H', 'DNT: 1',
]

def parse_skill():
    with open(SKILL) as f:
        channels, name = [], None
        for line in f:
            if line.startswith("#EXTINF:"):
                name = line.split(",", 1)[1].strip() if "," in line else None
            elif line.startswith("http") and name:
                channels.append((name, line.strip()))
                name = None
    return channels

def get_ref(url, name=""):
    for key, pid in [
        ("hbo2", 170), ("hbo3", 171), ("hbohd", 168), ("hbo", 168),
        ("cinemax2", 136), ("cinemaxhd", 135), ("cinemax", 135),
        ("axnblack", 126), ("axnspin", 128), ("axnwhite", 129),
        ("axn", 127), ("warner", 210), ("sky1", 693), ("sky2", 695),
        ("skyshowtime", 693), ("filmboxone", 167), ("filmbox", 167),
        ("amc", 124), ("comedycentral", 138), ("procinema", 230),
        ("filmnow", 240), ("filmcafe", 250), ("cinemaraton", 260),
        ("filmmania", 280), ("diva", 290), ("epicdrama", 300),
        ("tv1000", 310),
        ("primatv", 674), ("primacomedy", 674),
        ("antenacomedy", 57), ("filmecomedie1", 769), ("filmecomedie2", 771),
    ]:
        if key in url.lower() or key in name.lower().replace(" ", ""):
            return f"https://rdslive.tv/?p={pid}"
    return "https://rdslive.tv/"

def get_token(src, ref):
    url = f"{TOKEN_API}?source={urllib.parse.quote(src)}&ref={urllib.parse.quote(ref)}"
    try:
        result = subprocess.run(
            ['curl', '-s', '--max-time', '10', url] + HEADERS,
            capture_output=True, text=True, timeout=15)
        return json.loads(result.stdout)
    except Exception:
        return None

def log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(f"{time.ctime()}: {msg}\n")
    print(msg)

channels = parse_skill()
magicplaces = [(n, u) for n, u in channels if "magicplaces" in u]

# Sort: priority channels first, then rest
def priority_key(ch):
    name, url = ch
    for kw in PRIORITY_KEYWORDS:
        if kw in url.lower() or kw in name.lower().replace(" ", ""):
            return 0
    return 1
magicplaces.sort(key=priority_key)

try:
    with open(STATE_FILE) as f:
        state = json.load(f)
        idx = state.get("idx", 0)
        retry_count = state.get("retry", 0)
        last_rate_limit = state.get("last_rate_limit", 0)
except:
    idx, retry_count, last_rate_limit = 0, 0, 0

name, src = magicplaces[idx]
ref = get_ref(src, name)

# If we hit rate limit recently and this channel is fine (not expired), skip
now = time.time()
if "Too many requests" in open(LOG_FILE).read().split("\n")[-3:] and retry_count > 0:
    advance = False
else:
    advance = True

resp = get_token(src, ref)
token = resp.get("token") if resp else None
error = resp.get("error") if resp else ("no response" if resp else "curl failed")

if token:
    tu = f"{src}?token={token}"
    try:
        with open(TOKEN_CACHE) as f:
            cache = json.load(f)
        cache[src] = tu
        with open(TOKEN_CACHE, "w") as f:
            json.dump(cache, f, indent=2)
    except:
        pass
    log(f"OK {idx}/{len(magicplaces)}: {name}")
    next_idx = (idx + 1) % len(magicplaces)
    retry_count = 0
elif error and "too many" in error.lower():
    log(f"RL {idx}/{len(magicplaces)}: {name} -> rate-limit (retry #{retry_count+1})")
    next_idx = idx  # retry same channel
    retry_count += 1
else:
    log(f"XX {idx}/{len(magicplaces)}: {name} -> {error}")
    next_idx = (idx + 1) % len(magicplaces)

with open(STATE_FILE, "w") as f:
    json.dump({"idx": next_idx, "retry": retry_count, "last_rate_limit": int(now)}, f)
