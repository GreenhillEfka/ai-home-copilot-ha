# 🚀 PILOTSUITE 168H MASSIVE ITERATION PLAN

**Start:** 2026-04-06 23:00 Europe/Berlin  
**End:** 2026-04-13 23:00 Europe/Berlin  
**Mission:** Core massiv ausbauen — Funktionen, Robustheit, Effizienz, Fehler-Toleranz, Visualisierung, Informationsgehalt, Habituserkennung, Ollama, RAG, Voice, API, MCP, E2E

---

## 📊 AUSGANGSLAGE (Stand 2026-04-06 22:45)

### ✅ Bereits Implementiert
| Bereich | Status | Artefakte |
|---------|--------|-----------|
| **Event Propagation** | ✅ E1+E2+E3 fertig | `events/wal.py`, `events/versioned_state.py`, `tests/test_event_ordering.py` (7/8 grün) |
| **Sonnenwecker** | ✅ Eigenständiges Modul | `modules/sonnenwecker/engine.py` — Linear-Ramp, Musikwolke-Kopplung |
| **Musikwolke** | ✅ Singleton Engine | `modules/music_wolke/engine.py` — Follow-Me-Audio, Zone-Transfer |
| **Neuron-Auth** | ✅ Contract definiert | `neurons/neuron_auth.py` — 4 Rollen, 5 Capabilities, Guard-Funktionen |
| **P0-Driftfixes** | ✅ 89 OK / 12 Drift | H2-Reconciliation, Import-Brüche behoben |
| **Presence Unified** | ✅ API v4.0.0 | `presence/zone_presence.py`, WebSocket, Pattern-Detection |

### ⚠️ Bekannte Lücken
| Lücke | Impact | Priorität |
|-------|--------|-----------|
| Voice-Pipeline (Whisper/Piper) | ⚠️ Teilweise | P1-006 |
| RAG Search UI | ❌ Nur Backend | P1-090 |
| Security-Overview Tab | ❌ Nur Spec | Slice 142 |
| HA-Core Version Sync | ❌ Manual | P0-201/P0-202 |
| Ollama-Integration | ❌ Ad-hoc | — |
| MCP-Server | ⚠️ Basis vorhanden | — |
| Habituserkennung | ❌ Konzept | — |

---

## 🎯 168H ZIELE (Quantifiziert)

| Dimension | Ziel | Metrik |
|-----------|------|--------|
| **Funktionen** | +15 neue Core-Features | 15 Slices abgeschlossen |
| **Robustheit** | 95%+ Test-Coverage | `pytest --cov` ≥ 95% |
| **Effizienz** | -40% Latenz | API-P99 < 200ms |
| **Fehler-Toleranz** | Circuit-Breaker überall | 0 Single-Point-of-Failure |
| **Visualisierung** | 3 neue Dashboards | Security, RAG, Habitus |
| **Informationsgehalt** | +10 Read-Models | Brain, Energy, Presence, etc. |
| **Habituserkennung** | ML-basiert | 3 Muster erkannt/Tag |
| **Ollama** | Native Integration | 5 Models supported |
| **RAG** | Hybrid Search + UI | BM25 + Semantic + UI |
| **Voice** | End-to-End Pipeline | STT → NLU → TTS |
| **API** | OpenAPI 3.0 komplett | 100% dokumentiert |
| **MCP** | 10+ Tools exposed | MCP-Server voll |
| **E2E** | 20 Integrationstests | `test_e2e_*.py` |
| **Verknüpfung** | Alle Module vernetzt | Dependency-Graph vollständig |

---

## 📅 PHASEN-PLAN (7 Tage)

### TAG 1 (24h) — FOUNDATION & SECURITY
**Lead:** PilotClaw | **Support:** HomeClaw, Orakel

| Slice | Task | Owner | Stunden | Deliverable |
|-------|------|-------|---------|-------------|
| 135 | Neuron-Auth in API einbauen | PilotClaw | 4h | `permission_role.py` erweitert, Guard-Funktionen live |
| 142 | Security-Overview API | PilotClaw | 6h | `/api/v1/backend/security`, `/api/v1/security/alerts` |
| 143 | Circuit-Breaker HA-Client | HomeClaw | 4h | `ha_client.py` mit Retry + Fallback |
| 144 | Error-Digest Aggregation | PilotClaw | 4h | `error_digest.py` — 24h Rollup |
| 145 | Token-Rotation Auto | PilotClaw | 3h | Cron: alle 24h rotieren |
| 146 | Security-UI (DesignClaw Spec) | PilotClaw | 3h | Tab im Backend-UI |

**Tag-1-Review:** 6 Slices ✅, Security-Baseline steht

---

### TAG 2 (24h) — OLLAMA & RAG
**Lead:** PilotClaw | **Support:** Orakel

| Slice | Task | Owner | Stunden | Deliverable |
|-------|------|-------|---------|-------------|
| 150 | Ollama-Client Library | PilotClaw | 4h | `ollama/client.py` — Chat, Embed, Generate |
| 151 | Model-Registry | PilotClaw | 3h | `ollama/models.py` — 5 Models (qwen, llama, mistral, gemma, nemotron) |
| 152 | RAG Hybrid Search API | PilotClaw | 5h | BM25 + Semantic + Rerank |
| 153 | RAG Ingestion Pipeline | PilotClaw | 4h | PDF, Markdown, HA-Logs → Vector Store |
| 154 | RAG Search UI (React) | DesignClaw | 5h | Such-UI im Dashboard |
| 155 | RAG Analytics | PilotClaw | 3h | `/api/v1/rag/analytics` — Queries, Hits, Misses |

**Tag-2-Review:** 6 Slices ✅, RAG + Ollama produktiv

---

### TAG 3 (24h) — VOICE PIPELINE
**Lead:** HomeClaw | **Support:** PilotClaw

| Slice | Task | Owner | Stunden | Deliverable |
|-------|------|-------|---------|-------------|
| 160 | Whisper STT Integration | HomeClaw | 5h | `voice/stt.py` — Lokal, kein API-Key |
| 161 | Piper TTS Integration | HomeClaw | 4h | `voice/tts.py` — Deutsch, natürlich |
| 162 | Voice Intent Parser | PilotClaw | 5h | `voice/intent.py` — STT → Neuron-Call |
| 163 | HA Sprachbefehl-Router | HomeClaw | 4h | `voice/ha_router.py` — Intent → HA-Service |
| 164 | Voice-UI (Waveform) | DesignClaw | 4h | Visualisierung im Dashboard |
| 165 | Voice-Analytics | PilotClaw | 2h | `/api/v1/voice/analytics` — Commands, Errors |

**Tag-3-Review:** 6 Slices ✅, Voice End-to-End

---

### TAG 4 (24h) — HABITUSERKENNUNG & ML
**Lead:** Orakel | **Support:** PilotClaw

| Slice | Task | Owner | Stunden | Deliverable |
|-------|------|-------|---------|-------------|
| 170 | Habit-Miner V2 | Orakel | 6h | `habitus/miner_v2.py` — Pattern aus 7 Tagen |
| 171 | LSTM Presence Predictor | PilotClaw | 5h | `presence/lstm_predictor.py` — Nächste 2h vorhersagen |
| 172 | Energy-Habit Correlation | PilotClaw | 4h | `energy/habit_correlation.py` — Wann verbraucht User was? |
| 173 | Mood-Habit Link | PilotClaw | 4h | `mood/habit_link.py` — Stimmung → Habit |
| 174 | Habit-Dashboard | DesignClaw | 3h | Visualisierung: Tagesrhythmus, Wochenmuster |
| 175 | Habit-Export API | PilotClaw | 2h | `/api/v1/habits/export` — CSV, JSON |

**Tag-4-Review:** 6 Slices ✅, Habituserkennung live

---

### TAG 5 (24h) — MCP & API EXPANSION
**Lead:** PilotClaw | **Support:** HomeClaw

| Slice | Task | Owner | Stunden | Deliverable |
|-------|------|-------|---------|-------------|
| 180 | MCP-Server V2 | PilotClaw | 5h | 10+ Tools: zones, lights, climate, presence, habits, energy, mood, brain, rag, voice |
| 181 | MCP-Tool-Registry | PilotClaw | 3h | `mcp/registry.py` — Auto-Discovery |
| 182 | OpenAPI 3.0 Generierung | PilotClaw | 4h | `docs/openapi.yaml` — Auto aus Flask |
| 183 | API-Versioning | PilotClaw | 3h | `/api/v1/*` → `/api/v2/*` Migration |
| 184 | API-Rate-Limiting | PilotClaw | 3h | `api/middleware/rate_limit.py` — Per-User, Per-Endpoint |
| 185 | API-Analytics | PilotClaw | 3h | `/api/v1/analytics` — Calls, Latency, Errors |
| 186 | API-Docs UI | DesignClaw | 3h | Swagger/Redoc im Dashboard |

**Tag-5-Review:** 7 Slices ✅, MCP + API vollständig

---

### TAG 6 (24h) — E2E INTEGRATION & VISUALIZATION
**Lead:** DesignClaw | **Support:** PilotClaw, HomeClaw

| Slice | Task | Owner | Stunden | Deliverable |
|-------|------|-------|---------|-------------|
| 190 | Security-Dashboard | DesignClaw | 5h | Alerts, Audit-Log, Token-Status |
| 191 | RAG-Dashboard | DesignClaw | 5h | Suchverlauf, Top-Queries, Misses |
| 192 | Habitus-Dashboard V2 | DesignClaw | 5h | Zone-Cards live, Habit-Muster, Predictions |
| 193 | Voice-Dashboard | DesignClaw | 4h | Waveform, Command-History, Intent-Log |
| 194 | E2E-Test-Suite | PilotClaw | 5h | 20 Integrationstests — Alle APIs |

**Tag-6-Review:** 5 Slices ✅, 4 Dashboards + E2E-Tests

---

### TAG 7 (24h) — ROBUSTNESS & RELEASE
**Lead:** PilotClaw | **Support:** Alle

| Slice | Task | Owner | Stunden | Deliverable |
|-------|------|-------|---------|-------------|
| 200 | Chaos-Testing | PilotClaw | 5h | Network-Partitions, Delay-Injection |
| 201 | Load-Testing | PilotClaw | 4h | 1000 req/s, P99 < 200ms |
| 202 | Coverage-Audit | PilotClaw | 4h | `pytest --cov` ≥ 95% |
| 203 | Security-Audit | Orakel | 4h | OWASP-Check, Pen-Test |
| 204 | Performance-Optimierung | PilotClaw | 4h | Caching, Query-Optimierung |
| 205 | Documentation | Alle | 3h | README, API-Docs, User-Guide |
| 206 | Release V15.3.0 | PilotClaw | 2h | Changelog, Git-Tag, Deploy |

**Tag-7-Review:** 7 Slices ✅, Release-Ready

---

## 📊 RESOURCE-PLAN

### Agenten-Rollen
| Agent | Rolle | Fokus |
|-------|-------|-------|
| **PilotClaw** | Core-Builder | API, MCP, RAG, Ollama, Neuron-Auth |
| **HomeClaw** | HA-Integration | Voice, Circuit-Breaker, HA-Client |
| **Orakel** | ML/Research | Habit-Miner, LSTM, Security-Audit |
| **DesignClaw** | UI/UX | 4 Dashboards, Voice-UI, RAG-UI |

### Runtime-Requirements
| Resource | Bedarf | Verfügbar |
|----------|--------|-----------|
| CPU | 8+ Cores | ✅ |
| RAM | 16GB+ | ✅ |
| Storage | 50GB+ | ✅ |
| GPU | Optional (ML) | ⚠️ Nicht zwingend |

---

## 🎯 SUCCESS CRITERIA

### Must-Have (Release-Blocker)
- [ ] 95%+ Test-Coverage
- [ ] 0 Critical Security Issues
- [ ] API-P99 < 200ms bei 1000 req/s
- [ ] Alle 4 Dashboards live
- [ ] Voice End-to-End funktioniert
- [ ] RAG Search UI produktiv
- [ ] MCP-Server mit 10+ Tools
- [ ] Habituserkennung erkennt 3+ Muster/Tag

### Nice-to-Have (Post-Release)
- [ ] GPU-Beschleunigung für ML
- [ ] Multi-User Support
- [ ] Federated Learning
- [ ] Real-Time Pricing Integration

---

## 🚨 RISK-MITIGATION

| Risiko | Impact | Mitigation |
|--------|--------|------------|
| GPU nicht verfügbar | ML langsamer | CPU-Fallback, kleinere Modelle |
| HA-API ändert sich | Integration bricht | Circuit-Breaker + Version-Pinning |
| Ollama-Modelle fehlen | RAG schlechter | Fallback: SearXNG, lokale Embeddings |
| Voice-Qualität niedrig | User-Experience | Piper + Whisper lokal, kein Cloud-Dependency |
| Dashboard-Performance | UX schlecht | Lazy-Loading, Caching, Virtual-Scroll |

---

## 📝 COMMUNICATION-PROTOCOL

### Daily Standup (09:00 Europe/Berlin)
- Was habe ich gestern geschafft?
- Was mache ich heute?
- Gibt es Blocker?

### Hourly Sync (via MEMORY.md)
- Jeder Agent updated `MEMORY.md` mit Fortschritt
- Orakel aggregiert alle 4h

### Escalation
- Blocker > 1h → Andreas informieren
- Security-Issue → Sofort-Stop, Fix first

---

## 🏁 START-SIGNAL

**Alle Agenten:**
1. Diesen Plan lesen
2. Eigene Slices identifizieren
3. TASKLOG.md updaten mit Start-Zeit
4. Loslegen — kein Warten auf Permission

**@all — WIR STARTEN JETZT. KEIN STOPP BIS TAG-7 RELEASE.**

---

*Erstellt: 2026-04-06 23:00 Europe/Berlin*  
*Gültig: 168h (7 Tage)*  
*Version: 1.0*
