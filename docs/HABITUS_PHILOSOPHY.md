# Habitus Philosophy - Das lernende Zuhause

> *"Ein Smart Home ist nur so schlau wie sein Nutzer – aber es kann lernen, ihn besser zu verstehen."*

## Die Kernidee

### Das Problem
Heutige Smart Homes sind **statisch**: Sie kennen Regeln, aber nicht den Menschen. 
- "Licht an bei Bewegung" – aber welche Stimmung?
- "Heizung auf 21°C" – aber wann warum?
- "Rollläden runter" – aber welcher Kontext?

Der Nutzer muss sich anpassen. Das System lernt nicht.

### Die Lösung: HabitusZones
**HabitusZones** sind die Brücke zwischen statischen Regeln und individuellen Mustern.

```
┌─────────────────────────────────────────────────────────────────┐
│                     DER NUTZER LEBT                            │
│                          ↓                                     │
│   Ereignisse in Zonen (Küche, Wohnen, Schlafen, ...)          │
│                          ↓                                     │
│              HABITUS MINER ERKENNT MUSTER                      │
│                          ↓                                     │
│           A → B Regeln mit Confidence & Lift                   │
│                          ↓                                     │
│            TAGS VERBINDEN ZONEN + ENTITIES                     │
│                          ↓                                     │
│           VORSCHLÄGE, NICHT AUTOMATIK                          │
│                          ↓                                     │
│              NUTZER BESTÄTIGT                                  │
│                          ↓                                     │
│           SMART HOME WIRD INDIVIDUELL                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Die Philosophie

### 1. Zonen als Lebensraum

Eine **HabitusZone** ist kein Raum im architektonischen Sinn. 
Sie ist ein **funktionaler Kontext**, definiert durch:

- **Entities**: Welche Geräte/SENSOREN sind dort aktiv?
- **Zeit**: Wann wird die Zone genutzt?
- **Stimmung**: Welche Mood-Neuronen feuern?
- **Muster**: Welche A→B Regeln wurden erkannt?

**Beispiel:**
```
HabitusZone: "Wohnabend"
  Entities: [light.wohnzimmer, media_player.tv, sensor.bewegung_wohnzimmer]
  Time: 18:00-23:00
  Mood: relax → 0.8, social → 0.3
  Patterns:
    - light.on → media_player.play (confidence: 0.85, lift: 2.3)
    - media_player.pause → light.brighten (confidence: 0.72, lift: 1.8)
```

### 2. Tags als Semantik

**Tags** verleihen Entities Bedeutung:

| Tag | Bedeutung | Zone-Bezug |
|-----|-----------|------------|
| `aicp.place.wohnzimmer` | Ort | → Wohnen-Zone |
| `aicp.kind.light` | Typ | → Lighting-Kontext |
| `aicp.role.primary` | Wichtigkeit | → Prioritäts-Steuerung |
| `aicp.state.needs_repair` | Zustand | → Wartungs-Hinweis |
| `aicp.cap.dimmable` | Fähigkeit | → Automatisierungs-Option |

**Tag → Zone Integration:**
```
Wenn Entity getaggt mit aicp.place.X:
  → Automatisch zu HabitusZone("X") hinzufügen
  → Neue Zone erstellen falls nicht existiert
  → Member-Subject-IDs aktualisieren
```

### 3. Muster als Sprache

**A→B Regeln** sind die Sprache des Smart Home:

```
A: light.küche.on (Antecedent)
B: light.arbeitsfläche.on (Consequent)
Δt: 45 Sekunden (Typisches Delay)
Confidence: 0.87 (87% der Zeit folgt B auf A)
Lift: 3.2 (3.2x häufiger als Zufall)
```

**Aber:** Das System schlägt vor, der Nutzer entscheidet.

```
┌────────────────────────────────────────────────┐
│  VORSCHLAG                                     │
│                                                │
│  "Wenn Küchenlicht an, dann Arbeitsfläche"   │
│                                                │
│  Confidence: 87%  |  Lift: 3.2x               │
│  Beobachtet: 23 Mal in Küche                  │
│                                                │
│  [✓ Übernehmen]  [✗ Nie wieder]  [⏱ Später]  │
└────────────────────────────────────────────────┘
```

### 4. Mood als Kontext

**Mood-Neuronen** gewichten Vorschläge:

| Mood | Vorschlag-Gewichtung |
|------|---------------------|
| `relax` → 0.8 | Entspannungs-Vorschläge priorisieren |
| `focus` → 0.6 | Produktivitäts-Vorschläge |
| `social` → 0.4 | Gäste-Kontext |
| `sleep` → 0.9 | Nacht-Modus |

**Beispiel:**
```
Mood: relax → 0.85
Vorschlag: "Licht dimmen auf 30%"
→ Confidence × Mood = 0.87 × 0.85 = 0.74 (hoch priorisiert)

Mood: focus → 0.2
Vorschlag: "Licht dimmen auf 30%"  
→ Confidence × Mood = 0.87 × 0.2 = 0.17 (niedrig priorisiert)
```

---

## Architektur

### Layer-Modell

```
┌─────────────────────────────────────────────────────────┐
│ Layer 4: USER INTERFACE                                │
│   Repairs, Dashboard, Chat                             │
├─────────────────────────────────────────────────────────┤
│ Layer 3: DECISION                                      │
│   Suggestions, Candidates, Governance                  │
├─────────────────────────────────────────────────────────┤
│ Layer 2: CONTEXT                                       │
│   Mood-Neurons, HabitusZones, Tags                     │
├─────────────────────────────────────────────────────────┤
│ Layer 1: PERCEPTION                                   │
│   Brain Graph, Event Ingest, State Tracking            │
├─────────────────────────────────────────────────────────┤
│ Layer 0: HOME ASSISTANT                               │
│   Entities, Automations, Sensors, Devices              │
└─────────────────────────────────────────────────────────┘
```

### Datenfluss

```
Home Assistant State Change
        ↓
Event Ingest → Brain Graph
        ↓
Habitus Miner (Zone-gefiltert)
        ↓
A→B Rule Candidate
        ↓
Tag System (Entity-Kontext)
        ↓
Mood-Weighting (Aktuelle Stimmung)
        ↓
Suggestion (mit Confidence & Erklärung)
        ↓
User Decision (Accept/Reject/Defer)
        ↓
Automation erstellt / Verworfen
        ↓
Feedback → Brain Graph → Mood Learning
```

---

## Governance-Regeln

### Was das System DARF

✅ **Beobachten**: Alle Events, States, Muster  
✅ **Vorschlagen**: Candidates mit Confidence & Lift  
✅ **Lernen**: Aus Accept/Reject-Entscheidungen  
✅ **Erklären**: Warum ein Vorschlag gemacht wurde  

### Was das System NICHT DARF

❌ **Automatisch schalten** ohne explizite Freigabe  
❌ **Sicherheitskritische Entities** ohne Bestätigung  
❌ **Private Daten** nach außen senden  
❌ **Unbekannte Muster** ohne Erklärung anwenden  

### Sicherheits-Kategorien

| Kategorie | Entities | Aktion |
|-----------|----------|--------|
| **Safety Critical** | Alarm, Türschloss, Heizung | Immer bestätigen |
| **Comfort** | Licht, Rollläden, Media | Nach Confidence fragen |
| **Information** | Sensor, Status | Automatisch lernen |

---

## Implementierung

### Tag → Zone Integration

```python
# tagging/zone_integration.py

class TagZoneIntegration:
    """Verbindet Tags mit HabitusZones."""
    
    TAG_ZONE_MAPPING = {
        TagFacet.PLACE: "auto_zone",      # aicp.place.küche → Zone "küche"
        TagFacet.KIND: "context",          # aicp.kind.light → Lighting-Kontext
        TagFacet.ROLE: "priority",         # aicp.role.safety_critical → Immer fragen
    }
    
    async def on_tag_assigned(self, entity_id: str, tag_id: str):
        """Wird aufgerufen wenn ein Tag zugewiesen wird."""
        tag = self.registry.get_tag(tag_id)
        
        if tag.facet == TagFacet.PLACE:
            # Automatisch Zone erstellen/erweitern
            zone_name = tag.key  # "küche" aus "aicp.place.küche"
            await self.add_to_zone(zone_name, entity_id)
            
        elif tag.facet == TagFacet.ROLE and tag.id == "aicp.role.safety_critical":
            # Safety-Critical Entities immer bestätigen lassen
            await self.set_governance(entity_id, requires_confirmation=True)
```

### HabitusZone Definition

```python
@dataclass
class HabitusZone:
    """Eine funktionale Zone im Smart Home."""
    id: str                          # "wohnabend", "küche_kochen"
    name: str                        # "Wohnzimmer Abend"
    member_entity_ids: list[str]     # Entities in dieser Zone
    time_patterns: dict              # {"weekday_evening": 0.9}
    mood_weights: dict               # {"relax": 0.8, "social": 0.3}
    discovered_rules: list[str]      # Candidate-IDs
    governance: ZoneGovernance       # Sicherheitsregeln
```

---

## Roadmap

### Phase 1: Foundation (✅ Erledigt)
- [x] Brain Graph für Entity-Beziehungen
- [x] Habitus Miner für A→B Regeln
- [x] Tag System v0.2 mit HabitusZone
- [x] Mood-Neurons für Kontext

### Phase 2: Integration (🔄 In Progress)
- [x] Tag → Zone Integration
- [ ] Zone-basiertes Mining
- [ ] Mood-gewichtete Vorschläge
- [ ] Repairs UX Enhancement

### Phase 3: Learning (⏳ Geplant)
- [ ] Feedback-Learning aus User-Decisions
- [ ] Zone-Muster-Evolution
- [ ] Multi-User-Präferenzen
- [ ] saisonale Anpassung

---

## Zitate

> *"Das Smart Home soll nicht für mich entscheiden. Es soll mir helfen, bessere Entscheidungen zu treffen."*

> *"Jede Zone erzählt eine Geschichte. Der Habitus Miner übersetzt sie."*

> *"Ein Tag ist mehr als ein Label. Es ist ein Versprechen an das System."*

---

## Referenzen

- PILOTSUITE_VISION.md - Gesamtarchitektur
- MEMORY.md - Langzeit-Gedächtnis
- HEARTBEAT.md - Autopilot-Konfiguration

*Stand: 2026-02-15*