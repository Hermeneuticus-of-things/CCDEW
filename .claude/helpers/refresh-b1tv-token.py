#!/usr/bin/env python3
"""Reîmprospătează token-ul B1 TV în SKILL.md"""
import os, json, urllib.request
from urllib.parse import unquote, quote

SKILL = os.path.expanduser("~/.hermes/skills/zorin-romania-tv/SKILL.md")
API_URL = "https://www.b1tv.ro/wp-json/strawberry/v1/live"
BASE_CDN = "https://milos.cdn.dejacast.com/live/"

try:
    req = urllib.request.Request(API_URL, headers={"User-Agent": "Mozilla/5.0"})
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read())
    decoded = unquote(data.get("url", ""))
    new_url = BASE_CDN + decoded
    
    with open(SKILL) as f:
        lines = f.readlines()
    
    found = False
    with open(SKILL, "w") as f:
        for line in lines:
            if line.startswith("#EXTINF:-1,B1 TV (HD)"):
                f.write(line)
                found = True
            elif found and line.startswith("http"):
                f.write(new_url + "\n")
                found = False
            else:
                f.write(line)
    
    print(f"B1 TV token refreshed: {new_url[:60]}...")
except Exception as e:
    print(f"Failed to refresh B1 TV token: {e}")
