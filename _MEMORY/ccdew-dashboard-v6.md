---
tags: [dashboard, ccdew, systemd, performance, architecture]
updated: 2026-06-05
version: v6
---

# CCDEW Dashboard v6 — Arhitectură

## URL
`http://localhost:8765/dashboard`

## Fișiere cheie
| Fișier | Rol |
|---|---|
| `Open-Cload/.opencode/dashboard-server.cjs` | Server Node.js principal |
| `Open-Cload/.opencode/dashboard.html` | UI HTML single-page |
| `~/.config/systemd/user/ccdew-dashboard.service` | Auto-start boot |
| `~/.local/bin/ccdew-dashboard` | Script lansare app-mode |
| `~/.local/share/applications/ccdew-dashboard.desktop` | Entry meniu Zorin |

## Tiered Cache
- `rt`  5s  — cost/SSA/SAFLA/session (file reads)
- `sys` 8s  — htop CPU/procese/temps (Python subprocess)
- `svc` 30s — proxy/servicii/disk (curl + net)
- `proj`90s — git/obsidian/changelog (git + fs)

## Comenzi
```bash
ccdew-dashboard                           # lansează fereastra
systemctl --user status ccdew-dashboard   # stare server
systemctl --user restart ccdew-dashboard  # restart
journalctl --user -u ccdew-dashboard -f   # log live
```

## Auto-restart
Server are file watcher la 2s pe `dashboard-server.cjs` și `dashboard.html`.
La modificare → `process.exit(0)` → systemd Restart=on-failure repornește automat.
