# PilotSuite Styx — Home Assistant Integration

**Version:** 15.3.0  
**Status:** ✅ Life-Long-Learning Dachsystem

---

## 🎯 VISION

**"Ein SmartHome, das CLEVERER ist als sein Nutzer"**

Diese HA-Integration verbindet PilotSuite Core mit Home Assistant:
- **Zone Sync** — Core ↔ HA bidirektional
- **Entity Tags** — Automatische Zone-Zuordnung
- **Module Config** — active/learning/off pro Zone
- **Chat Interface** — Lovelace Card für PilotSuite Chat
- **Learning Viz** — Zeigt was System lernt

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

## 🔗 LOVELACE CARDS

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
```

### Cards

#### 1. Modules Card

```yaml
type: custom:styx-modules-card
title: PilotSuite Modules
show_state: true
```

#### 2. Zone Card

```yaml
type: custom:styx-zone-card
title: Habituszonen
show_entities: true
show_modules: true
```

#### 3. Learning Card

```yaml
type: custom:styx-learning-card
title: Lern-Fortschritt
show_intelligence_score: true
show_patterns: true
```

#### 4. Chat Card

```yaml
type: custom:styx-chat-card
title: PilotSuite Chat
session_id: default
character: styx
```

---

## 🏷️ TAG SYSTEM

### Automatische Entity-Zuordnung

Tags ermögichen automatische Zone→Entity Zuordnung:

```yaml
# Domain Tags
domain:light      # light.*, switch.light
domain:climate    # climate.*, sensor.temperature
domain:motion     # binary_sensor.motion, binary_sensor.presence
domain:media      # media_player.*
domain:energy     # sensor.power, sensor.energy

# Zone Tags
zone_living       # Wohnzimmer
zone_bath         # Bad
zone_kitchen      # Küche
zone_office       # Büro
zone_bedroom      # Schlafzimmer

# Status Tags
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
```

---

## 🔧 SERVICES

### `copilot_ha.sync_zones`

Synchronisiert Zonen zwischen Core und HA.

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

Gibt Feedback für ein Pattern.

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
| `sensor.pilotsuite_patterns_learned` | Gelernte Patterns |
| `sensor.pilotsuite_active_automations` | Aktive Automatisierungen |
| `sensor.pilotsuite_mood_state` | Aktuelle Stimmung |

### Buttons

| Entity | Beschreibung |
|--------|--------------|
| `button.pilotsuite_sync_zones` | Zonen synchronisieren |
| `button.pilotsuite_clear_cache` | Cache leeren |

### Selects

| Entity | Beschreibung |
|--------|--------------|
| `select.pilotsuite_living_light_scene` | Licht-Szene Wohnzimmer |
| `select.pilotsuite_living_climate_mode` | Klima-Modus Wohnzimmer |

---

## 🔗 API-ENDPOINTS (via Core)

| Endpoint | Beschreibung |
|----------|--------------|
| `/api/v1/habitus` | Life-Long-Learning API |
| `/api/v1/chat` | Chat API (Telegram, WhatsApp, REST) |
| `/api/v1/learning` | Learning Visualization |
| `/api/v1/backend` | Backend UI (10 Tabs) |
| `/api/v1/neurons` | Neurons API (3 Layers) |
| `/api/v1/hub/zones` | Zone Sync API |

---

## 🎉 RELEASE v15.3.0

**Datum:** 2026-04-01  
**Tag:** v15.3.0  
**Status:** ✅ READY FOR PRODUCTION

**Key Features:**
- ✅ Zone Sync (Core ↔ HA bidirektional)
- ✅ Tag System (automatische Entity-Zuordnung)
- ✅ Module Config (active/learning/off)
- ✅ Lovelace Cards (Modules, Zones, Learning, Chat)
- ✅ Services (sync_zones, set_module_state, add_feedback)

---

## 🔗 LINKS

| Resource | URL |
|----------|-----|
| **GitHub** | https://github.com/GreenhillEfka/pilotsuite-styx-ha |
| **Core Repo** | https://github.com/GreenhillEfka/pilotsuite-styx-core |
| **Vision** | https://github.com/GreenhillEfka/pilotsuite-styx-core/blob/main/docs/VISION.md |
| **Discord** | https://discord.com/invite/clawd |

---

**🚀 PILOTSUITE — DAS DACHSYSTEM.**
