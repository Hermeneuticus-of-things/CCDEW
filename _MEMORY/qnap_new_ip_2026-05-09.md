---
tags: [qnap, network, tailscale, ip-change]
date: 2026-05-09
---

# QNAP IP nou pe Tailscale (post tailscaled restart)

**Vechi:** 100.90.191.31 (nasruse)
**NOU:** **100.97.220.9** (qnap)

## Stare network actuală
- Hostname Tailscale: `qnap` (era `nasruse`)
- LAN IP: 192.168.123.25 (neschimbat)
- Direct connection visible în tailnet
- Connectivity Think → QNAP: încă timeout (Tailscale peer list propagation pending)

## Cauza
2026-05-09 13:23 — Think a încercat fix Tailscale Funnel pentru Plex. A omorât tailscaled (PID 12375) și restart cu socket custom. QNAP a re-auth în Tailscale ca peer nou cu hostname `qnap` și IP nou `100.97.220.9`.

## Update peste tot
- SSH config `~/.ssh/config` Host qnap-admin → IP nou
- SSHFS mount /home/think/qnap_claude → remap la IP nou
- Toate scripturile care folosesc 100.90.191.31:
  - bridge URL în `qnapgx_exec.py`
  - `gx_client_stub.py` BRIDGE
  - `coordinator.py` BRIDGE
  - `plex_skill.py`
  - `consiliu_daily_verify.sh`
  - `coordinator_report.sh`
  - `coordinator_pull_request.sh`
  - cron scripts
  - Caddy mTLS Caddyfile
  - Headscale config server_url
  - Plex `allowedNetworks` 100.0.0.0/8 deja prinde noul IP (CGNAT range)

## Recovery state când redevine accesibil
- Toți agenții pe QNAP rulează cu IP-ul vechi în config
- Trebuie batch update + restart toți (sau folosește hostname `qnap.consiliu` cu DNS)

## Lecție
NICIODATĂ nu kill tailscaled cu `--socket=` custom. Folosește `Tailscale.sh restart` (script oficial QPKG) care păstrează state + socket original.
