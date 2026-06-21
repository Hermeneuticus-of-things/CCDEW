#!/usr/bin/env python3
"""
Zorin Agent — Home v1.0
Descoperă și controlează device-uri smart: Bluetooth + WiFi.
Lights, cameras, sensors.
"""
import os, sys, json, time, threading, requests, subprocess, socket, struct, re
from datetime import datetime, timezone
from pathlib import Path

HOME = os.path.expanduser("~")
BUS_URL = "http://127.0.0.1:8765"
STATE_DIR = os.path.join(HOME, ".local", "state", "zorin-agent", "home")
os.makedirs(STATE_DIR, exist_ok=True)
DEVICES_FILE = os.path.join(STATE_DIR, "devices.json")

class AgentHome:
    def __init__(self):
        self.running = False
        self.devices = []  # {id, name, type, protocol, ip, mac, commands, last_seen}

    def _bus(self, method, path, data=None):
        try:
            url = f"{BUS_URL}{path}"
            r = (requests.get if method == "GET" else requests.post)(url, json=data, timeout=3)
            return r.json()
        except: return {}

    def _log(self, event, data=None):
        self._bus("POST", "/message/send", {
            "from": "zorin-agent-home", "to": "*",
            "type": "log", "payload": {"event": event, "data": data or {}}
        })

    def register(self):
        self._bus("POST", "/agent/register", {
            "name": "zorin-agent-home",
            "type": "home",
            "capabilities": ["bluetooth_scan", "wifi_scan", "zigbee", "philips_hue", "smart_devices", "light_control", "device_discovery"]
        })

    def heartbeat(self):
        while self.running:
            self._bus("POST", "/agent/heartbeat", {"name": "zorin-agent-home"})
            time.sleep(30)

    def _run(self, cmd, timeout=10):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return {"ok": r.returncode == 0, "stdout": r.stdout, "stderr": r.stderr}
        except subprocess.TimeoutExpired: return {"ok": False, "error": "timeout"}
        except FileNotFoundError: return {"ok": False, "error": f"not found: {cmd[0]}"}
        except Exception as e: return {"ok": False, "error": str(e)}

    # ── Bluetooth scan ──
    def scan_bluetooth(self):
        devices = []
        # Method 1: bluetoothctl
        r = self._run(["bluetoothctl", "--timeout", "5", "scan", "on"], 10)
        r2 = self._run(["bluetoothctl", "devices"], 5)
        if r2["ok"]:
            for line in r2["stdout"].split("\n"):
                m = re.match(r"Device\s+([0-9A-F:]+)\s+(.+)", line)
                if m:
                    mac, name = m.group(1), m.group(2).strip()
                    devices.append({
                        "id": f"bt-{mac.lower().replace(':', '')}",
                        "name": name,
                        "mac": mac,
                        "protocol": "bluetooth",
                        "type": self._guess_type(name),
                        "last_seen": datetime.now(timezone.utc).isoformat()
                    })
        # Method 2: hcitool
        r3 = self._run(["hcitool", "scan"], 10)
        if r3["ok"]:
            for line in r3["stdout"].split("\n"):
                m = re.match(r"\s*([0-9A-F:]+)\s+(.+)", line)
                if m and not any(d["mac"] == m.group(1) for d in devices):
                    mac, name = m.group(1), m.group(2).strip()
                    devices.append({
                        "id": f"bt-{mac.lower().replace(':', '')}",
                        "name": name, "mac": mac, "protocol": "bluetooth",
                        "type": self._guess_type(name),
                        "last_seen": datetime.now(timezone.utc).isoformat()
                    })
        self._merge_devices(devices)
        return devices

    # ── WiFi / LAN scan ──
    def scan_wifi(self):
        devices = []
        # Get local subnet
        iface = self._get_active_iface()
        subnet = self._get_subnet(iface)
        if not subnet:
            return devices

        # ARP scan (may need root)
        r = self._run(["arp-scan", "--localnet", "--retry=2", "--timeout=500"], 30)
        if not r["ok"]:
            r = self._run(["nmap", "-sn", subnet], 60)
        if not r["ok"] or not devices:
            # Ping sweep (works without root)
            devices = self.ping_sweep(subnet)
            self._merge_devices(devices)
            return devices

        if r["ok"]:
            for line in r["stdout"].split("\n"):
                m = re.search(r"([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+).*?([0-9A-Fa-f:]{17})", line)
                if m:
                    ip, mac = m.group(1), m.group(2).upper()
                    if ip.endswith(".1") or ip.endswith(".255"):
                        continue
                    name = self._resolve_hostname(ip)
                    devices.append({
                        "id": f"wifi-{mac.lower().replace(':', '')}",
                        "name": name or f"Device {ip}",
                        "ip": ip, "mac": mac, "protocol": "wifi",
                        "type": self._guess_type(name or "") or self._probe_device(ip),
                        "last_seen": datetime.now(timezone.utc).isoformat()
                    })

        # Try SSDP/mDNS discovery
        ssdp = self._run(["python3", "-c", """
import socket, struct, re
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
s.settimeout(3)
s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
msg = b'\\r\\n'.join([
    b'M-SEARCH * HTTP/1.1',
    b'HOST: 239.255.255.250:1900',
    b'MAN: "ssdp:discover"',
    b'ST: ssdp:all',
    b'MX: 2',
    b'', b''
])
s.sendto(msg, ('239.255.255.250', 1900))
found = set()
try:
    while True:
        data, addr = s.recvfrom(1024)
        ip = addr[0]
        host = data.decode('utf-8', errors='ignore')
        m = re.search(r'SERVER: (.+)', host)
        if m: found.add((ip, m.group(1).strip()[:60]))
except: pass
for ip, desc in found:
    print(json.dumps({'ip': ip, 'desc': desc}))
"""], 8)
        if ssdp["ok"]:
            for line in ssdp["stdout"].strip().split("\n"):
                try:
                    d = json.loads(line)
                    if not any(dev.get("ip") == d["ip"] for dev in devices):
                        devices.append({
                            "id": f"ssdp-{d['ip'].replace('.', '')}",
                            "name": d.get("desc", d["ip"]),
                            "ip": d["ip"], "protocol": "wifi",
                            "type": self._guess_type(d.get("desc", "")),
                            "last_seen": datetime.now(timezone.utc).isoformat()
                        })
                except: pass

        self._merge_devices(devices)
        return devices

    def _get_active_iface(self):
        r = self._run(["ip", "route", "get", "8.8.8.8"], 5)
        if r["ok"]:
            m = re.search(r"dev\s+(\w+)", r["stdout"])
            if m: return m.group(1)
        return "wlan0"

    def _get_subnet(self, iface):
        r = self._run(["ip", "-4", "addr", "show", iface], 5)
        if r["ok"]:
            m = re.search(r"inet\s+(\d+\.\d+\.\d+\.\d+)/(\d+)", r["stdout"])
            if m:
                ip, cidr = m.group(1), int(m.group(2))
                mask = (0xFFFFFFFF << (32 - cidr)) & 0xFFFFFFFF
                ip_int = struct.unpack("!I", socket.inet_aton(ip))[0]
                network = ip_int & mask
                return f"{socket.inet_ntoa(struct.pack('!I', network))}/{cidr}"
        return "192.168.1.0/24"

    def _resolve_hostname(self, ip):
        try: return socket.gethostbyaddr(ip)[0]
        except: return ""

    def _probe_device(self, ip):
        """Probe common smart device ports."""
        ports = {80: "web", 554: "camera_rtsp", 8080: "web_alt",
                 1900: "ssdp", 5353: "mdns", 8443: "camera_https",
                 2000: "smart_tv", 5555: "android"}
        for port, dtype in ports.items():
            try:
                s = socket.socket()
                s.settimeout(0.5)
                if s.connect_ex((ip, port)) == 0:
                    s.close()
                    return dtype
                s.close()
            except: pass
        return "unknown"

    def _guess_type(self, name):
        name = name.lower()
        if any(w in name for w in ["hue", "lamp", "light", "bulb", "led"]):
            return "light"
        if any(w in name for w in ["camera", "cam", "cctv", "ip_cam"]):
            return "camera"
        if any(w in name for w in ["tv", "television", "display", "mi tv"]):
            return "tv"
        if any(w in name for w in ["speaker", "sound", "audio", "sonos", "soundlink", "flex"]):
            return "speaker"
        if any(w in name for w in ["thermo", "ac", "climate", "temp"]):
            return "climate"
        if any(w in name for w in ["sensor", "motion", "door", "window"]):
            return "sensor"
        if any(w in name for w in ["plug", "switch", "outlet"]):
            return "switch"
        if any(w in name for w in ["hub", "bridge", "gateway"]):
            return "hub"
        if any(w in name for w in ["headphone", "headset", "earphone", "earbud", "qc", "bose"]):
            return "headphones"
        if any(w in name for w in ["phone", "galaxy", "iphone", "pixel", "oneplus", "g6", "s39"]):
            return "phone"
        if any(w in name for w in ["box", "freebox", "bbox"]):
            return "tv_box"
        if any(w in name for w in ["remote", "brc"]):
            return "remote"
        return "unknown"

    def _merge_devices(self, new_devices):
        existing_ids = {d["id"] for d in self.devices}
        for d in new_devices:
            if d["id"] not in existing_ids:
                self.devices.append(d)
        self.devices = self.devices[:200]
        with open(DEVICES_FILE, "w") as f:
            json.dump(self.devices, f, indent=2, ensure_ascii=False)

    # ── Ping sweep (rootless WiFi scan) ──
    def ping_sweep(self, subnet="192.168.99.0/24"):
        import concurrent.futures, ipaddress
        devices = []
        net = ipaddress.IPv4Network(subnet, strict=False)
        def _ping(ip):
            try:
                r = subprocess.run(["ping", "-c1", "-W1", str(ip)],
                    capture_output=True, timeout=2)
                if r.returncode == 0:
                    name = self._resolve_hostname(str(ip))
                    mac = self._mac_from_arp(str(ip))
                    return {"ip": str(ip), "name": name, "mac": mac}
            except: pass
            return None
        with concurrent.futures.ThreadPoolExecutor(30) as ex:
            for f in concurrent.futures.as_completed([ex.submit(_ping, ip) for ip in net.hosts()]):
                r = f.result()
                if r:
                    devices.append({
                        "id": f"wifi-{r['mac'].lower().replace(':', '') if r['mac'] else 'host-'+r['ip'].replace('.', '')}",
                        "name": r["name"] or f"Device {r['ip']}",
                        "ip": r["ip"], "mac": r["mac"] or "", "protocol": "wifi",
                        "type": self._guess_type(r["name"] or "") or self._probe_device(r["ip"]),
                        "last_seen": datetime.now(timezone.utc).isoformat()
                    })
        self._merge_devices(devices)
        return devices

    def _mac_from_arp(self, ip):
        try:
            r = subprocess.run(["arp", "-n", ip], capture_output=True, text=True, timeout=3)
            m = re.search(r"([0-9a-fA-F:]{17})", r.stdout)
            if m: return m.group(1)
        except: pass
        return ""

    # ── Sonos control ──
    def discover_sonos(self):
        devices = []
        known_ips = ["192.168.99.223"]
        for ip in known_ips:
            try:
                r = requests.get(f"http://{ip}:1400/status/zp", timeout=3)
                if r.status_code == 200 and "ZoneName" in r.text:
                    import xml.etree.ElementTree as ET
                    m = re.search(r"<ZoneName>(.*?)</ZoneName>", r.text)
                    zonename = m.group(1) if m else "Sonos"
                    m2 = re.search(r"<MACAddress>(.*?)</MACAddress>", r.text)
                    mac = m2.group(1) if m2 else ""
                    uid = re.search(r"<LocalUID>(.*?)</LocalUID>", r.text)
                    sn = re.search(r"<SerialNumber>(.*?)</SerialNumber>", r.text)
                    devices.append({
                        "id": f"sonos-{ip.replace('.', '')}",
                        "name": f"Sonos {zonename}",
                        "type": "speaker", "protocol": "sonos",
                        "ip": ip, "mac": mac,
                        "zone": zonename,
                        "uid": uid.group(1) if uid else "",
                        "serial": sn.group(1) if sn else "",
                        "last_seen": datetime.now(timezone.utc).isoformat()
                    })
            except: pass
        self._merge_devices(devices)
        return devices

    def _sonos_soap(self, ip, service, action, body_xml):
        import xml.etree.ElementTree as ET
        service_map = {
            "avtransport": "/MediaRenderer/AVTransport/Control",
            "rendering": "/MediaRenderer/RenderingControl/Control",
            "group": "/MediaRenderer/GroupManagement/Control",
        }
        path = service_map.get(service.lower(), service_map["avtransport"])
        ns = f"urn:schemas-upnp-org:service:{service}:1"
        soap = f'''<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <s:Body>
    <u:{action} xmlns:u="{ns}">
      {body_xml}
    </u:{action}>
  </s:Body>
</s:Envelope>'''
        try:
            s = socket.socket()
            s.settimeout(5)
            s.connect((ip, 1400))
            req = (f'POST {path} HTTP/1.1\r\nHost: {ip}:1400\r\n'
                   f'Content-Type: text/xml; charset="utf-8"\r\n'
                   f'SOAPAction: "{ns}#{action}"\r\n'
                   f'Content-Length: {len(soap)}\r\n\r\n{soap}')
            s.sendall(req.encode())
            resp = b""
            while True:
                chunk = s.recv(4096)
                if not chunk: break
                resp += chunk
            s.close()
            text = resp.decode("utf-8", errors="ignore")
            # Extract response values
            result = {}
            for m in re.finditer(r"<(\w+)>(.*?)</\1>", text):
                result[m.group(1)] = m.group(2)
            return result
        except Exception as e:
            return {"error": str(e)}

    def sonos_control(self, device, command, params=None):
        ip = device.get("ip", "192.168.99.223")
        if command == "play":
            return {"ok": True, "result": self._sonos_soap(ip, "AVTransport", "Play", "<InstanceID>0</InstanceID><Speed>1</Speed>")}
        elif command == "pause":
            return {"ok": True, "result": self._sonos_soap(ip, "AVTransport", "Pause", "<InstanceID>0</InstanceID>")}
        elif command == "stop":
            return {"ok": True, "result": self._sonos_soap(ip, "AVTransport", "Stop", "<InstanceID>0</InstanceID>")}
        elif command == "next":
            return {"ok": True, "result": self._sonos_soap(ip, "AVTransport", "Next", "<InstanceID>0</InstanceID>")}
        elif command == "previous":
            return {"ok": True, "result": self._sonos_soap(ip, "AVTransport", "Previous", "<InstanceID>0</InstanceID>")}
        elif command == "volume":
            vol = max(0, min(100, int(params or 50)))
            return {"ok": True, "result": self._sonos_soap(ip, "RenderingControl", "SetVolume",
                "<InstanceID>0</InstanceID><Channel>Master</Channel><DesiredVolume>" + str(vol) + "</DesiredVolume>")}
        elif command == "mute":
            return {"ok": True, "result": self._sonos_soap(ip, "RenderingControl", "SetMute",
                "<InstanceID>0</InstanceID><Channel>Master</Channel><DesiredMute>1</DesiredMute>")}
        elif command == "unmute":
            return {"ok": True, "result": self._sonos_soap(ip, "RenderingControl", "SetMute",
                "<InstanceID>0</InstanceID><Channel>Master</Channel><DesiredMute>0</DesiredMute>")}
        elif command == "status":
            info = self._sonos_soap(ip, "AVTransport", "GetTransportInfo", "<InstanceID>0</InstanceID>")
            vol = self._sonos_soap(ip, "RenderingControl", "GetVolume", "<InstanceID>0</InstanceID><Channel>Master</Channel>")
            return {"ok": True, "transport": info.get("CurrentTransportState", "UNKNOWN"),
                    "volume": vol.get("CurrentVolume", "?"), "result": info}
        else:
            return {"result": f"unknown command: {command}", "supported": ["play","pause","stop","next","previous","volume","mute","unmute","status"]}

    def get_devices(self, device_type=None):
        if device_type:
            return [d for d in self.devices if d.get("type") == device_type]
        return self.devices

    # ── Control ──
    def discover_zigbee(self):
        devices = []
        try:
            r = requests.get("http://localhost:8080/api/zigbee2mqtt/bridge/devices", timeout=5)
            if r.status_code == 200:
                for d in r.json():
                    devices.append({
                        "id": f"zigbee-{d.get('ieee_address', d.get('friendly_name', '')).replace(':', '')}",
                        "name": d.get("friendly_name", d.get("type", "Zigbee")),
                        "type": self._guess_type(d.get("type", "") + d.get("friendly_name", "")),
                        "protocol": "zigbee",
                        "ieee": d.get("ieee_address", ""),
                        "model": d.get("model_id", ""),
                        "vendor": d.get("vendor", ""),
                        "last_seen": datetime.now(timezone.utc).isoformat()
                    })
        except: pass
        self._merge_devices(devices)
        return devices

    def discover_hue(self):
        devices = []
        bridges = []
        try:
            r = requests.get("https://discovery.meethue.com/", timeout=5)
            if r.status_code == 200:
                bridges = [b["internalipaddress"] for b in r.json()]
        except: pass
        for ip in ["192.168.123.10", "192.168.1.100", "192.168.0.100"]:
            try:
                r = requests.get(f"http://{ip}/description.xml", timeout=2)
                if "Philips" in r.text or "hue" in r.text.lower():
                    bridges.append(ip)
            except: pass
        bridges = list(set(bridges))
        for bridge_ip in bridges:
            try:
                r = requests.get(f"http://{bridge_ip}/api/newdeveloper/lights", timeout=5)
                if r.status_code == 200:
                    for lid, ldata in r.json().items():
                        name = ldata.get("name", f"Hue Light {lid}")
                        devices.append({
                            "id": f"hue-{bridge_ip.replace('.', '')}-{lid}",
                            "name": name, "type": "light", "protocol": "hue",
                            "ip": bridge_ip, "light_id": lid, "bridge": bridge_ip,
                            "model": ldata.get("modelid", ""),
                            "reachable": ldata.get("state", {}).get("reachable", False),
                            "on": ldata.get("state", {}).get("on", False),
                            "bri": ldata.get("state", {}).get("bri", 0),
                            "last_seen": datetime.now(timezone.utc).isoformat()
                        })
            except: pass
        self._merge_devices(devices)
        return devices

    def control_device(self, device_id, command, params=None):
        device = next((d for d in self.devices if d["id"] == device_id), None)
        if not device:
            return {"error": "device not found"}

        result = {"device": device.get("name"), "command": command}
        proto = device.get("protocol", "")

        if proto == "sonos":
            result.update(self.sonos_control(device, command, params))
        elif proto == "hue":
            result.update(self.control_hue(device, command, params))
        elif proto == "zigbee":
            result.update(self.control_zigbee(device, command, params))
        elif device.get("type") == "light" and proto == "bluetooth":
            result.update(self._bt_light(device, command))
        elif device.get("ip"):
            result.update(self._http_device(device, command, params))
        else:
            result["result"] = "unknown control method"

        self._log("device_control", result)
        return result

    def control_hue(self, device, command, params=None):
        ip = device.get("ip"); lid = device.get("light_id")
        if not ip or not lid: return {"result": "missing hue info"}
        body = {}
        if command == "on": body = {"on": True}
        elif command == "off": body = {"on": False}
        elif command == "brightness":
            body = {"bri": max(0, min(254, int(params or 254)))}
        elif command == "color":
            if params: body = {"xy": params}
        try:
            r = requests.put(f"http://{ip}/api/newdeveloper/lights/{lid}/state",
                           json=body, timeout=3)
            return {"ok": r.status_code == 200, "result": r.json()}
        except Exception as e: return {"ok": False, "error": str(e)}

    def control_zigbee(self, device, command, params=None):
        name = device.get("name")
        try:
            payload = {"state": command.upper()} if command in ("on","off") else {}
            if command == "brightness":
                payload = {"brightness": max(0, min(254, int(params or 254)))}
            r = requests.post(f"http://localhost:8080/api/zigbee2mqtt/{name}/set",
                            json=payload, timeout=3)
            return {"ok": r.status_code in (200, 202)}
        except Exception as e: return {"ok": False, "error": str(e)}

    def _bt_light(self, device, command):
        mac = device.get("mac", "")
        if command == "on":
            r = self._run(["gatttool", "-b", mac, "--char-write-req",
                          "--handle=0x0012", "--value=cc2333"], 5)
        elif command == "off":
            r = self._run(["gatttool", "-b", mac, "--char-write-req",
                          "--handle=0x0012", "--value=cc2433"], 5)
        else:
            return {"result": "unsupported command", "supported": ["on", "off"]}
        return {"ok": r["ok"], "result": "sent" if r["ok"] else r.get("error")}

    def _http_device(self, device, command, params=None):
        ip = device.get("ip")
        if not ip: return {"result": "no ip"}
        # Try common smart device APIs
        APIs = [
            f"http://{ip}/cm?cmnd=Power%20{command.upper()}",
            f"http://{ip}/api/v1/{command}",
            f"http://{ip}/control?cmd={command}",
        ]
        for url in APIs:
            try:
                r = requests.get(url, timeout=3)
                if r.status_code < 500:
                    return {"ok": True, "api": url, "status": r.status_code}
            except: pass
        return {"result": "no compatible API found", "ip": ip}

    def discover_all(self):
        results = {"bluetooth": [], "wifi": [], "zigbee": [], "hue": [], "sonos": []}
        try: results["bluetooth"] = self.scan_bluetooth()
        except: pass
        try: results["wifi"] = self.scan_wifi()
        except: pass
        try: results["zigbee"] = self.discover_zigbee()
        except: pass
        try: results["hue"] = self.discover_hue()
        except: pass
        try: results["sonos"] = self.discover_sonos()
        except: pass
        total = sum(len(v) for v in results.values())
        self._log("discovery_complete", {"total": total, "bt": len(results["bluetooth"]), "wifi": len(results["wifi"])})
        self._bus("POST", "/memory/store", {
            "agent": "zorin-agent-home",
            "namespace": "home_devices",
            "key": "last_discovery",
            "value": json.dumps({"total": total, "ts": datetime.now(timezone.utc).isoformat()})
        })
        return results

    def scan_loop(self):
        while self.running:
            self.discover_all()
            time.sleep(300)

    def run(self):
        self.running = True
        self.register()
        threading.Thread(target=self.heartbeat, daemon=True).start()
        threading.Thread(target=self.scan_loop, daemon=True).start()
        # Start Hue Bridge emulation in a thread (import here to avoid circular)
        try:
            sys.path.insert(0, os.path.join(HOME, "CCDEW", ".claude", "helpers"))
            from zorin_hue_bridge import start_hue_bridge, load_config, register_known_devices
            load_config()
            register_known_devices()
            threading.Thread(target=start_hue_bridge, daemon=True).start()
            self._log("hue_bridge_started", {"port": int(os.environ.get("HUE_PORT", "8767"))})
        except Exception as e:
            self._log("hue_bridge_error", {"error": str(e)})
        self._log("home_agent_ready")
        print(json.dumps({"event": "zorin_home_ready"}))
        while self.running: time.sleep(1)

    def stop(self): self.running = False

if __name__ == "__main__":
    agent = AgentHome()
    try:
        if "--scan" in sys.argv:
            print(json.dumps(agent.discover_all(), indent=2))
        elif "--devices" in sys.argv:
            dtype = sys.argv[sys.argv.index("--devices")+1] if "--devices" in sys.argv and len(sys.argv) > sys.argv.index("--devices")+1 else None
            devs = agent.get_devices(dtype)
            print(f"Total device-uri: {len(devs)}")
            for d in devs:
                print(f"  {d.get('type','?'):10s} {d.get('name','?'):30s} {d.get('ip','') or d.get('mac','')}")
        elif "--control" in sys.argv:
            idx = sys.argv.index("--control")
            did = sys.argv[idx+1]
            cmd = sys.argv[idx+2] if len(sys.argv) > idx+2 else "on"
            print(json.dumps(agent.control_device(did, cmd)))
        else:
            agent.run()
    except KeyboardInterrupt:
        agent.stop()
