# Zone Cards Implementation

## Übersicht

Zone-Cards mit Live-Daten für das PilotSuite Styx Dashboard. Jede Zone zeigt:
- Temperatur, Luftfeuchtigkeit, Licht-Status, Bewegung
- Live-Updates via WebSocket (alle 5s)
- Mini-Chart (24h Verlauf) mit D3.js Sparklines
- Quick-Actions: Licht an/aus, Szene aktivieren
- Alert-Badges bei Problemen

## Erstellte Dateien

### 1. Widget Backend: `widgets/zone_summary.py`
- Flask Blueprint mit REST API Endpunkten
- WebSocket Event-Handler für Live-Updates
- Zone-Konfiguration mit Home Assistant Entity-Mappings
- Simulierte Daten (für Demo) mit realistischer Historie
- Alert-Erkennung basierend auf Schwellwerten

**API Endpunkte:**
- `GET /widget/zone_summary/api` - Alle Zonen-Daten
- `GET /widget/zone_summary/api/<zone_id>` - Detail-Daten einer Zone
- `GET /widget/zone_summary/api/config` - Zone-Konfiguration

**WebSocket Events:**
- `connect` / `disconnect` - Verbindung-Status
- `request_zones` - Alle Zonen anfordern
- `zone_data` - Zone-Daten Broadcast
- `zone_update` - Einzelne Zone Update
- `light_control` - Licht steuern
- `scene_activate` - Szene aktivieren

### 2. Zone Card Template: `templates/zone_card.html`
- Material Design Card Layout
- MDI Icons für alle Metriken
- Farb-Indikatoren (grün=OK, rot=Problem)
- Alert-Badges mit Animation
- Hover-Effekte für Details

### 3. JavaScript Client: `static/js/zone_cards.js`
- `ZoneCardsManager` Klasse für alle Zone-Interactions
- WebSocket Client mit Auto-Reconnect
- D3.js Sparklines für 24h-Charts
- Live-Updates alle 5 Sekunden
- Quick-Actions (Licht, Szene, Details)

### 4. Widget Template: `templates/widgets/zone_summary.html`
- Widget-Container mit Filter-Optionen
- Zone-Cards Grid Layout
- Connection-Status Anzeige
- Responsive Design

### 5. App Integration: `app.py`
- Blueprint Registration hinzugefügt
- Socket.IO Events registriert
- Zone-Simulation im Start-Prozess

## Features

### Pro Zone Metriken
- **Temperatur**: °C mit Status-Indikator
- **Luftfeuchtigkeit**: % mit Optimal-Bereich
- **Licht-Status**: An/Aus mit Helligkeit
- **Bewegung**: Aktiv/Inaktiv
- **Fenster**: Offen/Geschlossen (falls verfügbar)

### Live-Updates
- WebSocket Verbindung (`/zone_summary` namespace)
- Updates alle 5 Sekunden
- Auto-Reconnect bei Verbindungsverlust
- Debouncing für Performance

### Mini-Charts (Sparklines)
- D3.js basierte 24h-Verlaufscharts
- Toggle zwischen Temperatur und Luftfeuchtigkeit
- Gradient-Füllung für moderne Optik
- Current-Value-Dot am Ende

### Quick-Actions
- **Licht**: Toggle An/Aus mit visuellem Feedback
- **Szene**: Szene-Auswahl (Entspannen, Fokus, Lesen, Film, Nacht)
- **Details**: Zone-Detailansicht mit allen Werten

### Alert-System
- Temperatur zu niedrig/hoch
- Luftfeuchtigkeit zu niedrig/hoch
- Fenster offen
- Farb-kodierte Badges (warning=danger, info=blau)
- Alert-Details auf Hover

## Design

### Material Design Cards
- Shadows: `0 2px 8px rgba(0, 0, 0, 0.2)`
- Rounded Corners: `12px`
- Hover-Effekt: `translateY(-4px)` + Shadow-Boost
- Border-Left Indikator (grün=OK, rot=Problem)

### MDI Icons
- `mdi-thermometer` - Temperatur
- `mdi-water-percent` - Luftfeuchtigkeit
- `mdi-lightbulb` - Licht
- `mdi-motion-sensor` - Bewegung
- `mdi-window-open-variant` - Fenster
- `mdi-alert` - Warnungen

### Farb-Indikatoren
- **Grün (#22c55e)**: OK, Optimal, Comfortable
- **Gelb (#f59e0b)**: Warning, Moderat
- **Rot (#ef444e)**: Danger, Zu hoch/niedrig
- **Blau (#2563eb)**: Info, Kalt

## Integration ins Dashboard

### In index.html einfügen:
```html
<div id="page-zones" class="page">
    <div class="page-header">
        <h2>Zones</h2>
        <p>Live zone monitoring</p>
    </div>
    {% include 'widgets/zone_summary.html' %}
</div>
```

### Navigation hinzufügen:
```html
<li class="nav-item">
    <a href="#zones" data-page="zones">
        <span class="icon">🏠</span>
        <span class="label">Zones</span>
    </a>
</li>
```

### D3.js einbinden (wird automatisch geladen):
```html
<script src="https://d3js.org/d3.v7.min.js"></script>
```

## Testen

### Widget direkt aufrufen:
```
http://localhost:8766/widget/zone_summary/
```

### API testen:
```bash
curl http://localhost:8766/widget/zone_summary/api
curl http://localhost:8766/widget/zone_summary/api/living_room
```

### Dashboard starten:
```bash
cd /config/.openclaw/workspace/pilotsuite-styx-core/dashboard
python3 app.py
```

## Home Assistant Integration

Für echte HA-Daten muss `zone_summary.py` angepasst werden:

1. **HA API Client hinzufügen** (siehe `sensor_overview.py` für Beispiel)
2. **Entity-Mappings** in `ZONE_CONFIG` mit echten Entity-IDs füllen
3. **WebSocket Subscription** für HA State-Updates
4. **Service-Calls** für Licht-Steuerung und Szenen

Beispiel HA API Call:
```python
import requests

HA_URL = "http://homeassistant:8123"
HA_TOKEN = "YOUR_TOKEN"

def get_ha_state(entity_id):
    headers = {"Authorization": f"Bearer {HA_TOKEN}"}
    resp = requests.get(f"{HA_URL}/api/states/{entity_id}", headers=headers)
    return resp.json()
```

## Performance

- **Update-Intervall**: 5s (simuliert), 500ms Batch-Interval für andere Widgets
- **D3.js Charts**: Client-side Rendering, nur bei Daten-Änderung
- **WebSocket**: Namespace-isoliert (`/zone_summary`)
- **History**: 288 Punkte (24h bei 5min-Intervallen)
