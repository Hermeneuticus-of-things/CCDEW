#!/usr/bin/env python3
"""Colector lent — 1 token la 5 minute, evitand rate limit."""
import subprocess, json, time, urllib.parse, os

TOKEN_API = "https://rdslive.tv/token_proxy_test.php"
CACHE_PATH = os.path.expanduser("~/.hermes/skills/zorin-romania-tv/.token_cache.json")

CHANNELS = [
    ("HBO HD", "https://p11.magicplaces.eu/rds_hbo/video.m3u8", "https://rdslive.tv/?p=168"),
    ("HBO 2", "https://p11.magicplaces.eu/rds_hbo2/video.m3u8", "https://rdslive.tv/?p=170"),
    ("HBO 3", "https://p11.magicplaces.eu/rds_hbo3/video.m3u8", "https://rdslive.tv/?p=171"),
    ("Cinemax HD", "https://p11.magicplaces.eu/cinemaxhd/video.m3u8", "https://rdslive.tv/?p=135"),
    ("Cinemax 2", "https://p11.magicplaces.eu/rds_cinemax2/video.m3u8", "https://rdslive.tv/?p=136"),
    ("AXN", "https://p11.magicplaces.eu/rds_axn/video.m3u8", "https://rdslive.tv/?p=127"),
    ("AXN Black", "https://p11.magicplaces.eu/rds_axnblack/video.m3u8", "https://rdslive.tv/?p=126"),
    ("AXN Spin", "https://p11.magicplaces.eu/rds_axnspin/video.m3u8", "https://rdslive.tv/?p=128"),
    ("AXN White", "https://p11.magicplaces.eu/rds_axnwhite/video.m3u8", "https://rdslive.tv/?p=129"),
    ("Warner TV", "https://p11.magicplaces.eu/rds_warner/video.m3u8", "https://rdslive.tv/?p=210"),
    ("SkyShowTime", "https://p11.magicplaces.eu/rds_sky1/video.m3u8", "https://rdslive.tv/?p=693"),
    ("SkyShowTime 2", "https://p11.magicplaces.eu/rds_sky2/video.m3u8", "https://rdslive.tv/?p=695"),
    ("FilmBox Stars", "https://p13.magicplaces.eu/rds_filmboxone/video.m3u8", "https://rdslive.tv/?p=167"),
    ("AMC", "https://p11.magicplaces.eu/rds_amc/video.m3u8", "https://rdslive.tv/?p=124"),
    ("Comedy Central", "https://p11.magicplaces.eu/rds_comedycentral/index.m3u8", "https://rdslive.tv/?p=138"),
    ("Pro Cinema", "https://p11.magicplaces.eu/procinemasd/video.m3u8", "https://rdslive.tv/?p=230"),
    ("FilmNow", "https://p13.magicplaces.eu/filmnow/video.m3u8", "https://rdslive.tv/?p=240"),
    ("Film Cafe", "https://p11.magicplaces.eu/filmcafesd/video.m3u8", "https://rdslive.tv/?p=250"),
    ("CineMaraton", "https://p11.magicplaces.eu/cinemaratonsd/video.m3u8", "https://rdslive.tv/?p=260"),
    ("CineMaraton Plus", "https://p13.magicplaces.eu/cinemaratonplus/video.m3u8", "https://rdslive.tv/?p=270"),
    ("FilmMania", "https://p11.magicplaces.eu/filmmania/video.m3u8", "https://rdslive.tv/?p=280"),
    ("Antena Comedy", "https://p13.magicplaces.eu/free_antenacomedy/video.m3u8", "https://rdslive.tv/?p=57"),
    ("Filme Comedie 1", "https://p13.magicplaces.eu/rds_filmecomedie1/video.m3u8", "https://rdslive.tv/?p=769"),
    ("Filme Comedie 2", "https://p13.magicplaces.eu/rds_filmecomedie2/video.m3u8", "https://rdslive.tv/?p=771"),
    ("Prima Comedy", "https://p11.magicplaces.eu/rds_primacomedy/video.m3u8", "https://rdslive.tv/?p=674"),
]

CURL_HEADERS = [
    '-H', 'User-Agent: Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36',
    '-H', 'Referer: https://rdslive.tv/',
    '-H', 'Accept: application/json, text/plain, */*',
    '-H', 'Accept-Language: ro-RO,ro;q=0.9,en;q=0.8',
    '-H', 'Origin: https://rdslive.tv',
    '-H', 'DNT: 1',
]

def get_token(src, ref):
    url = f"{TOKEN_API}?source={urllib.parse.quote(src)}&ref={urllib.parse.quote(ref)}"
    try:
        result = subprocess.run(
            ['curl', '-s', '--max-time', '10', url] + CURL_HEADERS,
            capture_output=True, text=True, timeout=15)
        if result.returncode != 0:
            return None, None
        d = json.loads(result.stdout)
        if "token" in d:
            return d["token"], None
        if "error" in d:
            return None, d["error"]
        return None, str(d)[:60]
    except Exception as e:
        return None, str(e)

idx = 0
while True:
    name, src, ref = CHANNELS[idx]
    print(f"[{idx}] {name}: trying...", end=" ", flush=True)
    token, err = get_token(src, ref)
    if token:
        tu = f"{src}?token={token}"
        try:
            with open(CACHE_PATH) as f:
                cache = json.load(f)
            cache[src] = tu
            with open(CACHE_PATH, "w") as f:
                json.dump(cache, f, indent=2)
        except:
            pass
        print(f"OK -> token salvat", flush=True)
        idx = (idx + 1) % len(CHANNELS)
    elif err and "too many" in err.lower():
        print(f"RATE-LIMIT, wait 300s", flush=True)
        time.sleep(300)
        continue
    else:
        print(f"FAIL: {err}", flush=True)
        idx = (idx + 1) % len(CHANNELS)

    print(f"  Waiting 300s...", flush=True)
    time.sleep(300)
