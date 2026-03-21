# PS-135 Tasklog: Area Presence Aggregation Pattern

**Datum:** 2026-03-20  
**Agent:** PilotClaw (HA/UI-Spur)  
**Status:** ✅ Implementiert

---

## Was wurde getan

### Pattern: Multi-Source Presence Aggregation

Ziel war die Erweiterung der Core-Presence-Logic auf ein Magic-Areas/Auto-Areas-ähnliches
Multi-Source-Aggregation-Muster mit ANY-ON-Regel, Timeout-Reset und Hold-Switch.

### Änderungen

#### 1. Neuer File: `sensors/area_presence_sensor.py` (v1.0.0)

Vollständige Implementierung des `AreaPresenceSensor` (binary_sensor):

**Multi-Source Aggregation (Prioritäts-Reihenfolge):**
```
1. mmWave / Presence radar  (device_class: presence)   — Timeout: 60s
2. Motion PIR              (device_class: motion)       — Timeout: 120s
3. BLE / device_tracker    (source_type: bluetooth)     — Timeout: 180s
4. Person zone assignment  (person.home)               — Timeout: 300s
```

**ANY-ON-Regel:**
Zone ist belegt, wenn IRGENDEINE Quelle Presence meldet. Zone wird OFF erst
wenn ALLE Quellen expired oder abwesend sind.

**Timeout-Reset:**
Jede Quelle hat einen individuellen Timeout. `last_changed`-Timestamp wird
geprüft; bei Überschreitung wird die Quelle als inaktiv gewertet.

**Hold-Switch:**
Manuelle Override-States: `auto` (normal), `force_on` (immer besetzt),
`force_off` (immer leer). API: `async_set_hold(hold)`.

**Sync-Contract:**
Primär: Sync mit Core `/api/v1/zone-automation/dashboard`.  
Fallback: HA-native Direktevaluierung aller Entity-States.

**Entity-ID:** `binary_sensor.area_presence_{zone_id}`

#### 2. Neuer File: `sensors/area_presence_sensor_factory.py`

Factory-Funktion `async_build_area_presence_sensors()`:
- Liest alle Habitus Zones v2
- Auto-Discover Presence-Entities aus den Zone-Rolle-Zuordnungen
- Split mmWave vs. PIR via `device_class` Check
- Findet BLE-Tracker (`source_type: bluetooth`) und zugeordnete `person`-Entities

#### 3. Geändert: `sensor.py` — Area Presence Sensor-Registrierung

Import + Factory-Call nach den Zone-Aggregate-Sensoren, mit Fehler-Isolation
(`try/except`) damit ein Fehlschlag nicht die gesamte Sensor-Registrierung blockiert.

#### 4. Geändert: `binary_sensor.py` — Zone Presence Trigger Integration

- Import von `ZonePresenceTriggerSensor` und `ZonePresenceOverviewSensor`
- Registrierung: pro Zone ein `binary_sensor.pilotsuite_zone_presence_{zone_id}`
  plus ein `binary_sensor.pilotsuite_zone_presence_overview`
- Diese Sensoren beziehen ihre Daten aus Core `/api/v1/zone-automation/dashboard`
  und haben dasselbe ANY-ON/Timeout/Hold-Muster über die Core-Schicht

### Sync mit HA-specific `binary_sensor.area_presence_{zone}`

Die neue `AreaPresenceSensor`-Entity verwendet:
- `binary_sensor.area_presence_{zone_id}` als Entity-ID
- Namensschema analog zu HA-nativen `area_presence`-Sensoren aus anderen Integrationen
- Attribute exponieren alle Sources + Timeout-Konfiguration für Debugging

### Nicht implementiert (Folgetasks)

1. **Core-API-Erweiterung:** `async_set_zone_presence_hold()` in `coordinator.api`
   ist als try/except wrapped — Core-Seite noch zu implementieren
2. **Dashboard-Integration:** Lovelace-Karten für Hold-Switch UI-Controls
3. **Neuron-Feed-Sync:** Area-P presence nach Core-Neurons forwarden

---

## Dateien

| File | Status | Änderung |
|---|---|---|
| `sensors/area_presence_sensor.py` | ✅ NEU | Hauptimplementierung |
| `sensors/area_presence_sensor_factory.py` | ✅ NEU | Factory |
| `binary_sensor.py` | ✅ Geändert | Trigger-Sensor-Registrierung |
| `sensor.py` | ✅ Geändert | Area-P presence-Registrierung |

## Verifikation

```bash
python3 -m py_compile sensors/area_presence_sensor.py       # OK
python3 -m py_compile sensors/area_presence_sensor_factory.py # OK
python3 -m py_compile binary_sensor.py                        # OK
python3 -m py_compile sensor.py                               # OK
```
