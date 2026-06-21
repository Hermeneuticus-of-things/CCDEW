#!/usr/bin/env python3
"""Roteste logul de token refresh - pastreaza ultimele 500 linii."""
import os

LOG = os.path.expanduser("~/.hermes/skills/zorin-romania-tv/.token-refresh.log")
MAX_LINES = 500

if os.path.exists(LOG):
    with open(LOG) as f:
        lines = f.readlines()
    if len(lines) > MAX_LINES:
        with open(LOG, "w") as f:
            f.writelines(lines[-MAX_LINES:])
        print(f"Log rotit: {len(lines)} -> {MAX_LINES} linii")
