# Multi-User Preference Learning v0.1 - Konzept

> **Stand: 2026-02-15** – Autopilot Task #2

## 1. Problemstellung

Das aktuelle Mood-System ist **Zonen-basiert**, aber **nicht User-spezifisch**:
- Mood wird pro Zone berechnet (`zone_id` → `mood`)
- Vorschläge basieren auf Zonen-Mood, nicht auf User-Präferenzen
- Keine Unterscheidung zwischen verschiedenen Personen im Haushalt

## 2. Ziel

**User-spezifische Preference-Learning**:
1. User unterscheiden (via `person.*` entities)
2. Präferenzen pro User lernen (Licht, Temperatur, Musik, etc.)
3. Preferences in Mood-Context einfließen lassen
4. Vorschläge personalisieren

## 3. Architektur

### 3.1 Datenmodell

```json
{
  "user_preferences": {
    "person.efka": {
      "display_name": "Efka",
      "preferences": {
        "light_brightness_default": 0.7,
        "light_color_temp_default": "warm",
        "music_volume_default": 0.5,
        "preferred_zones": ["wohnbereich", "buero"],
        "sleep_time": "23:00",
        "wake_time": "07:00",
        "temperature_comfort": 21.5
      },
      "learned_patterns": [
        {
          "trigger": "movie_mode",
          "action": "dim_lights",
          "confidence": 0.9,
          "learned_at": "2026-02-15T..."
        }
      ],
      "mood_history": [
        {
          "timestamp": "2026-02-15T20:00:00+01:00",
          "zone": "wohnbereich",
          "mood": "relax",
          "confidence": 0.85
        }
      ]
    }
  }
}
```

### 3.2 Komponenten

#### HA Integration (Neu)
- `user_preference_module.py` – User-Erkennung, Preference-Storage
- `user_preference_entities.py` – Sensoren für User-Preferences
- User-Selection im Config Flow

#### Core Add-on (Erweiterung)
- API-Endpoint `/api/v1/preferences/{user_id}` (CRUD)
- Preference-basierte Mood-Gewichtung
- Pattern-Learning pro User

### 3.3 Workflow

```
1. User-Erkennung
   person.* state change → who is where?

2. Context-Building
   active_user + zone → combined context

3. Mood-Inference
   zone_mood + user_preferences → personalized_mood

4. Suggestion-Generation
   personalized_mood → weighted suggestions

5. Learning
   user_action → preference_update
```

## 4. Implementierung

### 4.1 Phase 1: User-Erkennung (MVP)

**Files:**
- `custom_components/ai_home_copilot/user_preference_module.py`
- `custom_components/ai_home_copilot/user_preference_entities.py`

**Entities:**
```yaml
sensor.ai_copilot_active_user:
  name: "AI CoPilot Active User"
  icon: mdi:account

sensor.ai_copilot_user_preferences:
  name: "AI CoPilot User Preferences"
  icon: mdi:account-cog
```

**Config Flow:**
- User-Entities auswählen (`person.*`)
- Primary User definieren
- Lern-Modus aktivieren/deaktivieren

### 4.2 Phase 2: Preference-Storage

**Storage:**
- `.storage/ai_home_copilot/user_preferences.json`
- Pro User: Preferences, Learned Patterns, Mood History

**API (Core):**
```python
# GET /api/v1/preferences/{user_id}
# POST /api/v1/preferences/{user_id}
# PATCH /api/v1/preferences/{user_id}
# DELETE /api/v1/preferences/{user_id}
```

### 4.3 Phase 3: Pattern-Learning

**Pattern-Detection:**
- Wenn User Aktion ausführt → Kontext speichern
- Bei wiederholten Mustern → Preference vorschlagen
- Nach Bestätigung → Preference übernehmen

**Beispiel:**
```
User dimmt Licht im Wohnbereich auf 30% bei "movie_mode"
→ Nach 5 Wiederholungen: Vorschlag "Dimmen auf 30% bei Movie"
→ Nach Bestätigung: Preference "movie_mode → brightness: 0.3"
```

## 5. API Design

### 5.1 HA Integration

```python
# Services
ai_home_copilot.set_user_preference:
  user_id: person.efka
  preference_key: light_brightness_default
  preference_value: 0.7

ai_home_copilot.learn_pattern:
  user_id: person.efka
  trigger: movie_mode
  action: dim_lights
  confidence: 0.9

ai_home_copilot.forget_pattern:
  user_id: person.efka
  pattern_id: xyz
```

### 5.2 Core Add-on

```python
# GET /api/v1/preferences
# GET /api/v1/preferences/{user_id}
# POST /api/v1/preferences/{user_id}/learn
# POST /api/v1/preferences/{user_id}/confirm/{pattern_id}
```

## 6. UI Integration

### 6.1 Dashboard Card

```yaml
type: custom:ai-copilot-user-preferences
user: person.efka
show_learned_patterns: true
show_mood_history: false
```

### 6.2 Config Flow

1. User Selection (Multi-Select)
2. Primary User
3. Learning Mode (Active/Passive/Off)
4. Privacy Settings (Local Only / Sync to Core)

## 7. Privacy & Security

- **Local-First**: Alle Preferences lokal in HA gespeichert
- **Opt-In**: Learning muss explizit aktiviert werden
- **User-Control**: Jederzeit löschbar
- **No Cloud**: Keine externen APIs

## 8. Versionierung

- **v0.8.0**: Multi-User Preference Learning MVP
  - User-Erkennung
  - Preference-Storage
  - Basic UI

- **v0.8.1**: Pattern-Learning
  - Automatische Muster-Erkennung
  - Vorschlags-System

- **v0.8.2**: Personalized Suggestions
  - Preference-basierte Vorschläge
  - Mood-History pro User

## 9. Erfolgsmetriken

- User-Preferences korrekt erkannt
- Vorschläge relevant personalisiert
- Lern-Rate > 70% (bestätigte Patterns)
- Privacy gewährleistet

## 10. Nächste Schritte

1. ✅ Konzept erstellt
2. ⏳ Dev-Branch erstellen
3. ⏳ `user_preference_module.py` implementieren
4. ⏳ Config Flow erweitern
5. ⏳ Core API erweitern
6. ⏳ Tests schreiben
7. ⏳ CHANGELOG aktualisieren
8. ⏳ Release v0.8.0

---

**Autopilot Status:** Concept Phase
**Nächster Schritt:** Dev-Branch erstellen, Implementierung starten