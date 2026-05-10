---
tags: [proiect, consiliu, qnapgx, gx, ai-distribuit]
created: 2026-05-10
---

# Proiect Consiliu — QnapGX + GX

## Locatie pe disc

```
/home/think/Downloads/Clode code Local/PROJECTS/Consiliu/
```

## Ce este

Sistem AI distribuit multi-agent. Duo permanent autonom:
- **QnapGX** (QNAP NAS, 24/7) — executa cod, matematica, memorie master
- **GX** (telefon Android, mobil) — vorbeste cu Ionut, voce, senzori

**Regula fundamentala:** GX vorbeste, QnapGX executa. Niciodata invers.

## Noduri

| Nod | IP Tailscale | LLM | Rol |
|---|---|---|---|
| QnapGX | 100.90.191.31 | qwen-4b GPU + qwen3:8b CPU | Gardian + executor 24/7 |
| GX | 100.104.150.52 (test Oppo) | Qwen3-0.6B LiteRT-LM | Brat mobil Ionut |
| Think | 100.74.102.89 | Claude Code | Constructie + tutor (temporar) |
| Honor | 100.92.121.22 | Claude Code | Build APK (temporar) |

## Bridge MCP

- Acum: `Think:9876` (temporar)
- La final: migrare pe QNAP port ~9877

## Naming

- Agentul QNAP = **QnapGX** (nu "Hermes" — doar path legacy)
- Script: `qnapgx_exec.py` | Boot: `[QnapGX-exec v6.1]`
- APK: `com.gx.app` v4.9.17-qnap-first

## Fisiere cheie proiect

- `CLAUDE.md` — reguli + viziune
- `GX_AGENT.md` — specificatie agent mobil
- `ARCHITECTURE_GAPS.md` — 33 gaps ramase
- `gx_client_stub.py` — stub Python GX
- `PROJECT_LOG.md` — jurnal complet

## Resursa externa

NotebookLM: https://notebooklm.google.com/notebook/67477efb-c2c1-4886-9c31-cbd82fd0b3cb
