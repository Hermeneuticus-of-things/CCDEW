#!/bin/bash
# CCDEW Brave Browser Fix - Repară problemele Brave pe Zorin OS/Wayland

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║           CCDEW Brave Browser Repair Tool                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Funcție pentru afișare cu culori
green() { echo -e "\e[32m$1\e[0m"; }
red() { echo -e "\e[31m$1\e[0m"; }
yellow() { echo -e "\e[33m$1\e[0m"; }
blue() { echo -e "\e[34m$1\e[0m"; }

# 1. Verifică dacă Brave este instalat
echo "1. Verificare Brave..."
if command -v brave-browser &> /dev/null; then
    BRAVE_PATH=$(which brave-browser)
    green "   ✅ Brave găsit: $BRAVE_PATH"
else
    red "   ❌ Brave nu este instalat!"
    echo "   Instalează cu: sudo apt install brave-browser"
    exit 1
fi

# 2. Oprește toate procesele Brave
echo ""
echo "2. Oprire procese Brave..."
BRAVE_COUNT=$(pgrep -c brave)
if [ $BRAVE_COUNT -gt 0 ]; then
    killall -9 brave 2>/dev/null
    sleep 2
    green "   ✅ $BRAVE_COUNT procese oprite"
else
    yellow "   ℹ️  Nu rulează procese Brave"
fi

# 3. Curățare cache corupt
echo ""
echo "3. Curățare cache..."
CACHE_DIR="$HOME/.cache/BraveSoftware"
if [ -d "$CACHE_DIR" ]; then
    rm -rf "$CACHE_DIR"/*
    green "   ✅ Cache curățat"
else
    yellow "   ℹ️  Nu există cache de curățat"
fi

# 4. Verificare GPU/Vulkan
echo ""
echo "4. Verificare GPU..."
if lspci | grep -qi nvidia; then
    yellow "   ⚠️  Detectat NVIDIA - posibile probleme driver"
    echo "   Soluție: --disable-gpu sau update driver"
fi
if lspci | grep -qi amd; then
    yellow "   ⚠️  Detectat AMD - verifică mesa drivers"
fi
if lspci | grep -qi intel; then
    green "   ✅ Detectat Intel GPU"
fi

# 5. Verificare display server
echo ""
echo "5. Verificare Display Server..."
if [ "$XDG_SESSION_TYPE" = "wayland" ]; then
    yellow "   ⚠️  Rulezi Wayland - Brave poate avea probleme"
    echo "   Se generează launcher X11..."
else
    green "   ✅ Rulezi X11 - compatibilitate OK"
fi

# 6. Creează launcher fix
echo ""
echo "6. Generare launcher Brave (mod compatibilitate)..."
LAUNCHER="$HOME/.local/bin/brave-fixed"
cat > "$LAUNCHER" << 'EOF'
#!/bin/bash
# Brave Browser - Mod Compatibilitate CCDEW
# Fix pentru Wayland/Zorin OS

# Forțează X11 backend
export QT_QPA_PLATFORM=xcb
export GDK_BACKEND=x11
export SDL_VIDEODRIVER=x11
export MOZ_ENABLE_WAYLAND=0

# Dezactivează features problematice
export GBM_BACKEND=llvmpipe
export LIBGL_ALWAYS_SOFTWARE=0

# Parametri Brave pentru stabilitate
BRAVE_FLAGS=(
    --ozone-platform=x11
    --disable-gpu
    --disable-software-rasterizer
    --disable-features=VizDisplayCompositor,CanvasOopRasterization
    --no-sandbox
    --disable-smooth-scrolling
    --disable-gpu-compositing
    --disable-gpu-rasterization
    --enable-features=VaapiVideoDecoder
)

# Dacă există argument, folosește-l (URL)
if [ $# -eq 0 ]; then
    /opt/brave.com/brave/brave "${BRAVE_FLAGS[@]}" &
else
    /opt/brave.com/brave/brave "${BRAVE_FLAGS[@]}" "$@" &
fi
EOF
chmod +x "$LAUNCHER"
green "   ✅ Launcher creat: $LAUNCHER"

# 7. Creează desktop entry
echo ""
echo "7. Creare iconiță desktop..."
DESKTOP="$HOME/Desktop/Brave-Fixed.desktop"
cat > "$DESKTOP" << EOF
[Desktop Entry]
Name=Brave (Fixed)
Comment=Brave Browser - Mod Compatibilitate CCDEW
Exec=$LAUNCHER %U
Icon=brave-browser
Terminal=false
Type=Application
Categories=Network;WebBrowser;
StartupNotify=true
StartupWMClass=brave
EOF
chmod +x "$DESKTOP"
green "   ✅ Iconiță desktop creată: $DESKTOP"

# 8. Testare rapidă
echo ""
echo "8. Testare Brave..."
echo "   Se pornește Brave în modul compatibilitate..."
sleep 1

$LAUNCHER "http://localhost:8765/.opencode/dashboard.html" &
BRAVE_PID=$!
sleep 3

if ps -p $BRAVE_PID > /dev/null 2>&1; then
    green "   ✅ Brave a pornit cu succes (PID: $BRAVE_PID)"
    
    # Verifică dacă fereastra există
    if command -v xwininfo &> /dev/null; then
        WINDOW=$(xwininfo -root -tree 2>/dev/null | grep -i "brave" | head -1)
        if [ -n "$WINDOW" ]; then
            green "   ✅ Fereastra grafică detectată"
        else
            yellow "   ⚠️  Brave rulează dar fereastra poate fi invizibilă în RDP"
        fi
    fi
else
    red "   ❌ Brave nu a putut porni"
    echo "   Încearcă manual: $LAUNCHER"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
green  " Reparație completă!"
echo ""
echo " Pentru a folosi Brave:"
echo "  1. Dă click pe iconița 'Brave (Fixed)' de pe desktop"
echo "  2. Sau rulează în terminal: brave-fixed [URL]"
echo ""
echo " Pentru CCDEV Dashboard:"
echo "  brave-fixed http://localhost:8765/.opencode/dashboard.html"
echo ""
echo " Dacă tot nu funcționează, încearcă:"
echo "  - Restart sistem"
echo "  - Update Brave: sudo apt update && sudo apt upgrade brave-browser"
echo "  - Verifică drivere GPU: lspci | grep VGA"
echo "═══════════════════════════════════════════════════════════════"
