#!/usr/bin/env bash
# CCDEW Email Intelligence — instalare addon în Betterbird.
#
#   ./install-addon.sh           → împachetează .xpi + ghidează instalarea din UI
#   ./install-addon.sh --direct  → instalare DIRECTĂ (fără dialog): înregistrează
#                                  addon-ul în extensions.json al profilului.
#
# NOTĂ: --direct înregistrează un addon nesemnat local. E acțiunea TA, pe mașina TA.
# Scriptul închide Betterbird, face backup la extensions.json și e reversibil.
set -u

SRC="$(cd "$(dirname "$0")" && pwd)"
XPI="/tmp/ccdew-email-intelligence.xpi"
APP="eu.betterbird.Betterbird"
ID="ccdew-email-intelligence@ccdew"
PROFILE="$HOME/.var/app/$APP/.thunderbird/b8e98ik1.default-default"
MODE="${1:-ui}"

echo "── CCDEW Email Intelligence — install addon ──"

# 1. Validare fișiere necesare
for f in manifest.json background.js sidebar.html; do
  [ -f "$SRC/$f" ] || { echo "✗ Lipsește $f în $SRC"; exit 1; }
done

# 2. Verifică manifestul e MV2 (altfel BB 128 nu-l încarcă din UI corect)
MV=$(python3 -c "import json; print(json.load(open('$SRC/manifest.json')).get('manifest_version'))" 2>/dev/null)
if [ "$MV" != "2" ]; then
  echo "✗ manifest_version=$MV (trebuie 2). Rulează conversia MV2 înainte."; exit 1
fi
VER=$(python3 -c "import json; print(json.load(open('$SRC/manifest.json')).get('version','?'))" 2>/dev/null)

# ─────────────────────────────────────────────────────────────
# MOD --direct: instalare fără dialog (înregistrare în extensions.json)
# ─────────────────────────────────────────────────────────────
if [ "$MODE" = "--direct" ] || [ "$MODE" = "direct" ]; then
  EXTDIR="$PROFILE/extensions/$ID"
  EXTJSON="$PROFILE/extensions.json"
  USERJS="$PROFILE/user.js"

  [ -d "$PROFILE" ] || { echo "✗ Profil Betterbird negăsit: $PROFILE"; exit 1; }

  echo "→ Mod DIRECT (fără dialog). Profil: $PROFILE"

  # a. Închide Betterbird (altfel suprascrie extensions.json la ieșire)
  if pgrep -x betterbird-bin >/dev/null 2>&1; then
    echo "→ Închid Betterbird..."
    flatpak kill "$APP" 2>/dev/null
    for i in $(seq 1 8); do pgrep -x betterbird-bin >/dev/null 2>&1 || break; sleep 1; done
    if pgrep -x betterbird-bin >/dev/null 2>&1; then
      for pid in $(pgrep -f "bwrap.*betterbird"); do kill "$pid" 2>/dev/null; done; sleep 2
    fi
  fi

  # b. Copiază fișierele addon-ului ca director despachetat
  mkdir -p "$EXTDIR/icons"
  cp "$SRC/manifest.json" "$SRC/background.js" "$SRC/sidebar.html" "$EXTDIR/"
  cp "$SRC/icons/"*.png "$EXTDIR/icons/" 2>/dev/null
  echo "✓ Fișiere copiate în $EXTDIR"

  # c. Asigură pref-urile (semnătură off + scanare scopuri) în user.js
  for pref in \
    'user_pref("xpinstall.signatures.required", false);' \
    'user_pref("extensions.autoDisableScopes", 0);' \
    'user_pref("extensions.startupScanScopes", 15);'; do
    key=$(echo "$pref" | sed -E 's/user_pref\("([^"]+)".*/\1/')
    grep -q "$key" "$USERJS" 2>/dev/null || echo "$pref" >> "$USERJS"
  done
  echo "✓ Pref-uri verificate în user.js"

  # d. Înregistrează în extensions.json (cu backup)
  python3 - "$EXTJSON" "$EXTDIR" "$ID" "$VER" <<'PYEOF'
import json, sys, os, time, uuid, shutil
ef, desc, ID, VER = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
d = json.load(open(ef))
addons = d.get("addons", [])
addons = [a for a in addons if a.get("id") != ID]   # idempotent: scoate vechea intrare
now = int(time.time() * 1000)
addons.append({
  "id": ID, "syncGUID": str(uuid.uuid4()), "version": VER, "type": "extension",
  "loader": None, "optionsURL": None,
  "defaultLocale": {"name": "CCDEW Email Intelligence",
                    "description": "La deschiderea Betterbird vezi alertele de impact."},
  "status": 4, "active": True, "userDisabled": False, "appDisabled": False,
  "descriptor": desc, "installDate": now, "updateDate": now, "applyBackgroundUpdates": 1,
  "location": "app-profile", "seen": True, "hasBinaryComponents": False,
  "dependencies": [], "hasEmbeddedWebExtension": False, "softDisabled": False,
  "userPermissions": {"permissions": ["tabs","accountsRead","messagesRead","messagesUpdate","http://localhost:8766/*"],
                      "origins": ["http://localhost:8766/*"]},
  "optionalPermissions": [], "blocklistState": 0, "manifestVersion": 2,
  "multiprocessCompatible": True,
})
d["addons"] = addons
shutil.copy(ef, ef + ".pre-ccdew.bak")
json.dump(d, open(ef, "w"))
print(f"✓ Înregistrat în extensions.json (backup: {os.path.basename(ef)}.pre-ccdew.bak)")
PYEOF
  [ $? -eq 0 ] || { echo "✗ Eroare la înregistrare"; exit 1; }

  # e. Pornește Betterbird
  echo "→ Pornesc Betterbird..."
  nohup flatpak run "$APP" >/dev/null 2>&1 & disown
  sleep 12

  # f. Verifică înregistrarea
  python3 - "$EXTJSON" "$ID" <<'PYEOF'
import json, sys
d = json.load(open(sys.argv[1]))
a = next((x for x in d.get("addons", []) if x.get("id") == sys.argv[2]), None)
if a and a.get("active"):
    print(f"✓ SUCCES — addon activ: {a['id']} v{a.get('version')}")
else:
    print("⚠ Addon-ul nu apare activ încă. Verifică în Betterbird → Add-ons.")
PYEOF
  echo "── Gata. Restaurare: cp \"$EXTJSON.pre-ccdew.bak\" \"$EXTJSON\" (cu BB închis)"
  exit 0
fi

# 3. Împachetează .xpi (zip cu manifest la rădăcină)
rm -f "$XPI"
( cd "$SRC" && zip -q -r -X "$XPI" manifest.json background.js sidebar.html icons \
    -x '*.bak' -x 'install*.sh' -x 'README.md' ) \
  || { echo "✗ Eroare la împachetare (zip instalat?)"; exit 1; }
echo "✓ Împachetat: $XPI  (v$VER, $(du -h "$XPI" | cut -f1))"

# 4. Acordă Betterbird acces să citească .xpi din /tmp (sandbox flatpak)
if flatpak info "$APP" >/dev/null 2>&1; then
  flatpak override --user --filesystem=/tmp:ro "$APP" 2>/dev/null \
    && echo "✓ Acces flatpak /tmp:ro acordat lui Betterbird"
fi

# 5. Instrucțiuni clare pentru instalarea din UI
cat <<EOF

── INSTALARE (UI Betterbird, ~30s) ──
  1. Deschide Betterbird
  2. Meniu ☰  →  Add-ons and Themes   (sau Ctrl+Shift+A)
  3. Click pe rotița ⚙  →  Install Add-on From File…
  4. Alege fișierul:   $XPI
  5. Confirmă instalarea (BB te întreabă o dată)

După instalare apare butonul "CCDEW Impact Alerts" în bara de unelte.
Click pe el → vezi alertele de impact (dashboard pe localhost:8766).

EOF

# 6. Opțional: deschide direct pagina de add-ons (dacă BB rulează)
if pgrep -x betterbird-bin >/dev/null 2>&1; then
  read -r -p "Deschid acum pagina Add-ons în Betterbird? [y/N] " ans
  if [ "${ans,,}" = "y" ]; then
    flatpak run "$APP" "about:addons" >/dev/null 2>&1 &
    echo "→ Deschis about:addons. Continuă de la pasul 3."
  fi
fi
