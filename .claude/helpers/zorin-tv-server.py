#!/usr/bin/env python3
"""Zorin TV Stream UI Server — port 8899, cu cache + auto-heal permanent"""
import os, json, http.server, urllib.parse, urllib.request, urllib.error, subprocess, concurrent.futures, time, re, threading

_token_lock = threading.Lock()
_token_cache = {}  # src -> tokenized_url
_token_cache_path = os.path.expanduser("~/.hermes/skills/zorin-romania-tv/.token_cache.json")
# QNAP token cache (IP diferit) — merge automat in _token_cache
_qnap_token_cache_path = os.path.expanduser("~/.hermes/skills/zorin-romania-tv/.token_cache_qnap.json")

def _load_token_cache():
    for p in [_token_cache_path, _qnap_token_cache_path]:
        if os.path.exists(p):
            try:
                with open(p) as f:
                    _token_cache.update(json.load(f))
            except: pass

# Load persistent token cache on startup
_load_token_cache()

def _save_token_cache():
    try:
        os.makedirs(os.path.dirname(_token_cache_path), exist_ok=True)
        with open(_token_cache_path, "w") as f:
            json.dump(_token_cache, f, indent=2)
    except: pass

def valid_url(u):
    return isinstance(u, str) and u.startswith(("http://", "https://")) and len(u) >= 11

SKILL = os.path.expanduser("~/.hermes/skills/zorin-romania-tv/SKILL.md")
HTML = os.path.join(os.path.dirname(__file__), "zorin-tv-ui.html")
CACHE = os.path.expanduser("~/.hermes/skills/zorin-romania-tv/.cache.json")

GROUPS = [
    ("TVR", ["tvr"]),
    ("Premium", ["hbo", "cinemax", "axn", "warner", "filmbox",
                 "skyshowtime"]),
    ("Filme", ["pro cinema", "film cafe", "filmnow", "cine maraton", "cinemaraton",
               "epic drama", "tv 1000", "film mania", "filmmania", "amc", "diva",
               "bollywood", "tlc"]),
    ("Comedie", ["comedy central", "comedy play", "prima comedy"]),
    ("Sport", ["digi sport", "eurosport", "prima sport", "sport extra", "pro arena",
               "exploris", "fishing"]),
    ("Știri", ["digi 24", "antena 3", "b1 tv", "românia tv", "romania tv",
               "realitatea", "aleph news", "aleph business", "observator",
               "euronews", "cnn", "profit 24", "national 24", "informatia",
               "news", "tv8", "dw deutsch", "nasul tv"]),
    ("Copii", ["disney", "nick", "cartoon", "junior", "da vinci", "nickelodeon"]),
    ("Muzică", ["mtv", "party mix", "mooz dance", "balkan music", "impact dance",
                "impact manele", "music channel", "hit music", "mezzo", "fashion tv",
                "kiss tv", "rock tv", "atomic", "liratv", "rapsodia", "taraf tv",
                "zut tv", "etno tv", "tralala", "tele 7 music", "tele7music",
                "traditional tv", "magic tv", "favorit tv"]),
    ("Divertisment", ["pro tv", "acasă", "acasa", "antena 1", "antena star",
                      "happy channel", "super tv", "dotto",
                      "mireasa", "prima history", "entertainment",
                      "travel mix", "prima tv", "kanal d", "tvsat",
                      "rai 1", "rai 3", "job tv", "h365"]),
    ("Documentare", ["nat geo", "discovery", "history channel", "viasat",
                     "bbc earth", "bbc first", "cbs reality", "hgtv",
                     "travel channel", "hello taste", "tv paprika", "medicool",
                     "digi animal world", "digi life", "digi world", "agro"]),
    ("Religios", ["alfa omega", "angelus", "credo", "light channel", "speranta",
                  "trinitas", "a7 tv", "tezaur", "blessing", "sens tv"]),
    ("Moldova", ["moldova 1", "moldova 2", "moldova tv", "privesc", "realitatea md",
                 "rtn chicago", "telemoldova"]),
    ("Locale", ["banat tv", "bucovina tv", "hunedoara", "nova tv", "iasitv",
                "telem", "tele 7 abc", "buzau", "suceava", "arges",
                "moinesti", "sor tv", "tv-nord", "metropola", "academy tv",
                "lightning", "angels tv"]),
    ("AntenaPlay", ["antenaplay.ro"]),
    ("Broadcasting", ["broadcasting.ro"]),
    ("Diverse", []),
]

def get_group(url, name=""):
    for g, patterns in GROUPS:
        for p in patterns:
            if p in url or p in name.lower():
                return g
    return "Diverse"

def get_channels():
    channels = []
    if os.path.exists(SKILL):
        with open(SKILL) as f:
            name = None
            for line in f:
                if line.startswith("#EXTINF:"):
                    name = line.split(",", 1)[1].strip() if "," in line else None
                elif line.startswith("http") and name:
                    channels.append({"name": name, "url": line.strip(), "group": get_group(line.strip(), name)})
                    name = None
    if len(channels) < 10:
        for bk in [SKILL + ".bak3", SKILL + ".bak2", SKILL + ".bak"]:
            if os.path.exists(bk) and os.path.getsize(bk) > 1000:
                with open(bk) as f:
                    content = f.read()
                if content.count("#EXTINF:") >= 10:
                    with open(SKILL, "w") as f:
                        f.write(content)
                    channels = get_channels()
                    break
    return channels

def probe_channel(url, timeout=10):
    if "magicplaces.eu" in url:
        old_url = url
        url_w_token = refresh_token(url)
        got_fresh_token = (url_w_token != url)
        if not got_fresh_token:
            # Rate-limited / nu putem verifica acum → proxy-ul incearca la /hls
            return True, {"needs_token": True}
        try:
            status, ctype, data, _ = fetch_upstream(url_w_token)
            if status == 200 and data[:7] == b'#EXTM3U':
                return True, {"codec": "h264", "w": 0, "h": 0}
            return False, f"http_{status}"
        except urllib.error.HTTPError as e:
            if e.code == 403:
                return True, {"needs_token": True}
            return False, f"http_{e.code}"
        except Exception as e:
            return False, str(e)[:30]
    # Pentru URL-uri care nu sunt HTTP standard (UDP, porturi non-standard, etc.)
    # sau care nu se termina cu m3u8, incercam simple TCP/HTTP inainte de ffprobe
    if not url.endswith(".m3u8") or "udp://" in url or "://" not in url:
        try:
            req = urllib.request.Request(url, method="HEAD",
                headers={"User-Agent": "Mozilla/5.0", "Accept": "*/*"})
            resp = urllib.request.urlopen(req, timeout=5)
            return True, {"http": resp.getcode(), "w": 0, "h": 0}
        except:
            pass
    try:
        r = subprocess.run(
            ["timeout", str(timeout), "ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_streams", "-select_streams", "v:0", url],
            capture_output=True, text=True, timeout=timeout + 3)
        if r.returncode != 0:
            return False, "ffprobe_error"
        data = json.loads(r.stdout)
        if not data.get("streams"):
            return False, "no_video"
        s = data["streams"][0]
        return True, {"codec": s.get("codec_name","?"), "w": s.get("width",0), "h": s.get("height",0)}
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:
        return False, str(e)[:30]

def load_cache():
    if os.path.exists(CACHE):
        try:
            with open(CACHE) as f:
                return json.load(f)
        except: pass
    return None

def save_cache(data):
    tmp = CACHE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f)
    os.replace(tmp, CACHE)

# ---- Căutare variante (self-healing on-demand) ----
# Surse de playlist publice cautate dupa nume (extensibil: adauga (tag, url) aici)
ALT_SOURCES = [
    ("iptv-org", "https://iptv-org.github.io/iptv/countries/ro.m3u"),
    ("Free-TV", "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlists/playlist_romania.m3u8"),
    ("iptv-org-lang", "https://iptv-org.github.io/iptv/languages/ron.m3u"),
]
TOKEN_API = "https://rdslive.tv/token_proxy_test.php"
AJAX_API = "https://rdslive.tv/wp-admin/admin-ajax.php"

CHANNEL_REFS = {
    "acasa": "acasa-tv", "prima": "prima-tv", "romania": "romania-tv",
    "proarena": "pro-arena", "pro": "pro-tv", "kanald2": "kanal-d2",
    "national24": "national-24-plus", "cartoonito": "cartoonito",
    "disneychannel": "disney-channel", "disneyjunior": "disney-junior",
    "nickjr": "nick-junior", "nicktoons": "nick-toons", "tvr_cultural": "tvr-cultural",
    "digisport1": "digisport-1", "digisport4": "digisport-4", "eurosport2": "eurosport-2",
    "eurosport": "eurosport-1", "primasport1": "primasport-1", "sportextra": "sport-extra",
}
# Premium channels use /?p= format, not /canal/ format
PREMIUM_REFS = {
    "hbo": "?p=168", "hbo2": "?p=170", "hbo3": "?p=171", "hbohd": "?p=168",
    "cinemax": "?p=135", "cinemax2": "?p=136", "cinemaxhd": "?p=135",
    "axn": "?p=127", "axnblack": "?p=126", "axnspin": "?p=128", "axnwhite": "?p=129",
    "warner": "?p=210", "filmbox": "?p=167",
    "comedycentral": "?p=138",
    "skyshowtime": "?p=693", "skyshowtime2": "?p=695",
    "amc": "?p=124",
    "procinema": "?p=230", "filmnow": "?p=240", "filmcafe": "?p=250",
    "cinemaraton": "?p=260", "cinemaratonplus": "?p=270",
    "filmmania": "?p=280", "epicdrama": "?p=303",
    "diva": "?p=311", "tv1000": "?p=312",
}
# All keywords that identify a premium/film channel (for token-health)
PREMIUM_KEYWORDS = list(PREMIUM_REFS.keys()) + ["filmecomedie", "antenacomedy", "primacomedy"]
POST_IDS = {
    "acasa": 59, "prima": 43, "romania": 195, "protv": 39, "proarena": 188,
    "kanald2": 69, "national24": 67, "cartoonito": 617, "disneychannel": 150,
    "disneyjunior": 151, "nickjr": 185, "nicktoons": 186, "tvr_cultural": 717,
    "digisport1": 93, "digisport4": 147, "eurosport": 158, "eurosport2": 159,
    "primasport1": 83, "sportextra": 197, "acasagold": 59,
    "amc": 124, "axnblack": 126, "axn": 127, "axnspin": 128, "axnwhite": 129,
    "cinemaxhd": 135, "cinemax2": 136, "hbohd": 168, "hbo2": 170, "hbo3": 171,
    "warner": 210, "skyshowtime": 693, "filmbox": 167,
    "comedycentral": 138,
}

# Backup URLs for tab2 (cand tab1 face refresh_token fails, incearca tab2)
TAB2_BACKUPS = {
    "acasa": "https://p11.magicplaces.eu/roacasahd/video.m3u8",
    "primasport1": "https://p13.magicplaces.eu/roprimasport1hd/video.m3u8",
    "digisport1": "https://p13.magicplaces.eu/13.backup.digisport1/index.fmp4.m3u8",
    "digisport4": "https://p13.magicplaces.eu/16.backup.digisport4/video.m3u8",
    "eurosport": "https://p13.magicplaces.eu/22.backup.eurosport1/video.m3u8",
    "eurosport2": "https://p13.magicplaces.eu/23.backup.eurosport2/video.m3u8",
    "proarena": "https://p13.magicplaces.eu/39.backup.prox/video.m3u8",
    "romania": "https://p13.magicplaces.eu/41.backup.romaniatv/video.m3u8",
    "b1": "https://p13.magicplaces.eu/4.backup.b1/video.m3u8",
    "digi24": "https://p13.magicplaces.eu/10.backup.digi24/video.m3u8",
    "digianimalworld": "https://p13.magicplaces.eu/11.backup.digianimalworld/index.fmp4.m3u8",
    "digilife": "https://p13.magicplaces.eu/12.backup.digilife/video.m3u8",
    "digisport2": "https://p13.magicplaces.eu/14.backup.digisport2/video.m3u8",
    "digisport3": "https://p13.magicplaces.eu/15.backup.digisport3/video.m3u8",
    "digiworld": "https://p13.magicplaces.eu/17.backup.digiworld/video.m3u8",
    "diva": "https://p13.magicplaces.eu/19.backup.diva/video.m3u8",
    "filmnow": "https://p13.magicplaces.eu/25.backup.filmnow/video.m3u8",
    "procinema": "https://p13.magicplaces.eu/37.backup.procinema/video.m3u8",
    "tlc": "https://p13.magicplaces.eu/42.backup.tlc/video.m3u8",
    "viasatexplore": "https://p13.magicplaces.eu/46.backup.viasatexplore/video.m3u8",
    "viasathistory": "https://p13.magicplaces.eu/47.backup.viasathistory/video.m3u8",
    "viasatnature": "https://p13.magicplaces.eu/48.backup.viasatnature/video.m3u8",
    "cinemaxhd": "https://p13.magicplaces.eu/6.backup.cinemax/video.m3u8",
    "cinemax2": "https://p13.magicplaces.eu/7.backup.cinemax2/video.m3u8",
    "hbohd": "https://p13.magicplaces.eu/27.backup.hbo/video.m3u8",
    "hbo2": "https://p13.magicplaces.eu/28.backup.hbo2/video.m3u8",
    "hbo3": "https://p13.magicplaces.eu/29.backup.hbo3/video.m3u8",
}

def norm_name(n):
    n = re.sub(r"\s*\(.*?\)|\s*\[.*?\]", "", n)
    n = re.sub(r"\b(HD|FHD|SD|UHD|4K)\b", "", n, flags=re.I)
    n = re.sub(r"[^0-9A-Za-zĂÂÎȘȚăâîșț ]", " ", n)  # elimina simboluri ca Ⓖ, ., +
    return re.sub(r"\s+", " ", n).strip().lower()

def _guess_ref(src_url):
    for key, slug in PREMIUM_REFS.items():
        if key in src_url.lower():
            return f"https://rdslive.tv/{slug}"
    for key, slug in CHANNEL_REFS.items():
        if key in src_url.lower():
            return f"https://rdslive.tv/canal/{slug}/"
    return "https://rdslive.tv/"

TOKEN_LAST_SERVER = 0.0

def refresh_token(url):
    """Get tokenized URL for magicplaces channels.
    First checks disk cache (from cron), then memory cache, then tries API.
    API call rate-limited to max 1 per 30s to avoid Cloudflare 429."""
    global TOKEN_LAST_SERVER
    if "magicplaces.eu" not in url:
        return url
    src = url.split("?")[0]
    # 1. Check memory cache for fresh token
    if src in _token_cache and not _mp_token_expired(_token_cache[src]):
        return _token_cache[src]
    # 2. Check disk cache from cron refreshes
    _load_token_cache()
    if src in _token_cache and not _mp_token_expired(_token_cache[src]):
        return _token_cache[src]
    # 3. Only try API if we have a cached fallback (even expired)
    if src in _token_cache:
        return _token_cache[src]
    # 4. No cache at all — try API very slowly
    with _token_lock:
        now = time.time()
        if now - TOKEN_LAST_SERVER < 30.0:
            return url
        TOKEN_LAST_SERVER = time.time()
        ref = _guess_ref(src)
        try:
            req = urllib.request.Request(
                f"{TOKEN_API}?source={urllib.parse.quote(src)}&ref={urllib.parse.quote(ref)}",
                headers={"User-Agent": "Mozilla/5.0", "Referer": "https://rdslive.tv/"})
            data = json.loads(urllib.request.urlopen(req, timeout=10).read())
            if data.get("token"):
                tokenized = f"{src}?token={data['token']}"
                _token_cache[src] = tokenized
                _save_token_cache()
                return tokenized
        except Exception:
            pass
        return url

def rediscover_source(name, old_url):
    for key, pid in POST_IDS.items():
        if key in old_url.lower() or key in name.lower().replace(" ", ""):
            try:
                body = urllib.parse.urlencode({"action": "get_video_source",
                    "tab": "tab1", "post_id": str(pid)}).encode()
                req = urllib.request.Request(AJAX_API, data=body,
                    headers={"User-Agent": "Mozilla/5.0",
                             "Content-Type": "application/x-www-form-urlencoded"})
                src = (json.loads(urllib.request.urlopen(req, timeout=10).read()) or {}).get("data", "")
                if src and src != old_url:
                    return src
            except Exception:
                pass
            break
    return ""

def _fetch_source(tag, url):
    path = f"/tmp/zorin-altsrc-{tag}.m3u"
    try:
        if not os.path.exists(path) or time.time() - os.path.getmtime(path) > 21600:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            data = urllib.request.urlopen(req, timeout=15).read()
            with open(path, "wb") as f:
                f.write(data)
    except Exception:
        pass
    return path

def playlist_candidates(name):
    target = norm_name(name)
    out = []
    for tag, url in ALT_SOURCES:
        path = _fetch_source(tag, url)
        if not os.path.exists(path):
            continue
        nm = None
        with open(path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line.startswith("#EXTINF") and "," in line:
                    nm = line.split(",", 1)[1]
                elif line.startswith("http") and nm:
                    if norm_name(nm) == target and line not in out:
                        out.append(line)
                    nm = None
    return out

# ---- Proxy HLS (rezolva CORS + referer-lock pentru redare in browser) ----
import base64

def _b64u(s):
    return base64.urlsafe_b64encode(s.encode()).decode()

def _b64u_dec(s):
    return base64.urlsafe_b64decode(s.encode()).decode()

def _proxify(abs_url):
    return f"/hls?u={_b64u(abs_url)}"

def rewrite_m3u8(text, base_url):
    """Rescrie URI-urile dintr-un manifest HLS ca sa treaca prin /hls (segmente, variante, chei)."""
    out = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            out.append(line)
            continue
        if s.startswith("#"):
            m = re.search(r'URI="([^"]+)"', s)
            if m:
                abs_u = urllib.parse.urljoin(base_url, m.group(1))
                s = s.replace(m.group(1), _proxify(abs_u))
            out.append(s)
        else:
            out.append(_proxify(urllib.parse.urljoin(base_url, s)))
    return "\n".join(out) + "\n"

def _mp_token_expired(url):
    """Tokenul magicplaces e <hash>.<unixtime>; expirat daca timpul < acum."""
    m = re.search(r"token=[0-9a-f]+\.(\d+)", url)
    if not m:
        return True  # fara token -> trebuie reimprospatat
    return int(m.group(1)) <= time.time()

MP_SERVERS = ["p11.magicplaces.eu", "p13.magicplaces.eu", "p9.magicplaces.eu"]

def fetch_upstream(url):
    """GET server-side cu UA + Referer derivat. Returneaza (status, ctype, data, final_url).
    Pentru magicplaces: failover automat intre p9/p11/p13 + tab2 backup."""
    if "magicplaces.eu" in url and _mp_token_expired(url):
        url = refresh_token(url)
    try:
        p = urllib.parse.urlparse(url)
        referer = f"{p.scheme}://{p.netloc}/"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0", "Referer": referer, "Accept": "*/*"})
        resp = urllib.request.urlopen(req, timeout=15)
        ctype = resp.headers.get("Content-Type", "")
        data = resp.read()
        # Detect dead token: magicplaces returns HTML for expired/invalid tokens
        if "magicplaces" in url and data[:6] == b"<!DOC" and url.split("?")[0].endswith(".m3u8"):
            new_url = refresh_token(url)
            if new_url != url:
                p = urllib.parse.urlparse(new_url)
                req = urllib.request.Request(new_url, headers={
                    "User-Agent": "Mozilla/5.0", "Referer": f"{p.scheme}://{p.netloc}/", "Accept": "*/*"})
                resp2 = urllib.request.urlopen(req, timeout=15)
                ctype = resp2.headers.get("Content-Type", "")
                data = resp2.read()
                return resp2.getcode(), ctype, data, resp2.geturl()
        return resp.getcode(), ctype, data, resp.geturl()
    except Exception:
        if "magicplaces.eu" not in url:
            raise
        # Failover 1: try alternative servers (p11 -> p13 -> p9)
        base = url.split("?")[0]
        for srv in MP_SERVERS:
            alt = re.sub(r"p\d+\.magicplaces\.eu", srv, base)
            if alt == base:
                continue
            try:
                alt_w_token = refresh_token(alt)
                p = urllib.parse.urlparse(alt_w_token)
                req = urllib.request.Request(alt_w_token, headers={
                    "User-Agent": "Mozilla/5.0", "Referer": f"{p.scheme}://{p.netloc}/", "Accept": "*/*"})
                resp = urllib.request.urlopen(req, timeout=15)
                return resp.getcode(), resp.headers.get("Content-Type", ""), resp.read(), resp.geturl()
            except Exception:
                continue
        # Failover 2: try tab2 backup URL
        for key, tab2_url in TAB2_BACKUPS.items():
            if key in url.lower():
                try:
                    tab2_w_token = refresh_token(tab2_url)
                    p = urllib.parse.urlparse(tab2_w_token)
                    req = urllib.request.Request(tab2_w_token, headers={
                        "User-Agent": "Mozilla/5.0", "Referer": f"{p.scheme}://{p.netloc}/", "Accept": "*/*"})
                    resp = urllib.request.urlopen(req, timeout=15)
                    return resp.getcode(), resp.headers.get("Content-Type", ""), resp.read(), resp.geturl()
                except Exception:
                    pass
                break
        raise

def find_alternative(name, url):
    cands = []
    if "magicplaces.eu" in url:
        t = refresh_token(url)
        if t != url:
            cands.append(t)
        new = rediscover_source(name, url)
        if new:
            cands.append(refresh_token(new))
            cands.append(new)
    cands += playlist_candidates(name)
    seen = set()
    for c in cands:
        if c in seen or c == url or not valid_url(c):
            continue
        seen.add(c)
        live, info = probe_channel(c, timeout=10)
        if live:
            return c, info
    return None, None

def replace_url(old_url, new_url):
    if not os.path.exists(SKILL):
        return False
    with open(SKILL) as f:
        lines = f.readlines()
    changed = False
    for i, l in enumerate(lines):
        if l.strip() == old_url:
            lines[i] = new_url + "\n"
            changed = True
            break
    if changed:
        tmp = SKILL + ".tmp"
        with open(tmp, "w") as f:
            f.writelines(lines)
        os.replace(tmp, SKILL)
    return changed


def auto_heal_channel(name, url, cache=None):
    """Gaseste URL alternativ pentru un canal mort. Intoarce (new_url, info) sau (None, None)."""
    new_url, info = find_alternative(name, url)
    if new_url:
        replace_url(url, new_url)
        c = cache or load_cache()
        if c:
            for coll in ("channels", "results"):
                for item in c.get(coll, []):
                    if item.get("url") == url:
                        item["url"] = new_url
                        item["live"] = True
                        item["info"] = info
            save_cache(c)
    return new_url, info


def auto_heal_background():
    """Thread background: la fiecare 15min, verifica TOATE canalele si repara ce e mort."""
    while True:
        time.sleep(900)
        try:
            cache = load_cache()
            if not cache:
                continue
            results = cache.get("results", [])
            for r in results:
                if r.get("live"):
                    continue
                try:
                    if "magicplaces.eu" in r["url"] and _mp_token_expired(r["url"]):
                        r["url"] = refresh_token(r["url"])
                    live, info = probe_channel(r["url"], timeout=8)
                    if live:
                        r["live"] = True
                        r["info"] = info
                        continue
                    new_url, info = auto_heal_channel(r["name"], r["url"], cache)
                    if new_url:
                        r["url"] = new_url
                        r["info"] = info
                except Exception:
                    pass
                time.sleep(1)
            save_cache(cache)
        except Exception:
            pass


class Handler(http.server.BaseHTTPRequestHandler):
    def _bg_auto_heal(self):
        """Porneste repararea canalelor moarte in background."""
        try:
            self.probe_all_and_cache()
        except Exception:
            pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        if path == "/token-health":
            _load_token_cache()
            now = time.time()
            valid, expired, no_token = 0, 0, 0
            premium_valid, premium_dead = 0, 0
            for c in get_channels():
                u = c["url"]
                if "magicplaces" not in u:
                    continue
                token_url = _token_cache.get(u.split("?")[0])
                if token_url and "token=" in token_url:
                    m = re.search(r"token=[0-9a-f]+\.(\d+)", token_url)
                    if m and int(m.group(1)) > now:
                        valid += 1
                        if any(k in u.lower() for k in PREMIUM_KEYWORDS):
                            premium_valid += 1
                    else:
                        expired += 1
                else:
                    no_token += 1
                    if any(k in u.lower() for k in PREMIUM_KEYWORDS):
                        premium_dead += 1
            self.json({
                "total_magicplaces": valid + expired + no_token,
                "valid": valid, "expired": expired, "no_token": no_token,
                "premium_valid": premium_valid,
                "premium_dead": premium_dead,
                "coverage_pct": round(valid / max(valid + expired + no_token, 1) * 100, 1),
                "next_refresh_at": "cron la fiecare 2min",
                "hint": "foloseste /refresh-tokens pentru refresh fortat"
            })
            return

        if path == "/channels.json":
            self.json(get_channels())
            return

        elif path == "/status.json":
            cache = load_cache()
            if not cache:
                threading.Thread(target=self._bg_auto_heal, daemon=True).start()
                self.json({"ok": False, "message": "probe in background...", "results": [], "channels": get_channels(), "checked_at": 0})
                return
            for arr in ["channels", "results"]:
                for c in cache.get(arr, []):
                    if "group" not in c:
                        c["group"] = get_group(c.get("url",""), c.get("name",""))
                    u = c.get("url", "")
                    if "magicplaces" in u and "token=" in u:
                        m = re.search(r"token=[0-9a-f]+\.(\d+)", u)
                        if m:
                            remaining = int(m.group(1)) - time.time()
                            c["token_remaining"] = int(remaining)
                            c["token_ok"] = remaining > 0
                    elif "magicplaces" in u and "token=" not in u:
                        c["token_ok"] = False
                        c["token_remaining"] = 0
            self.json(cache)

        elif path == "/probe-all":
            # force re-probe all in background, returneaza imediat
            threading.Thread(target=self._bg_auto_heal, daemon=True).start()
            self.json({"ok": True, "message": "probe started in background"})
            self.json(load_cache())

        elif path == "/probe-one":
            url = (params.get("url") or [""])[0]
            if not valid_url(url):
                self.json({"live": False, "error": "invalid_url"})
                return
            live, info = probe_channel(url)
            self.json({"live": live, "info": info if live else str(info)})

        elif path == "/find-alternative":
            name = (params.get("name") or [""])[0]
            url = (params.get("url") or [""])[0]
            if not name and not url:
                self.json({"ok": False, "message": "lipsesc parametrii"})
                return
            new_url, info = find_alternative(name, url)
            if new_url:
                replaced = replace_url(url, new_url)
                cache = load_cache()
                if cache:
                    for coll in ("channels", "results"):
                        for item in cache.get(coll, []):
                            if item.get("url") == url:
                                item["url"] = new_url
                                item["live"] = True
                                item["info"] = info
                    save_cache(cache)
                self.json({"ok": True, "url": new_url, "info": info, "replaced": replaced})
            else:
                self.json({"ok": False, "message": "nicio variantă funcțională găsită"})

        elif path == "/refresh-tokens":
            forced = 0
            for c in get_channels():
                u = c["url"]
                if "magicplaces" in u:
                    old = u
                    u = refresh_token(u)
                    if u != old:
                        forced += 1
            self.json({"ok": True, "refreshed": forced, "message": f"{forced} tokens refresh-incercate"})

        elif path == "/":
            threading.Thread(target=self._bg_auto_heal, daemon=True).start()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            if os.path.exists(HTML):
                with open(HTML) as f:
                    self.wfile.write(f.read().encode())
            else:
                self.wfile.write(b"<h1>Zorin TV</h1>")
        elif path == "/gallery":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            with open("/tmp/ott-captures/gallery.html") as f:
                self.wfile.write(f.read().encode())
        elif path == "/gallery-unknown":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            with open("/tmp/ott-captures/gallery-unknown.html") as f:
                self.wfile.write(f.read().encode())
        elif path == "/rename-page":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            with open("/tmp/ott-captures/rename.html") as f:
                self.wfile.write(f.read().encode())

        elif path == "/hls":
            b = (params.get("u") or [""])[0]
            try:
                up = _b64u_dec(b)
            except Exception:
                up = ""
            if not valid_url(up):
                self.send_response(400)
                self.end_headers()
                return
            try:
                status, ctype, data, final_url = fetch_upstream(up)
            except Exception:
                auto_healed = False
                for c in get_channels():
                    if c["url"] == up or c["url"].split("?")[0] == up.split("?")[0]:
                        new_url, info = auto_heal_channel(c["name"], c["url"])
                        if new_url:
                            try:
                                status, ctype, data, final_url = fetch_upstream(new_url)
                                auto_healed = True
                                break
                            except Exception:
                                pass
                        break
                if not auto_healed:
                    self.send_response(502)
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    return
            is_m3u8 = (up.split("?")[0].endswith(".m3u8")
                       or "mpegurl" in ctype.lower()
                       or data[:7].lstrip().startswith(b"#EXTM3U"))
            if is_m3u8:
                body = rewrite_m3u8(data.decode("utf-8", "ignore"), final_url).encode()
                out_ctype = "application/vnd.apple.mpegurl"
            else:
                body = data
                out_ctype = ctype or "application/octet-stream"
            self.send_response(200)
            self.send_header("Content-Type", out_ctype)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif path.startswith("/captures/"):
            raw = urllib.parse.unquote(path.split("/captures/", 1)[1])
            filename = os.path.basename(raw)
            filepath = os.path.join("/tmp/ott-captures", filename)
            if not os.path.exists(filepath):
                filepath = os.path.join("/tmp/ott-solo", filename)
            if os.path.exists(filepath):
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.end_headers()
                with open(filepath, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode() if length else ""
        params = urllib.parse.parse_qs(body)
        path = urllib.parse.urlparse(self.path).path

        if path == "/add-channel":
            name = (params.get("name") or [""])[0].strip()
            url = (params.get("url") or [""])[0].strip()
            if name and not valid_url(url):
                self.json({"ok": False, "message": "URL invalid (trebuie http:// sau https://)"})
                return
            if name and url:
                with open(SKILL, "a") as f:
                    f.write(f'#EXTINF:-1,{name}\n{url}\n')
                # preserve existing cache, add new channel as never_checked
                cache = load_cache() or {"channels": [], "results": [], "checked_at": 0}
                new_ch = {"name": name, "url": url, "live": True, "info": "never_checked",
                          "group": get_group(url, name)}
                cache["channels"].append(new_ch)
                cache["results"].append({"name": name, "url": url, "live": True, "info": "never_checked"})
                cache["results"].sort(key=lambda x: x["name"].lower())
                save_cache(cache)
                self.json({"ok": True, "message": f"Adăugat {name}"})
            else:
                self.json({"ok": False, "message": "Nume și URL obligatorii"})

        elif path == "/delete-channel":
            url = (params.get("url") or [""])[0].strip()
            if not url:
                self.json({"ok": False, "message": "URL lipsă"})
                return
            removed = False
            if os.path.exists(SKILL):
                with open(SKILL) as f:
                    lines = f.readlines()
                out = []
                i = 0
                while i < len(lines):
                    if (lines[i].startswith("#EXTINF:") and i + 1 < len(lines)
                            and lines[i + 1].strip() == url):
                        removed = True
                        i += 2
                        continue
                    out.append(lines[i])
                    i += 1
                with open(SKILL, "w") as f:
                    f.writelines(out)
            cache_ch = get_channels()
            for c in cache_ch:
                c["live"] = True
                c["info"] = "never_checked"
            save_cache({"channels": cache_ch, "results": [], "checked_at": 0})
            self.json({"ok": removed, "message": "Șters" if removed else "Nu am găsit URL-ul"})

        elif path == "/rename":
            old_name = (params.get("old_name") or [""])[0].strip()
            new_name = (params.get("new_name") or [""])[0].strip()
            if not old_name or not new_name:
                self.json({"ok": False, "message": "Nume vechi și nou obligatorii"})
                return
            if os.path.exists(SKILL):
                with open(SKILL) as f:
                    content = f.read()
                # Replace in #EXTINF lines only
                lines = content.split('\n')
                renamed = False
                for i, line in enumerate(lines):
                    if line.startswith("#EXTINF:") and old_name in line:
                        lines[i] = line.replace(old_name, new_name, 1)
                        renamed = True
                if renamed:
                    with open(SKILL, "w") as f:
                        f.write('\n'.join(lines))
                    save_cache({"channels": get_channels(), "results": [], "checked_at": 0})
                    self.json({"ok": True, "message": f"Redenumit {old_name} → {new_name}"})
                else:
                    self.json({"ok": False, "message": f"Nu am găsit '{old_name}'"})
            else:
                self.json({"ok": False, "message": "SKILL.md lipsă"})

        else:
            self.json({"ok": False, "message": "Endpoint necunoscut"})

    def probe_all_and_cache(self):
        channels = get_channels()
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            fut = {}
            for c in channels:
                fu = pool.submit(probe_channel, c["url"])
                fut[fu] = c
            for f in concurrent.futures.as_completed(fut):
                c = fut[f]
                try:
                    live, info = f.result()
                except Exception:
                    live, info = False, "probe_error"
                if live:
                    results.append({"name": c["name"], "url": c["url"], "live": True, "info": info})
                else:
                    try:
                        new_url, new_info = auto_heal_channel(c["name"], c["url"])
                    except Exception:
                        new_url, new_info = None, None
                    if new_url:
                        results.append({"name": c["name"], "url": new_url, "live": True, "info": new_info})
                    else:
                        results.append({"name": c["name"], "url": c["url"], "live": False, "info": str(info)})
        results.sort(key=lambda x: x["name"].lower())
        cache_data = {"channels": get_channels(), "results": results, "checked_at": int(time.time())}
        save_cache(cache_data)

    def json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, *a): pass

if __name__ == "__main__":
    t = threading.Thread(target=auto_heal_background, daemon=True)
    t.start()
    port = int(os.environ.get("TV_UI_PORT", 8899))
    httpd = http.server.HTTPServer(("127.0.0.1", port), Handler)
    print(f"Zorin TV UI: http://127.0.0.1:{port}  (auto-heal activ)")
    httpd.serve_forever()


