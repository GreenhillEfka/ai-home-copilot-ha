# Zone-Editor UX Best Practices — Recherche Report

**Datum:** 2026-03-01  
**Agent:** @perplexya  
**Aufgabe:** UX-Recherche für PilotSuite Zone-Editor

---

## 📋 Zusammenfassung

Die Recherche ergab, dass moderne Smart-Home-Dashboards (insbesondere Home Assistant) auf **modulare Sections**, **Drag&Drop-Interaktionen** und **kontextabhängige Entity-Filter** setzen. Erfolgreiche Zone-Editoren gruppieren Entities visuell klar, bieten intuitive Add/Remove-Mechanismen und verwenden farbcodierte Tags zur schnellen Orientierung. Die PilotSuite sollte diese Patterns adaptieren, aber um **auto-tag-Vorschläge** (regelbasiert) erweitern, um die UX von der Konkurrenz abzuheben.

---

## 🔑 Key-Findings

### Home Assistant Dashboard Patterns
- **Sections View** (seit 2024.3): Native Unterstützung für gruppierte Karten mit automatischem Grid-Layout
- **Drag&Drop**: Cards und Sections können per Drag&Drop neu angeordnet werden (Z-Grid Pattern)
- **Responsive Design**: Sections behalten relative Positionen bei Screen-Size-Änderungen bei
- **Header + Badges**: Jede View kann Titel, Badges und konditionale Sichtbarkeit haben

### Entity-Management UIs
- **Entities Card**: Standard-UI für Entity-Listen mit folgenden Features:
  - Add/Remove über Plus/Trash-Icons
  - Custom Entity-Objects mit name, icon, secondary_info
  - Special Rows: Button, Buttons, Attribute, Divider, Section, Weblink
  - Tap/Hold/Double-Tap Actions konfigurierbar
- **Entity Filter Badge**: Zeigt Entities nur bei bestimmten States (z.B. "Lichter an")
- **Konditionale Sichtbarkeit**: Sections/Badges können user- oder state-basiert ein-/ausgeblendet werden

### Tag-Visualisierung
- **Badges**: Kleine Widgets oben im Panel, zeigen Entity-State mit Icon + Farbe
- **Farbcodierung**: 
  - `state`-basiert (default)
  - `domain`-basiert (light=gelb, switch=blau, etc.)
  - Custom Hex-Codes oder Color-Tokens möglich
- **Entity Badge Config**:
  ```yaml
  type: entity
  entity: light.living_room
  color: state  # oder Hex "#FF5733"
  show_icon: true
  show_state: true
  ```

### Auto-Tag-Vorschläge
- **Home Assistant**: Keine ML-basierten Vorschläge, aber regelbasierte Filter:
  - `state_filter`: Zeige Entities nur wenn State = X
  - `conditions`: Numeric-State, Screen-Size, User-Rolle
- **Best Practice**: Tags sollten aus Entity-Metadaten abgeleitet werden:
  - `device_class` → Auto-Tag (z.B. "temperature", "motion")
  - `area` → Raum-Zuordnung (z.B. "living-room", "kitchen")
  - `domain` → Geräte-Typ (z.B. "light", "switch", "sensor")

---

## 🎨 UI-Beispiele

### Beispiel 1: Home Assistant Sections View (Drag&Drop)
```yaml
# Sections View mit Grid-Layout
type: sections
max_columns: 3
dense_section_placement: true
sections:
  - title: "Wohnzimmer"
    cards:
      - type: entities
        entities:
          - light.living_room_main
          - light.living_room_lamp
      - type: thermostat
        entity: climate.living_room
  - title: "Küche"
    cards:
      - type: entities
        entities:
          - switch.kitchen_coffee
          - sensor.kitchen_temperature
```
**Beschreibung:** Sections sind visuell klar getrennt, Cards können per Drag&Drop zwischen Sections verschoben werden. Dense Placement füllt Lücken automatisch.

### Beispiel 2: Entity Filter Badge (Farbcodierung)
```yaml
# Badge zeigt nur aktive Lichter
type: entity-filter
entities:
  - light.living_room
  - light.kitchen
  - light.bedroom
conditions:
  - condition: state
    state: "on"
# Farbe: Gelb für Lichter im State "on"
```
**Beschreibung:** Badge erscheint nur wenn Bedingung erfüllt (Licht an). Farbe domänenbasiert (light=gelb).

### Beispiel 3: Custom Entity Row mit Buttons
```yaml
type: entities
title: "Szenen-Steuerung"
entities:
  - type: button
    name: "Filmabend"
    icon: mdi:movie
    tap_action:
      action: call-service
      service: scene.turn_on
      target:
        entity_id: scene.movie_night
  - type: button
    name: "Lesen"
    icon: mdi:book-open-page-variant
    tap_action:
      action: call-service
      service: scene.turn_on
      target:
        entity_id: scene.reading
  - type: divider
  - entity: input_boolean.guest_mode
    name: "Gast-Modus"
    secondary_info: last-changed
```
**Beschreibung:** Button-Rows für Schnellaktionen, Divider zur visuellen Trennung, Entity mit Timestamp.

### Beispiel 4: Konditionale Section-Sichtbarkeit
```yaml
type: sections
sections:
  - title: "Gäste-Bereich"
    visibility:
      - condition: user
        users:
          - guest_user_id
      - condition: state
        entity: input_boolean.guest_mode
        state: "on"
    cards:
      - type: entities
        entities:
          - light.guest_room
          - lock.front_door
```
**Beschreibung:** Section nur sichtbar für Gast-User ODER wenn Gast-Modus aktiv ist.

### Beispiel 5: Tag-Legende mit Color-Tokens
```yaml
# Legende oben im Dashboard
type: markdown
content: |
  ### Legende
  - 🟡 Lichter (domain: light)
  - 🔵 Schalter (domain: switch)
  - 🟢 Sensoren (domain: sensor)
  - 🔴 Alarme (domain: alarm_control_panel)
```
**Beschreibung:** Markdown-Card als Legende für farbcodierte Tags/Badges.

---

## 💡 UX-Empfehlungen für PilotSuite Zone-Editor

### 1. **Zone-Struktur (Priorität: Hoch)**
- **Sections als Basis**: Jede Zone = eine Section mit Titel-Card
- **Max 3-4 Spalten**: Responsive Grid mit `max_columns: 3` für Mobile-First
- **Dense Placement**: Automatische Lückenfüllung aktivieren (optional deaktivierbar)

### 2. **Entity-Management (Priorität: Hoch)**
- **Add-Button**: Plus-Icon in jeder Zone öffnet Entity-Selector mit:
  - Suchfunktion
  - Filter nach Domain/Area/Device-Class
  - Preview des Entity-States
- **Remove-Button**: Trash-Icon pro Entity mit Undo (5s Toast)
- **Drag&Drop**: Entities zwischen Zonen verschiebbar (langes Drücken + Ziehen)

### 3. **Tag-System (Priorität: Mittel)**
- **Auto-Tags aus Metadaten**:
  ```javascript
  // Regelbasierte Tag-Generierung
  const autoTags = {
    domain: entity.domain,           // "light", "switch"
    device_class: entity.device_class, // "temperature", "motion"
    area: entity.area,               // "living-room", "kitchen"
  }
  ```
- **Farbcodierung**:
  - Domain-basiert (HA-Standard adaptieren)
  - Custom Colors pro Zone konfigurierbar
- **Tag-Legende**: Fixierte Legende oben im Editor (ausklappbar)

### 4. **Auto-Tag-Vorschläge (Priorität: Niedrig, USP!)**
- **Regelbasierte Vorschläge**:
  - "Alle Lichter im Wohnzimmer → Tag: 'Abend-Stimmung'"
  - "Alle Temperatursensoren → Tag: 'Klima'"
  - "Alle Bewegungsmelder → Tag: 'Sicherheit'"
- **ML-Zukunft**: Nutzerakzeptanz tracken (welche Tags werden angenommen?) → Modell trainieren

### 5. **Visuelle Hierarchie**
```
┌─────────────────────────────────────────────┐
│  [📍 Zone: Wohnzimmer]          [+ Add] [⚙️] │
├─────────────────────────────────────────────┤
│  🟡 light.main      [🗑️]  ← Drag Handle     │
│  🟡 light.lamp      [🗑️]                    │
│  🔵 switch.tv       [🗑️]                    │
│  🟢 sensor.temp     [🗑️]                    │
└─────────────────────────────────────────────┘
```
- **Zone-Header**: Titel + Add-Button + Settings
- **Entity-Row**: Icon (farbcodiert) + Name + Remove-Button + Drag-Handle
- **Hover-Effekte**: Leichte Animation bei Drag-Start

### 6. **Konditionale Features**
- **Expert-Mode**: Toggle für erweiterte Config (YAML-Editor, Custom Actions)
- **User-Rollen**: 
  - Admin: Volle Bearbeitung
  - User: Nur Entity-Reihenfolge ändern
  - Guest: Read-Only

---

## 📚 Quellen für Deep-Dive

1. **Home Assistant Dashboards Docs**  
   https://www.home-assistant.io/dashboards/

2. **Sections View (Drag&Drop)**  
   https://www.home-assistant.io/dashboards/sections/

3. **Entities Card Konfiguration**  
   https://www.home-assistant.io/dashboards/entities/

4. **Badges & Entity-Filter**  
   https://www.home-assistant.io/dashboards/badges/

5. **Project Grace Blog (Design-Entscheidungen)**  
   https://www.home-assistant.io/blog/2024/03/04/dashboard-chapter-1/

6. **Custom Cards GitHub**  
   https://github.com/custom-cards

7. **Home Assistant Demo**  
   https://demo.home-assistant.io

---

## ✅ Nächste Schritte

1. **Wireframes erstellen**: Zone-Editor Layout skizzieren (Figma/Paper)
2. **Tech-Spike**: Drag&Drop-Bibliothek evaluieren (dnd-kit, react-beautiful-dnd)
3. **Entity-Selector Design**: Modal/Popover für Add-Entity UX
4. **Tag-System Prototyp**: Regelbasierte Auto-Tags implementieren
5. **User-Testing**: 3-5 Nutzer den Editor testen lassen (Time-on-Task messen)

---

**Report erstellt von @perplexya** ✨  
**Recherche-Dauer:** ~10 Minuten  
**Status:** ✅ Abgeschlossen
