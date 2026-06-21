#!/usr/bin/env python3
"""Zorin TV Clean — probează toate streamurile cu brightness+movement, păstrează doar live"""
import os, json, subprocess, concurrent.futures, time, shutil, cv2, numpy as np, urllib.request, urllib.parse, threading, urllib.error

_token_lock = threading.Lock()

SKILL = os.path.expanduser("~/.hermes/skills/zorin-romania-tv/SKILL.md")
CACHE = os.path.expanduser("~/.hermes/skills/zorin-romania-tv/.cache.json")
BACKUP = SKILL + ".bak"

def get_channels():
    channels = []
    if os.path.exists(SKILL):
        with open(SKILL) as f:
            name = None
            for line in f:
                if line.startswith("#EXTINF:"):
                    name = line.split(",", 1)[1].strip() if "," in line else None
                elif line.startswith("http") and name:
                    channels.append({"name": name, "url": line.strip()})
                    name = None
    return channels

TOKEN_API = "https://rdslive.tv/token_proxy_test.php"
TOKEN_REFS = {"https://rdslive.tv/canal/romania-tv/", "https://rdslive.tv/canal/acasa-tv/",
              "https://rdslive.tv/canal/prima-tv/", "https://rdslive.tv/canal/pro-tv/",
              "https://rdslive.tv/canal/pro-arena/", "https://rdslive.tv/canal/kanal-d2/",
              "https://rdslive.tv/canal/national-24-plus/", "https://rdslive.tv/canal/cartoonito/",
              "https://rdslive.tv/canal/disney-channel/", "https://rdslive.tv/canal/disney-junior/",
              "https://rdslive.tv/canal/nick-junior/", "https://rdslive.tv/canal/nick-toons/",
              "https://rdslive.tv/canal/tvr-cultural/", "https://rdslive.tv/canal/digisport-1/",
              "https://rdslive.tv/canal/digisport-4/", "https://rdslive.tv/canal/eurosport-1/",
              "https://rdslive.tv/canal/eurosport-2/", "https://rdslive.tv/canal/primasport-1/",
              "https://rdslive.tv/canal/sport-extra/", "https://rdslive.tv/canal/pro-tv/"}

# Map of channel names to their rdslive.tv ref for source lookup
CHANNEL_REFS = {
    "acasa": "https://rdslive.tv/canal/acasa-tv/",
    "prima": "https://rdslive.tv/canal/prima-tv/",
    "romania": "https://rdslive.tv/canal/romania-tv/",
    "pro": "https://rdslive.tv/canal/pro-tv/",
    "proarena": "https://rdslive.tv/canal/pro-arena/",
    "kanald2": "https://rdslive.tv/canal/kanal-d2/",
    "national24": "https://rdslive.tv/canal/national-24-plus/",
    "cartoonito": "https://rdslive.tv/canal/cartoonito/",
    "disneychannel": "https://rdslive.tv/canal/disney-channel/",
    "disneyjunior": "https://rdslive.tv/canal/disney-junior/",
    "nickjr": "https://rdslive.tv/canal/nick-junior/",
    "nicktoons": "https://rdslive.tv/canal/nick-toons/",
    "tvr_cultural": "https://rdslive.tv/canal/tvr-cultural/",
    "digisport1": "https://rdslive.tv/canal/digisport-1/",
    "digisport4": "https://rdslive.tv/canal/digisport-4/",
    "eurosport": "https://rdslive.tv/canal/eurosport-1/",
    "eurosport2": "https://rdslive.tv/canal/eurosport-2/",
    "primasport1": "https://rdslive.tv/canal/primasport-1/",
    "sportextra": "https://rdslive.tv/canal/sport-extra/",
    "acasagold": "https://rdslive.tv/canal/acasa-tv/",
    # Premium channels
    "hbo": "https://rdslive.tv/?p=168",
    "hbo2": "https://rdslive.tv/?p=170",
    "hbo3": "https://rdslive.tv/?p=171",
    "cinemax": "https://rdslive.tv/?p=135",
    "cinemax2": "https://rdslive.tv/?p=136",
    "axn": "https://rdslive.tv/?p=127",
    "axnblack": "https://rdslive.tv/?p=126",
    "axnspin": "https://rdslive.tv/?p=128",
    "axnwhite": "https://rdslive.tv/?p=129",
    "warner": "https://rdslive.tv/?p=210",
    "skyshowtime": "https://rdslive.tv/?p=693",
    "filmbox": "https://rdslive.tv/?p=167",
    "amc": "https://rdslive.tv/?p=124",
    "comedycentral": "https://rdslive.tv/?p=138",
}

def _guess_ref(src_url):
    """Guess the rdslive ref from the source URL path segment."""
    for key, ref in CHANNEL_REFS.items():
        if key in src_url.lower():
            return ref
    return "https://rdslive.tv/"

def refresh_token(url, max_retries=3):
    if "magicplaces.eu" not in url:
        return url
    src = url.split("?")[0]
    ref = _guess_ref(src)
    for attempt in range(max_retries):
        with _token_lock:
            try:
                req = urllib.request.Request(
                    f"{TOKEN_API}?source={urllib.parse.quote(src)}&ref={urllib.parse.quote(ref)}",
                    headers={"User-Agent": "Mozilla/5.0", "Referer": "https://rdslive.tv/"})
                resp = urllib.request.urlopen(req, timeout=10)
                data = json.loads(resp.read())
                if data.get("token"):
                    return f"{src}?token={data['token']}"
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt < max_retries - 1:
                    wait = 5 * (2 ** attempt)  # 5s, 10s, 20s
                    time.sleep(wait)
                    continue
            except: pass
    return url

def probe(url):
    tid = threading.get_ident()
    outdir = None
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_streams", "-select_streams", "v:0", url],
            capture_output=True, text=True, timeout=10)
        if r.returncode != 0: return "dead"
        data = json.loads(r.stdout)
        if not data.get("streams"): return "dead"
    except:
        return "dead"

    try:
        outdir = f"/tmp/zorin-clean-{tid}_{int(time.time())}"
        os.makedirs(outdir, exist_ok=True)
        subprocess.run(["ffmpeg", "-y", "-t", "8", "-i", url,
                        "-frames:v", "2", "-vf", "select='eq(pict_type,PICT_TYPE_I)'",
                        "-fps_mode", "vfr", f"{outdir}/f_%02d.png"],
                       capture_output=True, timeout=15)
        files = sorted(os.listdir(outdir))
        if len(files) < 2:
            return "fake"
        i1 = cv2.imread(os.path.join(outdir, files[0]), 0)
        i2 = cv2.imread(os.path.join(outdir, files[1]), 0)
        if i1 is None or i2 is None:
            return "fake"
        avg_brightness = float(i1.mean())
        mse = float((cv2.absdiff(i1.astype('float32'), i2.astype('float32'))**2).mean())
        return "live" if avg_brightness > 20 and mse > 100 else "fake"
    except:
        return "dead"
    finally:
        if outdir and os.path.exists(outdir):
            shutil.rmtree(outdir, ignore_errors=True)

def save_cache(all_channels, live_names):
    now = int(time.time())
    results = []
    for ch in all_channels:
        is_live = ch["name"] in live_names
        ch["live"] = is_live
        ch["info"] = "live" if is_live else "dead"
        url = ch.get("token_url", ch["url"])
        results.append({"name": ch["name"], "url": url,
                        "live": is_live, "info": "live" if is_live else "dead"})
    results.sort(key=lambda x: x["name"].lower())
    data = {"channels": all_channels, "results": results, "checked_at": now}
    with open(CACHE, "w") as f:
        json.dump(data, f, indent=2)

# Post IDs for re-discovery when a stream dies
POST_IDS = {
    "acasa": 59, "prima": 43, "romania": 195, "protv": 39,
    "proarena": 188, "kanald2": 69, "national24": 67,
    "cartoonito": 617, "disneychannel": 150, "disneyjunior": 151,
    "nickjr": 185, "nicktoons": 186, "tvr_cultural": 717,
    "digisport1": 93, "digisport4": 147, "eurosport": 158,
    "eurosport2": 159, "primasport1": 83, "sportextra": 197,
    "acasagold": 59,
    # Premium channels
    "hbo": 168, "hbo2": 170, "hbo3": 171,
    "cinemax": 135, "cinemax2": 136,
    "axn": 127, "axnblack": 126, "axnspin": 128, "axnwhite": 129,
    "warner": 210, "skyshowtime": 693, "skyshowtime2": 695,
    "skyshowtime 2": 695,
    "filmbox": 167, "amc": 124, "comedycentral": 138,
}

AJAX_API = "https://rdslive.tv/wp-admin/admin-ajax.php"

def rediscover_source(name, old_url):
    """When a magicplaces stream dies, try to find its new URL from rdslive.tv."""
    for key, pid in POST_IDS.items():
        if key in old_url.lower() or key in name.lower():
            try:
                data = urllib.parse.urlencode({"action": "get_video_source",
                    "tab": "tab1", "post_id": str(pid)}).encode()
                req = urllib.request.Request(AJAX_API, data=data,
                    headers={"User-Agent": "Mozilla/5.0",
                             "Content-Type": "application/x-www-form-urlencoded"})
                resp = urllib.request.urlopen(req, timeout=10)
                result = json.loads(resp.read())
                new_src = result.get("data", "")
                if new_src and new_src != old_url and "magicplaces" in new_src:
                    print(f"    REDISCOVERED: {name} -> {new_src}")
                    return new_src
            except: pass
            break
    return old_url

def preprocess_tokens(channels):
    for c in channels:
        if "magicplaces.eu" in c["url"]:
            tokenized = refresh_token(c["url"])
            if "?token=" in tokenized:
                c["token_url"] = tokenized
            time.sleep(2)  # avoid rate limit
    return channels

def main():
    channels = preprocess_tokens(get_channels())
    if not channels:
        print("No channels found.")
        return
    print(f"Probează {len(channels)} streamuri...")
    live, dead = [], []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        fut = {pool.submit(probe, c.get("token_url", c["url"])): c for c in channels}
        for f in concurrent.futures.as_completed(fut):
            c = fut[f]
            status = f.result()
            if status == "live":
                live.append(c)
                print(f"  LIVE: {c['name']}")
            else:
                dead.append(c)
                print(f"  DEAD: {c['name']}")
    print(f"\nRezultat: {len(live)} live, {len(dead)} dead")

    # Self-healing: rediscover source for dead magicplaces channels
    recovered = []
    for c in dead[:]:
        if "magicplaces" in c["url"]:
            new_url = rediscover_source(c["name"], c["url"])
            if new_url != c["url"]:
                c["url"] = new_url
                c["token_url"] = None
                tokenized = refresh_token(new_url, max_retries=5)
                if "?token=" in tokenized:
                    c["token_url"] = tokenized
                    status = probe(tokenized)
                    if status == "live":
                        live.append(c)
                        dead.remove(c)
                        recovered.append(c)
                        print(f"  RECOVERED: {c['name']}")
    print(f"Auto-vindecare: {len(recovered)} recuperate")

    if len(live) == len(channels):
        print("Toate canalele sunt live. Nimic de actualizat.")
        save_cache(channels, {c["name"] for c in live})
        return

    # KEEP all magicplaces channels even if dead — server auto-refreshes tokens on /hls
    for c in dead[:]:
        if "magicplaces" in c["url"]:
            live.append(c)
            dead.remove(c)
            print(f"  KEPT: {c['name']} (magicplaces — server handles tokens)")

    live_names = {c["name"] for c in live}
    if os.path.exists(SKILL):
        shutil.copy2(SKILL, BACKUP)
        print(f"Backup: {BACKUP}")

    with open(SKILL, "w") as f:
        f.write("# Romanian TV Channels (auto-curated)\n")
        f.write(f"# {len(live)} live, {len(dead)} dead\n")
        f.write("# EXTM3U\n")
        for c in live:
            f.write(f'#EXTINF:-1,{c["name"]}\n{c["url"]}\n')

    print(f"SKILL.md rescris cu {len(live)} canale live.")
    save_cache(channels, live_names)
    print(f"Cache salvat.")

if __name__ == "__main__":
    main()
