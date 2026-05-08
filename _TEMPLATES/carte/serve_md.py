"""
Preview LIVE Server — randeaza fisiere .md ca HTML cu auto-refresh.

UTILIZARE:
  1. Copiaza acest fisier in folderul cu .md-uri
  2. Modifica BASE sa pointeze la folderul dorit
  3. Porneste: python serve_md.py
  4. Sau din Claude Code: preview_start("nume-din-launch-json")

LAUNCH.JSON (pune in .claude/launch.json al proiectului):
{
  "version": "0.0.1",
  "configurations": [
    {
      "name": "md-viewer",
      "runtimeExecutable": "python",
      "runtimeArgs": ["cale/catre/serve_md.py"],
      "port": 8766
    }
  ]
}

FUNCTIONALITATI:
  - Browsing: navigare pe foldere si fisiere .md
  - Renderizare: Markdown → HTML cu font Georgia, stil carte
  - Auto-refresh: pagina se reincarca singura la 2s daca fisierul s-a schimbat
  - Navigare: prev/next intre fisiere, breadcrumb catre radacina
  - LIVE indicator: badge verde in coltul dreapta-sus
  - Threaded: nu se blocheaza la conexiuni multiple
  - Exclude: .bak, CLAUDE.md, foldere ascunse
"""

import http.server, os, urllib.parse, sys, json, socketserver

PORT = 8766
BASE = os.path.dirname(os.path.abspath(__file__))  # folderul curent

try:
    import markdown
    HAS_MD = True
except:
    HAS_MD = False
    print("ATENTIE: pip install markdown — fara el, fisierele se afiseaza ca text brut")

STYLE = """<style>
body{max-width:780px;margin:40px auto;padding:0 20px;font-family:Georgia,serif;font-size:17px;line-height:1.7;color:#1a1a1a;background:#fafaf8}
h1{font-size:1.5em;border-bottom:1px solid #ccc;padding-bottom:8px}
h2{font-size:1.2em;margin-top:2em}
em{color:#555}hr{border:none;border-top:1px solid #ddd;margin:2em 0}
a{color:#2a5db0;text-decoration:none}a:hover{text-decoration:underline}
.nav{background:#f0f0ee;padding:10px 14px;border-radius:6px;margin-bottom:20px;font-size:14px}
.nav a{margin-right:10px}
.live{position:fixed;top:8px;right:12px;background:#2a2;color:#fff;padding:3px 8px;border-radius:4px;font-size:11px;font-family:sans-serif}
</style>"""

REFRESH_SCRIPT = """<script>
(function(){
  var path = location.pathname;
  var lastMtime = 0;
  setInterval(function(){
    fetch('/mtime?f=' + encodeURIComponent(path))
      .then(function(r){return r.json()})
      .then(function(d){
        if(lastMtime && d.mtime > lastMtime) location.reload();
        lastMtime = d.mtime;
      }).catch(function(){});
  }, 2000);
})();
</script>
<div class="live">LIVE</div>"""

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            if self.path.startswith('/mtime'):
                self.send_mtime()
            else:
                path = urllib.parse.unquote(self.path.lstrip('/'))
                full = os.path.join(BASE, path) if path else BASE
                if os.path.isdir(full):
                    self.send_dir(full, path)
                elif full.endswith('.md') and os.path.isfile(full):
                    self.send_md(full, path)
                else:
                    self.send_error(404)
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type','text/html;charset=utf-8')
            self.end_headers()
            self.wfile.write(f"<pre>Error: {e}</pre>".encode('utf-8'))

    def send_mtime(self):
        qs = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(qs)
        f = params.get('f', [''])[0].lstrip('/')
        full = os.path.join(BASE, f)
        mt = os.path.getmtime(full) if os.path.isfile(full) else 0
        self.send_response(200)
        self.send_header('Content-Type','application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"mtime": mt}).encode())

    def send_dir(self, full, rel):
        dirs = sorted([d for d in os.listdir(full) if os.path.isdir(os.path.join(full,d)) and not d.startswith('.')])
        files = sorted([f for f in os.listdir(full) if f.endswith('.md') and not f.endswith('.bak') and f!='CLAUDE.md'])
        items = []
        if rel:
            parent = '/'.join(rel.strip('/').split('/')[:-1])
            items.append(f'<a href="/{parent}">&#8592; Inapoi</a><br><br>')
        for d in dirs:
            items.append(f'<a href="/{rel}/{d}" style="font-weight:bold">&#128193; {d}/</a><br>')
        for f in files:
            items.append(f'<a href="/{rel}/{f}">&#128196; {f}</a><br>')
        title = os.path.basename(full) or "Fisiere"
        html = f"<!DOCTYPE html><html><head><meta charset=utf-8><title>{title}</title>{STYLE}</head><body><div class=nav><a href='/'>Radacina</a></div><h1>{title}</h1>{''.join(items)}</body></html>"
        self.out(html)

    def send_md(self, full, rel):
        text = open(full, encoding='utf-8').read()
        if HAS_MD:
            body = markdown.markdown(text, extensions=['extra'])
        else:
            body = '<pre>' + text.replace('<','&lt;') + '</pre>'
        dirpath = os.path.dirname(full)
        files = sorted([f for f in os.listdir(dirpath) if f.endswith('.md') and not f.endswith('.bak') and f!='CLAUDE.md'])
        fname = os.path.basename(full)
        idx = files.index(fname) if fname in files else -1
        dir_rel = '/'.join(rel.strip('/').split('/')[:-1])
        nav = f"<a href='/'>Radacina</a> / <a href='/{dir_rel}'>{dir_rel}</a> / {fname}<br>"
        if idx > 0:
            nav += f"<a href='/{dir_rel}/{files[idx-1]}'>&#8592; {files[idx-1]}</a> "
        if idx < len(files)-1:
            nav += f"<a href='/{dir_rel}/{files[idx+1]}'>{files[idx+1]} &#8594;</a>"
        html = f"<!DOCTYPE html><html><head><meta charset=utf-8><title>{fname}</title>{STYLE}</head><body><div class=nav>{nav}</div>{body}{REFRESH_SCRIPT}</body></html>"
        self.out(html)

    def out(self, html):
        self.send_response(200)
        self.send_header('Content-Type','text/html;charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def log_message(self, *a):
        pass

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

if __name__ == '__main__':
    print(f"Preview LIVE: http://localhost:{PORT}", flush=True)
    ThreadedHTTPServer(('0.0.0.0', PORT), H).serve_forever()
