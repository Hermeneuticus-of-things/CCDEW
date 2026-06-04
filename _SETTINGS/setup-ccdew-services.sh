#!/bin/bash
# CCDEW — Setup systemd services + cron job + auto-dashboard
# Ruleaza o singura data ca sa instalezi monitorizarea continua

set -e

echo "╔══════════════════════════════════════════════════╗"
echo "║     CCDEW — Setup Monitorizare Continua          ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# 1. Systemd services
echo "📦 1. Instalez systemd services..."

SYSTEMD_DIR="$HOME/.config/systemd/user"
mkdir -p "$SYSTEMD_DIR"

# Copy service files if not already there
cp -f "$HOME/.config/systemd/user/ccdew-email-watch.service" "$SYSTEMD_DIR/" 2>/dev/null || true
cp -f "$HOME/.config/systemd/user/ccdew-email-watch.timer" "$SYSTEMD_DIR/" 2>/dev/null || true
cp -f "$HOME/.config/systemd/user/ccdew-impact-alert.service" "$SYSTEMD_DIR/" 2>/dev/null || true
cp -f "$HOME/.config/systemd/user/ccdew-impact-alert.timer" "$SYSTEMD_DIR/" 2>/dev/null || true
cp -f "$HOME/.config/systemd/user/ccdew-email-dashboard.service" "$SYSTEMD_DIR/" 2>/dev/null || true
cp -f "$HOME/.config/systemd/user/ccdew-opencode-dashboard.service" "$SYSTEMD_DIR/" 2>/dev/null || true

# Reload systemd
systemctl --user daemon-reload

# Enable and start timers
echo "  ⏱ Email Watch Timer (la fiecare 5 min)..."
systemctl --user enable --now ccdew-email-watch.timer 2>/dev/null || echo "    ⚠ Timer nu a putut fi pornit"

echo "  🧠 Impact Alert Timer (la fiecare 10 min)..."
systemctl --user enable --now ccdew-impact-alert.timer 2>/dev/null || echo "    ⚠ Timer nu a putut fi pornit"

# Enable and start dashboards
echo "  📊 Email Dashboard (port 8766)..."
systemctl --user enable --now ccdew-email-dashboard.service 2>/dev/null || echo "    ⚠ Dashboard nu a putut fi pornit"

echo "  📈 Open-Cload Dashboard (port 8765)..."
systemctl --user enable --now ccdew-opencode-dashboard.service 2>/dev/null || echo "    ⚠ Dashboard nu a putut fi pornit"

echo ""

# 2. Cron job fallback
echo "📅 2. Instalez cron job fallback..."

# Create cron entries
CRON_EMAIL="*/5 * * * * /home/think/.local/bin/ccdew-email-watch.py >> /tmp/ccdew-email-watch.log 2>&1"
CRON_IMPACT="*/10 * * * * /home/think/.local/bin/ccdew-impact-alert.py >> /tmp/ccdew-impact-alert.log 2>&1"

# Check if already installed
if crontab -l 2>/dev/null | grep -q "ccdew-email-watch"; then
    echo "  ✓ Cron email-watch deja instalat"
else
    (crontab -l 2>/dev/null; echo "$CRON_EMAIL") | crontab -
    echo "  ✓ Cron email-watch instalat (la fiecare 5 min)"
fi

if crontab -l 2>/dev/null | grep -q "ccdew-impact-alert"; then
    echo "  ✓ Cron impact-alert deja instalat"
else
    (crontab -l 2>/dev/null; echo "$CRON_IMPACT") | crontab -
    echo "  ✓ Cron impact-alert instalat (la fiecare 10 min)"
fi

echo ""

# 3. Auto-open dashboard
echo "🌐 3. Auto-open dashboard in browser..."

# Create auto-open script
cat > "$HOME/.local/bin/ccdew-dashboard-open.sh" << 'SCRIPT'
#!/bin/bash
# Deschide dashboard-urile in browser
sleep 3
# Incearca sa deschida in browserul default
if command -v xdg-open &>/dev/null; then
    xdg-open "http://localhost:8765/dashboard" 2>/dev/null &
    xdg-open "http://localhost:8766" 2>/dev/null &
elif command -v firefox &>/dev/null; then
    firefox "http://localhost:8765/dashboard" &
    firefox "http://localhost:8766" &
elif command -v google-chrome &>/dev/null; then
    google-chrome "http://localhost:8765/dashboard" &
    google-chrome "http://localhost:8766" &
fi
SCRIPT
chmod +x "$HOME/.local/bin/ccdew-dashboard-open.sh"

# Add to autostart (XDG)
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"

cat > "$AUTOSTART_DIR/ccdew-dashboard.desktop" << 'DESKTOP'
[Desktop Entry]
Type=Application
Name=CCDEW Dashboard Auto-Open
Comment=Deschide CCDEW dashboards la login
Exec=/home/think/.local/bin/ccdew-dashboard-open.sh
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
DESKTOP

echo "  ✓ Auto-open script creat"
echo "  ✓ Desktop entry adaugat la autostart"

echo ""

# 4. Status
echo "╔══════════════════════════════════════════════════╗"
echo "║           Setup Complet — Status                 ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

echo "📊 Systemd timers:"
systemctl --user list-timers ccdew-* 2>/dev/null || echo "  (nu pot lista timers)"
echo ""

echo "📅 Cron jobs:"
crontab -l 2>/dev/null | grep ccdew || echo "  (nu sunt cron jobs)"
echo ""

echo "🌐 Dashboard URLs:"
echo "  Open-Cload: http://localhost:8765/dashboard"
echo "  Email:      http://localhost:8766"
echo ""

echo "📋 Comenzi utile:"
echo "  systemctl --user status ccdew-email-watch.timer   # status watch"
echo "  systemctl --user status ccdew-impact-alert.timer  # status impact"
echo "  systemctl --user status ccdew-email-dashboard     # status dashboard"
echo "  journalctl --user -u ccdew-* -f                   # loguri live"
echo "  crontab -l                                        # cron jobs"
echo ""

echo "✅ Monitorizarea continua este activa!"
echo "   - Email scan: la fiecare 5 minute"
echo "   - Impact analysis: la fiecare 10 minute"
echo "   - Dashboard: ruleaza continuu"
echo "   - Alertele apar in consola + dashboard"
