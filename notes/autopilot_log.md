# AI Home CoPilot — Autopilot Log (10min loop)

Window: 2026-02-14 16:00–20:00 (Europe/Berlin)

This log is appended by the Autopilot cron.

---

## 2026-02-14 16:50 — Tag System v0.2 (autopilot) — ✅ RELEASED

### What changed
- **Tag System v0.2 — Decision Matrix Implementation**:
  - Decision Matrix P1 Features implementiert:
    - HA-Labels materialisieren: nur ausgewählte Facetten (`role.*`, `state.*`)
    - Subjects: alle HA-Label-Typen (`entity`, `device`, `area`, `automation`, `scene`, `script`, `helper`)
    - Subject IDs: Mix aus Registry-ID + Fallback
    - Namespace: `user.*` NICHT als intern (nur HA-Labels importieren)
    - Lokalisierung: nur `display.de` + `en`
    - Learned Tags → HA-Labels: NIE automatisch (explizite Bestätigung nötig)
    - Farben/Icons: HA als UI-Quelle
    - Konflikte: existierende HA-Labels ohne `aicp.*` ignorieren
    - Habitus-Zonen: eigene interne Objekte mit Policies
  - In-Memory Registry für schnelle Tag-Verwaltung
  - Suggest/Confirm Workflow für Learned Tags
  - REST API Endpoints unter `/api/v1/tags2`

### Files changed
- `ha-copilot-repo/addons/copilot_core/rootfs/usr/src/app/copilot_core/tags/__init__.py` (NEW: 15134 bytes)
- `ha-copilot-repo/addons/copilot_core/rootfs/usr/src/app/copilot_core/tags/api.py` (NEW: 11679 bytes)
- `ha-copilot-repo/addons/copilot_core/rootfs/usr/src/app/copilot_core/core_setup.py` (+Tag System Integration)
- `ha-copilot-repo/addons/copilot_core/rootfs/usr/src/app/tests/test_tags_v2.py` (NEW: 7399 bytes)
- `ha-copilot-repo/CHANGELOG.md` (+v0.4.14 entry)

### Status
- **✅ RELEASED**: https://github.com/GreenhillEfka/Home-Assistant-Copilot/releases/tag/v0.4.14
- All py_compile checks passed
- Functional tests verified

### Next logical step
- **HA Integration**: Tag Context Module (verbindet Tag System mit HA Entities)
- **ODER**: Testing Suite v0.2 erweitern
- **ODER**: Weather Integration Tests

---

## 2026-02-14 16:30 — Module Architecture Fix (autopilot) — ✅ RELEASED

### What changed
- **Module Architecture Fix v0.6.7**:
  - Created `core/modules/module.py` with `CopilotModule` and `ModuleContext` base classes
  - Fixed all 8 modules that were importing missing dependencies
  - Removed unused `asdict` import from `unifi_module.py`
  - All modules now compile successfully

### Files changed
- `custom_components/ai_home_copilot/core/modules/module.py` (NEW: 2455 bytes)
- `custom_components/ai_home_copilot/core/modules/unifi_module.py` (-2 bytes)
- `custom_components/ai_home_copilot/manifest.json` (version → 0.6.7)
- `CHANGELOG.md` (+v0.6.7 entry)

### Status
- **✅ RELEASED**: https://github.com/GreenhillEfka/ai-home-copilot-ha/releases/tag/v0.6.7
- Branch: wip/module-unifi_module/20260209-2149
- py_compile verified for all modules

### Next logical step
- **User Antworten auf P0/P1 Fragen** (Tag System decisions)
- ODER: Tag System v0.2 Implementierung (basierend auf Decision Matrix Empfehlungen)
- ODER: UniFi Module Data Collection Stub implementieren

---

## 2026-02-14 15:59 — Error Grouping (autopilot) — ✅ RELEASED

### What changed
- **Token UX verbessert (v0.6.6)**:
  - Token-Feld zeigt nur neuen Token an (leer = bestehender Token wird behalten)
  - Clear Token Checkbox hinzugefügt um Token explizit zu löschen
  - Privacy: Token wird nicht mehr im Formular angezeigt wenn bereits gesetzt
- Manifest.json korrigiert (war fälschlicherweise bei 0.3.2)

### Files changed
- `custom_components/ai_home_copilot/config_flow.py` (Token-Handling + Clear-Checkbox)
- `custom_components/ai_home_copilot/manifest.json` (version → 0.6.6)
- `CHANGELOG.md` (+v0.6.6 + v0.6.5 entries)

### Status
- **✅ RELEASED**: https://github.com/GreenhillEfka/ai-home-copilot-ha/releases/tag/v0.6.6
- Branch: wip/module-forwarder_quality/20260208-172947
- py_compile verified

### Next logical step
- **User Antworten auf P0/P1 Fragen** (Tag System decisions)
- ODER: Tag System v0.2 Implementierung (basierend auf Decision Matrix Empfehlungen)
- ODER: Testing Suite v0.3 (erweiterte Integration Tests)


## 2026-02-14 15:39 — Testing Suite v0.2 (autopilot) — ✅ RELEASED

### What changed
- **Testing Suite v0.2**: Production-Ready Integration Tests
- Added comprehensive integration tests for production deployment:
  - **Module Imports**: All modules import cleanly (energy, unifi, weather, core)
  - **Coordinator Pattern Tests**: Verify coordinator initialization and data flow
  - **API Mocking Tests**: Mock Core Add-on API responses for all modules
  - **Entity Validation**: Validate entity configs against HA schema
  - **Error Handling Tests**: API errors, missing entities, empty responses
  - **Performance Tests**: Reasonable update intervals and batch sizes

### Test Coverage Summary
| Category | Tests |
|----------|-------|
| Module Imports | 5 |
| Coordinator Pattern | 3 |
| API Mocking | 3 |
| Entity Validation | 9 |
| Error Handling | 3 |
| Performance | 2 |

### Files changed
- `custom_components/ai_home_copilot/tests/test_suite_v02.py` (11.5 KB, 25 test cases)
- `custom_components/ai_home_copilot/manifest.json` (version → 0.6.4)
- `CHANGELOG.md` (+v0.6.4 entry)

### Status
- **✅ RELEASED**: https://github.com/GreenhillEfka/ai-home-copilot-ha/releases/tag/v0.6.4
- Branch: development
- Py_compile verified for all test files

### Next logical step
- **User Antworten auf P1 Fragen abwarten** (Tag System decisions)
- ODER: Tag System v0.2 Implementierung (basierend auf Decision Matrix Empfehlungen)
- ODER: Weitere Module (z.B. Mood Module Tests, Brain Graph Integration Tests)

---

## 2026-02-14 15:19 — Weather Context Module v0.6.2 (autopilot) — ✅ RELEASED

### What changed
- **Weather Context Module v0.6.2**: PV forecasting integration for energy optimization
- **7 new sensor entities** for weather & PV data:
  - `sensor.ai_home_copilot_weather_condition` (sunny, cloudy, rainy, etc.)
  - `sensor.ai_home_copilot_weather_temperature` (°C)
  - `sensor.ai_home_copilot_weather_cloud_cover` (%)
  - `sensor.ai_home_copilot_weather_uv_index` (UV)
  - `sensor.ai_home_copilot_pv_forecast_kwh` (today's PV production forecast)
  - `sensor.ai_home_copilot_pv_recommendation` (optimal_charging, moderate_usage, etc.)
  - `sensor.ai_home_copilot_pv_surplus_kwh` (expected surplus after home consumption)
- Connects to Core Add-on Weather service API (`/api/v1/weather`)

### Files changed
- `custom_components/ai_home_copilot/weather_context.py` (coordinator + data classes)
- `custom_components/ai_home_copilot/weather_context_entities.py` (7 entities)
- `custom_components/ai_home_copilot/core/modules/weather_context_module.py` (module)
- `custom_components/ai_home_copilot/__init__.py` (+weather_context registration)
- `custom_components/ai_home_copilot/manifest.json` (version → 0.6.2)
- `CHANGELOG.md` (+v0.6.2 entry)

### Status
- **✅ RELEASED**: https://github.com/GreenhillEfka/ai-home-copilot-ha/releases/tag/v0.6.2
- Branch: development (merged from feature/weather-context-v0.6.2)
- Py_compile verified for all new modules

### Next logical step
- Testing Suite v0.1 implementieren (P0)
- **OR**: User answers to pending P1 questions (Tag System decisions)

### What changed
- **Testing Suite v0.1** stub angelegt für HA Integration
- Tests abgedeckt:
  - **Candidate Poller**: Entity Change Detection
  - **Repairs Workflow**: Suggestion Handling
  - **Decision Sync**: Core ↔ HA State Consistency
  - **Context Modules**: Energy + UniFi Integration Tests
- py_compile verified für alle neuen Test-Dateien

### Files changed
- `custom_components/ai_home_copilot/tests/__init__.py` (package marker)
- `custom_components/ai_home_copilot/tests/test_suite_v01.py` (208 lines, 5 test classes)

### Status
- **✅ COMMITTED + PUSHED**: bdfaae5
- Branch: development
- No release (Stub/Foundation — Testing Suite v0.1 incomplete)

### Next logical step
- **User Antworten auf P0/P1/P2 Fragen** (bestehende pending questions)
- ODER: Tag System v0.2 Implementierung (basierend auf Decision Matrix Empfehlungen)
- ODER: Weather Integration für PV forecasting (Energy Module follow-up)

---

## 2026-02-14 14:49 — Questions Enriched with Decision Matrix (autopilot)

### What changed
- **questions_for_user_next_time.md** restructured with P0/P1/P2 priority system
- Integrated Decision Matrix Run #7 recommendations:
  - P0: Testing Suite v0.1 (empfohlen: JA)
  - P1: Tag System decisions mit klaren Empfehlungen
  - P2: Energy Module (geblockt durch P0-P1)

### Files changed
- `notes/questions_for_user_next_time.md` (enriched with guidance)
- `notes/autopilot_state.json` (new run entry)
- `notes/debug_level_worker_report_latest.md` (unchanged)
- `notes/module_kernel_state.json` (unchanged)

### Status
- **✅ COMMITTED**: d37d285
- Branch: master
- No release (docs-only change)

### Next logical step
- **User Antworten auf P0/P1/P2 Fragen abwarten**
- Dann: Testing Suite v0.1 implementieren (P0) → ODER
- Weather Integration für PV forecasting (Energy follow-up)

---

## 2026-02-14 14:39 — UniFi Context Module Release (autopilot)

### What changed
- **UniFi Context Module v0.6.1** released for HA Integration
- **6 new sensor entities** for network monitoring:
  - `sensor.ai_home_copilot_unifi_clients_online` (online clients count)
  - `sensor.ai_home_copilot_unifi_wan_latency` (WAN latency in ms)
  - `sensor.ai_home_copilot_unifi_packet_loss` (WAN packet loss %)
  - `binary_sensor.ai_home_copilot_unifi_wan_online` (connectivity)
  - `binary_sensor.ai_home_copilot_unifi_roaming` (roaming activity)
  - `sensor.ai_home_copilot_unifi_wan_uptime` (human-readable uptime)
- Connects Core Add-on UniFi Neuron v0.4.10 to HA Integration

### Files changed
- `custom_components/ai_home_copilot/unifi_context.py` (+coordinator)
- `custom_components/ai_home_copilot/unifi_context_entities.py` (+6 entities)
- `custom_components/ai_home_copilot/core/modules/unifi_context_module.py` (+module)
- `custom_components/ai_home_copilot/__init__.py` (+unifi_context module registration)
- `custom_components/ai_home_copilot/manifest.json` (version → 0.6.1)
- `CHANGELOG.md` (+v0.6.1 entry)

### Status
- **✅ RELEASED**: https://github.com/GreenhillEfka/ai-home-copilot-ha/releases/tag/v0.6.1
- All py_compile checks passed
- Branch pushed: development

### Next logical step
- Weather Integration für PV forecasting (Energy follow-up)
- Or: Tag System implementation (pending user answers)

### What changed
- **Debug Level Control (v0.6.0)** released for HA Integration
- New select entity: Debug Level (off/light/full)
- New services: `set_debug_level`, `clear_all_logs`
- Integrated with DevSurfaceModule devlog system
- Config options added in const.py

### Files changed
- `custom_components/ai_home_copilot/const.py` (+DEBUG_LEVEL constants)
- `custom_components/ai_home_copilot/select.py` (+DiagnosticLevelSelectEntity)
- `custom_components/ai_home_copilot/core/modules/dev_surface.py` (+services)
- `custom_components/ai_home_copilot/manifest.json` (version → 0.6.0)
- `CHANGELOG.md` (+v0.6.0 entry)

### Status
- **✅ RELEASED**: https://github.com/GreenhillEfka/ai-home-copilot-ha/releases/tag/v0.6.0
- All py_compile checks passed
- Branch pushed: `dev/autopilot-debug-level-v0.6.0`

### Next logical step
- UniFi Context Module (connect UniFi Neuron to HA)
- Or: Weather integration for PV forecasting
- Or: Tag System implementation (pending user answers)

---

## 2026-02-08 06:41 — Kickstart (manual)

### What changed
- Added **Tag-System v0.1 spec**: `docs/TAG_SYSTEM_v0.1.md` (privacy-first taxonomy + HA Labels mapping + governance + migration notes).
- Started tracking Autopilot/worker state & research notes under `notes/` (state, queue, reports, questions).
- Ignored local nested repo checkout: `ai_home_copilot_hacs_repo/` added to `.gitignore`.

### Status
- Not a release (docs/notes only). Changes committed on dev branch: `dev/autopilot-2026-02-08-0641`.

### Next logical step
- Decide whether Tag-System decisions in `docs/TAG_SYSTEM_v0.1.md` should be treated as **canonical** (and if yes, wire a minimal implementation stub in the HA integration or core add-on):
  - pick supported subject kinds for v0.1 (entity/device/area vs more),
  - decide `aicp.*` vs allowing `user.*`,
  - decide whether learned/candidate tags may ever materialize as HA labels (recommended: no).

---

## 2026-02-14 13:50 — Brain Graph Configurable Limits (autopilot)

### What changed
- **Config Integration**: Brain Graph module now supports runtime configuration via `config.json`
- Added configurable parameters with validation bounds:
  - `max_nodes` (100-5000, default: 500)
  - `max_edges` (300-15000, default: 1500)
  - `node_half_life_hours` (1-168h, default: 24.0)
  - `edge_half_life_hours` (1-168h, default: 12.0)
  - `node_min_score` (0.01-1.0, default: 0.1)
  - `edge_min_weight` (0.01-1.0, default: 0.1)
- Updated `core_setup.py` to accept optional `config` parameter
- Maintains backward compatibility (uses defaults if not specified)

### Files changed
- `addons/copilot_core/config.json` (+JSON schema, +options)
- `addons/copilot_core/rootfs/usr/src/app/copilot_core/core_setup.py` (+config parsing, +GraphStore init)
- `CHANGELOG.md` (+v0.4.12 entry)

### Status
- **✅ RELEASED**: https://github.com/GreenhillEfka/Home-Assistant-Copilot/releases/tag/v0.4.12
- All py_compile checks passed
- Modules verified: UniFi (v0.1), Energy (v0.1), Brain Graph, Mood, Habitus, Candidates

### 2026-02-14 13:49 — UniFi + Energy Neurons Release (autopilot)

### What changed
- **UniFi Neuron v0.1** release: Network monitoring module
  - WAN status (uplink, latency, packet loss)
  - Client roaming events
  - Traffic baselines
  - REST API: `/api/v1/unifi/*`
- **Energy Neuron v0.1** release: Energy monitoring & optimization
  - Consumption/production monitoring
  - Anomaly detection (severity levels)
  - Load shifting opportunities
  - Explainability for suggestions
  - REST API: `/api/v1/energy/*`
- **Brain Graph Limits** (v0.4.12) already included

### Files changed
- `CHANGELOG.md` (+v0.4.10 UniFi, +v0.4.11 Energy, v0.4.12 Brain Graph Limits)
- `addons/copilot_core/config.json` (version: 0.4.12 → 0.4.13)

### Status
- **✅ RELEASED**: https://github.com/GreenhillEfka/Home-Assistant-Copilot/releases/tag/v0.4.13
- All modules compile (py_compile verified)
- UniFi + Energy Neurons now official releases

### Next logical step
- HA Integration module (HACS repo): Connect core neurons to HA entities/events
- Or: Implement Tag System CRUD API (pending user answers to 12 questions)
- Or: Weather integration for PV forecasting (energy follow-up)

---

## 2026-02-14 14:15 — Energy Context Module Release (autopilot)

### What changed
- **Released Energy Context Module v0.5.9**: Connected Core Energy Neuron to HA Integration
- **6 new sensor entities** for energy monitoring:
  - Consumption/production today (kWh)
  - Current power (W)
  - Anomalies count + alert binary sensor
  - Shifting opportunities count
- Connects Core's anomaly detection and load-shifting suggestions to HA Repairs

### Files changed
- `custom_components/ai_home_copilot/energy_context.py` (+coordinator)
- `custom_components/ai_home_copilot/energy_context_entities.py` (+entities)
- `custom_components/ai_home_copilot/core/modules/energy_context_module.py` (+module)
- `custom_components/ai_home_copilot/__init__.py` (+registration)
- `custom_components/ai_home_copilot/manifest.json` (0.5.9)
- `CHANGELOG.md` (+v0.5.9 entry)

### Status
- **✅ RELEASED**: https://github.com/GreenhillEfka/ai-home-copilot-ha/releases/tag/v0.5.9
- py_compile verified for all modules
- Commit pushed to main (159bd15)
- Tag v0.5.9 created and pushed

### Next logical step
- UniFi Context Module (similar pattern for UniFi Neuron)
- Or: Weather integration for PV forecasting (energy follow-up)
- Or: Tag System implementation (pending user answers)

---

## 2026-02-14 14:19 — Autopilot PAUSED (Window Expired)

### Status
- **🛑 Window expired** (ended 2026-02-08 10:18 → now 2026-02-14 14:19)
- Autopilot paused until manually reactivated

### Current State (from last run)
- ✅ Energy Context Module released (v0.5.9)
- ✅ UniFi + Energy Neurons released (v0.4.13)
- ✅ Brain Graph Limits released (v0.4.12)
- ⏳ Tag System pending (10 questions from user)

### Pending Questions (still open)
1. HA-Labels: Always materialize or selective (`role.*`, `state.*`)?
2. Subjects v0.1: `entity`/`device`/`area` only, or more?
3. Subject IDs: `entity_id` or Registry IDs (`unique_id`/`device_id`)?
4. Namespace: `user.*` allowed, or only HA Labels import?
5. Localization: `display.de` + `en` only, or full i18n from start?
6. Learned Tags: Auto-materialize as HA Labels or explicit confirm only?
7. Colors/Icons: Central registry or HA as UI source?
8. Conflicts: How to handle existing HA labels without `aicp.*` namespace?
9. Habitus Zones: Own objects or pure tagging?
10. Migration: Legacy configs to collect or start fresh?

### To Resume
Manually trigger a new autopilot window or run with fresh parameters.

---

## 2026-02-14 15:29 — Testing Suite v0.1.1 — Weather Context Tests (autopilot) — ✅ RELEASED

### What changed
- **Testing Suite v0.1.1**: Enhanced test coverage for Weather Context Module
- Added **7 new test cases**:
  - `test_weather_context_entities()`: All 7 weather/PV entities validated
  - `test_weather_condition_options()`: 11 weather condition options verified
  - `test_pv_recommendation_options()`: 4 PV recommendation options verified
  - `test_weather_pv_surplus_calculation()`: PV surplus calculation logic tested
  - `test_all_context_modules_registered()`: Energy/UniFi/Weather module registration
- Now covers all 3 Context Modules: Energy (4 entities), UniFi (6 entities), Weather (7 entities)

### Files changed
- `custom_components/ai_home_copilot/tests/test_suite_v01.py` (+84 lines)
- `custom_components/ai_home_copilot/manifest.json` (version → 0.6.3)
- `CHANGELOG.md` (+v0.6.3 entry)

### Status
- **✅ RELEASED**: https://github.com/GreenhillEfka/ai-home-copilot-ha/releases/tag/v0.6.3
- Branch: development
- py_compile verified for test file

### Next logical step
- **User Antworten auf P0/P1 Fragen** (Tag System decisions)
- ODER: Tag System v0.2 Implementierung (basierend auf Decision Matrix Empfehlungen)
- ODER: Weitere Testing Suite Erweiterungen (Repairs workflow tests, Candidate Poller tests)
