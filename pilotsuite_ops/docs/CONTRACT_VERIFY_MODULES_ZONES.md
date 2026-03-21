# CORE↔HA CONTRACT VERIFY — Modulkonfiguration + Habitus-Zonen

> **Erstellt:** 2026-03-21 18:00 GMT+1
> **Andreas-Direktive:** Core = Source of Truth für Zone-Management + Konfiguration. HA = Visualisierung.
> **Branch/Commit:** `origin/main` @ `50c36cac`
> **Live-System:** HA (Port 8123) + Core (Port 8909)

---

## 1. MODULKONFIGURATION — Core↔HA Contract

### Core Module Status (API `/api/v1/modules`)
```json
{
  "modules": {
    "brain_graph": "learning",
    "camera_context": "off",
    "conversation_memory": "learning",
    "energy_context": "learning",
    "event_forwarder": "learning",
    "habitus_miner": "learning",
    "knowledge_graph": "learning",
    "mcp_server": "active",
    "media_zones": "learning",
    "mood_engine": "learning",
    "network": "learning",
    "neurons": "learning",
    "proactive": "learning",
    "telegram_bot": "off",
    "weather_context": "learning"
  }
}
```
**15 Module total.** Core meldet `telegram_bot: off`, `camera_context: off`, alle anderen `learning/active`.

### HA Module-Repräsentation
- HA hat **keine** `sensor.pilotsuite_module_*` Entities
- Nur Buttons zum Reload/Generate: `button.pilotsuite_reload`, `button.pilotsuite_generate_pilotsuite_dashboard`
- **Drift:** HA zeigt Module-Zustand NICHT als Sensoren — keinelive Visualisierung der Core-Module

### Contract-Status Module
| Aspekt | Erwartung (Andreas-Regel) | Realität |
|--------|---------------------------|----------|
| Core verwaltet Modulkonfiguration | ✅ Core `/api/v1/modules` | ✅ 15 Module |
| HA visualisiert Modulzustände | ❌ Keine Sensoren | Keine `sensor.pilotsuite_module_*` |
| HA kann Module steuern | ❌ Buttons existieren aber keine WS-API | Kein Modul-Control in HA |

---

## 2. HABITUS-ZONEN — Core↔HA Contract

### Live Zone-Status

| System | Zone-API | Zone-Count | Notes |
|--------|----------|-----------|-------|
| **Core** `/api/v1/zones` | `{"total": 0, "zones": []}` | **0** | Empty — keine Zonen |
| **HA** `sensor.pilotsuite_habitus_zones` | — | **12/12 active** | Zones in HA gemanagt |

### Zones in HA (live):
```
sensor.pilotsuite_habitus_zones: 12/12 active ✅
sensor.pilotsuite_habitus_zones_count: 12 ✅
select.pilotsuite_zones_v2_global_state: auto ✅
```

### Wo sind die 12 Zones definiert?
- **HA-seitig:** `habitus_zones_store_v2.py` (HA Storage API, v2)
- **Core-seitig:** `zone_matcher.py` existiert in Core aber **nicht in HA-Runtime-Python-path**
- HA importiert aus `copilot_core.homeassistant.zone_matcher` → **Import fail → Fallback**

### Import-Check (Runtime)
```python
# habitus_zones_api.py:
try:
    from copilot_core.homeassistant.zone_matcher import ...
    HAS_ZONE_MATCHER = True
except ImportError:
    HAS_ZONE_MATCHER = False  # ← AKTUELL FALSE
```
**Runtime-Status:** `HAS_ZONE_MATCHER = False` — HA nutzt Fallback-Matching, nicht Core's `zone_matcher.py`

### ZoneMatcher Existenz (nicht identisch mit habitus_zones_matcher)
| File | Path | Existiert? | In HA-Runtime? |
|------|------|-----------|----------------|
| `zone_matcher.py` | Core `homeassistant/` | ✅ Ja (295 lines) | ❌ Nein (Import fail) |
| `habitus_zones_matcher.py` | Core `homeassistant/` | ❓ Unbekannt | ❌ HA sucht |

### Andreas-Regel Verifikation
> "Core = Management/Logik. HA = Visualisierung."

| Aspekt | Erwartung | Realität | Status |
|--------|-----------|----------|--------|
| Core verwaltet Zonen | Zone-API | 0 zones (leer) | ❌ |
| HA visualisiert Zonen | 12 zones | 12/12 active | ✅ |
| Core Matcher in HA | `zone_matcher.py` | Import fail → Fallback | ❌ |
| Zone-Data-Flow | HA→Core oder Core→HA | Kein Data-Flow | ❌ |

---

## 3. ZONEN-MAPPING — area_zone_map.json

```json
{
  "version": 1,
  "mappings": [
    {"area_id": "wohnzimmer", "zone_id": "wohnbereich", "aggregated": false},
    {"area_id": "esszimmer", "zone_id": "wohnbereich", "aggregated": true},
    {"area_id": "badezimmer", "zone_id": "badbereich", "aggregated": false},
    ...
  ],
  "unmatched_fallback": "ungeordnet"
}
```
**10 Mappings, 3 Aggregation Rules.** Funktioniert in HA (12 zones aus 10 mappings + 2 additional zones).

---

## 4. SMOKE/E2E — REFERENZIERTE COMMITS

| Test | Letzter erfolgreicher Lauf | Commit | Status |
|------|---------------------------|--------|--------|
| E2E Contract Pipeline | 11:27 UTC | `origin/main` | ✅ PASS |
| Python Syntax | earlier today | — | ✅ PASS |
| CI | 50c36cac | `50c36cac` | ✅ GREEN |

**smoke_test_v15.py** — geschrieben für v15.0.0, System läuft v14.7.3. NICHT LAUFFÄHIG für aktuelles System.

---

## 5. ZUSAMMENFASSUNG — BLOCKER

### 🔴 Critical für Andreas-Direktive

| # | Blocker | Beschreibung |
|---|---------|-------------|
| 1 | **Core Zone-API = 0** | Andreas-Regel (Core=Management) ist nicht verdrahtet. HA verwaltet alle 12 Zones eigenständig. |
| 2 | **zone_matcher Import fail** | `HAS_ZONE_MATCHER = False` in Runtime. HA nutzt Fallback, nicht Core's Matcher. |
| 3 | **Kein Module-Sensor in HA** | Core's 15 Module-Zustände werden nicht in HA visualisiert. |

### 🟡 Bekannte Drift

| # | Item | Beschreibung |
|---|------|-------------|
| 4 | Runtime- vs Repo-Pfade | `/config/clawd/custom_components/` (Runtime) ≠ Repo. Änderungen müssen nach Git. |
| 5 | Stxy's efb8bd19 im Worktree | Nicht in origin/main. Aufräumen erforderlich. |

---

## 6. NÄCHSTER SCHRITT (für meine Lane)

1. **Konfigurations-Matrix bauen:** Welche Core-Module haben Schemas/Settings die HA anzeigen sollte?
2. **Zone-Contract klarstellen:** Soll HA Zonen eigenständig verwalten ODER soll Core die Source of Truth sein?
3. **Modul-Sensoren:** Ist die Visualisierung von 15 Core-Modulen in HA geplant?

---

*Verify durchgeführt: HomeClaw Lane, 2026-03-21 18:00*
*Branch: origin/main @ 50c36cac*
