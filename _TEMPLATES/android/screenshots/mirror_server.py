"""Live phone mirror — serves ADB screenshots as auto-refreshing web page with tap support.

Setup:
  1. Connect phone via USB, enable USB debugging
  2. Run: adb devices   -> copy device ID
  3. Set DEVICE below to your device ID (or leave empty for auto-detect)
  4. Run: python mirror_server.py
  5. Open http://localhost:8777 in browser (or use Preview panel)

Controls:
  Click      = tap on phone
  Drag       = swipe on phone
  Right-click = back button

For Preview panel integration, add to .claude/launch.json:
  {
    "version": "0.0.1",
    "configurations": [
      {
        "name": "phone-mirror",
        "runtimeExecutable": "python",
        "runtimeArgs": ["<PROJECT_PATH>/screenshots/mirror_server.py"],
        "port": 8777
      }
    ]
  }
"""
import subprocess, base64, http.server, socketserver, threading, time, sys, json, os

# -- CONFIG -------------------------------------------------------------------
# Auto-detect ADB path (Windows default); override if needed
ADB = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Android", "Sdk", "platform-tools", "adb.exe")
DEVICE = ""  # leave empty for auto-detect first connected device
PORT = 8777
# -----------------------------------------------------------------------------

latest_b64 = ""
screen_w, screen_h = 1080, 2400

def _si():
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 0
    return si

def get_device():
    if DEVICE:
        return DEVICE
    try:
        r = subprocess.run([ADB, "devices"], capture_output=True, timeout=5,
                           startupinfo=_si(), text=True)
        for line in r.stdout.strip().split("\n")[1:]:
            if "\tdevice" in line:
                return line.split("\t")[0]
    except Exception:
        pass
    return ""

def capture_loop():
    global latest_b64, screen_w, screen_h
    dev = get_device()
    if not dev:
        print("WARNING: No device found. Connect phone and restart.", flush=True)
        return
    print(f"Capturing from device: {dev}", flush=True)
    while True:
        try:
            r = subprocess.run([ADB, "-s", dev, "exec-out", "screencap", "-p"],
                               capture_output=True, timeout=5, startupinfo=_si())
            if r.returncode == 0 and len(r.stdout) > 1000:
                latest_b64 = base64.b64encode(r.stdout).decode()
                if len(r.stdout) > 24:
                    w = int.from_bytes(r.stdout[16:20], 'big')
                    h = int.from_bytes(r.stdout[20:24], 'big')
                    if w > 0 and h > 0:
                        screen_w, screen_h = w, h
        except Exception:
            pass
        time.sleep(0.8)

def adb_tap(dev, x, y):
    try:
        subprocess.run([ADB, "-s", dev, "shell", "input", "tap", str(int(x)), str(int(y))],
                       timeout=3, startupinfo=_si(), capture_output=True)
    except Exception:
        pass

def adb_swipe(dev, x1, y1, x2, y2, duration=300):
    try:
        subprocess.run([ADB, "-s", dev, "shell", "input", "swipe",
                       str(int(x1)), str(int(y1)), str(int(x2)), str(int(y2)), str(duration)],
                       timeout=3, startupinfo=_si(), capture_output=True)
    except Exception:
        pass

def adb_back(dev):
    try:
        subprocess.run([ADB, "-s", dev, "shell", "input", "keyevent", "4"],
                       timeout=3, startupinfo=_si(), capture_output=True)
    except Exception:
        pass

HTML = b"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Phone Mirror</title>
<style>
body{margin:0;background:#111;display:flex;justify-content:center;align-items:flex-start;min-height:100vh;user-select:none}
img{max-height:98vh;max-width:100vw;object-fit:contain;cursor:pointer}
#dot{position:fixed;width:24px;height:24px;border-radius:50%;background:rgba(255,255,255,0.5);
pointer-events:none;transform:translate(-50%,-50%);display:none;z-index:99}
</style></head>
<body>
<div id="dot"></div>
<img id="s">
<script>
const img=document.getElementById('s'), dot=document.getElementById('dot');
async function refresh(){try{const r=await fetch('/frame');const d=await r.text();
if(d.length>100)img.src='data:image/png;base64,'+d}catch(e){}
setTimeout(refresh,900)}refresh();

img.addEventListener('click', e=>{
  const rect=img.getBoundingClientRect();
  const rx=(e.clientX-rect.left)/rect.width;
  const ry=(e.clientY-rect.top)/rect.height;
  dot.style.left=e.clientX+'px'; dot.style.top=e.clientY+'px';
  dot.style.display='block';
  setTimeout(()=>dot.style.display='none',300);
  fetch('/tap',{method:'POST',body:JSON.stringify({rx,ry}),headers:{'Content-Type':'application/json'}});
});

let dragStart=null;
img.addEventListener('mousedown', e=>{dragStart={x:e.clientX,y:e.clientY};e.preventDefault()});
img.addEventListener('mouseup', e=>{
  if(!dragStart)return;
  const dx=e.clientX-dragStart.x, dy=e.clientY-dragStart.y;
  if(Math.sqrt(dx*dx+dy*dy)>30){
    const rect=img.getBoundingClientRect();
    const rx1=(dragStart.x-rect.left)/rect.width, ry1=(dragStart.y-rect.top)/rect.height;
    const rx2=(e.clientX-rect.left)/rect.width, ry2=(e.clientY-rect.top)/rect.height;
    fetch('/swipe',{method:'POST',body:JSON.stringify({rx1,ry1,rx2,ry2}),headers:{'Content-Type':'application/json'}});
  }
  dragStart=null;
});

img.addEventListener('contextmenu', e=>{
  e.preventDefault();
  fetch('/back',{method:'POST'});
});
</script></body></html>"""

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if self.path == "/frame":
                data = latest_b64.encode()
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_header("Content-Length", str(len(HTML)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(HTML)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length > 0 else b""
            dev = get_device()
            if self.path == "/tap":
                d = json.loads(body)
                threading.Thread(target=adb_tap, args=(dev, d["rx"]*screen_w, d["ry"]*screen_h), daemon=True).start()
            elif self.path == "/swipe":
                d = json.loads(body)
                threading.Thread(target=adb_swipe, args=(dev, d["rx1"]*screen_w, d["ry1"]*screen_h, d["rx2"]*screen_w, d["ry2"]*screen_h), daemon=True).start()
            elif self.path == "/back":
                threading.Thread(target=adb_back, args=(dev,), daemon=True).start()
            self.send_response(200)
            self.send_header("Content-Length", "0")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, *a): pass

class ThreadedServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

t = threading.Thread(target=capture_loop, daemon=True)
t.start()

server = ThreadedServer(("0.0.0.0", PORT), H)
print(f"Mirror server on http://localhost:{PORT}", flush=True)
print("  Click = tap | Drag = swipe | Right-click = back", flush=True)
sys.stdout.flush()
server.serve_forever()
