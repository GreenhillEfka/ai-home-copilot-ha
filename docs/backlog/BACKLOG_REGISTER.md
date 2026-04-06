# BACKLOG_REGISTER.md — PilotSuite

**Created:** 2026-04-06 22:15 Europe/Berlin  
**Owner:** openclaw-main (Subagent: backlog-analysis)  
**Purpose:** Zentrale Registrierung aller offenen Aufgaben, Fragen und technischer Schulden  
**Update-Cycle:** Bei jeder Backlog-Analyse oder nach Abschluss größerer Slices

---

## 📊 BACKLOG-SUMMARY

| Kategorie | Offen | In Progress | Blockiert | Gesamt |
|-----------|-------|-------------|-----------|--------|
| **Architektur** | 4 | 0 | 1 | 5 |
| **Integration** | 8 | 2 | 0 | 10 |
| **Testing** | 3 | 0 | 0 | 3 |
| **Docs** | 5 | 0 | 0 | 5 |
| **Performance** | 2 | 1 | 0 | 3 |
| **API-Surface** | 12 | 0 | 0 | 12 |
| **GESAMT** | **34** | **3** | **1** | **38** |

---

## 🎯 PRIORISIERUNG (Impact/Effort Matrix)

### P0 — KRITISCH (High Impact, Low Effort)
*Sofort erledigen — Blockaden oder Stabilitätsrisiken*

| ID | Titel | Kategorie | Impact | Effort | Status | Owner |
|----|-------|-----------|--------|--------|--------|-------|
| **BL-001** | Backend UI Zone Module Alignment | Architektur | 🔴 Hoch | 🟢 Niedrig | ❌ Offen | pilotclaw |
| **BL-002** | RAG UI: Echte VectorStore-Anbindung | API-Surface | 🔴 Hoch | 🟢 Niedrig | ❌ Offen | pilotclaw |
| **BL-003** | Neurons UI: Echte State-Anbindung | API-Surface | 🔴 Hoch | 🟢 Niedrig | ❌ Offen | pilotclaw |
| **BL-004** | Media UI: Echte Sonos-Integration | API-Surface | 🔴 Hoch | 🟢 Mittel | ❌ Offen | pilotclaw |

### P1 — HOCH (High Impact, Medium Effort)
*Nächste Iteration — Kernfunktionalität*

| ID | Titel | Kategorie | Impact | Effort | Status | Owner |
|----|-------|-----------|--------|--------|--------|-------|
| **BL-010** | Conversation Agent: HA-Assist Integration | Integration | 🔴 Hoch | 🟡 Mittel | ❌ Offen | homeclaw |
| **BL-011** | RAG-Kontext: HA-States + Historie | Integration | 🔴 Hoch | 🟡 Mittel | ❌ Offen | pilotclaw |
| **BL-012** | LLM-Fallback: OpenAI → Ollama → Tiny | Architektur | 🔴 Hoch | 🟡 Mittel | ❌ Offen | pilotclaw |
| **BL-013** | Zero-Config: Auto-Discovery + HA Token | Integration | 🔴 Hoch | 🟡 Mittel | ❌ Offen | homeclaw |
| **BL-014** | Habitus Admin: Echte Sync-Logik | API-Surface | 🟡 Mittel | 🟢 Niedrig | ❌ Offen | pilotclaw |
| **BL-015** | Room Context: HA Scene Activation | API-Surface | 🟡 Mittel | 🟢 Niedrig | ❌ Offen | pilotclaw |

### P2 — MITTEL (Medium Impact, Variable Effort)
*Geplante Verbesserung — Tech Debt*

| ID | Titel | Kategorie | Impact | Effort | Status | Owner |
|----|-------|-----------|--------|--------|--------|-------|
| **BL-020** | Neuron Manager: Echte Evaluation | API-Surface | 🟡 Mittel | 🟡 Mittel | ❌ Offen | pilotclaw |
| **BL-021** | Mood History: Echte History-Anbindung | API-Surface | 🟡 Mittel | 🟢 Niedrig | ❌ Offen | pilotclaw |
| **BL-022** | Musikwolke: Echte Konfiguration | API-Surface | 🟡 Mittel | 🟢 Niedrig | ❌ Offen | pilotclaw |
| **BL-023** | Camera: Echte Snapshot-API | API-Surface | 🟡 Mittel | 🟡 Mittel | ❌ Offen | pilotclaw |
| **BL-024** | Notifications: Telegram/WhatsApp/FCM | Integration | 🟡 Mittel | 🟡 Mittel | ❌ Offen | pilotclaw |
| **BL-025** | Zone Module Assignment Klärung | Architektur | 🟡 Mittel | 🟢 Niedrig | ❓ Unklar | orakel |

### P3 — NIEDRIG (Low Impact, Low Effort)
*Polish — Wenn Kapazität vorhanden*

| ID | Titel | Kategorie | Impact | Effort | Status | Owner |
|----|-------|-----------|--------|--------|--------|-------|
| **BL-030** | Dashboard: SVG Graph Generierung | Performance | 🟢 Niedrig | 🟢 Niedrig | ❌ Offen | designclaw |
| **BL-031** | SearchXNG: Echte Status-Prüfung | Integration | 🟢 Niedrig | 🟢 Niedrig | ❌ Offen | pilotclaw |
| **BL-032** | Hybrid Search: Local + SearXNG | Integration | 🟢 Niedrig | 🟡 Mittel | ❌ Offen | pilotclaw |

### P4 — DOKUMENTATION (Low Impact, Low Effort)
*Dokumentationsschulden*

| ID | Titel | Kategorie | Impact | Effort | Status | Owner |
|----|-------|-----------|--------|--------|--------|-------|
| **BL-040** | Release Guidelines: TODO-Free Releases | Docs | 🟢 Niedrig | 🟢 Niedrig | ⚠️ Check | all |
| **BL-041** | API_REFERENCE.md: Legacy Update | Docs | 🟢 Niedrig | 🟢 Niedrig | ❌ Offen | orakel |
| **BL-042** | ZONE_DASHBOARD.md: Erweiterungen | Docs | 🟢 Niedrig | 🟢 Niedrig | ❌ Offen | designclaw |
| **BL-043** | UX Governance: Learning/Autonomy | Docs | 🟡 Mittel | 🟢 Niedrig | ❓ Unklar | designclaw |
| **BL-044** | Live System Checkplan: HA Auth | Docs | 🟢 Niedrig | 🟢 Niedrig | ❌ Offen | orakel |

---

## 📋 DETAILLIERTE BESCHREIBUNGEN

### Architektur (5 Items)

#### BL-001: Backend UI Zone Module Alignment
- **Quelle:** `team/worktrees/pilotsuite-styx-core-current/docs/analysis/PS_CORE_SLICE_124_*.md`
- **Problem:** `/api/v1/backend/zones/<zone_id>/modules` schreibt parallel auf `enabled_modules` + TODO-Semantik
- **Lösung:** Auf kanonische Zone-Override-Wahrheit (ModuleRegistry) umstellen
- **Impact:** Verhindert Inkonsistenzen zwischen Backend UI und Core-Surface
- **Effort:** 🟢 Niedrig (Refactoring bestehender Pfade)

#### BL-012: LLM-Fallback Kaskade
- **Quelle:** `docs/RELEASE_V12.2.0_PLAN.md`
- **Problem:** Keine Fallback-Strategie bei API-Ausfällen
- **Lösung:** OpenAI → Ollama → Ollama Tiny (immer online!)
- **Impact:** 🔴 Hoch (Systemverfügbarkeit)
- **Effort:** 🟡 Mittel (Routing-Logik + Health Checks)

#### BL-025: Zone Module Assignment Klärung
- **Quelle:** `team/worktrees/pilot-haclane/pilotsuite_ops/docs/E2E_VERIFY_PER_ZONE_MODULES.md`
- **Problem:** ❓ Nicht klar ob Modul-Zuweisung aus Core oder HA kommt
- **Lösung:** Architektur-Decision-Record + klare Schnittstelle
- **Impact:** 🟡 Mittel (Verhindert zukünftige Drift)
- **Effort:** 🟢 Niedrig (Dokumentation + Contract)

#### BL-043: UX Governance off/learning/autonomy
- **Quelle:** `team/worktrees/pilotsuite-styx-ha-recovery-v15.0.1/pilotsuite/V15_UX_GATE.md`
- **Problem:** ❓ Wo in HA sichtbar? Governance unklar
- **Lösung:** UX-Contract + Lovelace-Integration definieren
- **Impact:** 🟡 Mittel (User Experience)
- **Effort:** 🟢 Niedrig (Konzept + Implementation)

---

### Integration (10 Items)

#### BL-010: Conversation Agent — HA-Assist Integration
- **Quelle:** `docs/RELEASE_V12.2.0_PLAN.md`
- **Problem:** Sprachsteuerung nicht integriert
- **Lösung:** HA-Assist Pipeline anbinden
- **Impact:** 🔴 Hoch (Core Feature)
- **Effort:** 🟡 Mittel (API + Event-Wiring)

#### BL-011: RAG-Kontext — HA-States + Historie
- **Quelle:** `docs/RELEASE_V12.2.0_PLAN.md`
- **Problem:** RAG hat keinen Zugriff auf HA-Kontext
- **Lösung:** States + Historie + Dokumente im Prompt
- **Impact:** 🔴 Hoch (Kontextqualität)
- **Effort:** 🟡 Mittel (Data Pipeline)

#### BL-013: Zero-Config Auto-Discovery
- **Quelle:** `docs/RELEASE_V12.2.0_PLAN.md`
- **Problem:** Manuelle Konfiguration erforderlich
- **Lösung:** Auto-Discovery + Long-Life HA Token
- **Impact:** 🔴 Hoch (User Experience)
- **Effort:** 🟡 Mittel (Discovery-Protocol)

#### BL-024: Notifications Delivery
- **Quelle:** `copilot_core/notifications/delivery_engine.py`
- **Problem:** # TODO: Implement actual API calls (Telegram, WhatsApp, SMTP, FCM/APNs, HA notify)
- **Lösung:** Echte Delivery-Implementierung
- **Impact:** 🟡 Mittel (Benachrichtigungen)
- **Effort:** 🟡 Mittel (5 Delivery-Channels)

---

### API-Surface (12 Items)

#### BL-002: RAG UI — Echte VectorStore-Anbindung
- **Quelle:** `copilot_core/api/v1/rag_ui.py:74,98,121,149,170,191,234,264`
- **TODOs:**
  - Line 74: Echte Vectors aus VectorStore laden
  - Line 98: Echte Embeddings laden
  - Line 121: Echten Search-Log laden
  - Line 149: Echte RAG-Suche durchführen
  - Line 170: Echten SearXNG-Status prüfen
  - Line 191: Echte SearXNG-Suche durchführen
  - Line 234: Whisper STT + RAG-Suche
  - Line 264: Echte Hybrid-Suche (local + SearXNG)
- **Impact:** 🔴 Hoch (Kernfunktionalität)
- **Effort:** 🟢 Niedrig (Bestehende Stores anbinden)

#### BL-003: Neurons UI — Echte State-Anbindung
- **Quelle:** `copilot_core/api/v1/neurons_ui.py:78,113,126,139,156,175,193,218`
- **TODOs:**
  - Line 78: Echte States aus NeuronManager laden
  - Line 113-139: Echte States laden (4x)
  - Line 156: Echte Pipeline-Stats laden
  - Line 175: NeuronManager.evaluate() aufrufen
  - Line 193: Echte History aus MoodHistoryStore laden
  - Line 218: SVG-Graph generieren
- **Impact:** 🔴 Hoch (Dashboard-Funktionalität)
- **Effort:** 🟢 Niedrig (Manager-APIs nutzen)

#### BL-004: Media UI — Echte Sonos-Integration
- **Quelle:** `copilot_core/api/v1/media_ui.py:55,112,142,156,202,215,253`
- **TODOs:**
  - Line 55: Echte Sonos-Player aus SonosHTTPClient laden
  - Line 112: Echte Favorites aus Sonos laden
  - Line 142: SonosHTTPClient.play_favorite()
  - Line 156: Echte Musikwolke-Konfiguration laden
  - Line 202: In ZoneConfig speichern
  - Line 215: Echte Camera-Status laden
  - Line 253: Echten Snapshot von Camera laden
- **Impact:** 🔴 Hoch (User-Facing Feature)
- **Effort:** 🟡 Mittel (Sonos + Camera Integration)

#### BL-014: Habitus Admin Sync
- **Quelle:** `copilot_core/api/v1/habitus_admin.py:117`
- **TODO:** Call actual sync logic from symbiosis layer
- **Impact:** 🟡 Mittel (Symbiosis-Integration)
- **Effort:** 🟢 Niedrig (Symbiosis-Layer aufrufen)

#### BL-015: Room Context Scene Activation
- **Quelle:** `copilot_core/api/v1/room_context_admin.py:70`
- **TODO:** Call HA API to activate scene
- **Impact:** 🟡 Mittel (Room Automation)
- **Effort:** 🟢 Niedrig (HA API Call)

---

### Testing (3 Items)

#### BL-050: Integration Test Gaps
- **Quelle:** `copilot_core/rootfs/usr/src/app/tests/integration/`
- **TODOs:**
  - `test_event_processing_integration.py:6`: Implement /api/events/* endpoints
  - `test_dashboard_api_integration.py:6`: Implement /api/dashboard/* endpoints
  - `test_zone_management_integration.py:6`: Implement /api/zones/* endpoints
- **Impact:** 🟡 Mittel (Test-Coverage)
- **Effort:** 🟡 Mittel (API-Endpoints + Tests)

#### BL-051: Test Activation
- **Quelle:** `team/worktrees/pilotsuite-styx-ha-release-prep-v14.7.3/docs/TASKLISTE.md:T-042`
- **Task:** Übersprungene Tests aktivieren (HA: 41, Core: 112)
- **Impact:** 🟢 Niedrig (Test-Coverage)
- **Effort:** 🟡 Mittel (153 Tests)

#### BL-052: Test Coverage Increase
- **Quelle:** `team/worktrees/pilotsuite-styx-ha-release-prep-v14.7.3/docs/TASKLISTE.md:T-043`
- **Task:** Test-Coverage erhöhen (Ziel: HA 500+, Core 1800+)
- **Impact:** 🟡 Mittel (Quality Gate)
- **Effort:** 🟡 Mittel (Laufende Aufgabe)

---

### Docs (5 Items)

#### BL-040: Release Guidelines — TODO-Free Releases
- **Quelle:** `docs/GITHUB_RELEASE_GUIDELINES.md:211`
- **Check:** Keine TODOs/FIXMEs im Release-Code
- **Impact:** 🟢 Niedrig (Release-Quality)
- **Effort:** 🟢 Niedrig (Pre-Release Check)

#### BL-041: API_REFERENCE.md Legacy Update
- **Quelle:** MEMORY.md (H1 Truth Map Findings)
- **Problem:** `docs/API_REFERENCE.md` und `docs/API_COMPLETE.md` sind Legacy-Referenz
- **Lösung:** Als deprecated markieren oder auf Worktree-Truth verweisen
- **Impact:** 🟢 Niedrig (Dokumentationshygiene)
- **Effort:** 🟢 Niedrig (Markierung + Verweise)

#### BL-042: ZONE_DASHBOARD.md Erweiterungen
- **Quelle:** `copilot_core/rootfs/usr/src/app/docs/ZONE_DASHBOARD.md:251`
- **Section:** ## Erweiterungen (TODO)
- **Impact:** 🟢 Niedrig (Dokumentation)
- **Effort:** 🟢 Niedrig (Dokumentation vervollständigen)

#### BL-044: Live System Checkplan HA Auth
- **Quelle:** `pilotsuite_ops/docs/LIVE_SYSTEM_CHECKPLAN_v15.md:16`
- **Problem:** Cannot read without HA token
- **Lösung:** HA Token im Checkplan hinterlegen oder Auth-Flow dokumentieren
- **Impact:** 🟢 Niedrig (Operational Readiness)
- **Effort:** 🟢 Niedrig (Dokumentation)

---

### Performance (3 Items)

#### BL-060: Dashboard SVG Graph Generierung
- **Quelle:** `copilot_core/api/v1/neurons_ui.py:218`
- **TODO:** SVG-Graph generieren basierend auf Neuron-Aktivität
- **Impact:** 🟢 Niedrig (Visualisierung)
- **Effort:** 🟢 Niedrig (SVG-Generierung)

#### BL-061: RAG Search Performance
- **Quelle:** `copilot_core/api/v1/rag_ui.py`
- **TODO:** Echte Hybrid-Suche (local + SearXNG)
- **Impact:** 🟢 Niedrig (Search Performance)
- **Effort:** 🟡 Mittel (Search-Optimization)

#### BL-062: Backend UI Performance-Baseline
- **Quelle:** PILOTSUITE_PROGRESS_LEDGER.md (Slice 134 done)
- **Status:** ✅ Done — Alle 10 Tabs <50ms, RAG <200ms
- **Impact:** 🔴 Hoch (bereits erledigt)
- **Effort:** — (abgeschlossen)

---

## 🔍 HERKUNFTSANALYSE

### Fundorte nach Häufigkeit

| Ort | TODOs | FIXMEs | ❓ | Gesamt |
|-----|-------|--------|----|--------|
| `copilot_core/api/v1/rag_ui.py` | 8 | 0 | 0 | 8 |
| `copilot_core/api/v1/neurons_ui.py` | 8 | 0 | 0 | 8 |
| `copilot_core/api/v1/media_ui.py` | 7 | 0 | 0 | 7 |
| `copilot_core/api/v1/backend_ui.py` | 3 | 0 | 0 | 3 |
| `docs/RELEASE_V12.2.0_PLAN.md` | 4 | 0 | 0 | 4 |
| `copilot_core/notifications/delivery_engine.py` | 5 | 0 | 0 | 5 |
| `team/worktrees/.../TASKLISTE.md` | 0 | 0 | 15 | 15 |
| **Andere** | 10 | 0 | 3 | 13 |
| **GESAMT** | **45** | **0** | **18** | **63** |

### Duplikate in Worktrees
Viele TODOs erscheinen mehrfach in verschiedenen Worktree-Varianten:
- `pilotsuite-styx-core-current` (aktuell)
- `pilotsuite-styx-core-v15.2.0` (Release)
- `pilotsuite-styx-ha-release-prep-v14.7.3` (HA Release)
- `pilotsuite-styx-ha-recovery-v15.0.1` (HA Recovery)
- `pilotsuite-styx-core-release-prep-v14.7.3` (Core Release)

**Empfehlung:** Nur `pilotsuite-styx-core-current` als kanonische Quelle betrachten, andere als Snapshots.

---

## 📈 EMPFOHLENE REIHENFOLGE

### Nächste 3 Tasks (P0)
1. **BL-001** — Backend UI Zone Module Alignment (Architektur-Konsistenz)
2. **BL-002** — RAG UI VectorStore-Anbindung (Kernfunktionalität)
3. **BL-003** — Neurons UI State-Anbindung (Dashboard-Funktionalität)

### Nächste Iteration (P1)
4. **BL-010** — Conversation Agent HA-Assist
5. **BL-011** — RAG-Kontext HA-States
6. **BL-012** — LLM-Fallback Kaskade

### Tech Debt Sprint (P2)
7. **BL-020** — Neuron Manager Evaluation
8. **BL-024** — Notifications Delivery
9. **BL-050** — Integration Test Gaps

---

## 🔄 UPDATE-HISTORIE

| Datum | Owner | Änderung |
|-------|-------|----------|
| 2026-04-06 22:15 | openclaw-main (subagent) | Ersterstellung — Komplette Backlog-Analyse |

---

## 📎 ANHANG: GEFUNDENE MARKIERUNGEN

### TODO (45 Vorkommen)
```
# Top-Files mit TODOs:
copilot_core/api/v1/rag_ui.py:8
copilot_core/api/v1/neurons_ui.py:8
copilot_core/api/v1/media_ui.py:7
copilot_core/api/v1/backend_ui.py:3
copilot_core/notifications/delivery_engine.py:5
docs/RELEASE_V12.2.0_PLAN.md:4
```

### ❓ (18 Vorkommen)
```
# Offene Fragen:
team/worktrees/pilot-haclane/pilotsuite_ops/docs/E2E_VERIFY_PER_ZONE_MODULES.md:98
team/worktrees/pilotsuite-styx-ha-recovery-v15.0.1/pilotsuite/V15_UX_GATE.md:19
team/worktrees/pilotsuite-styx-ha-recovery-v15.0.1/pilotsuite_ops/docs/LIVE_SYSTEM_CHECKPLAN_v15.md:16,56
```

### FIXME (0 Vorkommen)
Keine FIXME-Markierungen gefunden.

---

*Letztes Update: 2026-04-06 22:15 Europe/Berlin*
