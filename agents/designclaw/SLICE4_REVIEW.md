# SLICE 4 REVIEW — Zone E2E + Modulkonfiguration Deep-Dive
**Lane:** Design/UX (Stxy)
**Date:** 2026-03-21 18:15
**Based on:** Andreas Direktive, HomeClaw Verify, Code Deep-Dive

---

## Zone E2E Flow — Architecture Analysis

### Zone E2E Flow (verifiziert funktioniert)
```
HA: habitus_zones_store_v2 (HA Storage)
    ↓ async_get_zones_v2() → zone_ids mit "zone:" prefix
Coordinator._first_zone_sync() [first refresh only]
    ↓ strip "zone:" prefix
    ↓ async_ensure_zone_automation_zones(clean_ids)
    POST /api/v1/zone-automation/ensure-zones
    ↓ Core: _controller._configs auto-created via get_zone_config()
    ↓ return dashboard mit zones
    ↓ async_sync_zone_definitions(zone_defs)
    POST /api/v1/zone-automation/sync-definitions
```

### Endpoint-Verfügbarkeit (Core)
| Endpoint | Existiert | Status |
|----------|-----------|--------|
| `/api/v1/zone-automation/ensure-zones` | ✅ Ja (zone_automation.py:393) | FUNKTIONIERT |
| `/api/v1/zone-automation/sync-definitions` | ❌ Nicht gefunden | **MISSING** |

### Root Cause — Zone E2E Block
`/api/v1/zone-automation/sync-definitions` existiert in Core **NICHT**. Der Endpoint wird von HA aufgerufen aber Core antwortet mit 404.

**Das erklärt den HomeClaw-Befund:** 12 zones in HA, 0 in Core → `ensure-zones` erstellt ZoneAutomationConfigs, aber `sync-definitions` schlägt fehl (404) → Zones werden nie mit voller Definition (entities, roles, metadata) nach Core gepusht.

### Zone Automation Dashboard
| Schicht | Zones | Entities | Status |
|---------|-------|----------|--------|
| HA (habitus_zones_store_v2) | 12 | many | ✅ |
| Core (_controller._configs) | 0 (nach HomeClaw Verify) | 0 | 🔴 |
| Core /dashboard endpoint | ? | ? | vermutlich 0 |

---

## Modulkonfiguration Surface — UX Audit

### Zone Automation Entities ✅
`zone_automation_entities.py` (717 lines) — vollständige UX Surface:

| Entity-Typ | Klassen | Funktion |
|-----------|---------|---------|
| Select | 1 | `ZoneAutomationModeSelect` (off/learning/autonomy) |
| Switch | 7+ | LightAuto, MusicAuto, MusicFollow, LuxComp, ColorTempAuto, MusicAutoPlay, + Module Switches |
| Number | 9+ | BrightnessTarget, PresenceDelay, AbsenceDelay, MusicVolume, BrightnessMin, DampeningBand, LuxTarget, ColorTemp, Music Delays |
| 20+ Entities total | | |

**UX-Bewertung:** ✅ Konsistent, vollständig, keine toten Controls. Alle Slider/Selects/Switches sind für Zone-Automation-Config.

### Zone Automation — Coordinator vs Entity Layer
| Funktion | Ort | OK? |
|---------|-----|------|
| Modus lesen/schreiben | `zone_automation_entities.py` | ✅ |
| Presence Hold | `coordinator.py:508` + `area_presence_sensor.py:540` | ✅ |
| Zone Sync (HA→Core) | `coordinator.py` + `zone_automation_api` | 🔴 sync-definitions missing |

### Modulkonfiguration — weitere Module
| Modul | Config Surface | Status |
|-------|---------------|--------|
| Licht | `zone_automation_entities.py` | ✅ |
| Musik | `zone_automation_entities.py` | ✅ |
| Climate | `zone_automation_entities.py` | ✅ |
| Presence | `area_presence_sensor.py` | ✅ |
| Energy | `zone_energy_devices.py` | ⚠️ |
| Scene | ? | ⚠️ |

---

## UX Surface Findings

### ✅ FREIGEGEBEN
- Zone Automation Entities (alle Slider/Switches/Selects)
- Presence Hold Integration
- Modul-Switches (pro Zone)

### 🔴 BLOCKIERT / RISIKEN
1. `/api/v1/zone-automation/sync-definitions` fehlt in Core
2. Zone Automation Dashboard zeigt 0 zones in Core (HomeClaw Verify)
3. `sync-definitions` 404 → Zone-Definitionen (entities, roles) werden nie nach Core gepusht
4. Modulkonfiguration für Energy/Scene unklar

---

## NÄCHSTER SCHRITT

**PilotClaw:**
1. `/api/v1/zone-automation/sync-definitions` → implementieren in Core ODER
2. prüfen ob `/api/v1/habitus/zones/sync` das gleiche tut

**HomeClaw:**
1. Area→Zone Verify → zeigt dass `_first_zone_sync` aufgerufen wird
2. Prüfen ob `sync-definitions` 404 zurückgibt

**Stxy:**
- Zone Lovelace Card UX → prüfen ob UI an Core-Zustand oder HA-lokal gebunden
- Modulkonfiguration UX → konsistente Darstellung aller 7 Module pro Zone

---

*Stxy — UX Lane — 2026-03-21 18:15*
