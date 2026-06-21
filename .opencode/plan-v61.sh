#!/bin/bash
# plan-v61.sh - Plan v6.1 SLIM runner pentru OpenCode
# Usage: /home/think/CCDEW/.opencode/plan-v61.sh [cmd]

PLAN_DIR="/home/think/CCDEW"
EXECUTOR="$PLAN_DIR/.opencode/plan-executor.cjs"
DASHBOARD_PORT=8765

case "$1" in
  status)
    echo "📊 Status Plan v6.1 SLIM"
    echo "========================="
    echo ""
    node "$EXECUTOR" status
    ;;
  init)
    echo "🚀 Inițializare Faza 0"
    echo "====================="
    node "$EXECUTOR" init
    ;;
  phase1)
    echo "🔧 Faza 1: Fundație Solidă"
    echo "=========================="
    node "$EXECUTOR" phase1
    ;;
  phase2)
    echo "🧠 Faza 2: Memorie + Learning"
    echo "============================="
    node "$EXECUTOR" phase2
    ;;
  phase3)
    echo "🔗 Faza 3: Orchestration"
    echo "========================"
    node "$EXECUTOR" phase3
    ;;
  dashboard)
    echo "🌐 Deschid Dashboard..."
    brave-browser --app=http://localhost:$DASHBOARD_PORT --new-window --user-data-dir=/home/think/.config/open-cload-app 2>/dev/null &
    ;;
  monitor)
    echo "📊 Monitorizare Dashboard"
    echo "========================"
    echo "Dashboard: http://localhost:$DASHBOARD_PORT"
    echo "Logs: /tmp/open-cload-app.log"
    echo ""
    tail -f /tmp/open-cload-app.log 2>/dev/null | head -30 || tail -30 /tmp/open-cload-app.log
    ;;
  *)
    echo "Plan v6.1 SLIM Commands"
    echo "======================"
    echo ""
    echo "  plan-v61.sh status    - Status curent"
    echo "  plan-v61.sh init      - Faza 0 (baseline)"
    echo "  plan-v61.sh phase1   - Faza 1 (fundație)"
    echo "  plan-v61.sh phase2   - Faza 2 (memorie)"
    echo "  plan-v61.sh phase3   - Faza 3 (orchestration)"
    echo "  plan-v61.sh dashboard - Deschide dashboard"
    echo "  plan-v61.sh monitor  - Monitorizează server"
    ;;
esac