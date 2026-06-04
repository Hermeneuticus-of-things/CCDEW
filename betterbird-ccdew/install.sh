#!/bin/bash
# Instaleaza CCDEW ca sidebar panel in Betterbird (Flatpak)

set -e

EXT_DIR="$HOME/CCDEW/betterbird-ccdew"
BB_FLATPAK="eu.betterbird.Betterbird"
BB_PROFILE="$HOME/.var/app/$BB_FLATPAK/.thunderbird"

echo "═══════════════════════════════════════════════════"
echo "    CCDEW Betterbird Extension — Instalare Flatpak"
echo "═══════════════════════════════════════════════════"
echo ""

# 1. Verifica Flatpak
if ! flatpak list --app | grep -q "$BB_FLATPAK"; then
    echo "  ✗ BetterBird nu este instalat ca Flatpak"
    echo "  Instaleaza: flatpak install flathub eu.betterbird.Betterbird"
    exit 1
fi
echo "  ✓ BetterBird Flatpak detectat"

# 2. Verifica dashboard-ul
echo ""
echo "📊 Verific dashboard-ul CCDEW..."
if curl -s http://localhost:8766/api/health > /dev/null 2>&1; then
    echo "  ✓ Dashboard ruleaza pe port 8766"
else
    echo "  ⚠ Dashboard-ul nu ruleaza — pornesc..."
    nohup python3 "$HOME/CCDEW/.claude/helpers/email-dashboard-server.py" 8766 > /tmp/ccdew-email-dashboard.log 2>&1 &
    sleep 2
    if curl -s http://localhost:8766/api/health > /dev/null 2>&1; then
        echo "  ✓ Dashboard pornit"
    else
        echo "  ✗ Nu am putut porni dashboard-ul"
        exit 1
    fi
fi

# 3. Creeaza zip pentru instalare
echo ""
echo "📦 Creez pachetul de instalare..."
cd "$EXT_DIR"
ZIP_FILE="/tmp/ccdew-betterbird-extension.xpi"
rm -f "$ZIP_FILE"
zip -r "$ZIP_FILE" manifest.json sidebar.html background.js icons/ -q -x "*.bak"
echo "  ✓ Pachet creat: $ZIP_FILE"

# 4. Grant access pentru Flatpak la folderul CCDEW
echo ""
echo "🔓 Configurez acces Flatpak la CCDEW..."
flatpak override --user "$BB_FLATPAK" --filesystem="$HOME/CCDEW:ro" 2>/dev/null || true
echo "  ✓ Acces acordat"

# 5. Copiaza extensia in locatia Flatpak
echo ""
echo "📋 Instalez extensia in profilul BetterBird..."
EXT_TARGET="$BB_PROFILE/b8e98ik1.default-default/extensions"
if [ -d "$EXT_TARGET" ]; then
    # Remove old version if exists
    rm -f "$EXT_TARGET"/ccdew-email-intelligence@ccdew.xpi 2>/dev/null || true
    cp "$ZIP_FILE" "$EXT_TARGET/ccdew-email-intelligence@ccdew.xpi"
    echo "  ✓ Extensie copiata in profil"
else
    echo "  ⚠ Directorul extensiilor nu a fost gasit"
    echo "  Foloseste metoda manuala de mai jos"
fi

# 6. Instructiuni
echo ""
echo "═══════════════════════════════════════════════════"
echo "              Instalare Completa                   "
echo "═══════════════════════════════════════════════════"
echo ""
echo "1. Deschide BetterBird (sau restart daca e deschis)"
echo "2. Verifica sidebar-ul stanga — ar trebui sa vezi"
echo "   iconita CCDEW cu alertele de impact"
echo ""
echo "Daca nu apare:"
echo "  a. Ctrl+Shift+A → Add-ons → verifica CCDEW"
echo "  b. about:debugging → Load Temporary Add-on"
echo "     → selecteaza: $EXT_DIR/manifest.json"
echo ""
echo "Click pe orice alerta → email-ul se deschide instant."
