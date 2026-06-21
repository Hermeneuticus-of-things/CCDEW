#!/usr/bin/env python3
"""
Zorin Hue Bridge Emulator v1.0
Emulează API-ul Philips Hue Bridge.
Ascultă pe portul 8767 (sau 80).
Toate device-urile sunt gestionate prin bus-ul :8765.
"""
import os, sys, json, time, threading, socket, re, struct
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone

HOME = os.path.expanduser("~")
BUS_URL = "http://127.0.0.1:8765"
HUE_PORT = int(os.environ.get("HUE_PORT", "8767"))
HUE_API_KEY = "zorin-home-agent"
STATE_DIR = os.path.join(HOME, ".local", "state", "zorin-agent", "hue")
os.makedirs(STATE_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(STATE_DIR, "bridge_config.json")
SCENE_FILE = os.path.join(STATE_DIR, "scenes.json")

import requests as req

def bus_get(path):
    try:
        r = req.get(f"{BUS_URL}{path}", timeout=3)
        return r.json()
    except: return {}

def bus_post(path, data=None):
    try:
        r = req.post(f"{BUS_URL}{path}", json=data, timeout=3)
        return r.json()
    except: return {}

BRIDGE_CONFIG = {
    "name": "Zorin Home Bridge",
    "zigbeechannel": 11,
    "bridgeid": "ZORINHOMEBRIDGE01",
    "mac": "00:17:88:00:00:01",
    "modelid": "ZORIN-BRIDGE-v1",
    "apiversion": "1.60.0",
    "swversion": "1958202001",
    "factorynew": True,
    "replacesbridgeid": None,
    "datastoreversion": "136",
    "starterkitid": "",
    "config": {
        "name": "Zorin Home Bridge",
        "bridgeid": "ZORINHOMEBRIDGE01",
        "mac": "00:17:88:00:00:01",
        "modelid": "ZORIN-BRIDGE-v1",
        "apiversion": "1.60.0",
        "swversion": "1958202001",
        "url": f"http://127.0.0.1:{HUE_PORT}",
        "port": HUE_PORT,
        "linkbutton": False,
        "ipaddress": "127.0.0.1",
        "netmask": "255.255.255.0",
        "gateway": "192.168.99.1",
        "dhcp": True,
        "proxyaddress": "",
        "proxyport": 0,
        "whitelist": {HUE_API_KEY: {"name": "Zorin Agent", "create date": "2026-06-18T21:00:00"}},
        "swupdate": {"updatestate": 0, "checkforupdate": False, "devicetypes": {"bridge": False, "lights": [], "sensors": []}, "url": "", "text": "", "notify": False},
        "timezone": "Europe/Bucharest",
        "utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
        "localtime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    },
    "lights": {},
    "groups": {"0": {"name": "Toate luminile", "lights": [], "type": "Room", "class": "Other", "action": {"on": False, "bri": 0}}},
    "sensors": {},
    "scenes": {},
    "rules": {},
    "resourcelinks": {}
}

SCENE_NAMES = [
    "Relax", "Read", "Concentrate", "Energize", "Bright",
    "Dim", "Nightlight", "Savana sunset", "Tropical twilight",
    "Arctic aurora", "Spring blossom", "Summer glow"
]

def load_config():
    global BRIDGE_CONFIG
    try:
        with open(CONFIG_FILE) as f:
            saved = json.load(f)
            BRIDGE_CONFIG.update(saved)
    except: pass

def save_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump(BRIDGE_CONFIG, f, indent=2)

def device_to_light(dev):
    lid = dev.get("id", "unknown")
    name = dev.get("name", "Light")
    dtype = dev.get("type", "light")
    proto = dev.get("protocol", "")
    reachable = True

    if proto == "hue":
        return {
            "state": {"on": dev.get("on", False), "bri": dev.get("bri", 254),
                      "hue": 0, "sat": 0, "xy": [0.5, 0.5], "ct": 350,
                      "alert": "none", "effect": "none", "colormode": "ct",
                      "reachable": dev.get("reachable", True)},
            "type": "Extended color light",
            "name": name,
            "modelid": dev.get("model", "LCT001"),
            "manufacturername": "Philips",
            "productname": "Hue color light",
            "uniqueid": f"{dev.get('mac', lid).replace('-', ':')}:00:00:00-01",
            "swversion": "1.50.2_r31159",
            "protocol": proto
        }
    elif proto == "bluetooth" and "hue" in name.lower():
        return {
            "state": {"on": False, "bri": 200, "reachable": reachable},
            "type": "On/Off light",
            "name": name,
            "modelid": "LOM001",
            "manufacturername": "Philips",
            "productname": "Hue Go",
            "uniqueid": f"{dev.get('mac', lid).replace('-', ':')}:00:00:00-02",
            "swversion": "1.0.0",
            "protocol": proto
        }
    elif dtype == "light" or "light" in name.lower() or "innr" in name.lower():
        return {
            "state": {"on": False, "bri": 254, "reachable": reachable},
            "type": "Dimmable light",
            "name": name,
            "modelid": "BR286",
            "manufacturername": "Innr",
            "productname": "Innr BR 286 C-2",
            "uniqueid": f"zorin-{lid[:8]}:00:00:00-03",
            "swversion": "1.0.0",
            "protocol": proto
        }
    return None

def build_lights():
    lights = {}
    used_names = set()
    devices_file = os.path.join(HOME, ".local", "state", "zorin-agent", "home", "devices.json")
    devices = []
    try:
        with open(devices_file) as f:
            devices = json.load(f)
    except: pass

    # Adaugă device-urile descoperite primele (au nume reale)
    idx = 1
    for dev in devices:
        light = device_to_light(dev)
        if light:
            lid = str(idx)
            lights[lid] = light
            used_names.add(light["name"].lower())
            idx += 1

    # Adaugă device-urile din config care nu sunt deja descoperite
    for lid, ldata in sorted(BRIDGE_CONFIG.get("lights", {}).items()):
        if ldata.get("name", "").lower() not in used_names:
            lights[str(idx)] = ldata
            used_names.add(ldata.get("name", "").lower())
            idx += 1

    # Actualizează grupurile
    BRIDGE_CONFIG["groups"]["0"]["lights"] = list(lights.keys())
    return lights

# ── Hue API Request Handler ──
class HueHandler(BaseHTTPRequestHandler):
    def _send(self, data, status=200):
        body = json.dumps(data, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_xml(self, xml, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "text/xml; charset=utf-8")
        self.send_header("Content-Length", str(len(xml)))
        self.end_headers()
        self.wfile.write(xml.encode())

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length > 0:
            return self.rfile.read(length).decode("utf-8", errors="ignore")
        return ""

    def log_message(self, fmt, *args):
        sys.stderr.write(f"[HueBridge] {args[0] if args else ''}\n")

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        params = parse_qs(parsed.query)

        # UPnP discovery
        if path == "/description.xml":
            xml = f'''<?xml version="1.0" encoding="UTF-8" ?>
<root xmlns="urn:schemas-upnp-org:device-1-0">
<specVersion><major>1</major><minor>0</minor></specVersion>
<URLBase>http://127.0.0.1:{HUE_PORT}/</URLBase>
<device>
<deviceType>urn:schemas-upnp-org:device:bridge:1</deviceType>
<friendlyName>Zorin Home Bridge (Zorin Home Bridge)</friendlyName>
<manufacturer>Zorin Agent</manufacturer>
<modelName>ZORIN-BRIDGE-v1</modelName>
<modelNumber>ZORINBRIDGE01</modelNumber>
<UDN>uuid:2f402f80-da50-11e8-8000-001788000001</UDN>
<serialNumber>ZORINBRIDGE01</serialNumber>
</device>
</root>'''
            return self._send_xml(xml)

        # Hue API
        parts = path.split("/")
        if len(parts) >= 3 and parts[1] == "api":
            key = parts[2]
            if key not in BRIDGE_CONFIG.get("config", {}).get("whitelist", {}) and key != "newdeveloper":
                self._send([{"error": {"type": 1, "address": path, "description": "unauthorized user"}}])
                return

            # GET /api/<key> - full config
            if len(parts) == 3:
                cfg = BRIDGE_CONFIG.copy()
                cfg["lights"] = build_lights()
                self._send(cfg)
            # GET /api/<key>/lights
            elif len(parts) == 4 and parts[3] == "lights":
                self._send(build_lights())
            # GET /api/<key>/lights/<id>
            elif len(parts) == 5 and parts[3] == "lights":
                lights = build_lights()
                lid = parts[4]
                self._send(lights.get(lid, {"error": "light not found"}))
            # GET /api/<key>/config
            elif len(parts) == 4 and parts[3] == "config":
                self._send(BRIDGE_CONFIG.get("config", {}))
            # GET /api/<key>/groups
            elif len(parts) == 4 and parts[3] == "groups":
                self._send(BRIDGE_CONFIG.get("groups", {}))
            # GET /api/<key>/scenes
            elif len(parts) == 4 and parts[3] == "scenes":
                self._send(BRIDGE_CONFIG.get("scenes", {}))
            # GET /api/<key>/sensors
            elif len(parts) == 4 and parts[3] == "sensors":
                self._send(BRIDGE_CONFIG.get("sensors", {}))
            else:
                self._send({"error": "not found"}, 404)
        else:
            self._send({"error": "not found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        body = self._read_body()
        parts = path.split("/")

        # POST /api - create user (link button)
        if path == "/api":
            data = json.loads(body) if body else {}
            devicetype = data.get("devicetype", "unknown")
            if not BRIDGE_CONFIG["config"]["linkbutton"]:
                self._send([{"error": {"type": 101, "address": "", "description": "link button not pressed"}}])
                return
            username = HUE_API_KEY
            BRIDGE_CONFIG["config"]["whitelist"][username] = {
                "name": devicetype,
                "create date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S"),
                "last use date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
            }
            save_config()
            self._send([{"success": {"username": username}}])

        # POST /api/<key>/lights - search for new lights
        elif len(parts) == 4 and parts[3] == "lights":
            key = parts[2]
            if key not in BRIDGE_CONFIG["config"]["whitelist"] and key != "newdeveloper":
                self._send([{"error": {"type": 1, "address": path, "description": "unauthorized"}}])
                return
            t = threading.Thread(target=self._search_lights, daemon=True)
            t.start()
            self._send([{"success": {"/lights": "Searching for new devices..."}}])

        else:
            self._send([{"error": {"type": 4, "address": path, "description": "method not allowed"}}], 405)

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        body = self._read_body()
        parts = path.split("/")

        if len(parts) >= 6 and parts[3] == "lights" and parts[5] == "state":
            key = parts[2]; lid = parts[4]
            if key not in BRIDGE_CONFIG["config"]["whitelist"] and key != "newdeveloper":
                self._send([{"error": {"type": 1, "address": path, "description": "unauthorized"}}])
                return
            try:
                data = json.loads(body) if body else {}
            except: data = {}
            result = self._control_light(lid, data)
            self._send(result)

        elif len(parts) == 4 and parts[3] == "config":
            key = parts[2]
            try:
                data = json.loads(body) if body else {}
                if "linkbutton" in data:
                    BRIDGE_CONFIG["config"]["linkbutton"] = data["linkbutton"]
                    save_config()
                self._send([{"success": {"/config": "updated"}}])
            except:
                self._send([{"error": {"type": 7, "address": path, "description": "invalid json"}}])

        else:
            self._send([{"error": {"type": 4, "address": path, "description": "method not allowed"}}], 405)

    def _search_lights(self):
        time.sleep(3)
        devs = bus_get("/home/devices") if False else []
        bus_post("/task/add", {"agent": "zorin-agent-home", "action": "discover_all", "payload": {}})

    def _control_light(self, lid, data):
        lights = build_lights()
        if lid not in lights:
            return [{"error": {"type": 3, "address": f"/lights/{lid}", "description": "resource not available"}}]

        light = lights[lid]
        proto = light.get("protocol", "")
        name = light.get("name", "")
        state = light.get("state", {})

        on = data.get("on", state.get("on"))
        bri = data.get("bri", state.get("bri", 254))

        command = "on" if on else "off"
        if "bri" in data:
            command = "brightness"

        # Trimite comanda prin bus
        result = bus_post("/message/send", {
            "from": "zorin-hue-bridge",
            "to": "zorin-agent-home",
            "type": "command",
            "payload": {"action": "control_device", "device_name": name, "command": command, "params": bri}
        })

        state["on"] = on
        state["bri"] = bri
        state["reachable"] = True
        responses = []
        if "on" in data:
            responses.append({"success": {f"/lights/{lid}/state/on": on}})
        if "bri" in data:
            responses.append({"success": {f"/lights/{lid}/state/bri": bri}})
        return responses

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

# ── Main ──
def start_hue_bridge(port=HUE_PORT):
    server = HTTPServer(("0.0.0.0", port), HueHandler)
    print(json.dumps({"event": "hue_bridge_ready", "port": port,
                       "api": f"http://127.0.0.1:{port}/api/{HUE_API_KEY}/lights"}))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()

def register_known_devices():
    """Adaugă device-uri cunoscute în config dacă nu există."""
    known = [
        {"name": "Hue Go", "model": "LOM001", "manufacturer": "Philips", "type": "light"},
        {"name": "Innr BR 286 C-2 #1", "model": "BR286", "manufacturer": "Innr", "type": "light"},
        {"name": "Innr BR 286 C-2 #2", "model": "BR286", "manufacturer": "Innr", "type": "light"},
    ]
    lights = BRIDGE_CONFIG.get("lights", {})
    for i, dev in enumerate(known):
        lid = str(i + 1)
        if lid not in lights:
            lights[lid] = {
                "state": {"on": False, "bri": 254, "reachable": True},
                "type": "Dimmable light",
                "name": dev["name"],
                "modelid": dev["model"],
                "manufacturername": dev["manufacturer"],
                "productname": dev["name"],
                "uniqueid": f"00:17:88:{i:02x}:00:00:00-{i+1:02x}",
                "swversion": "1.0.0",
            }
            if lid not in BRIDGE_CONFIG["groups"]["0"]["lights"]:
                BRIDGE_CONFIG["groups"]["0"]["lights"].append(lid)
    BRIDGE_CONFIG["lights"] = lights
    save_config()

if __name__ == "__main__":
    load_config()
    register_known_devices()
    print(json.dumps({"config": f"Hue Bridge emulation on port {HUE_PORT}"}))
    start_hue_bridge()
