# PilotSuite Styx — Home Assistant Integration

**Version:** 15.4.0
**Status:** ✅ Integration des lernenden Dachsystems — End-to-End Verkabelt

---

## 🎯 VISION

**"Ein SmartHome, das CLEVERER ist als sein Nutzer"**

Diese HA-Integration verbindet PilotSuite Core mit Home Assistant:
- **Zone Sync** — Core ↔ HA bidirektional (Unified Store)
- **Entity Tags** — Automatische Zone-Zuordnung
- **Module Config** — active/learning/off pro Zone
- **Chat Interface** — Lovelace Card für PilotSuite Chat
- **Learning Viz** — Zeigt was System lernt (Intelligence Score)
- **End-to-End** — Alle Komponenten verkabelt

---

## 📦 INSTALLATION

### Via HACS (Empfohlen)

1. **HACS installieren** (falls nicht vorhanden)
2. **Repository hinzufügen:**
   ```
   https://github.com/GreenhillEfka/pilotsuite-styx-ha
   ```
3. **PilotSuite Styx installieren**
4. **Neu starten**
5. **Integration einrichten:**
   - Einstellungen → Geräte & Dienste → + Hinzufügen
   - "PilotSuite Styx" wählen
   - Core URL eingeben (default: `http://homeassistant.local:8909`)
   - API Token eingeben (aus Core Config)

### Manuell

```bash
# Clone Repository
git clone https://github.com/GreenhillEfka/pilotsuite-styx-ha
cd pilotsuite-styx-ha

# Copy to HA custom_components
cp -r custom_components/copilot_ha /config/custom_components/

# Restart HA
```

---

## ⚙️ KONFIGURATION

### Config Flow (UI)

1. **Core Connection:**
   - Host: `homeassistant.local` oder IP
   - Port: `8909` (default)
   - Token: Aus Core Config

2. **Zone Auto-Discovery:**
   - HA Areas scannen
   - Zone Types zuweisen (living, bath, kitchen, ...)
   - Bestätigen

3. **Entity Mapping:**
   - Auto-Assign via Tags
   - Manuell korrigieren (optional)

4. **Module Config:**
   - Pro Zone Module aktivieren
   - State setzen (active/learning/off)

### YAML (Optional)

```yaml
copilot_ha:
  core_url: http://homeassistant.local:8909
  core_token: YOUR_API_TOKEN
  
  zones:
    - zone_id: living
      zone_type: living
      name: Wohnzimmer
      modules:
        light: active
        motion: active
        music: learning
  
  tags:
    - entity_id: light.wohnzimmer_haupt
      tags: [domain:light, zone_living, auto_assign]
```

---

## 🔗 SERVICES

### `copilot_ha.sync_zones`

Synchronisiert Zonen zwischen Core und HA (Unified Store).

```yaml
service: copilot_ha.sync_zones
data:
  direction: bidirectional  # core_to_ha, ha_to_core, bidirectional
```

### `copilot_ha.set_module_state`

Setzt Module-State für eine Zone.

```yaml
service: copilot_ha.set_module_state
data:
  zone_id: living
  module_id: light
  state: active  # active, learning, off
```

### `copilot_ha.add_feedback`

Gibt Feedback für ein Pattern (End-to-End Wiring).

```yaml
service: copilot_ha.add_feedback
data:
  pattern_id: p_001
  feedback_type: accepted  # accepted, rejected, ignored, corrected
  comment: "Funktioniert perfekt!"
```

---

## 📊 ENTITIES

### Sensors

| Entity | Beschreibung |
|--------|--------------|
| `sensor.pilotsuite_system_health` | Core System Health |
| `sensor.pilotsuite_intelligence_score` | Intelligence Score (0-100) |
| `sensor.pilotsuite_patterns_learned` | Gelernte Patterns (Unified Store) |
| `sensor.pilotsuite_active_automations` | Aktive Automatisierungen |
| `sensor.pilotsuite_mood_state` | Aktuelle Stimmung (Neurons) |
| `sensor.pilotsuite_anomaly_detected` | Anomalie erkannt (ja/nein) |

### Buttons

| Entity | Beschreibung |
|--------|--------------|
| `button.pilotsuite_sync_zones` | Zonen synchronisieren |
| `button.pilotsuite_clear_cache` | Cache leeren |
| `button.pilotsuite_generate_proposals` | Vorschläge generieren |

### Selects

| Entity | Beschreibung |
|--------|--------------|
| `select.pilotsuite_living_light_scene` | Licht-Szene Wohnzimmer |
| `select.pilotsuite_living_climate_mode` | Klima-Modus Wohnzimmer |

---

## 🏷️ TAG SYSTEM

### Automatische Entity-Zuordnung

Tags ermögichen automatische Zone→Entity Zuordnung:

```yaml
# Domain Tags (9 Kategorien)
domain:light      # light.*, switch.light
domain:climate    # climate.*, sensor.temperature
domain:motion     # binary_sensor.motion, binary_sensor.presence
domain:media      # media_player.*
domain:energy     # sensor.power, sensor.energy
domain:humidity   # sensor.humidity
domain:camera     # camera.*
domain:cover      # cover.*
domain:lock       # lock.*

# Zone Tags (10 Zonen)
zone_living       # Wohnzimmer
zone_bath         # Bad
zone_kitchen      # Küche
zone_office       # Büro
zone_bedroom      # Schlafzimmer
zone_hallway      # Flur
zone_room_mira    # Kinderzimmer Mira
zone_room_paul    # Kinderzimmer Paul
zone_terrace      # Terrasse
zone_outside      # Außen

# Status Tags (3)
auto_assign       # Automatisch zuweisen
needs_review      # Manuelle Prüfung nötig
manual_override   # Manuell überschrieben
```

### Beispiel

```yaml
entity:
  entity_id: light.wohnzimmer_haupt
  tags:
    - domain:light
    - zone_living
    - auto_assign
  
  # Ergebnis:
  assigned_zone: living
  enabled_modules: [light]
  automations: [motion→light, sunset→light]
```

---

## 🔗 API-ENDPOINTS (via Core)

### Unified Habitus Store

```
GET  /api/v1/habitus              — Overview + Stats
GET  /api/v1/habitus/patterns     — Patterns (filterbar by zone)
POST /api/v1/habitus/feedback     — Feedback geben
GET  /api/v1/habitus/preferences  — Nutzer-Präferenzen (zone-scoped)
```

### Chat (Externer Zugang)

```
POST /api/v1/chat/sessions                 — Session erstellen
POST /api/v1/chat/sessions/<id>/messages   — Nachricht senden
POST /api/v1/chat/webhooks/telegram        — Telegram Webhook
POST /api/v1/chat/webhooks/rest            — REST Webhook
```

### Learning Visualization

```
GET  /api/v1/learning/overview    — Intelligence Score
GET  /api/v1/learning/patterns    — Patterns (visualisiert)
GET  /api/v1/learning/progress    — Fortschritt pro Zone/Modul
POST /api/v1/learning/correct     — Manuelle Korrektur
```

### End-to-End Wiring

```
POST /api/v1/hub/zones/sync             — Bidirectional Sync
PUT  /api/v1/hub/zones/<id>/modules/<m> — Module State Sync
PUT  /api/v1/hub/zones/tags/<entity>    — Entity Tags Sync
```

---

## 🎴 LOVELACE CARDS (Vorbereitet)

### Installation

```yaml
# configuration.yaml
lovelace:
  mode: yaml
  resources:
    - url: /hacsfiles/copilot_ha/styx-modules-card.js
      type: module
    - url: /hacsfiles/copilot_ha/styx-zone-card.js
      type: module
    - url: /hacsfiles/copilot_ha/styx-learning-card.js
      type: module
    - url: /hacsfiles/copilot_ha/styx-chat-card.js
      type: module
```

### Cards

#### 1. Modules Card

```yaml
type: custom:styx-modules-card
title: PilotSuite Modules
show_state: true  # active/learning/off
```

#### 2. Zone Card

```yaml
type: custom:styx-zone-card
title: Habituszonen
show_entities: true
show_modules: true
show_dependencies: true  # Module Dependencies
```

#### 3. Learning Card

```yaml
type: custom:styx-learning-card
title: Lern-Fortschritt
show_intelligence_score: true
show_patterns: true
show_zone_progress: true  # Pro Zone
```

#### 4. Chat Card

```yaml
type: custom:styx-chat-card
title: PilotSuite Chat
session_id: default
character: styx
```

---

## 📈 INTELLIGENCE SCORE

### Berechnung

```python
score = pattern_score + active_score + acceptance_score

pattern_score = min(total_patterns * 2, 40)     # Max 40
active_score = min(active_patterns * 5, 30)     # Max 30
acceptance_score = min(acceptance_rate * 30, 30) # Max 30

Level:
- 80-100: Expert
- 60-79:  Advanced
- 40-59:  Intermediate
- 20-39:  Beginner
- 0-19:   Novice
```

### Anzeige in HA

```yaml
type: gauge
entity: sensor.pilotsuite_intelligence_score
name: Intelligence Score
min: 0
max: 100
```

---

## 🎉 RELEASE PREP v15.4.0

**Datum:** 2026-04-05
**Geplanter Tag:** v15.4.0
**Status:** 🟡 Repo-Stand konsolidiert — separater Tag-/Release-/Asset-Schritt noch ausstehend

**Konsolidierter Stand:**
- ✅ main-basierte HA-Wahrheit als Basis festgezogen
- ✅ Versionsparität auf den führenden Release-Surfaces hergestellt
- ✅ README-/CHANGELOG-Drift bereinigt
- ✅ HACS-Dateiname-Vertrag bleibt `pilotsuite-styx-ha.zip`
- ⛔ Noch kein Tag gesetzt
- ⛔ Noch kein GitHub-Release publiziert
- ⛔ Noch kein HACS-usable-Claim

---

## 🔗 LINKS

| Resource | URL |
|----------|-----|
| **GitHub** | https://github.com/GreenhillEfka/pilotsuite-styx-ha |
| **Core Repo** | https://github.com/GreenhillEfka/pilotsuite-styx-core |
| **Vision** | https://github.com/GreenhillEfka/pilotsuite-styx-core/blob/main/docs/VISION.md |
| **Architektur** | https://github.com/GreenhillEfka/pilotsuite-styx-core/blob/main/README.md |
| **Discord** | https://discord.com/invite/clawd |

---

**🚀 PILOTSUITE — DAS LEBENDIGE, LERNENDE, VERKABELTE DACHSYSTEM.**
# trigger CI
