#!/bin/bash
# Zorin TV Watchdog — menține serverul mereu pornit
SERVER_SCRIPT="/home/think/CCDEW/.claude/helpers/zorin-tv-server.py"
LOG="/tmp/zorin-watchdog.log"

# Verifică dacă serverul răspunde
if ! curl -sf "http://localhost:8899/status.json" --max-time 3 > /dev/null 2>&1; then
    echo "[$(date)] Server mort. Îl repornesc..." >> "$LOG"
    # Kill orfani
    pkill -f "zorin-tv-server.py" 2>/dev/null
    sleep 1
    nohup python3 "$SERVER_SCRIPT" >> /tmp/zorin-server.log 2>&1 &
    echo "[$(date)] Repornit PID $!" >> "$LOG"
    
    # Așteaptă să pornească
    sleep 3
    if curl -sf "http://localhost:8899/status.json" --max-time 3 > /dev/null 2>&1; then
        echo "[$(date)] Server funcțional." >> "$LOG"
    else
        echo "[$(date)] Eșec la pornire!" >> "$LOG"
    fi
fi
