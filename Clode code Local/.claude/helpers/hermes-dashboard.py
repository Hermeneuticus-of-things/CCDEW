#!/usr/bin/env python3
"""
Hermes Dashboard v2 — Email Intelligence Viewer
Vizualizare web a analizei emailurilor de către Hermes.
"""
import http.server
import socketserver
import json
import os
from urllib.parse import urlparse, parse_qs

PORT = 8767
MEMORY = os.path.expanduser("~/CCDEW/_MEMORY")
STATE = os.path.expanduser("~/.local/state")

HTML = '''<!DOCTYPE html>
<html lang="ro">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Hermes Email Intelligence Dashboard</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', system-ui, sans-serif; background: #0f172a; color: #e2e8f0; line-height: 1.6; }
  .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
  header { text-align: center; padding: 30px 0; border-bottom: 2px solid #3b82f6; margin-bottom: 30px; }
  header h1 { font-size: 2.5rem; background: linear-gradient(90deg, #3b82f6, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
  header p { color: #94a3b8; margin-top: 10px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }
  .card { background: #1e293b; border-radius: 12px; padding: 20px; border: 1px solid #334155; transition: transform 0.2s; }
  .card:hover { transform: translateY(-2px); border-color: #3b82f6; }
  .card h3 { font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em; color: #94a3b8; margin-bottom: 10px; }
  .card .value { font-size: 2.5rem; font-weight: 700; }
  .urgent { color: #ef4444; }
  .safe { color: #22c55e; }
  .warn { color: #f59e0b; }
  .info { color: #3b82f6; }
  .category-bar { display: flex; align-items: center; margin: 8px 0; }
  .category-bar .label { width: 100px; font-size: 0.875rem; }
  .category-bar .bar { flex: 1; height: 24px; background: #334155; border-radius: 12px; overflow: hidden; }
  .category-bar .fill { height: 100%; border-radius: 12px; transition: width 0.5s ease; }
  .category-bar .count { width: 60px; text-align: right; font-size: 0.875rem; }
  .alert-list { max-height: 400px; overflow-y: auto; }
  .alert-item { background: #1e293b; border-left: 4px solid; padding: 12px; margin-bottom: 8px; border-radius: 0 8px 8px 0; }
  .alert-item.URGENT { border-color: #ef4444; }
  .alert-item.RISK { border-color: #f59e0b; }
  .alert-item .subject { font-weight: 600; margin-bottom: 4px; }
  .alert-item .meta { font-size: 0.75rem; color: #94a3b8; }
  .action-btn { display: inline-block; padding: 4px 12px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; margin-top: 6px; }
  .ACT_NOW { background: #ef444420; color: #ef4444; }
  .REVIEW { background: #f59e0b20; color: #f59e0b; }
  .SCHEDULE { background: #3b82f620; color: #3b82f6; }
  table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
  th { text-align: left; padding: 12px; background: #1e293b; color: #94a3b8; font-weight: 600; position: sticky; top: 0; }
  td { padding: 10px 12px; border-bottom: 1px solid #334155; }
  tr:hover td { background: #1e293b; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 0.75rem; font-weight: 600; }
  .badge-urgent { background: #ef444420; color: #ef4444; }
  .badge-vehicul { background: #f9731620; color: #f97316; }
  .badge-legal { background: #a855f720; color: #a855f7; }
  .badge-financial { background: #22c55e20; color: #22c55e; }
  .badge-safe { background: #22c55e20; color: #22c55e; }
  .badge-medium { background: #f59e0b20; color: #f59e0b; }
  .badge-high { background: #ef444420; color: #ef4444; }
  .timestamp { position: fixed; bottom: 20px; right: 20px; background: #1e293b; padding: 10px 20px; border-radius: 8px; font-size: 0.875rem; color: #94a3b8; }
</style>
</head>
<body>
  <div class="container">
    <header>
      <h1>🧠 HERMES Email Intelligence</h1>
      <p>Autonomous Analysis Dashboard • Agent Zero Style</p>
    </header>

    <div class="grid">
      <div class="card">
        <h3>Total Emails Analyzed</h3>
        <div class="value info">{{total}}</div>
      </div>
      <div class="card">
        <h3>Urgent Actions Required</h3>
        <div class="value urgent">{{urgent}}</div>
      </div>
      <div class="card">
        <h3>High Risk / Spam</h3>
        <div class="value warn">{{high_risk}}</div>
      </div>
      <div class="card">
        <h3>Accounts Monitored</h3>
        <div class="value safe">{{accounts}}</div>
      </div>
    </div>

    <div class="grid">
      <div class="card" style="grid-column: span 2;">
        <h3>📊 Category Distribution</h3>
        <div id="categories">{{categories}}</div>
      </div>
      <div class="card">
        <h3>⚠️ Priority Alerts (Top 10)</h3>
        <div class="alert-list">{{alerts}}</div>
      </div>
    </div>

    <div class="card">
      <h3>📧 Recent Emails Requiring Action</h3>
      <div style="overflow-x: auto;">
        <table>
          <thead>
            <tr>
              <th>Account</th>
              <th>Subject</th>
              <th>Category</th>
              <th>Risk</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {{email_rows}}
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <div class="timestamp">Last updated: {{timestamp}}</div>
</body>
</html>
'''

def load_data():
    """Load latest analysis state."""
    state_file = os.path.join(STATE, "hermes-email-analysis.json")
    if os.path.exists(state_file):
        with open(state_file) as f:
            return json.load(f)
    return {}

def build_dashboard():
    """Build HTML dashboard with live data."""
    data = load_data()
    
    total = data.get('total_analyzed', 0)
    accounts = len(data.get('accounts', []))
    
    # Count urgent/high risk from semantic
    semantic_dir = os.path.join(MEMORY, "semantic")
    urgent = 0
    high_risk = 0
    categories = Counter()
    alert_items = []
    email_rows = []
    
    if os.path.exists(semantic_dir):
        files = sorted(os.listdir(semantic_dir), reverse=True)[:200]
        for fname in files:
            if not fname.endswith('.json'):
                continue
            try:
                with open(os.path.join(semantic_dir, fname)) as f:
                    e = json.load(f)
                
                cat = e.get('category', 'other')
                categories[cat] += 1
                
                if e.get('priority', 0) >= 8:
                    urgent += 1
                if e.get('risk') == 'HIGH':
                    high_risk += 1
                
                # Alert items
                if e.get('priority', 0) >= 8 or e.get('risk') == 'HIGH':
                    alert_items.append(e)
                
                # Table rows (top actions)
                if e.get('action', {}).get('type') in ['ACT_NOW', 'PAY', 'REVIEW', 'CONSULT']:
                    email_rows.append(e)
            except:
                continue
    
    # Build category bars
    max_cat = max(categories.values()) if categories else 1
    cat_html = ""
    cat_colors = {
        'urgent': '#ef4444', 'vehicul': '#f97316', 'legal': '#a855f7',
        'financial': '#22c55e', 'business': '#3b82f6', 'commercial': '#94a3b8',
        'medical': '#f472b6', 'travel': '#06b6d4', 'administratif': '#c084fc',
        'other': '#64748b'
    }
    for cat, count in categories.most_common(10):
        pct = (count / max_cat) * 100
        color = cat_colors.get(cat, '#64748b')
        cat_html += f'<div class="category-bar"><div class="label">{cat}</div><div class="bar"><div class="fill" style="width:{pct}%;background:{color}"></div></div><div class="count">{count}</div></div>'
    
    # Build alerts
    alert_html = ""
    for e in sorted(alert_items, key=lambda x: x.get('priority', 0), reverse=True)[:10]:
        level = 'URGENT' if e.get('priority', 0) >= 8 else 'RISK'
        action = e.get('action', {})
        alert_html += f'<div class="alert-item {level}"><div class="subject">{html.escape(e.get("subject", "")[:60])}</div><div class="meta">{e.get("account", "")} • {e.get("category", "")}</div><span class="action-btn {action.get("type", "")}">{action.get("text", "")}</span></div>'
    
    # Build table rows
    rows_html = ""
    for e in email_rows[:20]:
        risk = e.get('risk', 'SAFE')
        risk_class = f'badge-{risk.lower()}'
        cat = e.get('category', 'other')
        cat_class = f'badge-{cat}'
        action = e.get('action', {})
        rows_html += f'<tr><td>{html.escape(e.get("account", "")[:30])}</td><td>{html.escape(e.get("subject", "")[:50])}</td><td><span class="badge {cat_class}">{cat}</span></td><td><span class="badge {risk_class}">{risk}</span></td><td><span class="action-btn {action.get("type", "")}">{action.get("text", "")[:25]}</span></td></tr>'
    
    return HTML.replace('{{total}}', str(total)) \
               .replace('{{urgent}}', str(urgent)) \
               .replace('{{high_risk}}', str(high_risk)) \
               .replace('{{accounts}}', str(accounts)) \
               .replace('{{categories}}', cat_html) \
               .replace('{{alerts}}', alert_html) \
               .replace('{{email_rows}}', rows_html) \
               .replace('{{timestamp}}', data.get('last_run', 'N/A'))

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            html = build_dashboard()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        elif self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(load_data()).encode())
        else:
            self.send_error(404)
    
    def log_message(self, format, *args):
        pass  # Quiet

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=PORT)
    args = parser.parse_args()
    
    with socketserver.TCPServer(("", args.port), Handler) as httpd:
        print(f"🌐 Hermes Dashboard running at http://localhost:{args.port}")
        print("Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n✅ Dashboard stopped")

if __name__ == '__main__':
    main()
