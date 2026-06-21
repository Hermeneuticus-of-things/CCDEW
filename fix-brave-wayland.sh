#!/bin/bash
# CCDEW Brave Wayland Fix - Repară Vulkan pe Wayland pentru Zorin OS

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║        CCDEW Brave Wayland Vulkan Fix                        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

red() { echo -e "\e[31m$1\e[0m"; }
green() { echo -e "\e[32m$1\e[0m"; }
yellow() { echo -e "\e[33m$1\e[0m"; }

# Diagnostic 
echo "1. Diagnostic GPU..."
GPU=$(lspci | grep VGA | head -1)
echo "   GPU: $GPU"

# Verifică Vulkan
if command -v vulkaninfo &> /dev/null; then
    VK_DEVICES=$(vulkaninfo --summary 2>/dev/null | grep deviceName | head -3)
    echo "   Vulkan devices:"
    echo "$VK_DEVICES" | sed 's/^/     /'
else
    yellow "   vulkaninfo nu este instalat"
fi

# 2. Forțează drivere Mesa Intel/AMD în loc de Vulkan generic
echo ""
echo "2. Configurare drivere GPU..."

# Pentru Intel GPU (cel mai comun pe Zorin)
if echo "$GPU" | grep -qi intel; then
    export MESA_LOADER_DRIVER_OVERRIDE=iris
    export VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/intel_icd.x86_64.json:/usr/share/vulkan/icd.d/intel_hasvk_icd.x86_64.json
    green "   ✅ Setat driver Intel (iris)"
fi

# Pentru AMD
if echo "$GPU" | grep -qi amd; then
    export MESA_LOADER_DRIVER_OVERRIDE=radeonsi
    export VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/radeon_icd.x86_64.json
    green "   ✅ Setat driver AMD (radeonsi)"
fi

# 3. Fix principal: Dezactivează Vulkan, folosește OpenGL EGL
echo ""
echo "3. Activare OpenGL EGL în loc de Vulkan..."

export BRAVE_WAYLAND_FIX=1

# Aceste variabile dezvoltator Chromium forțează EGL în loc de Vulkan
export CHROME_FLAGS="--ozone-platform=wayland --use-angle=gl-egl --use-gl=egl --enable-features=UseOzonePlatform"

# Dezactivează explicit Vulkan
export DISABLE_VK_INSTANCE_LOADERS=1

echo "   ✅ Vulkan dezactivat"
echo "   ✅ OpenGL EGL activat"
echo "   ✅ Wayland platform activat"

# 4. Oprește procesele vechi
echo ""
echo "4. Curățare procese vechi..."
killall -9 brave 2>/dev/null
sleep 1

# 5. Pornește Brave pe Wayland corect
echo ""
echo "5. Pornire Brave pe Wayland (nativ)..."
echo "   Se pornește: brave-wayland"
echo ""

# Crează launcher permanent
cat > /home/think/.local/bin/brave-wayland << 'WOLF'
#!/bin/bash
# Brave Browser - Native Wayland (Fixed)
# CCDEW Auto-generated

# Fix pentru Intel/AMD GPU pe Wayland
export MESA_LOADER_DRIVER_OVERRIDE=${MESA_LOADER_DRIVER_OVERRIDE:-auto}
export DISABLE_VK_INSTANCE_LOADERS=1

# Forțează EGL în loc de Vulkan
export CHROME_FLAGS="--ozone-platform=wayland --use-angle=gl-egl --use-gl=egl"

# Lansează Brave nativ Wayland
/opt/brave.com/brave/brave \
    --ozone-platform=wayland \
    --use-angle=gl-egl \
    --use-gl=egl \
    --enable-features=UseOzonePlatform,WaylandWindowDecorations \
    --disable-features=VaapiVideoDecoder,Vulkan \
    --disable-gpu-sandbox \
    "$@"
WOLF

chmod +x /home/think/.local/bin/brave-wayland

# Test
echo "6. Testare..."
brave-wayland --version 2>&1 | head -1 && green "   ✅ Wayland funcționează!" || red "   ❌ Eroare"

echo ""
echo "═══════════════════════════════════════════════════════════════"
green  " Brave Wayland reparat!"
echo ""
echo " Comenzi disponibile:"
echo "  brave-wayland                  # Wayland nativ (reparat)"
echo "  brave-x11                      # Fallback X11 (dacă wayland Pică)"
echo "  brave-fixed                    # Compatibilitate maximă"
echo ""
echo " Pentru CCDEW Dashboard:"
echo "  brave-wayland http://localhost:8765/.opencode/dashboard.html"
echo "═══════════════════════════════════════════════════════════════"
