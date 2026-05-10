#!/usr/bin/env python
"""nlm_auto_login.py — Permanent NLM auth solution.

Workflow:
1. Check if Brave is running with CDP on :9222
2. If not: launch Brave with --remote-debugging-port=9222 in dedicated profile
   (separate user-data-dir, doesn't disturb user's main Brave)
3. Extract cookies via CDP (uses extract_cdp_cookies.py)
4. Import via `nlm login --manual --file <cookies>` (proper auth state)
5. Verify via `nlm login --check`

Usage:
  python nlm_auto_login.py               # Full auto-login
  python nlm_auto_login.py --check       # Only check validity, exit 0/1
  python nlm_auto_login.py --refresh     # Force refresh even if valid
  python nlm_auto_login.py --silent      # Suppress progress, return code only

First run: user must login to NotebookLM once in the dedicated Brave window.
After that: cookies persist in dedicated profile, auto-refresh silently.
"""

import subprocess
import time
import urllib.request
import sys
import os
import json
from pathlib import Path

CDP_PORT = 9222
BRAVE_EXE = os.environ.get('BRAVE_EXE') or os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe")
NLM_PROFILE_DIR = Path.home() / ".claude" / "nlm-auth-profile"
EXTRACT_SCRIPT = Path.home() / ".claude" / "scripts" / "extract_cdp_cookies.py"
COOKIES_FILE = Path(os.environ.get('TEMP', '/tmp')) / "nlm_cookies.txt"
AUTH_JSON = Path.home() / ".notebooklm-mcp-cli" / "auth.json"
LOG_FILE = Path.home() / ".claude" / "scripts" / "nlm_auto_login.log"


def log(msg: str, silent: bool = False) -> None:
    """Log to file + optionally stderr."""
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + "\n")
    if not silent:
        print(line, file=sys.stderr)


def cdp_alive() -> bool:
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/version", timeout=2)
        return True
    except Exception:
        return False


def check_blocking_env_vars() -> list:
    """v2: Detect env vars that BLOCK auto-refresh per AUTHENTICATION.md."""
    blocking = []
    for var in ('NOTEBOOKLM_COOKIES', 'NOTEBOOKLM_CSRF_TOKEN', 'NOTEBOOKLM_SESSION_ID'):
        if os.environ.get(var):
            blocking.append(var)
    return blocking


def auth_is_valid() -> bool:
    """v2: Two-stage check — nlm login --check AND actual notebook list call."""
    # Stage 1: nlm CLI check (fast)
    try:
        env = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}
        result = subprocess.run(
            ['nlm', 'login', '--check'],
            capture_output=True, text=True, env=env, timeout=15
        )
        out = (result.stdout + result.stderr).lower()
        cli_ok = result.returncode == 0 and ('expired' not in out and 'invalid' not in out)
        if not cli_ok:
            return False
    except Exception:
        return False

    # Stage 2: actual API call (definitive proof)
    try:
        result = subprocess.run(
            ['nlm', 'list', 'notebooks', '--json'],
            capture_output=True, text=True, env=env, timeout=20
        )
        return result.returncode == 0 and 'authentication' not in result.stderr.lower()
    except Exception:
        return False


# NOTE: --keep-alive REMOVED v3 (2026-05-02) — interval refresh declanșa anti-bot
# detection în NLM (vezi reference_nlm_anti_suspicion_strategy.md). Refresh DOAR
# la failure efectiv (401 din notebook_query), nu preventiv.


def launch_brave_dedicated(silent: bool = False) -> subprocess.Popen:
    """Launch Brave with dedicated profile + CDP enabled."""
    NLM_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    args = [
        str(BRAVE_EXE),
        f'--remote-debugging-port={CDP_PORT}',
        f'--user-data-dir={NLM_PROFILE_DIR}',
        '--no-default-browser-check',
        '--no-first-run',
        '--disable-features=Translate,DefaultBrowserSettingEnforcement',
        '--window-size=900,700',
        'https://notebooklm.google.com'
    ]
    if silent:
        flags = 0x08000000  # CREATE_NO_WINDOW (background, no visible window)
    else:
        flags = 0  # Default: visible window for first-run login
    return subprocess.Popen(args, creationflags=flags)


def extract_cookies() -> str:
    """Run extract_cdp_cookies.py and return the cookies string."""
    result = subprocess.run(
        [sys.executable, str(EXTRACT_SCRIPT)],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        raise RuntimeError(f"extract_cdp_cookies.py failed: {result.stderr}")
    return result.stdout.strip()


def import_via_nlm(cookies_file: Path) -> bool:
    """Import cookies via `nlm login --manual --file`."""
    env = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}
    try:
        result = subprocess.run(
            ['nlm', 'login', '--manual', '--file', str(cookies_file), '--force'],
            capture_output=True, text=True, env=env, timeout=30
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        return False


def import_via_direct_json(cookies_str: str) -> bool:
    """Fallback: write cookies directly to auth.json."""
    cookies_dict = {}
    for pair in cookies_str.split('; '):
        if '=' in pair:
            k, v = pair.split('=', 1)
            cookies_dict[k] = v.strip()

    if 'SID' not in cookies_dict:
        return False

    auth_data = {
        "cookies": cookies_dict,
        "csrf_token": "",
        "session_id": cookies_dict.get('SID', ''),
        "build_label": "",
        "extracted_at": time.strftime('%Y-%m-%dT%H:%M:%S')
    }
    AUTH_JSON.parent.mkdir(parents=True, exist_ok=True)
    AUTH_JSON.write_text(json.dumps(auth_data, indent=2), encoding='utf-8')
    return True


def main():
    args = sys.argv[1:]
    silent = '--silent' in args
    check_only = '--check' in args
    force_refresh = '--refresh' in args

    # v2: Blocking env vars warning (per AUTHENTICATION.md)
    blocking = check_blocking_env_vars()
    if blocking and not silent:
        print(f"⚠ WARNING: env vars {blocking} BLOCK auto-refresh. Remove them.", file=sys.stderr)
        log(f"Blocking env vars detected: {blocking}", silent)

    log(f"nlm_auto_login start (check={check_only}, force={force_refresh})", silent)

    if check_only:
        valid = auth_is_valid()
        if valid:
            if not silent:
                print("AUTH_VALID")
            sys.exit(0)
        else:
            if not silent:
                print("AUTH_INVALID")
            sys.exit(1)

    # If already valid and not forcing refresh, skip
    if not force_refresh and auth_is_valid():
        log("Auth already valid, skipping refresh", silent)
        if not silent:
            print("AUTH_VALID (no refresh needed)")
        sys.exit(0)

    # Step 1: ensure CDP
    if not cdp_alive():
        first_run = not (NLM_PROFILE_DIR / "Default" / "Cookies").exists()
        log(f"CDP not alive. Launching Brave (first_run={first_run})", silent)
        if first_run and not silent:
            print("FIRST RUN: Brave will open. Please login to NotebookLM in that window.", file=sys.stderr)
            print("After login, this script will auto-extract cookies and complete setup.", file=sys.stderr)
        launch_brave_dedicated(silent=not first_run)

        # Wait for CDP
        for _ in range(30):
            time.sleep(1)
            if cdp_alive():
                break
        if not cdp_alive():
            log("ERROR: Brave failed to start with CDP", silent)
            sys.exit(2)
        log("Brave CDP ready", silent)
        # Extra wait for cookies to populate
        time.sleep(5 if not first_run else 30)

    # Step 2: extract cookies
    try:
        cookies_str = extract_cookies()
    except Exception as e:
        log(f"Extract failed: {e}", silent)
        sys.exit(3)

    if 'SID=' not in cookies_str:
        log("ERROR: No SID cookie. User not logged in.", silent)
        if not silent:
            print("Login at https://notebooklm.google.com in the Brave window, then re-run.", file=sys.stderr)
        sys.exit(4)

    log(f"Cookies extracted ({len(cookies_str)} bytes)", silent)

    # Step 3: import via nlm login (preferred) or direct JSON (fallback)
    if import_via_nlm(COOKIES_FILE):
        log("Imported via `nlm login --manual --file`", silent)
    else:
        log("nlm login failed, trying direct JSON write", silent)
        if not import_via_direct_json(cookies_str):
            log("ERROR: Both import methods failed", silent)
            sys.exit(5)
        log("Imported via direct auth.json write", silent)

    # Step 4: verify
    if auth_is_valid():
        log("✓ Auth verified", silent)
        if not silent:
            print("AUTH_REFRESHED_OK")
        sys.exit(0)
    else:
        log("⚠ Auth import succeeded but validation failed", silent)
        sys.exit(6)


if __name__ == "__main__":
    main()
