#!/usr/bin/env bash
# BB Email Dashboard — Test Runner complet
# Rulare: cd betterbird-ccdew && bash tests/run_all_tests.sh
set -uo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT="$(dirname "$DIR")"
PASS=0
FAIL=0
SKIP=0
TOTAL=0

RED='\033[0;31m'
GRN='\033[0;32m'
YLW='\033[1;33m'
BLU='\033[0;34m'
NC='\033[0m'

header() { echo -e "\n${BLU}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; echo -e "${BLU}  $1${NC}"; echo -e "${BLU}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"; }
ok()     { echo -e "  ${GRN}✓${NC} $1"; PASS=$((PASS+1)); TOTAL=$((TOTAL+1)); }
fail()   { echo -e "  ${RED}✗${NC} $1"; FAIL=$((FAIL+1)); TOTAL=$((TOTAL+1)); }
skip()   { echo -e "  ${YLW}~${NC} $1 (skip)"; SKIP=$((SKIP+1)); TOTAL=$((TOTAL+1)); }

# ── 0. Verificări de bază ────────────────────────────────────────────────────
header "0. Verificări mediu"

python3 --version > /dev/null 2>&1 && ok "Python3 disponibil" || fail "Python3 lipsă"
curl -s http://localhost:8766/api/health > /dev/null 2>&1 && ok "Server 8766 online" || { echo -e "  ${YLW}⚠${NC}  Serverul nu rulează — pornesc..."; python3 "$PROJECT/../.claude/helpers/email-dashboard-server.py" 8766 > /tmp/bb-test-server.log 2>&1 & sleep 3; curl -s http://localhost:8766/api/health > /dev/null 2>&1 && ok "Server pornit acum" || fail "Server nu pornit"; }
[[ -f "$PROJECT/sidebar.html" ]]   && ok "sidebar.html există" || fail "sidebar.html lipsă"
[[ -f "$PROJECT/manifest.json" ]]  && ok "manifest.json există" || fail "manifest.json lipsă"
[[ -f "$PROJECT/background.js" ]]  && ok "background.js există" || fail "background.js lipsă"
[[ -f "$PROJECT/icons/ccdew-48.png" ]] && ok "Icon 48px există" || fail "Icon 48px lipsă"

# ── 1. Unit Tests (server logic) ─────────────────────────────────────────────
header "1. Unit Tests — Server Logic"
cd "$PROJECT"
if python3 tests/test_server_unit.py -v 2>&1 | tail -5 | grep -q "OK"; then
    COUNT=$(python3 tests/test_server_unit.py 2>&1 | grep -oP '\d+ test' | head -1 | grep -oP '\d+' || echo '?')
    ok "Unit tests: $COUNT teste trecute"
else
    OUTPUT=$(python3 tests/test_server_unit.py 2>&1 | tail -20)
    fail "Unit tests eșuate:\n$OUTPUT"
fi

# ── 2. Frontend Static Tests ─────────────────────────────────────────────────
header "2. Frontend Static Tests"
if python3 tests/test_frontend_logic.py 2>&1 | tail -5 | grep -q "OK"; then
    ok "Frontend tests: toate trecute"
else
    OUTPUT=$(python3 tests/test_frontend_logic.py 2>&1 | grep -E "FAIL|ERROR" | head -10)
    fail "Frontend tests eșuate:\n$OUTPUT"
fi

# ── 3. Integration Tests (API HTTP) ──────────────────────────────────────────
header "3. Integration Tests — API HTTP"
if python3 tests/test_api_integration.py 2>&1 | tail -5 | grep -q "OK"; then
    ok "API integration tests: toate trecute"
else
    OUTPUT=$(python3 tests/test_api_integration.py 2>&1 | grep -E "FAIL|ERROR" | head -10)
    fail "API integration tests eșuate:\n$OUTPUT"
fi

# ── 4. Verificări rapide API (curl) ──────────────────────────────────────────
header "4. Smoke Tests — Curl"

check_endpoint() {
    local path=$1 expected=$2 label=$3
    local resp
    resp=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8766$path" 2>/dev/null)
    [[ "$resp" == "$expected" ]] && ok "$label → HTTP $resp" || fail "$label → expected $expected, got $resp"
}

check_endpoint "/api/health"         "200" "GET /api/health"
check_endpoint "/api/impact-alerts"  "200" "GET /api/impact-alerts"
check_endpoint "/api/actionable"     "200" "GET /api/actionable"
check_endpoint "/bb"                 "200" "GET /bb"
check_endpoint "/api/inexistent_xyz" "404" "GET endpoint inexistent → 404"

# CORS preflight
CORS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X OPTIONS \
  -H "Origin: http://localhost:8766" \
  -H "Access-Control-Request-Method: POST" \
  "http://localhost:8766/api/action" 2>/dev/null)
[[ "$CORS_STATUS" == "204" ]] && ok "OPTIONS /api/action → 204" || fail "OPTIONS preflight → $CORS_STATUS (expected 204)"

# POST /api/action
ACTION_RESP=$(curl -s -X POST http://localhost:8766/api/action \
  -H 'Content-Type: application/json' \
  -d '{"action":"archive","subject":"RunnerTest"}' 2>/dev/null)
echo "$ACTION_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get('ok') else 1)" 2>/dev/null \
  && ok "POST /api/action archive → ok:true" || fail "POST /api/action archive → ok:false"

# ── 5. Verificări Security statice ───────────────────────────────────────────
header "5. Security Checks"

# CSP în manifest
python3 -c "
import json
with open('manifest.json') as f: m=json.load(f)
csp=m.get('content_security_policy','')
assert \"script-src 'self'\" in csp, 'CSP lipsă script-src self'
assert \"'unsafe-inline'\" not in csp, 'CSP permite unsafe-inline!'
print('OK')
" 2>/dev/null && ok "manifest.json CSP corect" || fail "manifest.json CSP greșit/lipsă"

# messagesUpdate eliminat
python3 -c "
import json
with open('manifest.json') as f: m=json.load(f)
perms=m.get('permissions',[])
assert 'messagesUpdate' not in perms, 'messagesUpdate încă prezent!'
print('OK')
" 2>/dev/null && ok "manifest.json fără permisiuni inutile" || fail "manifest.json are permisiuni inutile"

# Server bind pe 127.0.0.1 (nu 0.0.0.0)
grep -q "127.0.0.1" "../.claude/helpers/email-dashboard-server.py" \
  && ok "Server bind pe 127.0.0.1" || fail "Server bind pe 0.0.0.0 (expus în rețea!)"

# Path traversal
TRAVERSAL=$(curl -s "http://localhost:8766/api/bb-open?q=../../etc/passwd" 2>/dev/null)
echo "$TRAVERSAL" | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(1 if d.get('ok')==True else 0)" 2>/dev/null \
  && ok "Path traversal blocat" || fail "Path traversal NU blocat!"

# ── 6. Verificări JS sidebar ─────────────────────────────────────────────────
header "6. JS Sidebar Checks"

html_check() {
    local pattern=$1 label=$2
    grep -q "$pattern" sidebar.html && ok "$label" || fail "$label lipsă"
}

html_check 'AbortController'        'Fetch timeout (AbortController)'
html_check 'clearInterval'          'clearInterval prezent'
html_check 'aria-live'              'aria-live pe alerts'
html_check 'tabindex="0"'           'tabindex keyboard nav'
html_check 'updateStickyTop'        'sticky top dinamic'
html_check 'hover:none'             'touch support media query'
html_check 'toast-container'        'toast container fix'
html_check '&#39;'                  'esc() apostrofe'
html_check '/api/action'            'endpoint action corect'
html_check 'prefers-reduced-motion' 'reduced motion support'
html_check 'focus-visible'          'focus styles keyboard'

# ── 7. Verificări background.js ───────────────────────────────────────────────
header "7. background.js Checks"

bg_check() {
    local pattern=$1 label=$2
    grep -q "$pattern" background.js && ok "$label" || fail "$label lipsă"
}

bg_check 'collectFolders'   'Recursie subfoldere'
bg_check 'spam'             'Skip spam folders'
bg_check 'junk'             'Skip junk folders'
bg_check 'trash'            'Skip trash folders'
bg_check 'subFolders'       'subFolders traversal'
bg_check 'return true'      'Async response handler'
bg_check 'priorityOrder'    'Prioritate inbox'

# ── SUMAR ─────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BLU}════════════════════════════════════════════════════${NC}"
echo -e "${BLU}  SUMAR TESTE${NC}"
echo -e "${BLU}════════════════════════════════════════════════════${NC}"
echo -e "  Total:   $TOTAL"
echo -e "  ${GRN}Trecute: $PASS${NC}"
[[ $FAIL -gt 0 ]] && echo -e "  ${RED}Eșuate:  $FAIL${NC}" || echo -e "  Eșuate:  0"
[[ $SKIP -gt 0 ]] && echo -e "  ${YLW}Sărite:  $SKIP${NC}"

PCT=$(( PASS * 100 / TOTAL ))
echo ""
if [[ $FAIL -eq 0 ]]; then
    echo -e "  ${GRN}✅ TOATE TESTELE TRECUTE ($PCT%)${NC}"
    exit 0
else
    echo -e "  ${RED}❌ $FAIL TESTE EȘUATE ($PCT% success rate)${NC}"
    exit 1
fi
