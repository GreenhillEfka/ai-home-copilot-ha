# SLICE 3 REVIEW — Zone E2E + Modulkonfiguration Surface
**Lane:** Design/UX (Stxy)
**Date:** 2026-03-21 18:05
**Based on:** Andreas Direktive, HomeClaw Verify (0 zones in Core)

---

## CRITICAL BLOCKER: Zone E2E Flow ist gebrochen

### HomeClaw Verify Befund (bestätigt)
- **HA: 12 zones** ✅
- **Core: 0 zones** 🔴
- Andreas-Regel: "Core = Source of Truth für Habitus-Zonen" → **NICHT VERDRAHTET**

### Root Cause — gefunden in Code

**1. `habitus_zones_api.py:18-27` — Import failure:**
```python
try:
    from copilot_core.homeassistant.zone_matcher import (
        create_zone_matcher, get_zone_suggestions
    )
    from copilot_core.homeassistant.habitus_zones import ZoneType
    HAS_ZONE_MATCHER = True
except ImportError:
    HAS_ZONE_MATCHER = False
    _LOGGER.warning("Habitus zone matcher not available...")
```
**Problem:** `copilot_core.homeassistant.zone_matcher` ist nicht im HA-Import-Pfad verfügbar. Zone-Matching ist in Core definiert aber in HA nicht erreichbar.

**2. `_first_zone_sync()` in `coordinator.py:1237`:**
```python
if not getattr(self, "_zone_auto_synced", False):
    await self._first_zone_sync(result)
```
**Problem:** Wird nur beim ersten Refresh getriggert. Wenn der Sync fehlschlägt → zones werden nie nach Core gepusht.

**3. Zone-Matching-Logik in HA dupliziert:**
- `habitus_zones_entities_v2.py` enthält eigenes `sort_entity_to_zone()` (keyword-basiert, 150+ lines)
- `zone_matcher.py` in Core (ML-basiert, 295 lines)
- Beide machen dasselbe — **Architectural violation**

### Zone E2E Flow (Ist-Zustand)
```
HA Zones (habitus_zones_store_v2)
    → coordinator._first_zone_sync()
    → POST /api/v1/zone-automation/sync-definitions
    → Core empfängt (0 zones gefunden)
```
**Das Core empfängt 0 zones** → wahrscheinlich `sync-definitions` Endpoint existiert nicht oder nimmt die Daten nicht an.

---

## Modulkonfiguration Surface Review

### Zone Automation Entities — UX Surface ✅
717 lines, 20+ Entity-Klassen:
- Select: ZoneAutomationModeSelect (off/learning/autonomy)
- Switches: ZoneLightAutoSwitch, ZoneMusicAutoSwitch, ZoneMusicFollowSwitch, etc.
- Numbers: ZoneBrightnessTargetNumber, ZonePresenceDelayNumber, etc.

**UX-Bewertung:** Konsistente, vollständige Oberfläche für Zone-Automation-Config. Alle Entities sind registriert und in Lovelace verfügbar.

### Zone Automation Entities — Architecture Check
- `zone_automation_entities.py` ist **HA-seitige Visualisierung/Steuerung** ✅
- Liest Core-Zustand über `coordinator` → schreibt über Core REST API ✅
- **Aber:** Presence Hold ist NICHT in `zone_automation_entities.py` — es ist in `coordinator.py:508` als API-Call

---

## RISIKO-BEWERTUNG

| Risiko | Schwere | Grund |
|--------|---------|-------|
| Core: 0 zones trotz HA: 12 | **KRITISCH** | Andreas-Regel verletzt, E2E gebrochen |
| Zone-Matcher Import failure | **HOCH** | Zone-Matching in HA fallbackt auf basic matching |
| sync-definitions Endpoint | **HOCH** | Wahrscheinlich nicht in Core implementiert |
| zone_auto_setup.py | **MITTEL** | Sortiert Entities, aber Zone-Matching ist HA-lokal |
| sort_entity_to_zone Duplikate | **NIEDRIG** | 3 Versionen, nur 1 wird verwendet |

---

## FREIGABE

| Artefakt | Status | Bemerkung |
|----------|--------|-----------|
| Zone Automation Entities (UX) | ✅ FREIGEGEBEN | Smarte HA-Visualisierung |
| Zone Automation Config | ✅ FREIGEGEBEN | Konsistente Slider/Selects |
| Modul-Schemas (schemas/) | ✅ FREIGEGEBEN | Saubere Pydantic Models |
| Zone E2E Flow | 🔴 **BLOCKIERT** | Core: 0 zones |
| Zone-Matching (HA) | 🔴 **BLOCKIERT** | Import failure, fallback |
| sync-definitions Endpoint | 🔴 **OFFEN** | Existiert in Core? |

---

## NÄCHSTER SCHRITT (an PilotClaw/HomeClaw)

**PilotClaw:**
1. Prüfen: Existiert `/api/v1/zone-automation/sync-definitions` in Core? Wenn nein → implementieren
2. Prüfen: Warum `_first_zone_sync` 0 zones nach Core pusht — endpoint broken oder payload empty?

**HomeClaw:**
1. Area→Zone E2E Verify → Zone-Definitions-Sync prüfen
2. `copilot_core.homeassistant.zone_matcher` → existiert im Core-Container?

**Stxy:**
- Zone Lovelace Cards → prüfen ob sie Core-Zustand oder HA-lokalen Zustand zeigen
- UX Surface für ZoneConfig → Konsistenz mit Core-Zustand

---

*Stxy — UX Lane — 2026-03-21 18:05*
