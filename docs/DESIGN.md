# PilotSuite Design-Entscheidungen

**Stand:** 2026-03-24  
**Owner:** DesignClaw / PilotDesign  
**Lane:** Design + Dokumentation

---

## 1. Architektur-Entscheidungen

### 1.1 Zone-per-Module Ansatz

**Entscheidung:** Jede Habituszone kapselt ihre Module autonom.

**Rationale:**
- Klare Trennung der Verantwortlichkeiten (Light, Climate, Motion, Media, Camera, Humidity, Volume)
- Module können pro Zone ein-/ausgeschaltet werden
- Reduziert Kopplung zwischen Zonen
- Ermöglicht inkrementelles Rollout (Zone für Zone)

**Architektur:**
```
Zone (Habitus-Typ)
├── light-Module      (Learning/Active/Off)
├── climate-Module    (Learning/Active/Off)
├── motion-Module     (Learning/Active/Off)
├── media-Module      (Learning/Active/Off)
├── camera-Module     (Learning/Active/Off)
├── humidity-Module   (Learning/Active/Off)
└── volume-Module     (Learning/Active/Off)
```

**10 Habituszonen:**
| ZoneType | DE | Icon | Default-Modules |
|----------|----|------|-----------------|
| living | Wohnbereich | mdi:sofa | light, climate, motion, media |
| bath | Badbereich | mdi:shower | light, climate, humidity |
| kitchen | Küche | mdi:stove | light, climate, motion |
| office | Büro | mdi:desk | light, climate, media |
| hallway | Flur | mdi:walk | light, motion |
| bedroom | Schlafzimmer | mdi:bed | light, climate, media |
| room_mira | Kinderzimmer Mira | mdi:human-child | light, climate, media |
| room_paul | Kinderzimmer Paul | mdi:human-child | light, climate, media |
| terrace | Terrasse | mdi:terrace | light, climate |
| outside | Außen | mdi:tree | light, camera |

---

### 1.2 Brain-Ansatz (Neuronale Targets)

**Entscheidung:** Module schreiben auf neuronale Targets statt direkt auf HA Entities.

**Rationale:**
- Entkopplung von HA-spezifischen Implementierungen
- Einheitliche Semantik über alle Zonen hinweg
- Ermöglicht Brain-Graph-Visualisierung
- Vorbereitung für Multi-Agent-Koordination

**Neuron-Targets pro Modul:**
| Modul | Neuron-Target | Semantik |
|-------|---------------|----------|
| light | ambient_need | Lichtbedarf (Helligkeit, Farbtemp, Szene) |
| climate | comfort_need | Komfortbedarf (Temp, Luftfeuchte, Modus) |
| motion | presence_intent | Anwesenheits-Intention (aktiv, passiv, abwesend) |
| media | media_intent | Medien-Intention (Play, Pause, Volume, Source) |
| camera | security_need | Sicherheitsbedarf (Aufnahme, Alert, Preview) |
| humidity | comfort_need | Luftfeuchte-Bedarf (Zielwert, Entfeuchtung) |
| volume | media_intent | Lautstärke-Intention (Level, Mute, Zone) |

**Pipeline:**
```
HA Entities (Input)
    ↓
Adapter (homeassistant)
    ↓
Module Engine (brain_module.py)
    ↓
Neuron Targets (semantic layer)
    ↓
Output → HA Service Calls / Proposals
```

---

## 2. UI-Prinzipien

### 2.1 Habitus-Dashboard Layout

**Entscheidung:** Sidebar-Navigation + Zone-Dashboard mit Modul-Cards.

**Layout:**
```
┌─────────────────────────────────────────────────────┐
│  🏠 Pilotsuite  │  Zone: Wohnbereich  │  ⚙️  │
├────────────┬────────────────────────────────────────┤
│            │                                        │
│  NAV       │   ZONE DASHBOARD                       │
│            │                                        │
│  🏠 Overview│  ┌────────┐ ┌────────┐ ┌────────┐    │
│  🛋️ Wohn    │  │ LIGHT  │ │CLIMATE │ │ MOTION │    │
│  🚿 Bad     │  │  🌙    │ │  🌡️    │ │  👤   │    │
│  🍳 Küche   │  │ an/aus │ │ 21.5°  │ │aktiv   │    │
│  💻 Büro    │  └────────┘ └────────┘ └────────┘    │
│  🚪 Flur    │                                        │
│  🛏️ Schlaf  │  ┌────────┐ ┌────────┐               │
│  👧 Mira    │  │ MEDIA  │ │CAMERA  │               │
│  👦 Paul    │  │  🔊    │ │  📹    │               │
│  🌿 Terrasse│  │ Sonos  │ │  —     │               │
│  🌳 Draußen │  └────────┘ └────────┘               │
│            │                                        │
│  📊 Brain  │  ─────────────────────────────────   │
│  ⚡ Energie │  Module-Konfiguration (pro Zone):     │
│  📡 System  │  [Light] [Climate] [Motion] [Media]   │
│            │  Modul-Zustand: ● Learning / ○ Active  │
└────────────┴────────────────────────────────────────┘
```

**Prinzipien:**
1. **Zone-First:** Immer eine Zone im Fokus
2. **Module als Cards:** Pro Modul eine Card mit State-Indikator
3. **Toggle-basiert:** Learning / Active / Off umschaltbar
4. **Progressive Disclosure:** Details auf Klick (Expand/Collapse)

---

### 2.2 Suggestion-Cards (Must-Fix Lücken)

**Aus V15_UX_GATE.md — 3 offene Lücken vor v15.0:**

#### Lücke 1: Pattern + Lift sichtbar machen (KRITISCH)

**Problem:** Card zeigt Confidence % aber nicht das zugrundeliegende Pattern und den Lift.

**Lösung:**
```html
<details class="sg-reasoning">
  <summary>Warum dieser Vorschlag?</summary>
  <div class="reasoning-body">
    <span class="pattern">🔗 Licht Küche → Kaffee-Maschine</span>
    <span class="lift">📈 Lift: 3.2× (starke Korrelation)</span>
    <span class="confidence">✓ Confidence: 89%</span>
  </div>
</details>
```

**Daten:**
- `pattern`: "light.kitchen:on → switch.coffee:on"
- `lift`: 3.2 (Korrelationsstärke)
- `confidence`: 0.89 (89%)
- `reasoning`: "In 47 von 52 Fällen..."

---

#### Lücke 2: Governance-Modi sichtbar (KRITISCH)

**Problem:** 3-Phasen-Modell (off/learning/autonomy) nicht in HA sichtbar.

**Lösung:** Dashboard-Indicator + Sensor-State

**Phasen:**
| Phase | Modus | Beschreibung |
|-------|-------|--------------|
| 1 | OFF | System beobachtet, keine Aktionen |
| 2 | LEARNING | System macht Vorschläge, Nutzer entscheidet |
| 3 | AUTONOMY | System handelt selbst |

**Sensor:** `sensor.pilotsuite_autonomie_status`  
**States:** `off`, `learning`, `autonomy`

---

#### Lücke 3: Core Connection Status (HOCH)

**Problem:** Core-Erreichbarkeit nicht auf einen Blick sichtbar.

**Lösung:** `sensor.copilot_ha_core_connection`  
**States:** `connected`, `degraded`, `disconnected`

**Status-Indikator im Dashboard:**
```
🟢 Core: verbunden
🟡 Core: degradiert
🔴 Core: getrennt
```

---

### 2.3 Card-Designs

#### Light-Card
```
┌──────────────────────────┐
│ 💡 Licht         [ON/OFF]│
├──────────────────────────┤
│ Deckenlicht      ●────── │
│ Stehlampe        ○       │
│ Wandleuchte      ○       │
├──────────────────────────┤
│ Helligkeit: 75%          │
│ Farbtemp: Warm (3000K)   │
│ [Szenen: Abend│Lesen│Aus]│
└──────────────────────────┘
```

#### Climate-Card
```
┌──────────────────────────┐
│ 🌡️ Heizung       [ON]    │
├──────────────────────────┤
│ Ist: 21.5°C    Soll: 22° │
│ ████████████░░ 95%       │
├──────────────────────────┤
│ Modus: Komfort           │
│ Fenster: geschlossen      │
│ [Eco] [Komfort] [Boost]  │
└──────────────────────────┘
```

---

## 3. Design-Language

### 3.1 Farbpalette (Dark Theme)

```css
:root {
  /* Backgrounds */
  --bg:        #0a0e14;   /* Haupt-Hintergrund */
  --surface:   #12171f;   /* Sekundär-Flächen */
  --card:      #171d27;   /* Karten-Hintergrund */
  --border:    #1e2a3a;   /* Rahmen-Linien */

  /* Text */
  --text:      #e0e6ed;   /* Haupt-Text */
  --dim:       #6b7a8d;   /* gedimmter Text */

  /* Accents */
  --accent:    #7c6aef;   /* Primär-Akzent (Lila) */
  --accent2:   #9b8afb;   /* Sekundär-Akzent (Hell-Lila) */

  /* States */
  --green:     #34d399;   /* Success / Active */
  --yellow:    #fbbf24;   /* Warning / Learning */
  --red:       #f87171;   /* Error / Off */
  --blue:      #60a5fa;   /* Info / Blue */
  --cyan:      #22d3ee;   /* Accent / Cyan */
}
```

**State-Codierung:**
| Zustand | Farbe | Verwendung |
|---------|-------|------------|
| Active | Grün (#34d399) | Modul aktiv, erfolgreich |
| Learning | Gelb (#fbbf24) | Modul lernt, Vorschläge |
| Off | Rot (#f87171) | Modul deaktiviert |
| Connected | Blau (#60a5fa) | Core verbunden |
| Degraded | Gelb (#fbbf24) | Core eingeschränkt |
| Disconnected | Rot (#f87171) | Core getrennt |

---

### 3.2 Typografie

**Font-Stack:** System-Fonts (performance-optimiert)

```css
:root {
  --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", 
               Roboto, Helvetica, Arial, sans-serif;
  --font-mono: "JetBrains Mono", "Fira Code", Menlo, Monaco, 
               Consolas, monospace;
  
  --text-xs:   0.75rem;   /* 12px */
  --text-sm:   0.875rem;  /* 14px */
  --text-base: 1rem;      /* 16px */
  --text-lg:   1.125rem;  /* 18px */
  --text-xl:   1.25rem;   /* 20px */
  --text-2xl:  1.5rem;    /* 24px */
}
```

**Hierarchie:**
- **Headline:** 1.5rem / 24px (Zone-Titel)
- **Subhead:** 1.25rem / 20px (Card-Titel)
- **Body:** 1rem / 16px (Inhalt)
- **Caption:** 0.875rem / 14px (Labels, Metadaten)
- **Mono:** 0.75rem / 12px (Technische Werte, IDs)

---

### 3.3 Icon-System

**Library:** Material Design Icons (mdi)

**Zone-Icons:**
| ZoneType | Icon |
|----------|------|
| living | mdi:sofa |
| bath | mdi:shower |
| kitchen | mdi:stove |
| office | mdi:desk |
| hallway | mdi:walk |
| bedroom | mdi:bed |
| room_mira | mdi:human-child |
| room_paul | mdi:human-child |
| terrace | mdi:terrace |
| outside | mdi:tree |

**Modul-Icons:**
| Modul | Icon |
|-------|------|
| light | mdi:lightbulb |
| climate | mdi:thermometer |
| motion | mdi:motion-sensor |
| media | mdi:speaker |
| camera | mdi:cctv |
| humidity | mdi:water-percent |
| volume | mdi:volume-high |

---

## 4. Status — P1-092 Design-Doc

**P1-092: Dashboard-Habituszonen-Design** — ✅ **DONE**

**Design-Doc vollständig** mit:
- 10 Habituszonen-Typen definiert (living, bath, kitchen, office, hallway, bedroom, room_mira, room_paul, terrace, outside)
- Modul-Matrix pro Zone (light, climate, motion, media, camera, humidity, volume)
- Card-Designs für Light/Climate/Module
- Farbpalette (Dark Theme) definiert
- Layout-Skizze (Sidebar + Zone Dashboard)
- API-Endpoints dokumentiert

**Offene Implementierungs-Tasks:**
- [ ] Zone-Entity-Mapping: Welche HA-Entity gehört zu welcher Zone?
- [ ] Tag-System: `zone:<type>` Tag pro Raum noch nicht aktiv
- [ ] Modul-Zuordnung: Wer entscheidet welches Modul in welcher Zone aktiv ist?
- [ ] Brain-Graph-Visualisierung: Wie werden Neuronen pro Zone angezeigt?
- [ ] Presence-Detection: motion → presence → zone_state

**UX-Gate Dependencies:**
- [x] M2 (Pattern+Lift in Suggestions) — ✅ Athene fixed
- [x] M3 (Governance-Modus sichtbar) — ✅ Athene fixed
- [x] M4 (Core-Connection-Sensor) — ✅ Athene fixed (c62d6da9)

---

*Erstellt: 2026-03-24 — DesignClaw / PilotDesign*
