# Styx Dashboard Design Proposal

**Erstellt:** 1. März 2026  
**Autor:** @cowdya (Subagent Research)  
**Status:** 🟡 Design-Phase  
**Referenz:** UX_FRONTEND_PRIORITIES.md

---

## 1. Executive Summary

**Empfehlung:** **Custom Panel (Lit + HA Lovelace-Cards)** als Hybrid-Ansatz

| Kriterium | Empfehlung | Begründung |
|-----------|------------|------------|
| **Haupt-Dashboard** | Custom Panel | Volle Kontrolle über Layout, Styx-spezifische Komponenten |
| **Zone-Editor** | Lovelace Cards | Wiederverwendung bestehender HA UI-Komponenten |
| **Neuronen-Visualisierung** | Custom Canvas/SVG | Einzigartige Darstellung, nicht als Lovelace-Card verfügbar |
| **Chat-Interface** | Custom Panel | Komplexe Interaktion, History, Tool-Calling |

---

## 2. Lovelace Dashboard vs. Custom Panel

### 2.1 Vergleich

| Feature | Lovelace Dashboard | Custom Panel |
|---------|-------------------|--------------|
| **Entwicklungsaufwand** | Niedrig (YAML + existierende Cards) | Hoch (eigene Komponenten) |
| **Flexibilität** | Mittel (durch Cards limitiert) | Hoch (volle Kontrolle) |
| **Performance** | Sehr gut (optimiert) | Gut (abhängig von Implementation) |
| **Wartbarkeit** | Sehr gut (HA-Standard) | Mittel (eigener Code) |
| **Mobile Support** | Automatisch | Muss implementiert werden |
| **Theming** | Automatisch (HA Theme) | Manuell (CSS Variables) |
| **WebSocket Integration** | Eingebaut | Manuell (ha-websocket) |

### 2.2 Existing HA Panels & Erweiterungen

| Panel/Extension | Zweck | Relevanz für Styx |
|-----------------|-------|-------------------|
| **Kiosk Mode** | Vollbild, keine UI-Elemente | ⚠️ Nur für Display-Modus |
| **Browser Mod** | Browser-Integration, Popups | ✅ Nützlich für Modal-Dialoge |
| **Lovelace Card Mod** | Card-Modifikation | ✅ Für Zone-Cards |
| **Mini Graph Card** | Zeitreihen | ⚠️ Nicht für Neuronen |
| **ApexCharts Card** | Diagramme | ⚠️ Limitiert für Network-Graph |
| **Custom: Button Card** | Interaktive Buttons | ✅ Für Action-Buttons |
| **Custom: Markdown Card** | Text/HTML | ✅ Für Status-Texte |

### 2.3 Integration-Möglichkeiten

**Option A: Lovelace-Only (nicht empfohlen)**
```yaml
# dashboard-styx.yaml
views:
  - title: "Styx Brain"
    cards:
      - type: custom:apexcharts-card
        # Neuronen als Chart (limitiert)
      - type: markdown
        # Chat-History (statisch)
```
❌ **Problem:** Keine echte Interaktion, kein Live-Update, keine Tool-Calling-Visualisierung

**Option B: Custom Panel (empfohlen)**
```
/custom_components/styx/
├── panel.py              # Panel-Registrierung
├── www/
│   ├── styx-dashboard.js # Haupt-Anwendung (Lit)
│   ├── components/
│   │   ├── neuron-brain.js
│   │   ├── chat-interface.js
│   │   ├── recommendations.js
│   │   └── zone-editor.js
│   └── styles/
│       └── styx-theme.css
```

**Option C: Hybrid (beste Lösung)**
- Custom Panel für Styx-spezifische Komponenten (Neuronen, Chat, Recommendations)
- Lovelace-Cards für Zone-Übersicht und Entity-Status
- Iframe oder Shadow DOM für Integration

---

## 3. Neuronen-Visualisierung Design

### 3.1 Tech-Stack Empfehlung

| Komponente | Technologie | Begründung |
|------------|-------------|------------|
| **Rendering** | **SVG + D3.js** | Beste Balance aus Performance & Flexibilität |
| **Animation** | CSS Transitions + requestAnimationFrame | Smooth, GPU-beschleunigt |
| **Layout Engine** | D3 Force-Directed Graph | Automatische Neuronen-Positionierung |
| **Interaktion** | Lit + Pointer Events | Touch & Mouse Support |

**Warum nicht Canvas?**
- Canvas ist pixel-basiert, schlechte Accessibility
- SVG ist DOM-basiert → CSS Styling, Screen Reader, einfache Events
- Bei ~50-200 Neuronen ist SVG-Performance ausreichend

**Warum nicht Chart.js?**
- Chart.js ist für statistische Charts, nicht Network-Graphen
- D3 bietet mehr Kontrolle über Nodes & Edges

### 3.2 Visualisierungskonzept

```
┌─────────────────────────────────────────────────────────────┐
│  🧠 STYX BRAIN                              [Live ●]        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│         ┌─────┐                                             │
│         │ N1  │◄─── Confidence: 0.87                        │
│         │ 🔥  │     Feuer-Rate: 12/min                     │
│         └──┬──┘                                             │
│            │ active                                         │
│      ┌─────┴─────┐                                          │
│      │           │                                          │
│   ┌──▼──┐     ┌──▼──┐                                       │
│   │ N2  │     │ N3  │◄─── inactive (Cooldown)               │
│   │ ⚡  │     │ 💤  │                                       │
│   └─────┘     └─────┘                                       │
│                                                             │
│  Legend:                                                    │
│  🔥 active (feuert)    💤 inactive    ⚡ ready               │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  System Status: Mood: Comfort | Entities: 47 | Zones: 8    │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 Dargestellte Informationen

| Info | Visualisierung | Update-Frequenz |
|------|----------------|-----------------|
| **Neuron Status** | Icon + Farbe (🔥/💤/⚡) | Echtzeit (WebSocket) |
| **Feuer-Rate** | Tooltip / Side-Label | Alle 5 Sek |
| **Confidence** | Node-Opacity oder Ring | Pro Event |
| **Verbindungen** | Linien (aktiv = pulsierend) | Echtzeit |
| **Letztes Feuer** | Zeitstempel im Tooltip | Pro Event |

### 3.4 Live-Update Strategie

**WebSocket (empfohlen):**
```javascript
// Custom HA WebSocket Verbindung
const conn = createHassConnection();
conn.subscribeMessage("styx/neuron_event", (event) => {
  updateNeuron(event.neuron_id, event.status);
});
```

**Payload-Struktur:**
```json
{
  "event_type": "styx.neuron_fired",
  "data": {
    "neuron_id": "n1",
    "status": "active",
    "confidence": 0.87,
    "trigger_entity": "light.living_room",
    "timestamp": "2026-03-01T10:32:00Z"
  }
}
```

**Fallback: Polling (nur wenn WebSocket nicht verfügbar)**
- Interval: 2-5 Sekunden
- Endpoint: `/api/styx/neurons/status`

---

## 4. Chat-Interface Design

### 4.1 Layout-Konzept

```
┌─────────────────────────────────────────────────────────────┐
│  💬 STYX CHAT                                   [Clear]     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ [System] Styx gestartet                               │  │
│  │ 10:30                                                 │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ [User] Licht im Wohnzimmer an                         │  │
│  │ 10:31                                      [You]      │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ [Styx] Ich habe das Licht eingeschaltet.              │  │
│  │                                                       │  │
│  │  🔧 Tool: light.turn_on                               │  │
│  │  📍 Zone: living_room                                 │  │
│  │  💡 Entity: light.living_room                         │  │
│  │  ✅ Success                                           │  │
│  │ 10:31                                      [Styx]     │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ [User] ...                                          │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  [Type message...]                              [Send ●]    │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Komponenten

| Komponente | Beschreibung | Tech |
|------------|--------------|------|
| **Message List** | Scrollbare History, virtuelles Rendering | Lit + virtual-repeat |
| **Message Bubble** | User (rechts) / Styx (links) | CSS Grid |
| **Tool-Call Card** | Expandierbare Details | Lit Component |
| **Context Panel** | Entities/Zonen als Chips | HA Entity Chips |
| **Input Area** | Text + Voice (optional) | HA Voice Pipeline |

### 4.3 Context-Panel Design

```
┌─────────────────────────────────────────────────────────────┐
│  📍 CONTEXT                                                 │
├─────────────────────────────────────────────────────────────┤
│  Active Zone:                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 🛋️ Living   │  │ 🍳 Kitchen  │  │ 🛏️ Bedroom  │      │
│  │   Room       │  │              │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                             │
│  Relevant Entities:                                         │
│  💡 light.living_room  🌡️ sensor.temperature  🚪 binary_sensor.door │
│                                                             │
│  Recent Actions:                                            │
│  ✓ light.turn_on (10:31)                                   │
│  ✓ climate.set_temperature (10:28)                         │
│  ⚠ automation.trigger_failed (10:25)                       │
└─────────────────────────────────────────────────────────────┘
```

### 4.4 Tool-Calling Visualisierung

**Collapsed (Default):**
```
┌─────────────────────────────────────────────────────────────┐
│  🔧 light.turn_on                              [▼ Details]  │
│  ✅ Success                                                 │
└─────────────────────────────────────────────────────────────┘
```

**Expanded:**
```
┌─────────────────────────────────────────────────────────────┐
│  🔧 light.turn_on                              [▲ Close]    │
├─────────────────────────────────────────────────────────────┤
│  Entity: light.living_room                                  │
│  Zone: living_room                                          │
│  Parameters:                                                │
│    - brightness: 200                                        │
│    - color_temp: 3000                                       │
│  Execution Time: 45ms                                       │
│  Response: { "state": "on" }                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Handlungsempfehlungen Side-Panel

### 5.1 Layout-Optionen

| Layout | Vorteil | Nachteil | Empfehlung |
|--------|---------|----------|------------|
| **Liste** | Kompakt, viele Items | Wenig Kontext pro Item | ❌ |
| **Cards** | Visuell, guter Kontext | Platzintensiv | ✅ **Empfohlen** |
| **Accordion** | Sehr kompakt | Versteckt Info | ⚠️ Für Phase 2+ |

### 5.2 Card-Design

```
┌─────────────────────────────────────────────────────────────┐
│  💡 HANDLUNGSEMPFEHLUNGEN                       [Sort ▼]    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ ⚠️  HIGH PRIORITY                                      │  │
│  │                                                       │  │
│  │  📌 Automation "Nachtmodus" fehlerhaft               │  │
│  │                                                       │  │
│  │  Begründung: Trigger-Bedingung nie erfüllt (Sonne   │  │
│  │  untergang > 22:00, aber Sunset ist um 20:30)        │  │
│  │                                                       │  │
│  │  Auswirkung: Nachtmodus wird nie aktiviert            │  │
│  │                                                       │  │
│  │  Vorschlag: Bedingung auf sunset - 30min ändern      │  │
│  │                                                       │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │  │
│  │  │  🔧 Fix    │  │  ✏️ Edit   │  │  ❌ Ignore │  │  │
│  │  └──────────────┘  └──────────────┘  └────────────┘  │  │
│  │                                                       │  │
│  │  Confidence: 94% | Impact: Hoch | Dauer: 2 Min       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ 💚 MEDIUM PRIORITY                                     │  │
│  │                                                       │  │
│  │  📌 Energie sparen: Heizung runter wenn Fenster offen │  │
│  │                                                       │  │
│  │  Begründung: Fenster (binary_sensor.bedroom_window)  │  │
│  │  ist oft >10 Min offen bei aktiver Heizung          │  │
│  │                                                       │  │
│  │  Auswirkung: ~5% Energieeinsparung pro Monat         │  │
│  │                                                       │  │
│  │  Vorschlag: Neue Automation erstellen                │  │
│  │                                                       │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │  │
│  │  │  ✅ Create │  │  📋 Preview │  │  ❌ Ignore │  │  │
│  │  └──────────────┘  └──────────────┘  └────────────┘  │  │
│  │                                                       │  │
│  │  Confidence: 78% | Impact: Mittel | Dauer: 5 Min     │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 Sorting-Optionen

| Kriterium | Beschreibung | Use Case |
|-----------|--------------|----------|
| **Priority** | Kritische Fehler zuerst | Default |
| **Impact** | Größte Auswirkung zuerst | Energie-Optimierung |
| **Confidence** | Sicherste Vorschläge zuerst | Neue User |
| **Duration** | Schnellste Fixes zuerst | Quick Wins |

### 5.4 Action-Buttons

| Button | Action | Folge |
|--------|--------|-------|
| **🔧 Fix** | Auto-Repair | Automation wird korrigiert (mit Confirmation) |
| **✅ Create** | New Automation | Erstellt neue Automation aus Vorschlag |
| **✏️ Edit** | Open Editor | Öffnet HA Automation Editor mit Pre-Fill |
| **📋 Preview** | Show Diff | Zeigt Before/After der Änderung |
| **❌ Ignore** | Dismiss | Vorschlag wird archiviert (reversibel) |

---

## 6. Gesamt-Layout (Dashboard Tab)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  PILOTSUITE STYX                                        [User] [⚙️]     │
├─────────────────────────────────────────────────────────────────────────┤
│  [🧠 Brain]  [💬 Chat]  [📍 Zones]  [💡 Recommendations]  [⚙️ Settings] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────┐  ┌──────────────────────────────────┐  │
│  │                             │  │  ┌────────────────────────────┐  │  │
│  │     🧠 NEURONEN-BRAIN       │  │  │  💬 CHAT                   │  │  │
│  │                             │  │  │                            │  │  │
│  │     [D3 Force-Directed      │  │  │  [Message List]            │  │  │
│  │      Network Graph]         │  │  │                            │  │  │
│  │                             │  │  │  ┌────────────────────────┐ │  │  │
│  │                             │  │  │  │ [Type message...]     │ │  │  │
│  │                             │  │  │  └────────────────────────┘ │  │  │
│  │                             │  │  └────────────────────────────┘  │  │
│  │                             │  │                                  │  │
│  │  ┌───────────────────────┐  │  │  ┌────────────────────────────┐  │  │
│  │  │ SYSTEM STATUS         │  │  │  │ 📍 CONTEXT               │  │  │
│  │  │                       │  │  │  │                            │  │  │
│  │  │ Mood: Comfort 😊      │  │  │  │ [Zone Chips]              │  │  │
│  │  │ Confidence: 87%       │  │  │  │ [Entity List]             │  │  │
│  │  │ Active Neurons: 12    │  │  │  │ [Recent Actions]          │  │  │
│  │  │ Events/min: 45        │  │  │  └────────────────────────────┘  │  │
│  │  └───────────────────────┘  │  │                                  │  │
│  └─────────────────────────────┘  └──────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.1 Responsive Breakpoints

| Screen | Layout |
|--------|--------|
| **Desktop (>1200px)** | 2-Spalten: Brain (60%) + Chat (40%) |
| **Tablet (768-1200px)** | 1-Spalte, Brain oben, Chat unten |
| **Mobile (<768px)** | Tabs: Brain | Chat | Context | Recommendations |

---

## 7. Tech-Stack Zusammenfassung

| Schicht | Technologie | Begründung |
|---------|-------------|------------|
| **Framework** | **Lit 3.x** | Lightweight, HA-native, Web Components |
| **Styling** | CSS + HA Design Tokens | Konsistent mit HA UI |
| **Visualisierung** | **D3.js v7** | Beste Network-Graph-Unterstützung |
| **State Management** | Lit Reactive Properties | Einfach, ausreichend für Dashboard |
| **WebSocket** | HA `ha-websocket` | Native HA-Integration |
| **Build** | Vite + Rollup | Schnell, HA-kompatibel |
| **Testing** | Vitest + Playwright | Unit + E2E Tests |

### 7.1 Paket-Struktur

```json
{
  "name": "styx-dashboard",
  "version": "0.1.0",
  "dependencies": {
    "lit": "^3.0.0",
    "d3": "^7.8.0",
    "@material/web": "^1.0.0"
  },
  "devDependencies": {
    "vite": "^5.0.0",
    "vitest": "^1.0.0",
    "@playwright/test": "^1.40.0"
  }
}
```

---

## 8. Implementierungs-Plan (Schritt-für-Schritt)

### Phase 1: Foundation (Woche 1-2)

| Task | Beschreibung | Aufwand |
|------|--------------|---------|
| **1.1** | Custom Panel Skeleton erstellen | 2h |
| **1.2** | HA WebSocket Integration | 3h |
| **1.3** | Basic Routing (Tabs) | 2h |
| **1.4** | Theme Integration (HA Design Tokens) | 2h |
| **1.5** | Build Pipeline (Vite) | 2h |

**Deliverable:** Leeres Dashboard mit HA-Integration

### Phase 2: Neuronen-Visualisierung (Woche 3-4)

| Task | Beschreibung | Aufwand |
|------|--------------|---------|
| **2.1** | D3 Force-Directed Graph Setup | 4h |
| **2.2** | Neuron Node Component | 4h |
| **2.3** | Edge Rendering (aktiv/inaktiv) | 3h |
| **2.4** | WebSocket Event Handler | 3h |
| **2.5** | Tooltips & Interaktion | 3h |
| **2.6** | System Status Panel | 2h |

**Deliverable:** Live Neuronen-Brain mit Event-Updates

### Phase 3: Chat-Interface (Woche 5-6)

| Task | Beschreibung | Aufwand |
|------|--------------|---------|
| **3.1** | Message List Component | 4h |
| **3.2** | Message Bubble (User/Styx) | 3h |
| **3.3** | Tool-Call Card (expandierbar) | 4h |
| **3.4** | Context Panel (Entities/Zones) | 3h |
| **3.5** | Input Area + Send Logic | 3h |
| **3.6** | Chat History API Integration | 4h |

**Deliverable:** Vollwertiges Chat-Interface mit History

### Phase 4: Handlungsempfehlungen (Woche 7-8)

| Task | Beschreibung | Aufwand |
|------|--------------|---------|
| **4.1** | Recommendation Card Component | 4h |
| **4.2** | Sorting Logic (Priority/Impact) | 3h |
| **4.3** | Action Buttons (Fix/Create/Ignore) | 4h |
| **4.4** | Recommendations API Integration | 4h |
| **4.5** | Confirmation Dialogs | 2h |

**Deliverable:** Interaktives Recommendations Panel

### Phase 5: Zone-Editor (Woche 9-10)

| Task | Beschreibung | Aufwand |
|------|--------------|---------|
| **5.1** | Zone List Component | 3h |
| **5.2** | Zone Editor (Drag & Drop) | 6h |
| **5.3** | Tag Selection UI | 4h |
| **5.4** | Entity Assignment | 4h |
| **5.5** | Save/Cancel Logic | 2h |

**Deliverable:** Vollwertiger Zone-Editor

### Phase 6: Polish & Testing (Woche 11-12)

| Task | Beschreibung | Aufwand |
|------|--------------|---------|
| **6.1** | Responsive Design (Mobile/Tablet) | 4h |
| **6.2** | Accessibility (Screen Reader, Keyboard) | 4h |
| **6.3** | Performance Optimization | 4h |
| **6.4** | Unit Tests (Vitest) | 6h |
| **6.5** | E2E Tests (Playwright) | 6h |
| **6.6** | Documentation | 4h |

**Deliverable:** Production-Ready Dashboard

---

## 9. Risiken & Mitigation

| Risiko | Impact | Wahrscheinlichkeit | Mitigation |
|--------|--------|-------------------|------------|
| **D3 Performance bei vielen Neuronen** | Mittel | Niedrig | Virtual Rendering, Clustering |
| **WebSocket Disconnects** | Hoch | Mittel | Auto-Reconnect, Fallback Polling |
| **Mobile UX komplex** | Mittel | Hoch | Early Testing, Progressive Enhancement |
| **HA API Changes** | Hoch | Niedrig | Version Pinning, Abstraction Layer |

---

## 10. Nächste Schritte

1. **@styx:** Backend API Endpoints bereitstellen (`/api/styx/neurons`, `/api/styx/recommendations`)
2. **@cowdya:** Custom Panel Skeleton implementieren (Phase 1)
3. **@groky:** UX-Review nach Phase 2 (Neuronen-Brain Demo)
4. **@clawdya:** Integration in PilotSuite Release-Plan

---

## Anhang A: ASCII Mockups

### A.1 Neuronen-Brain (Detail)

```
                    ┌─────────┐
                    │  N1     │
                    │  🔥 0.9 │
                    └────┬────┘
                         │ ════════════ (active, high confidence)
              ┌──────────┼──────────┐
              │          │          │
         ┌────▼────┐ ┌───▼───┐ ┌────▼────┐
         │  N2     │ │  N4   │ │  N5     │
         │  ⚡ 0.7 │ │  💤   │ │  🔥 0.8 │
         └────┬────┘ └───────┘ └────┬────┘
              │                     │
              │ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ │ (inactive, low confidence)
              │                     │
         ┌────▼─────────────────────▼────┐
         │           N3                  │
         │           💤 (cooldown)       │
         └───────────────────────────────┘

Legend:
  🔥 = active (feuert gerade)
  ⚡ = ready (kann feuern)
  💤 = inactive (Cooldown oder nicht relevant)
  
  Linien-Stärke = Connection-Weight
  Linien-Pulsieren = Recent Activation
```

### A.2 Chat mit Tool-Call

```
╔═══════════════════════════════════════════════════════════╗
║  💬 STYX CHAT                                  [🗑️ Clear] ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  ╭─────────────────────────────────────────────────────╮  ║
║  │ [System] Styx Core verbunden                        │  ║
║  │ 10:30                                               │  ║
║  ╰─────────────────────────────────────────────────────╯  ║
║                                                           ║
║  ╭─────────────────────────────────────────────────────╮  ║
║  │ Mach das Licht gemütlicher                          │  ║
║  │ 10:31                                      [You]    │  ║
║  ╰─────────────────────────────────────────────────────╯  ║
║                                                           ║
║  ╭─────────────────────────────────────────────────────╮  ║
║  │ Ich mache das Licht gemütlicher im Wohnzimmer.      │  ║
║  │                                                     │  ║
║  │  ╭───────────────────────────────────────────────╮  │  ║
║  │  │ 🔧 light.turn_on                   [▼]       │  │  ║
║  │  │ ✅ Success                                    │  │  ║
║  │  ╰───────────────────────────────────────────────╯  │  ║
║  │                                                     │  ║
║  │  ╭───────────────────────────────────────────────╮  │  ║
║  │  │ 🔧 light.turn_on                   [▼]       │  │  ║
║  │  │ ✅ Success                                    │  │  ║
║  │  ╰───────────────────────────────────────────────╯  │  ║
║  │                                                     │  ║
║  │ Das Licht ist jetzt wärmer (2700K) und gedimmt.    │  ║
║  │ 10:31                                    [Styx]    │  ║
║  ╰─────────────────────────────────────────────────────╯  ║
║                                                           ║
╠═══════════════════════════════════════════════════════════╣
║  ┌─────────────────────────────────────────────────────┐  ║
║  │ 💡 Tippe deine Nachricht...              [🎤] [➤]   │  ║
║  └─────────────────────────────────────────────────────┘  ║
╚═══════════════════════════════════════════════════════════╝
```

### A.3 Recommendations Panel (Expanded)

```
╔═══════════════════════════════════════════════════════════╗
║  💡 HANDLUNGSEMPFEHLUNGEN                     [Sort: ▼]   ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  ╭─────────────────────────────────────────────────────╮  ║
║  │ ⚠️  HIGH PRIORITY                                    │  ║
║  │                                                     │  ║
║  │  📌 Automation "Nachtmodus" fehlerhaft             │  ║
║  │                                                     │  ║
║  │  ─────────────────────────────────────────────────  │  ║
║  │  BEGRÜNDUNG:                                        │  ║
║  │  Trigger-Bedingung "sun.set > 22:00" nie erfüllt,  │  ║
║  │  da Sunset im Sommer um 21:30 ist.                 │  ║
║  │                                                     │  ║
║  │  AUSWIRKUNG:                                        │  ║
║  │  Nachtmodus wird nie automatisch aktiviert.        │  ║
║  │                                                     │  ║
║  │  VORSCHLAG:                                        │  ║
║  │  Bedingung ändern zu: sun.set + 30min              │  ║
║  │                                                     │  ║
║  │  ─────────────────────────────────────────────────  │  ║
║  │                                                     │  ║
║  │  [  🔧 Auto-Fix  ]  [  ✏️ Edit  ]  [  ❌ Ignore  ]  │  ║
║  │                                                     │  ║
║  │  📊 Confidence: 94%  |  💥 Impact: Hoch  |  ⏱️ 2min │  ║
║  ╰─────────────────────────────────────────────────────╯  ║
║                                                           ║
║  ╭─────────────────────────────────────────────────────╮  ║
║  │ 💚 MEDIUM PRIORITY                                   │  ║
║  │                                                     │  ║
║  │  📌 Energie sparen: Heizung ↓ bei offenem Fenster  │  ║
║  │                                                     │  ║
║  │  ─────────────────────────────────────────────────  │  ║
║  │  BEGRÜNDUNG:                                        │  ║
║  │  Fenster (bedroom_window) ist oft >10min offen     │  ║
║  │  bei aktiver Heizung (radiator.bedroom).           │  ║
║  │                                                     │  ║
║  │  AUSWIRKUNG:                                        │  ║
║  │  ~5% Energieeinsparung pro Monat (~€8/Monat)       │  ║
║  │                                                     │  ║
║  │  VORSCHLAG:                                        │  ║
║  │  Neue Automation: "Fenster offen → Heizung aus"    │  ║
║  │                                                     │  ║
║  │  ─────────────────────────────────────────────────  │  ║
║  │                                                     │  ║
║  │  [  ✅ Create  ]  [  📋 Preview  ]  [  ❌ Ignore  ]  │  ║
║  │                                                     │  ║
║  │  📊 Confidence: 78%  |  💥 Impact: Mittel | ⏱️ 5min │  ║
║  ╰─────────────────────────────────────────────────────╯  ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
```

---

**End of Report**
