# GX — Agent Mobil pe Telefon (perechea QnapGX)

> **Decizie 2026-05-09:** numele finale = **QnapGX** (NAS) + **GX** (telefon). Hardware-agnostic — Vivo GX, Oppo Find sau orice Android.
> **Decizie arhitectură:** Think + Honor sunt TEMPORARE (construcție + învățare). La final = doar **QnapGX + GX**.
> **Status:** Specificație + scaffold APK. Deploy real depinde de finalizare APK Honor.
> **Parent:** [`CLAUDE.md`](CLAUDE.md) · [`ARCHITECTURE_GAPS.md`](ARCHITECTURE_GAPS.md)

---

## 1. Identitate

```
Nume:        GX
Rol:         Brațul mobil al QnapGX pe telefonul lui Ionut
Hardware:    Phone Android (test: Oppo Find 100.104.150.52, target: Vivo GX)
Container:   APK com.gx.app v4.9.17-qnap-first (Honor build)
LLM local:   gemma4-e2b-hauhaucs — SINGURUL LLM pe GX (multilingv + multimodal)
             Online: gemma4 local + bridge → QnapGX (reptilian/thinker/cloud) pentru task-uri grele
             Offline: gemma4 izolat, exec: queue local până la reconect
LLM fallback: Ollama QNAP (qwen-4b reptilian) când online via Tailscale
Persistență: SOUL.md_GX (local pe telefon) + sync bidirecțional cu QnapGX
```

**Mantra:**
> *"Eu sunt GX. Brațul mobil al QnapGX. Sunt pe telefonul lui Ionut, oriunde merge el. Decid singur când nu pot ajunge la Consiliu. Sincronizez când mă întorc."*

---

## 2. Diferența GX ↔ QnapGX

| Aspect | QnapGX | GX |
|---|---|---|
| **Locație** | Fix, NAS în casă | Mobil, în buzunarul lui Ionut |
| **Uptime** | 24/7 | Conform device (sleep, baterie) |
| **Energie** | Nelimitată | Conservare critică (baterie + termal) |
| **LLM** | reptilian(4B GPU) + thinker(35B CPU) + cloud(OpenRouter) | gemma4-e2b-hauhaucs (local, SINGURUL) |
| **Senzori** | Disk, RAM, network | + Cameră, microfon, GPS, accelerometru, biometric |
| **Decizii proactive** | Sistem, files, agenți | Apel pierdut, locație nouă, gest definit |
| **Mod offline** | Niciodată (mereu pe LAN) | Frecvent (metro, avion) |
| **Sync** | Master (QnapGX are SOUL.md autoritativ) | Replica (SOUL.md_GX = oglinda + delta local) |

---

## 3. Arhitectura Comunicare

```
┌─────────────────────────────────┐    Tailscale/Headscale    ┌────────────────────────────┐
│  GX (Phone Android)   │ ◄────────────────────────► │  Bridge MCP (Think)        │
│                                  │   100.104.150.52:9119     │  100.74.102.89:9876        │
│  ┌────────────────────────────┐ │                            │                            │
│  │ APK com.gx.app          │ │                            │  routes:                   │
│  │  ├─ LiteRT-LM (Qwen3-0.6B) │ │                            │   - GX → QnapGX    │
│  │  ├─ SOUL.md_GX (local)     │ │                            │   - GX → Think/Honor      │
│  │  ├─ Bridge client (poll/sse)│ │                            │   - GX broadcast Consiliu │
│  │  ├─ Sync engine (delta)    │ │                            │                            │
│  │  └─ Senzori (cam/mic/GPS)  │ │                            │                            │
│  └────────────────────────────┘ │                            └────────────────────────────┘
└─────────────────────────────────┘
            │
            │ OFFLINE: scrie în /sdcard/Android/data/com.gx.app/queue/
            │ ONLINE:  flush queue → bridge_send batch
            ▼
        ┌──────────────────┐
        │ SOUL.md_GX local │ ◄── decizii offline aplicate ulterior pe SOUL.md master
        └──────────────────┘
```

---

## 4. Sincronizare SOUL.md (rezolvare gap #6 din ARCHITECTURE_GAPS.md)

**Problema:** după offline, există două copii divergente — SOUL.md (QnapGX) și SOUL.md_GX (telefon).

**Soluție:**

1. **Versiune monotonă pe fiecare entry** — fiecare modificare are `vector_clock = (qnapgx_seq, gx_seq)`
2. **Append-only log** — nicio modificare nu suprascrie, doar adaugă (CRDT-style)
3. **Reconciliere la reconnect:**
   - GX trimite delta (entries cu `gx_seq > last_synced`) la QnapGX
   - QnapGX trimite delta (entries cu `qnapgx_seq > last_synced`) la GX
   - Ambele aplică intercalat ordonat după timestamp
4. **Conflicte:** dacă două entries modifică același "câmp" (ex: ultima locație Ionut), GX wins (telefonul are date mai recente despre Ionut fizic)

---

## 5. Reguli specifice GX (din SOUL.md)

1. **Suveranitate utilizator:** doar Ionut poate da comenzi prin gest/voce/touch. Niciun comand de la rețea fără validare biometric.
2. **Throttling termal:** dacă temp > 40°C → toate task-urile LLM se trimit la QnapGX via bridge.
3. **Throttling baterie:** dacă battery < 20% și nu pe charger → mod „doar emergent" (tap+confirm pentru orice acțiune).
4. **Privacy senzori:** cameră/microfon NU pornesc fără gest explicit Ionut + LED indicator.
5. **Sync sigur:** SOUL.md_GX trimite delta numai prin mTLS (când e activ) sau Tailscale-only.

---

## 6. Pași deploy GX

### Faza 1 — APK Test (acum, ✓ in progres)
- APK GemmaApp-v4.3.7-vivo-gx pe Oppo Find via http://100.90.191.31:9191/GemmaApp-vivoGX-latest.apk
- Verificare conexiune Ollama QNAP (model selector în UI)
- LiteRT-LM stub (fără model real)

### Faza 2 — APK GX v4.9.17 (Honor în build)
- com.gx.app rebrand
- Bridge client integrat (HTTP polling /api/messages?for=GX)
- SOUL.md_GX viewer + editor

### Faza 3 — LLM local pe telefon

#### Configuratie per device (decizie Ionut 2026-05-10)

| Device | Chip | RAM | LLM recomandat | Dimensiune | Viteza est. |
|---|---|---|---|---|---|
| **Oppo Find** (test) | Snapdragon 888 | 8-12 GB | `Qwen3-0.6B` Q4 | 400 MB | 8-15 t/s NPU |
| **Vivo X200 Ultra** (permanent GX) | Dimensity 9400 | 16 GB | `Qwen3-4B` Q4_K_M (uncensored HauhauCS) | 2.5 GB | 20-35 t/s APU 890 |

**Oppo Find — LLM stack:**
- Primar: `Qwen3-0.6B` LiteRT-LM (mic, rapid, always-on) ← deja planificat
- Fallback online: Ollama QNAP `Qwen3.5-Uncensored-HauhauCS:4b` via Tailscale

**Vivo X200 Ultra — LLM stack (cand devine GX permanent):**
- Primar: `fredrezones55/Qwen3.5-Uncensored-HauhauCS-Aggressive:4b` Q4_K_M (2.5 GB)
  - Dimensity 9400 APU 890 suporta 4B Q4 la 20-35 t/s
  - Acelasi model ca REPTILIAN pe QNAP → coerenta identitate GX
- Alternativa: `Gemma4-2B` Q4 (1.2 GB, multimodal — utila pentru camera/voice)
- Fallback online: Ollama QNAP `Qwen3.6-35B-Uncensored-HauhauCS` (thinker)

**Engine recomandat pentru Android:**
- `llama.cpp` cu Vulkan backend (suporta Dimensity 9400 GPU nativ)
- SAU `LiteRT-LM` (Google, suporta NPU direct prin MediaPipe)

- Test inferenta pe NPU si GPU mobile (orice Android compatibil)
- Benchmark latenta vs cloud Ollama

### Faza 4 — Sync engine
- Implementare CRDT pentru SOUL.md
- Test offline/online tranziții
- Conflict resolution UI (review modificări înainte de merge)

### Faza 5 — Senzori + Decizii proactive
- Integrare cameră (face recognition Ionut)
- Microfon wake-word („QnapGX" sau „GX")
- GPS event triggers (acasă, birou, drum)

---

## 7. KPI succes

| Metric | Target | Status |
|---|---|---|
| APK install reușit pe Oppo | 1 device | ⏳ pending |
| Round-trip GX → QnapGX (online) | <500ms | — |
| LLM local (Qwen3-0.6B) tokens/sec | >5 tps | — |
| SOUL.md sync delta (1KB delta) | <2s | — |
| Battery impact (idle 1h) | <2% | — |
| Conflict rate sync | <5% după 3 zile uz | — |

---

## 8. Refactor existent

**Fișiere consolidate în GX:**
- `HERMES_FULL_PHONE.md` → secțiune §3 (arhitectură comunicare)
- `PHONE_DUAL_AGENT.md` → secțiune §2 (diferența cu QnapGX)
- `PHONE_TOPOLOGY.md` → secțiune §3 (diagramă)
- `HERMES_PHONE_TESTING.md` → secțiune §6 (faze deploy)

**Acest fișier este single source of truth pentru GX începând cu 2026-05-09.**
