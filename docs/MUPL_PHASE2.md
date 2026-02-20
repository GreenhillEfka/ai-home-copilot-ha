# MUPL Phase 2: Action Attribution

## Übersicht

**Version:** v0.8.1
**Status:** In Entwicklung
**Branch:** dev/mupl-phase2-v0.8.1

## Ziel

Erweiterung des Multi-User Preference Learning (MUPL) um **Action Attribution**:
- Welcher User hat welche Aktion ausgeführt?
- User-spezifische Preference Patterns
- Integration mit bestehendem Mood Context

## Architektur

### Phase 1 (v0.8.0) - Bereits implementiert
- User-ID Context Extraction
- Per-User Preference Storage
- Basic User Identification

### Phase 2 (v0.8.1) - Neu

```
┌─────────────────────────────────────────────────────────┐
│                    Action Attribution                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Home Assistant Event → User Attribution → Preference   │
│                                                          │
│  Eingabe:                                                │
│  - Entity State Change                                   │
│  - Service Call                                          │
│  - Automation Trigger                                    │
│                                                          │
│  Attribution Sources:                                    │
│  - Presence Sensors (who is home)                        │
│  - Device Ownership (whose phone/tablet)                 │
│  - Room Location (who is in the room)                    │
│  - Time Patterns (who usually acts at this time)         │
│  - Manual Override (explicit user confirmation)          │
│                                                          │
│  Ausgabe:                                                │
│  - user_action: {user_id, entity, action, confidence}    │
│  - preference_update: {user_id, preference, weight}      │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Komponenten

### 1. ActionAttributor
**Datei:** `core/mupl/action_attributor.py`

```python
class ActionAttributor:
    """Attribuiert Home Assistant Aktionen zu spezifischen Usern"""
    
    def __init__(self, hass, presence_manager):
        self.hass = hass
        self.presence_manager = presence_manager
        self.attribution_sources = [
            PresenceAttribution(),
            DeviceOwnershipAttribution(),
            RoomLocationAttribution(),
            TimePatternAttribution(),
        ]
    
    async def attribute_action(self, entity_id: str, action: str) -> AttributionResult:
        """Ermittelt, welcher User eine Aktion wahrscheinlich ausgeführt hat"""
        ...
```

### 2. PresenceManager Integration
**Erweiterung:** `core/mupl/presence_manager.py`

- Integration mit bestehenden Presence-Sensoren
- User-to-Room Mapping
- Device-to-User Mapping

### 3. Preference Aggregator
**Erweiterung:** `core/mupl/preference_aggregator.py`

- Weighted Preference Updates basierend auf Attribution Confidence
- Conflict Resolution bei mehreren Usern
- Preference Decay (ältere Preferences verblassen)

## Datenmodell

### User Action Log
```yaml
# Stored in .storage/mupl_actions.json
actions:
  - timestamp: "2026-02-15T04:30:00+01:00"
    entity_id: "light.wohnzimmer"
    action: "turn_on"
    attribution:
      user_id: "efka"
      confidence: 0.85
      sources:
        - presence: 0.4
        - room_location: 0.3
        - time_pattern: 0.15
    context:
      mood: "relax"
      time_of_day: "evening"
      room: "wohnzimmer"
```

### User Preferences
```yaml
# Stored in .storage/mupl_preferences.json
preferences:
  efka:
    light.wohnzimmer:
      preferred_brightness: 80
      preferred_color_temp: 3000
      time_patterns:
        evening:
          turn_on_confidence: 0.9
      attribution_count: 45
      last_updated: "2026-02-15T04:30:00+01:00"
```

## API Endpoints

### POST /api/mupl/action
```json
{
  "entity_id": "light.wohnzimmer",
  "action": "turn_on",
  "service_data": {"brightness": 200}
}
```

### GET /api/mupl/preferences/{user_id}
```json
{
  "user_id": "efka",
  "preferences": {
    "light.wohnzimmer": {...},
    "climate.wohnzimmer": {...}
  }
}
```

## Services

### `mupl.learn_from_action`
```yaml
service: mupl.learn_from_action
data:
  entity_id: light.wohnzimmer
  action: turn_on
  user_id: efka  # Optional - wenn bekannt
```

### `mupl.get_user_suggestion`
```yaml
service: mupl.get_user_suggestion
data:
  entity_id: light.wohnzimmer
  user_id: efka
```

## Tests

1. **test_action_attribution.py** - Unit Tests für Attribution Logic
2. **test_presence_integration.py** - Integration Tests mit Presence Sensoren
3. **test_preference_aggregation.py** - Tests für Preference Updates

## Timeline

1. **Woche 1:** ActionAttributor Core Implementation
2. **Woche 2:** Presence Integration
3. **Woche 3:** Preference Aggregator Enhancement
4. **Woche 4:** API & Services + Tests

## Erfolgsmetriken

- Attribution Accuracy > 80%
- False Attribution Rate < 10%
- User Satisfaction Score (via Feedback)
- Preference Prediction Accuracy

## Abhängigkeiten

- MUPL v0.8.0 (bereits implementiert)
- Presence Sensoren konfiguriert
- User ID Mapping in configuration.yaml

---

*Erstellt: 2026-02-15*
*Autor: Autopilot Worker*