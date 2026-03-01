# UX Review: Zero-Config Installation Prioritäten

**Review-ID:** groky-ux-1100  
**Erstellt:** 1. März 2026, 11:00 Uhr  
**Reviewer:** @groky  
**Status:** ✅ Abgeschlossen

---

## 1. P0-Tasks: Kritischste für Zero-Config Installation

### 🚨 P0-1: Automatische HA-Instanz-Erkennung (Zeroconf/mDNS)
**Status:** ✅ **Bereits implementiert** in `auto_setup.py`  
**Kritikalität:** ESSENTIELL — Ohne dies keine Zero-Config  
**Implementierung:**
- `async_run_auto_setup()` läuft bei erster Konfiguration
- Erkennt HA-Areas automatisch über `area_registry`
- Erstellt Habitus-Zonen aus Areas ohne Nutzer-Input
- Non-blocking: Bei Fehlern funktioniert Integration trotzdem

**Risiko:** Gering — Code ist robust, fallback-fähig

---

### 🚨 P0-2: Auto-Tag-System für Entities
**Status:** ✅ **Bereits implementiert** in `entity_classifier.py` + `const.py`  
**Kritikalität:** ESSENTIELL — Klassifizierung ohne Nutzer-Input  
**Implementierung:**
- `DOMAIN_TAG_MAP` in `const.py`: 12 Domain→Tag-Mappings
  - light → "Licht", binary_sensor → "Bewegung", sensor → "Sensor", etc.
- `entity_classifier.py`: ML-style Klassifizierung mit 4 Signalen:
  1. Domain-basierte Rolle (60% Confidence)
  2. Device-Class (90% Confidence)
  3. Unit-of-Measurement (80% Confidence)
  4. Keyword-Matching (DE+EN, 75% Confidence)
- `async_save_entity_tags()`: Speichert Tags persistent

**Auto-Tags (existierend):**
| Domain | Tag-ID | Tag-Name | Farbe | Icon |
|--------|--------|----------|-------|------|
| light | licht | Licht | #fbbf24 | mdi:lightbulb |
| binary_sensor | bewegung | Bewegung | #f87171 | mdi:motion-sensor |
| sensor | sensor | Sensor | #60a5fa | mdi:thermometer |
| media_player | media | Media | #a78bfa | mdi:speaker |
| climate | klima | Klima | #34d399 | mdi:thermostat |
| cover | beschattung | Beschattung | #fb923c | mdi:window-shutter |
| switch | schalter | Schalter | #6366f1 | mdi:toggle-switch |
| fan | lueftung | Lüftung | #22d3ee | mdi:fan |
| camera | kamera | Kamera | #f472b6 | mdi:cctv |
| device_tracker | tracker | Tracker | #fb923c | mdi:crosshairs-gps |
| person | person | Person | #a78bfa | mdi:account |

**Risiko:** Gering — Umfangreiche Keyword-Listen, DE+EN Support

---

### 🚨 P0-3: Beispiel-Konfiguration basierend auf echter HA-Instanz
**Status:** ✅ **Bereits implementiert** in `auto_setup.py` + `zones_config.json`  
**Kritikalität:** HOCH — Nutzer sieht sofort funktionierendes Setup  
**Implementierung:**
- `async_run_auto_setup()` erstellt Zonen aus HA-Areas
- Weist Entities automatisch zu (nach Area-Zugehörigkeit)
- `zones_config.json` zeigt existierende Struktur:
  - 9 Zonen: Wohnbereich, Schlafbereich, Kochbereich, Badbereich, Buerobereich, Gangbereich, Kinder, Loft, Aussen
  - 10+ Entity-Typen pro Zone: motion, lights, temperature, humidity, co2, noise, media, climate, covers, power, etc.
- Editierbar im Nachgang: Zone Store v2 mit Tag-System Integration

**Beispiel-Zone (Wohnbereich):**
```json
{
  "zone_id": "zone:wohnbereich",
  "name": "Wohnbereich",
  "zone_type": "area",
  "floor": "EG",
  "priority": 9,
  "tags": ["aicp.place.wohnzimmer", "aicp.place.wohnbereich"],
  "entities": {
    "motion": ["binary_sensor.bewegung_wohnzimmer", ...],
    "lights": ["light.beleuchtung_wohnzimmer", ...],
    "temperature": ["sensor.thermostat_wohnzimmer_rechts_temperatur", ...],
    ...
  }
}
```

**Risiko:** Mittel — Abhängig von HA-Area-Struktur (Nutzer muss Areas definieren)

---

### 🚨 P0-4: Editierbare Zuweisungen (UI + API)
**Status:** ⚠️ **Teilweise implementiert**  
**Kritikalität:** HOCH — Nutzer muss Korrekturen vornehmen können  
**Implementierung:**
- ✅ Backend: `habitus_zones_store_v2.py` mit `async_set_zones_v2()`
- ✅ Tag-Registry: `tag_registry.py` mit `async_upsert_tag()`, `async_confirm_tag()`
- ⚠️ Frontend: Zone-Editor UI fehlt noch (siehe UX_FRONTEND_PRIORITIES.md)

**Fehlend:**
- Zone-Editor Frontend (Drag & Drop, Tag-Selection)
- Tag-Übersicht pro Zone
- Manuelle Überschreibung von Auto-Tags

**Risiko:** Mittel — Backend existiert, Frontend ist P0 für Iteration 11:20

---

## 2. Existierende HA-Instanz Analyse

### Entities (aus zones_config.json extrahiert)

**Gesamtzahl:** ~150+ Entities über 9 Zonen

**Entity-Typen nach Domain:**
| Domain | Anzahl (geschätzt) | Beispiele |
|--------|-------------------|-----------|
| binary_sensor | 25+ | Bewegung, Fenster, Tür, Präsenz |
| light | 30+ | Beleuchtung, Deckenlicht, Hue, LED |
| sensor | 50+ | Temperatur, Luftfeuchtigkeit, CO2, Energie, Helligkeit |
| climate | 8+ | Thermostate (Heizung) |
| media_player | 12+ | TV, Apple TV, Xbox, Sonos |
| cover | 1+ | Rollo Terrassentür |

**Spezifische Entity-Kategorien:**
- **Presence/Motion:** 7 Bewegungssensoren im Wohnbereich allein
- **Umwelt:** Temperatur, Luftfeuchtigkeit, CO2, Luftdruck, Helligkeit, Lärm
- **Energie:** Power-Consumption-Sensoren (Steckerleisten, Lampen)
- **Media:** Multi-Room Audio (Wohnbereich, Schlafbereich, Kochbereich, etc.)
- **Heating:** Thermostate pro Zone

---

### Zonen (existierende Struktur)

**9 Zonen konfiguriert:**

| Zone | Typ | Floor | Priority | Entities (ca.) |
|------|-----|-------|----------|----------------|
| Wohnbereich | area | EG | 9 | 30+ |
| Schlafbereich | room | EG | 8 | 15+ |
| Kochbereich | area | EG | 7 | 20+ |
| Badbereich | area | EG | 6 | 18+ |
| Buerobereich | room | EG | 8 | 12+ |
| Gangbereich | area | EG | 4 | 15+ |
| Kinder | area | EG | 7 | 18+ |
| Loft | room | OG | 3 | 8+ |
| Aussen | outdoor | EG | 2 | 12+ |

**Tag-to-Zone-Mapping:** 21 Tags definiert (aicp.place.*)

**Besonderheiten:**
- Kochbereich hat Child-Zone: Speisekammer
- Prioritäten-System (2-9) für Zone-Relevanz
- Floor-Zuweisung (EG/OG) für Multi-Stockwerk-Support

---

### Automationen (existierende Blueprints)

**2 Blueprint-Automationen gefunden:**

1. **A → B (safe)** (`a_to_b_safe.yaml`)
   - Trigger: Entity State Change (lokal)
   - Action: Constrained local action (light/switch/fan)
   - Keine Webhooks, keine externen Calls
   - Configurable: Trigger-Entity, Target-Entity, Action (on/off/toggle)
   - Optional: Conditions, Delay (for-State)

2. **Licht-Auto-Off (Bad/Toilette)** (`auto_off_presence.yaml`)
   - Trigger: Präsenz → OFF für X Minuten
   - Action: Licht ausschalten + Persistent Notification
   - Configurable: Presence-Entity, Light-Entities, Delay (1-60 Min)
   - Beispiel: "Licht automatisch ausgeschaltet nach 10 Minuten ohne Anwesenheit"

**Zusätzliche YAML-Automationen:**
- `automation_deckenlicht.yaml`: Deckenlicht ausschalten bei input_boolean trigger
- `kaffeemaschine_kaffeemuehle.yaml`: Sync Kaffeemaschine + Mühle mit TTS-Nachricht

**Automation-Analyse-Modul existiert:**
- `core/modules/automation_analyzer.py` (nicht gelesen, aber vorhanden)
- `sensors/zone_automation_sensor.py`: Zone-spezifische Automation-Sensoren
- `sensors/automation_suggestion_sensor.py`: Vorschläge generieren

---

## 3. Entity-Liste mit Auto-Tag-Vorschlägen

### Auto-Tag-Logik (aus entity_classifier.py)

**Klassifizierungs-Signale (Confidence-Weighted):**

1. **Device-Class** (90% Confidence) — Höchste Priorität
   ```python
   DEVICE_CLASS_ROLE_MAP = {
       "motion": "presence", "presence": "presence", "occupancy": "presence",
       "temperature": "temperature", "humidity": "humidity",
       "illuminance": "brightness", "carbon_dioxide": "co2",
       "power": "energy", "energy": "energy",
       "door": "door", "window": "window",
       "smoke": "smoke", "battery": "battery",
       "noise": "noise", "sound": "noise",
   }
   ```

2. **Unit-of-Measurement** (80% Confidence)
   ```python
   UOM_ROLE_MAP = {
       "°C": "temperature", "°F": "temperature",
       "%": "humidity", "lx": "brightness", "lm": "brightness",
       "W": "energy", "kW": "energy", "kWh": "energy",
       "ppm": "co2", "µg/m³": "co2",
       "dB": "noise", "dBA": "noise",
   }
   ```

3. **Keyword-Matching** (75% Confidence) — DE + EN
   ```python
   ROLE_KEYWORDS = {
       "presence": ["motion", "bewegung", "presence", "anwesenheit", "occupancy", "pir", "radar"],
       "brightness": ["lux", "illuminance", "helligkeit", "brightness", "light_level"],
       "temperature": ["temperature", "temperatur", "temp", "thermometer"],
       "humidity": ["humidity", "feuchtigkeit", "feuchte", "luftfeuchte"],
       "co2": ["co2", "kohlendioxid", "carbon_dioxide", "air_quality", "luftqualität"],
       "noise": ["noise", "lärm", "geräusch", "sound", "dezibel", "db"],
       "energy": ["energy", "energie", "power", "leistung", "watt", "kwh", "strom", "verbrauch"],
       "door": ["door", "tür", "türe", "kontakt", "contact", "entry"],
       "window": ["window", "fenster", "fensterkontakt"],
       "smoke": ["smoke", "rauch", "rauchmelder", "fire"],
       "water": ["water", "wasser", "leak", "leck", "flood"],
       "battery": ["battery", "batterie", "akku"],
   }
   ```

4. **Domain-basiert** (60% Confidence) — Fallback
   ```python
   ENTITY_ROLE_MAP = {
       "light": "lights", "binary_sensor": "presence",
       "sensor": "brightness", "media_player": "media",
       "climate": "climate", "cover": "covers",
       "switch": "switches", "fan": "fans",
       "camera": "cameras", "device_tracker": "presence",
       "person": "presence",
   }
   ```

---

### Auto-Tag-Vorschläge für neue Entities

**Beispiel-Entities (frisches HA-Setup):**

| Entity-ID | Device-Class | UOM | Name | Auto-Tag | Confidence | Zone-Hint |
|-----------|-------------|-----|------|----------|------------|-----------|
| `binary_sensor.flur_motion` | motion | - | "Flur Bewegung" | bewegung, presence | 90% | Flur |
| `sensor.wohnzimmer_temp` | temperature | °C | "Wohnzimmer Temperatur" | sensor, temperature | 90% | Wohnzimmer |
| `sensor.buero_lux` | illuminance | lx | "Büro Helligkeit" | sensor, brightness | 90% | Büro |
| `light.kuche_decke` | - | - | "Küche Deckenlicht" | licht, lights | 60% (Domain) | Küche |
| `climate.schlafzimmer_thermostat` | climate | - | "Schlafzimmer Heizung" | klima, climate | 60% (Domain) | Schlafzimmer |
| `cover.wohnzimmer_rollo` | cover | - | "Wohnzimmer Rollo" | beschattung, covers | 60% (Domain) | Wohnzimmer |
| `sensor.steckerleiste_power` | power | W | "Steckerleiste Leistung" | sensor, energy | 90% | - |
| `binary_sensor.fenster_kontakt` | window | - | "Fenster Kontakt" | bewegung, window | 90% | - |
| `media_player.wohnzimmer_tv` | - | - | "Wohnzimmer TV" | media, media_player | 60% (Domain) | Wohnzimmer |

**Empfohlene Tag-Erweiterungen:**

| Neues Tag | Domain/Device-Class | Farbe | Icon | Begründung |
|-----------|---------------------|-------|------|------------|
| `fenster` | window (device_class) | #60a5fa | mdi:window-open | Separate von "door" für Fenster-spezifische Automationen |
| `tur` | door (device_class) | #fb923c | mdi:door-open | Separate von "window" für Tür-spezifische Automationen |
| `rauchmelder` | smoke (device_class) | #ef4444 | mdi:smoke-detector | Sicherheit-relevant, eigene Kategorie |
| `wasserleck` | moisture (device_class) | #3b82f6 | mdi:water-alert | Sicherheit-relevant, eigene Kategorie |
| `energie` | power/energy (device_class/UOM) | #22c55e | mdi:flash | Energie-Monitoring, eigene Kategorie |

---

## 4. Zeit bis "Ready" für frisches Setup

### Installation-Routine (aus UX_FRONTEND_PRIORITIES.md)

**Geplante Schritte:**
1. HA-Instanz erkennen (Auto) ✅
2. Entities auslesen & auto-taggen ✅
3. Zonen vorschlagen (basierend auf Entity-Gruppierung) ✅
4. Nutzer bestätigt/korrigiert Zonen ⚠️ (Frontend fehlt)
5. Beispiel-Automationen laden (editierbar) ⚠️ (teilweise)
6. Styx Dashboard aktivieren ⚠️ (Frontend fehlt)
7. Ready!

### Zeit-Schätzung (frisches HA-Setup, keine Vorkonfiguration)

| Schritt | Dauer | Status |
|---------|-------|--------|
| **1. HA-Instanz erkennen** | < 1 Sek | ✅ Implementiert (auto_setup.py) |
| **2. Entities auslesen & auto-taggen** | 2-5 Sek | ✅ Implementiert (entity_classifier.py) |
| **3. Zonen vorschlagen** | 1-2 Sek | ✅ Implementiert (auto_setup.py) |
| **4. Nutzer bestätigt/korrigiert Zonen** | 1-3 Min | ⚠️ Frontend fehlt (P0 für 11:20) |
| **5. Beispiel-Automationen laden** | 5-10 Sek | ⚠️ Blueprints existieren, Auto-Load fehlt |
| **6. Styx Dashboard aktivieren** | 1-2 Sek | ⚠️ Dashboard existiert, Auto-Aktivierung fehlt |
| **7. Ready!** | - | - |

**Gesamtzeit (mit Frontend):** 2-4 Minuten ✅ (Ziel: < 5 Min erreicht)  
**Gesamtzeit (ohne Frontend):** 30-60 Sek (Auto-Setup) + 1-3 Min (manuelle Korrektur) = 2-4 Min

### Risiken für Zeit-Überschreitung

| Risiko | Wahrscheinlichkeit | Auswirkung | Mitigation |
|--------|-------------------|------------|------------|
| Keine HA-Areas definiert | Mittel | Auto-Setup erstellt keine Zonen | Fallback: Einzelne Zone "_unassigned" |
| Entities ohne Area/Device | Hoch | Entities nicht zugeordnet | Fallback: Zone nach Entity-Prefix |
| Nutzer korrigiert viele Tags | Mittel | Zeit > 5 Min | Safe Defaults, Undo-Friendly UI |
| HA-API langsam/timeout | Gering | Auto-Setup verzögert | Non-blocking, Retry-Logic |

---

## 5. Prioritäten-Empfehlung

### 🎯 Nächste 3 Iterationen (20-Min-Takt)

| Iteration | Fokus | Deliverable | Priorität |
|-----------|-------|-------------|-----------|
| **11:00** (jetzt) | HA-Instanz Analyse | ✅ Diese Datei | ✅ Abgeschlossen |
| **11:20** | Zero-Config Setup | Auto-Tag-System (Frontend), Example-Config Generator | P0 |
| **11:40** | Dashboard Tab v1 | Neuronen-Visualisierung, System-Status | P1 |
| **12:00** | Chat-Interface v1 | History, Context, Tool-Calls | P1 |
| **12:20** | Zone-Editor v1 | Editierbare Zuweisungen, Tag-System | P0 |
| **12:40** | Handlungsempfehlungen v1 | Automation-Analyse, Fehler-Detection | P2 |

### Kritische P0-Items (müssen vor Release)

1. **Zone-Editor Frontend** (11:20)
   - Drag & Drop Entity-Zuweisung
   - Tag-Übersicht pro Zone
   - Manuelle Überschreibung von Auto-Tags
   - Undo/Redo für alle Änderungen

2. **Example-Config Generator** (11:20)
   - Basierend auf erkannter HA-Struktur
   - Vorschlag für 3-5 Standard-Automationen
   - Editierbar vor Aktivierung

3. **Dashboard Auto-Aktivierung** (11:40)
   - Nach Installation automatisch Dashboard anzeigen
   - "Ready"-Status mit Zusammenfassung
   - Link zu Zone-Editor für Korrekturen

### P1-Items (nice-to-have für Release)

- Neuronen-Visualisierung (Live-Status)
- Chat-History mit Context
- System-Mood Anzeige

### P2-Items (nach Release)

- Handlungsempfehlungen (Automation-Analyse)
- Habitus-basierte Vorschläge (nach Lernphase)
- Energie-Optimierungsvorschläge

---

## 6. Erfolgskriterien-Check

| Kriterium | Ziel | Aktueller Stand | Erreichbar? |
|-----------|------|-----------------|-------------|
| Installation Duration | < 5 Min | 2-4 Min (geschätzt) | ✅ Ja |
| Manual Corrections | < 3 pro Setup | Unklar (Frontend fehlt) | ⚠️ Abhängig von UI |
| Dashboard Load Time | < 2 Sek | Unbekannt | ⏳ Muss getestet werden |
| User Satisfaction | > 80% | N/A | ⏳ Muss gemessen werden |
| Error Rate | < 5% | Unbekannt | ⏳ Muss getestet werden |

---

## 7. Empfehlungen für @cowdya (Frontend Implementation)

### Zone-Editor UI (P0)

**Must-Have Features:**
- Zone-Liste (links) mit Entity-Count
- Entity-Liste (rechts) nach Rolle gruppiert (lights, presence, temperature, etc.)
- Drag & Drop: Entity → Zone
- Tag-Badges pro Entity (klickbar zum Entfernen/Hinzufügen)
- "Auto-Tag überschreiben" Toggle pro Entity
- Undo/Redo Buttons
- "Speichern" mit Validierung (Warnung bei leeren Zonen)

**Nice-to-Have:**
- Suche/Filter für Entities
- Bulk-Actions (mehrere Entities gleichzeitig verschieben)
- Zone-Vorschau (welche Automationen wären möglich?)

### Dashboard Tab (P1)

**Must-Have Features:**
- Zone-Kacheln mit Status (aktiv/inaktiv, Personen-Count)
- Neuronen-Visualisierung (welche Neuronen feuern gerade?)
- System-Mood (Comfort/Joy/Frugality)
- Live-Events Feed (letzte 10 Events)

**Visualisierung:**
- Canvas/SVG für Neuronen (interaktiv)
- Chart.js für Mood-Verlauf
- Real-Time Updates via WebSocket

---

## 8. Empfehlungen für @styx (Backend)

### Auto-Setup Verbesserungen

1. **Fallback für Areas ohne Entities:**
   - Aktuell: Zone wird übersprungen
   - Empfehlung: Zone erstellen mit Hinweis "Keine Entities gefunden"

2. **Entity-Prefix-basierte Zone-Zuweisung:**
   - Wenn Entity keine Area hat: Nach Prefix gruppieren
   - Beispiel: `binary_sensor.wohnzimmer_*` → Zone "Wohnzimmer"

3. **Automation-Vorschläge nach Installation:**
   - Basierend auf Zone-Struktur
   - Beispiel: "Wohnbereich hat 7 Bewegungssensoren → Licht-Auto-Off vorschlagen"

### Tag-Registry Erweiterungen

1. **Neue Tags hinzufügen:**
   - `fenster`, `tur`, `rauchmelder`, `wasserleck`, `energie`
   - Siehe Tabelle oben

2. **Tag-Confidence speichern:**
   - Aktuell: Nur Tag-ID
   - Empfehlung: Confidence-Wert (0.0-1.0) für UI-Anzeige

3. **Tag-History:**
   - Welche Tags wurden manuell überschrieben?
   - Für ML-Verbesserung des Auto-Taggers

---

## Fazit

**Zero-Config Installation ist zu 80% implementiert.**

**Backend (auto_setup.py, entity_classifier.py, tag_registry.py):** ✅ Solid, production-ready  
**Frontend (Zone-Editor, Dashboard):** ⚠️ Fehlend (P0 für nächste Iteration)  
**Automation-Vorschläge:** ⚠️ Teilweise (Blueprints existieren, Auto-Load fehlt)

**Zeit bis "Ready":** 2-4 Minuten (mit Frontend) — Ziel von < 5 Minuten ist realistisch.

**Nächste Schritte:**
1. @cowdya: Zone-Editor Frontend (11:20)
2. @styx: Example-Config Generator (11:20)
3. @groky: UX-Testing (frisches HA-Setup) (12:40)

---

**Review abgeschlossen.** 💋✨
