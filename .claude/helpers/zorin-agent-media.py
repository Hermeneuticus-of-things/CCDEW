#!/usr/bin/env python3
"""
Zorin Agent — Media v1.0
Download, convertire, organizare media.
"""
import os, sys, json, time, threading, requests, subprocess
from datetime import datetime, timezone
from pathlib import Path

HOME = os.path.expanduser("~")
BUS_URL = "http://127.0.0.1:8765"
STATE_DIR = os.path.join(HOME, ".local", "state", "zorin-agent", "media")
os.makedirs(STATE_DIR, exist_ok=True)
MEDIA_CACHE = os.path.join(STATE_DIR, "media_index.json")
DOWNLOAD_DIR = os.path.join(HOME, "Downloads")

class AgentMedia:
    def __init__(self):
        self.running = False
        self.index = {}

    def _bus(self, method, path, data=None):
        try:
            url = f"{BUS_URL}{path}"
            r = (requests.get if method == "GET" else requests.post)(url, json=data, timeout=3)
            return r.json()
        except: return {}

    def _log(self, event, data=None):
        self._bus("POST", "/message/send", {
            "from": "zorin-agent-media", "to": "*",
            "type": "log", "payload": {"event": event, "data": data or {}}
        })

    def register(self):
        self._bus("POST", "/agent/register", {
            "name": "zorin-agent-media",
            "type": "media",
            "capabilities": ["download", "convert", "metadata", "organize_media", "yt_dlp"]
        })

    def heartbeat(self):
        while self.running:
            self._bus("POST", "/agent/heartbeat", {"name": "zorin-agent-media"})
            time.sleep(30)

    def download(self, url, output_dir=DOWNLOAD_DIR):
        try:
            r = subprocess.run(
                ["yt-dlp", "-o", f"{output_dir}/%(title)s.%(ext)s", url],
                capture_output=True, text=True, timeout=300
            )
            ok = r.returncode == 0
            if ok:
                self._log("download_ok", {"url": url[:80], "output": output_dir})
            return {"ok": ok, "output": r.stdout[-300:] or r.stderr[-300:]}
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "timeout"}
        except FileNotFoundError:
            return {"ok": False, "error": "yt-dlp not installed. Run: pip3 install yt-dlp"}

    def convert(self, input_path, output_format="mp3"):
        if not os.path.exists(input_path):
            return {"error": "file not found"}
        base = os.path.splitext(input_path)[0]
        output = f"{base}.{output_format}"
        try:
            if output_format in ("mp3", "ogg", "wav", "flac"):
                r = subprocess.run(
                    ["ffmpeg", "-i", input_path, "-y", output],
                    capture_output=True, text=True, timeout=120
                )
            elif output_format in ("mp4", "mkv", "avi"):
                r = subprocess.run(
                    ["ffmpeg", "-i", input_path, "-c:v", "libx264", "-c:a", "aac", "-y", output],
                    capture_output=True, text=True, timeout=300
                )
            else:
                return {"error": f"unsupported format: {output_format}"}
            ok = r.returncode == 0
            if ok:
                self._log("convert_ok", {"from": input_path, "to": output})
            return {"ok": ok, "output": output, "log": r.stderr[-200:]}
        except FileNotFoundError:
            return {"error": "ffmpeg not installed. Run: sudo apt install ffmpeg"}
        except Exception as e:
            return {"error": str(e)}

    def scan_media(self, path=DOWNLOAD_DIR):
        media = {"audio": [], "video": [], "image": []}
        audio_ext = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac"}
        video_ext = {".mp4", ".mkv", ".avi", ".mov", ".wmv"}
        image_ext = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"}

        for f in os.listdir(path):
            fpath = os.path.join(path, f)
            if os.path.isfile(fpath):
                ext = os.path.splitext(f)[1].lower()
                size = os.path.getsize(fpath)
                entry = {"file": f, "path": fpath, "size_mb": round(size/1024/1024, 1)}
                if ext in audio_ext:
                    media["audio"].append(entry)
                elif ext in video_ext:
                    media["video"].append(entry)
                elif ext in image_ext:
                    media["image"].append(entry)

        self.index = media
        with open(MEDIA_CACHE, "w") as f:
            json.dump(media, f, indent=2)
        self._log("media_scan", {k: len(v) for k, v in media.items()})
        return media

    def organize_by_type(self, target=DOWNLOAD_DIR):
        dirs = {"Audio": os.path.join(target, "Audio"),
                "Video": os.path.join(target, "Video"),
                "Imagini": os.path.join(target, "Imagini")}
        for d in dirs.values():
            os.makedirs(d, exist_ok=True)

        media = self.scan_media(target)
        moved = 0
        for f in media["audio"]:
            shutil.move(f["path"], os.path.join(dirs["Audio"], f["file"])); moved += 1
        for f in media["video"]:
            shutil.move(f["path"], os.path.join(dirs["Video"], f["file"])); moved += 1
        for f in media["image"]:
            shutil.move(f["path"], os.path.join(dirs["Imagini"], f["file"])); moved += 1

        self._log("media_organized", {"moved": moved})
        return {"moved": moved, "dirs": list(dirs.keys())}

    def run(self):
        self.running = True
        self.register()
        threading.Thread(target=self.heartbeat, daemon=True).start()
        self._log("media_agent_ready")
        print(json.dumps({"event": "zorin_media_ready"}))
        while self.running: time.sleep(1)

    def stop(self): self.running = False

if __name__ == "__main__":
    import shutil
    agent = AgentMedia()
    try:
        if "--dl" in sys.argv:
            url = sys.argv[sys.argv.index("--dl")+1]
            print(json.dumps(agent.download(url)))
        elif "--convert" in sys.argv:
            idx = sys.argv.index("--convert")
            f = sys.argv[idx+1]; fmt = sys.argv[idx+2] if len(sys.argv) > idx+2 else "mp3"
            print(json.dumps(agent.convert(f, fmt)))
        elif "--scan" in sys.argv:
            path = sys.argv[sys.argv.index("--scan")+1] if "--scan" in sys.argv and len(sys.argv) > sys.argv.index("--scan")+1 else DOWNLOAD_DIR
            print(json.dumps(agent.scan_media(path)))
        elif "--organize" in sys.argv:
            path = sys.argv[sys.argv.index("--organize")+1] if "--organize" in sys.argv and len(sys.argv) > sys.argv.index("--organize")+1 else DOWNLOAD_DIR
            print(json.dumps(agent.organize_by_type(path)))
        else:
            agent.run()
    except KeyboardInterrupt:
        agent.stop()
