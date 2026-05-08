# _SETTINGS/RULES/INDEX.md — Master Index Reguli

> **Scop:** Tabel-router "cand se citeste ce regula". Aplicabil **cross-project**.
> Reguli specifice proiectului stau in `PROJECTS/<Nume>/doc/` (nu aici).

## Cand citesc ce

| Trigger | Fisier | Cand exact |
|---|---|---|
| **Session start** | `session_start.md` | La prima interactiune in fiecare sesiune noua (3 reguli critice) |
| **Cerinta noua user** | `changelog.md` | INAINTE de prima linie cod — scriu cerinta in `PROJECTS/<Nume>/CHANGELOG.md` |
| **Cerinta nou mid-task** | `cerinta_noua.md` | User trimite cerinta in timp ce lucrez la alt task — salvare imediata in TODO.md |
| **Gasit bug** | `bug_log.md` | Bug descoperit (raportat de user sau identificat in testare) — intrare in BUG_LOG.md INAINTE de fix |
| **Bump versiune** | `versioning.md` | Orice modificare care necesita versionare noua (schema V [stadiu] Major.Minor.Build) |
| **Ruflo tools** | `ruflo_integration.md` | Evaluez daca task-ul beneficiaza de swarm/memory_search/hooks (on-demand, nu la task simplu) |
| **Swarm preset (holografic-mesh)** | `swarm_preset.md` | User cere "swarm", "mesh", "pine N agenti", "paraleli", "holografic", "ce am omis?", gap-audit, refactor >=5 fisiere. **Default: 1000 symbolic, hierarchical-mesh, specialized.** |
| **Routing agent (enneagram)** | `enneagram_topology.md` | Nu știu ce agent tip să aleg sau în ce ordine să dispatch; task multi-agent cu tranziții între specialiști. **CLI:** `python .claude/helpers/enneagram_router.py route <task_type>` |
| **Unde lucrez fizic** | `scope_routing.md` | Aleg proiectul sau radacina dupa scopul cererii; scriu memoria fizica in `.md` la nivelul potrivit |
| **Context lookup (memory/reguli)** | `obsidian_context_protocol.md` | Caut context semantic cu `obsidian_global_search` INAINTE de `Read` direct. Vault = `<WORKSPACE_DIR>` + `_MEMORY/` junction. |
| **NLM/RAG queries lente sau mass workload** | `nlm_async_multi_channel_protocol.md` | Orice queries către NotebookLM sau RAG cu latență variabilă. 10 nivele de soluții (async, timeout, grouped, multi-notebook batch, conversation reuse, CDP backup, throttle, tier limits). Anti-dezlogare obligatoriu. |
| **Rescriere narativă (carte/articol/doc) cu RAG-grounding** | `narrative_rewrite_protocol.md` | Orice rescriere conținut narativ care necesită fidelitate doctrinară/factuală + profunzime. Protocol 5 pași: scop → enneagrama selecție → consult RAG → craft → aplicare. Anti-pattern obligatoriu (em-dash, drift, LLM-signature). Distincție Exemplu/Ilustrație. |
| **Selecție dimensiuni dialog interior pentru scriere narativă** | `psycho_dimensions_repertoire.md` | Repertoriu universal ~75 dimensiuni psiho organizate în 14 grupe (A-N): cognitive/afective/agenție/temporale/relaționale/etice/imaginale/energetice/calitative + neurofenomenologie/psihanaliza/fenomenologie/contemplative/corp-exterior. Selecție per scop, NU mecanic. |
| **Multi-agent (4+ paraleli) — anti-omogenizare** | `multi_agent_divergent_convergent.md` | OBLIGATORIU la spawn 4+ agenți pe același task. Faza 1 DIVERGENT: fiecare agent primește ARIPĂ ENNEAGRAMATICĂ distinctă (Zoom/Lentilă/Perspectivă/Modalitate). Faza 2 CONVERGENT: 1 agent Reformer sintetizează. Praguri 2-3/4-6/7-10/>10. Aplicabilitate per domain (editorial/code review/architecture/bug/content/research). |

## Reguli care nu stau aici (referinte)

| Tip regula | Locatie |
|---|---|
| Reguli Android (build, stress test, UI patterns) | `PROJECTS/MyAndroidApp/doc/BUILD_TEST.md` + `HOME_SCREENS.md` |
| Reguli MyBook (protocoale editoriale) | `PROJECTS/MyBook/doc/BOOK_STRUCTURE.md` |
| Reguli MyResearch (format termen/entries) | `PROJECTS/MyResearch/doc/FORMAT.md` |
| Cerinte tehnice standard (per tip proiect) | `_SETTINGS/CERINTE_TEHNICE_STANDARD.md` |
| Conventii naming, plasare fisiere, workflow, prompts | `_SETTINGS/QUICK-START-CONFIG.md` |
| Cum creez proiect nou | `_SETTINGS/HOW-TO-CREATE-A-NEW-PROJECT.md` |

## Principiu holografic

Fiecare fisier de regula e **mic si focusat pe un singur moment operational**. Nu citesc `changelog.md` cand debugez un bug — citesc `bug_log.md`. Nu reincarc tot contextul.

Root `CLAUDE.md` contine doar pointer-ul la acest INDEX si 3 reguli critice inline. Restul e on-demand.
