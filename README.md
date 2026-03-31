# PilotSuite HACS Integration

[![Release](https://img.shields.io/github/v/release/GreenhillEfka/pilotsuite-styx-ha)](https://github.com/GreenhillEfka/pilotsuite-styx-ha/releases)

**PilotSuite HA Integration** — Die Home Assistant-Integration für PilotSuite Core. Stellt Entities, Dashboard-Cards und Config-Flow bereit.

**Aktuelle Version:** v15.2.10  
**Erfordert:** PilotSuite Core v15.2.93+

---

## Was ist PilotSuite HA?

PilotSuite HA ist die **Home Assistant-native Integration** für PilotSuite Core:

- **Entities** — Sensors, Buttons, Selects für alle Intelligence Modules
- **Dashboard Cards** — Lovelace Cards für Module, Zonen, Mood, Brain
- **Config Flow** — Einfache Einrichtung über Home Assistant UI
- **Event Forwarding** — HA Events → Core (state_changed)
- **Webhook Receiver** — Core Events → HA (mood, proposals, alerts)
- **Blueprints** — Vorkonfigurierte Automationen

---

## Installation

### Voraussetzungen

1. **Home Assistant** >= 2024.1.0
2. **HACS** installiert
3. **PilotSuite Core Add-on** installiert und laufend (v15.2.93+)

### Schritt 1: Core Add-on installieren

```
Home Assistant → Einstellungen → Add-ons → Add-on Store
→ ⋮ (Menü) → Repositories → URL hinzufügen:
   https://github.com/GreenhillEfka/pilotsuite-styx-core
→ PilotSuite Core installieren → Starten
```

### Schritt 2: HA Integration installieren (HACS)

```
HACS → Integrationen → ⋮ (Menü) → Benutzerdefinierte Repositories
→ Repository: https://github.com/GreenhillEfka/pilotsuite-styx-ha
→ Kategorie: Integration
→ PilotSuite installieren
→ Home Assistant NEU STARTEN
```

### Schritt 3: Integration konfigurieren

```
Einstellungen → Geräte & Dienste → Integration hinzufügen
→ PilotSuite suchen und auswählen
→ Config Flow folgt (Core wird auto-discovered)
→ Fertig
```

---

## Intelligence Modules (Slices 67-82)

### Presence Intelligence

**Entities:**
- `sensor.pilot_suite_presence_{zone}` — Präsenz-Status pro Zone
- `sensor.pilot_suite_presence_count` — Anzahl belegter Zonen
- `button.pilot_suite_presence_override_{zone}_{state}` — Präsenz überschreiben
- `select.pilot_suite_presence_mode_{zone}` — Präsenz-Modus

**Dashboard Card:**
```yaml
type: custom:styx-modules-card
title: Presence Modules
```

### Light Intelligence

**Entities:**
- `sensor.pilot_suite_light_{zone}` — Licht-Status pro Zone
- `button.pilot_suite_light_scene_{zone}_{scene}` — Licht-Szene aktivieren
- `select.pilot_suite_light_scene_{zone}` — Licht-Szene auswählen

**Szenen:** relax, focus, movie, night, morning, party, reading

### Climate/HVAC

**Entities:**
- `sensor.pilot_suite_climate_{zone}` — Temperatur pro Zone
- `button.pilot_suite_climate_setpoint_{zone}_{temp}` — Temperatur setzen
- `select.pilot_suite_climate_mode_{zone}` — Klima-Modus

**Modi:** heat, cool, auto, eco, comfort, away  
**Temperaturen:** 18°C, 20°C, 22°C, 24°C

### Humidity Control

**Entities:**
- `sensor.pilot_suite_humidity_{zone}` — Luftfeuchtigkeit pro Zone
- Attribute: ventilation_active, mold_risk

### Energy Management

**Entities:**
- `sensor.pilot_suite_energy_forecast` — Energie-Prognose
- `button.pilot_suite_energy_optimize` — Optimierung starten

**Forecast:** 24h, 7d, current_price, optimization_potential

### Time of Day

**Entities:**
- `sensor.pilot_suite_time_of_day` — Aktuelle Tageszeit
- `select.pilot_suite_timeofday_mode` — Tageszeit-Modus

**Zeiten:** morning, day, evening, night, late_night

### Rules Engine

**Entities:**
- `sensor.pilot_suite_active_rules` — Anzahl aktiver Regeln
- `button.pilot_suite_rule_activate_{rule}` — Regel aktivieren
- `select.pilot_suite_rules_mode` — Rules-Modus

**Modi:** active, passive, learning, disabled

---

## Dashboard Cards

### Modules Card

Übersicht aller Intelligence Modules:

```yaml
type: custom:styx-modules-card
title: PilotSuite Modules
refresh_interval: 30
show_actions: true
show_status: true
```

### Zone Card

Zonen-Übersicht mit Mood, Präsenz, Modulen:

```yaml
type: custom:styx-zone-card
entity: sensor.pilot_suite_habitus_zones
show_mood: true
show_presence: true
show_modules: true
```

### Brain Card

Brain Graph Visualisierung:

```yaml
type: custom:styx-brain-card
entity: sensor.pilot_suite_brain_graph
show_nodes: true
show_edges: true
```

### Mood Card

Mood Engine Dashboard:

```yaml
type: custom:styx-mood-card
entity: sensor.pilot_suite_mood
show_dimensions: true
show_history: true
```

---

## API-Endpoints

PilotSuite HA stellt folgende Core-APIs bereit:

| Endpoint | Beschreibung |
|----------|-------------|
| `GET /api/v1/modules/list` | Alle Module auflisten |
| `GET /api/v1/modules/presence/zones` | Präsenz aller Zonen |
| `GET /api/v1/modules/light/zones` | Licht-Status aller Zonen |
| `POST /api/v1/modules/light/zone/{id}/scene` | Licht-Szene aktivieren |
| `GET /api/v1/modules/climate/zones` | Klima-Status aller Zonen |
| `POST /api/v1/modules/climate/zone/{id}/setpoint` | Temperatur setzen |
| `GET /api/v1/modules/humidity/zones` | Luftfeuchtigkeit aller Zonen |
| `GET /api/v1/modules/energy/forecast` | Energie-Prognose |
| `GET /api/v1/modules/timeofday/current` | Aktuelle Tageszeit |
| `GET /api/v1/modules/rules/list` | Alle Regeln |

---

## Konfiguration

### Config Flow Optionen

| Option | Beschreibung | Default |
|--------|-------------|---------|
| **Host** | Core Add-on Host | auto-discover |
| **Port** | Core Add-on Port | 8909 |
| **Token** | API Auth Token | auto-fetch |
| **Modules Enabled** | Module aktivieren | alle |
| **Auto-Create Zones** | Zonen aus HA Areas | true |

### YAML-Konfiguration (optional)

```yaml
copilot_ha:
  host: homeassistant.local
  port: 8909
  token: !secret pilotsuite_token
  modules:
    - presence
    - light
    - climate
    - humidity
    - energy
    - timeofday
    - rules
```

---

## Entities Übersicht

### Sensors (Beispiele)

| Entity | Beschreibung |
|--------|-------------|
| `sensor.pilot_suite_presence_count` | Belegte Zonen |
| `sensor.pilot_suite_light_wohnzimmer` | Licht Wohnzimmer |
| `sensor.pilot_suite_climate_bad` | Klima Bad |
| `sensor.pilot_suite_humidity_kuche` | Luftfeuchtigkeit Küche |
| `sensor.pilot_suite_energy_forecast` | Energie-Prognose |
| `sensor.pilot_suite_time_of_day` | Tageszeit |
| `sensor.pilot_suite_active_rules` | Aktive Regeln |

### Buttons (Beispiele)

| Entity | Beschreibung |
|--------|-------------|
| `button.pilot_suite_light_scene_wohnzimmer_relax` | Szene Relax |
| `button.pilot_suite_climate_setpoint_bad_22` | 22°C Bad |
| `button.pilot_suite_rule_activate_movie_night` | Regel aktivieren |

### Selects (Beispiele)

| Entity | Beschreibung |
|--------|-------------|
| `select.pilot_suite_light_scene_wohnzimmer` | Szene auswählen |
| `select.pilot_suite_climate_mode_wohnzimmer` | Klima-Modus |
| `select.pilot_suite_presence_mode_wohnzimmer` | Präsenz-Modus |

---

## Troubleshooting

### Core wird nicht gefunden

```
1. Core Add-on läuft? → Add-ons → PilotSuite Core → Starten
2. Port 8909 erreichbar? → http://homeassistant.local:8909/health
3. Token korrekt? → Einstellungen → Geräte & Dienste → PilotSuite → Configure
```

### Entities fehlen

```
1. Integration neu laden → Einstellungen → Geräte & Dienste → PilotSuite → Reload
2. HA neu starten
3. Logs prüfen → Einstellungen → System → Logs
```

### Dashboard Cards laden nicht

```
1. Browser-Cache leeren (Strg+Shift+R)
2. Lovelace Resources prüfen → /config/lovelace/resources
3. Card-URL: /local/pilotsuite/www/styx-modules-card.js
```

---

## Links

| Resource | URL |
|----------|-----|
| **GitHub (HA)** | https://github.com/GreenhillEfka/pilotsuite-styx-ha |
| **GitHub (Core)** | https://github.com/GreenhillEfka/pilotsuite-styx-core |
| **Issues** | https://github.com/GreenhillEfka/pilotsuite-styx-ha/issues |
| **Docs** | https://github.com/GreenhillEfka/pilotsuite-styx-ha/tree/main/docs |

---

**PilotSuite HA Integration — v15.2.10 (2026-03-31)**
