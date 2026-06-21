#!/usr/bin/env python3
"""QNAP-side token collector (IP diferit → dubleaza rata)."""
import json, urllib.parse, subprocess, os, time

TOKEN_API = "https://rdslive.tv/token_proxy_test.php"
SKILL = "/share/CACHEDEV1_DATA/Container/hermes-agent/data/SKILL.md"
CACHE = "/share/CACHEDEV1_DATA/Container/hermes-agent/data/.token_cache_qnap.json"
STATE = "/share/CACHEDEV1_DATA/Container/hermes-agent/data/.qnap-state.txt"

HEADERS = [
    '-H', 'User-Agent: Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36',
    '-H', 'Referer: https://rdslive.tv/', '-H', 'Accept: application/json, text/plain, */*',
    '-H', 'Accept-Language: ro-RO,ro;q=0.9,en;q=0.8', '-H', 'Origin: https://rdslive.tv', '-H', 'DNT: 1',
]

if not os.path.exists(SKILL):
    print("No SKILL.md yet"); exit(0)

with open(SKILL) as f:
    chs, name = [], None
    for line in f:
        if line.startswith("#EXTINF:"):
            name = line.split(",", 1)[1].strip() if "," in line else None
        elif line.startswith("http") and name:
            chs.append((name, line.strip()))
            name = None

magic = [(n, u) for n, u in chs if "magicplaces" in u]
premium_kw = ["hbo", "cinemax", "axn", "warner", "skyshowtime", "filmbox", "amc", "comedycentral"]
magic.sort(key=lambda c: 0 if any(k in c[1].lower() for k in premium_kw) else 1)

try:
    with open(STATE) as f:
        idx = int(f.read().strip())
except:
    idx = 0

name, src = magic[idx]
ref = "https://rdslive.tv/?p=1"

url = f"{TOKEN_API}?source={urllib.parse.quote(src)}&ref=1"
result = subprocess.run(['curl', '-s', '--max-time', '10', url] + HEADERS,
                        capture_output=True, text=True, timeout=15)
resp = json.loads(result.stdout) if result.stdout else {}
token = resp.get("token")

if token:
    tu = f"{src}?token={token}"
    try:
        with open(CACHE) as f:
            cache = json.load(f)
        cache[src] = tu
        with open(CACHE, "w") as f:
            json.dump(cache, f, indent=2)
    except:
        pass
    print(f"OK {idx}/{len(magic)}: {name}")
    idx = (idx + 1) % len(magic)
else:
    err = resp.get("error", "no token")
    if "too many" in err.lower():
        print(f"RL {idx}: {name} (retry)")
    else:
        print(f"XX {idx}: {name} -> {err}")
        idx = (idx + 1) % len(magic)

with open(STATE, "w") as f:
    f.write(str(idx))
