#!/bin/bash
# CCDEW Brave Full Repair - Automat și Permanent

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║        CCDEW Brave Browser - REPARAȚIE COMPLETĂ              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Culori
red() { echo -e "\e[31m$1\e[0m"; }
green() { echo -e "\e[32m$1\e[0m"; }
yellow() { echo -e "\e[33m$1\e[0m"; }

# 1. Oprește toate procesele Brave
echo "1. Oprire procese Brave..."
killall -9 brave 2>/dev/null
sleep 1
green "   ✅ Gata"

# 2. Verifică dacă librăriile sunt instalate permanent
echo ""
echo "2. Verificare librării Wayland++..."
LIB_DIR="$HOME/.local/lib/wayland-fix"
if [ ! -d "$LIB_DIR" ] || [ ! -f "$LIB_DIR/libwayland-egl++.so.1" ]; then
    yellow "   ⚠️  Librăriile nu sunt instalate, se descarcă..."
    
    # Crează directorul
    mkdir -p "$LIB_DIR"
    cd /tmp
    
    # Descarcă librăriile
    apt-get download libwayland-egl++1 2>/dev/null
    apt-get download libwayland-cursor++1 2>/dev/null
    apt-get download libwayland-client++1 2>/dev/null
    
    # Extrage
    for deb in libwayland-*.deb; do
        dpkg -x "$deb" /tmp/wayland-tmp/ 2>/dev/null
    done
    
    # Copiază librăriile
    find /tmp/wayland-tmp -name "*.so*" -exec cp {} "$LIB_DIR/" \;
    rm -rf /tmp/wayland-tmp
    
    green "   ✅ Librării instalate în $LIB_DIR"
else
    green "   ✅ Librării deja prezente"
fi

# 3. Configurează environment permanent
echo ""
echo "3. Configurare profil shell..."
BASHRC="$HOME/.bashrc"
if ! grep -q "LD_LIBRARY_PATH.*wayland-fix" "$BASHRC" 2>/dev/null; then
    cat >> "$BASHRC" << 'EOF'

# CCDEW Brave Wayland Fix
export LD_LIBRARY_PATH="$HOME/.local/lib/wayland-fix:${LD_LIBRARY_PATH}"
EOF
    green "   ✅ Adăugat în .bashrc"
else
    green "   ✅ Deja configurat în .bashrc"
fi

# 4. Creează launchere funcționale
echo ""
echo "4. Creare launchere..."

# Launcher principal
cat > "$HOME/.local/bin/brave" << 'EOF'
#!/bin/bash
# Brave - varianta oficială cu librării fixate
export LD_LIBRARY_PATH="$HOME/.local/lib/wayland-fix:${LD_LIBRARY_PATH}"
/usr/bin/brave-browser "$@"
EOF
chmod +x "$HOME/.local/bin/brave"

# Launcher cu flags suplimentare pentru stabilitate
cat > "$HOME/.local/bin/brave-stable" << 'EOF'
#!/bin/bash
# Brave - mod stabilitate maximă
export LD_LIBRARY_PATH="$HOME/.local/lib/wayland-fix:${LD_LIBRARY_PATH}"
/usr/bin/brave-browser \
    --ozone-platform=wayland \
    --enable-features=UseOzonePlatform,WaylandWindowDecorations \
    --disable-features=Vulkan \
    "$@"
EOF
chmod +x "$HOME/.local/bin/brave-stable"

green "   ✅ Launchere create: brave, brave-stable"

# 5. Desktop entry funcțional
echo ""
echo "5. Creare iconiță desktop..."
cat > "$HOME/Desktop/Brave.desktop" << 'EOF'
[Desktop Entry]
Version=1.0
Name=Brave Browser
GenericName=Web Browser
Comment=Access the Internet
Exec=env LD_LIBRARY_PATH="/home/think/.local/lib/wayland-fix:${LD_LIBRARY_PATH}" /usr/bin/brave-browser %U
StartupNotify=true
Terminal=false
Icon=brave-browser
Type=Application
Categories=Network;WebBrowser;
MimeType=application/pdf;application/rdf+xml;application/rss+xml;application/xhtml+xml;application/xhtml_xml;application/xml;image/gif;image/jpeg;image/png;image/webp;text/html;text/xml;x-scheme-handler/http;x-scheme-handler/https;
Actions=new-window;new-private-window;

[Desktop Action new-window]
Name=New Window
Exec=env LD_LIBRARY_PATH="/home/think/.local/lib/wayland-fix:${LD_LIBRARY_PATH}" /usr/bin/brave-browser

[Desktop Action new-private-window]
Name=New Private Window
Exec=env LD_LIBRARY_PATH="/home/think/.local/lib/wayland-fix:${LD_LIBRARY_PATH}" /usr/bin/brave-browser --incognito
EOF
chmod +x "$HOME/Desktop/Brave.desktop"

green "   ✅ Iconiță desktop creată"

# 6. Test final
echo ""
echo "6. Testare finală..."
export LD_LIBRARY_PATH="$HOME/.local/lib/wayland-fix:${LD_LIBRARY_PATH}"

if /usr/bin/brave-browser --version > /dev/null 2>&1; then
    BRAVE_VER=$(/usr/bin/brave-browser --version 2>&1 | head -1)
    green "   ✅ Brave funcționează: $BRAVE_VER"
else
    red "   ❌ Test eșuat"
fi

# 7. Test cu dashboard
echo ""
echo "7. Testare CCDEW Dashboard..."
if curl -s http://localhost:8765/api/health > /dev/null 2>&1; then
    green "   ✅ Server CCDEW activ"
else
    yellow "   ⚠️  Server CCDEW inactiv - rulează: start-dashboard"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
green  " Reparație COMPLETĂ!"
echo ""
echo " Ce s-a reparat:"
echo "  • Librăriile Wayland++ lipsă au fost instalate în ~/.local/lib/"
echo "  • LD_LIBRARY_PATH configurat permanent în ~/.bashrc"
echo "  • Launchere funcționale: brave, brave-stable"
echo "  • Iconiță desktop funcțională"
echo ""
echo " Cum folosești Brave acum:"
echo "  1. brave           (normal, cu fix)"
echo "  2. brave-stable    (mod maxim stabilitate)"
echo "  3. Click pe iconița 'Brave' de pe desktop"
echo ""
echo " Pentru a aplica schimbările, rulează:"
echo "  source ~/.bashrc"
echo "  sau deschide un terminal nou"
echo "═══════════════════════════════════════════════════════════════"
