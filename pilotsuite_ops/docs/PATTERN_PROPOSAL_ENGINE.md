# Pattern Proposal Engine

## Overview

Die Pattern Proposal Engine generiert kontextbezogene Vorschläge aus wiederkehrenden Zonenmustern — statt starrer Presets.

**Boundary:** Rohe Sensorwerte bleiben in HA. Nur abstrakte `SuggestionCandidate`-Objekte werden an Core/Dashboard übergeben.

## Architecture

```
Core (Stxy)              HA (copilot_ha)
────────────────         ─────────────────────────────────
Zone Registry            Observation-Log schreiben
Statische Presets        PatternMatcher
Pattern Store lesen →   SuggestionGenerator
                         Cache (5min TTL)
```

## Components

### `models.py`
- `SuggestionTrigger` (9 Typen)
- `SuggestionConfidence` (HIGH/MEDIUM/LOW)
- `PatternObservation` — einzelner Ereignis/Sensorwert
- `SuggestionCandidate` — generierter Vorschlag

### `store.py`
- Append-only JSON Lines Store, pro Zone
- `record_observation()`, `get_observations()`
- `save_candidate()`, `get_candidates()`
- `accept_candidate()`, `dismiss_candidate()`
- `prune_old()` — entfernt Observations älter als 7 Tage

### `matcher.py`
- `PatternMatcher.match()` — erkennt Muster pro Trigger-Typ
- 5 Match-Strategien: temperature, energy, presence, manual_repeat, window_open
- Group-by-hour + threshold comparison

### `generator.py`
- `SuggestionGenerator` — high-level API
- Cache mit 5min TTL
- Deduplizierung
- Sortierung: HIGH > MEDIUM > LOW

### `ha_service.py`
- `async_setup_pattern_proposal()` — HA-Integration
- `async_record_observation()` — Beobachtung erfassen

## Trigger Types (9)

| Trigger | Beschreibung |
|---|---|
| `temperature_pattern` | Wiederkehrend kalte Raumtemperatur zur selben Stunde |
| `energy_spike` | Mehrfache Energiespitzen erkannt |
| `presence_arrival` | Regelmäßige Ankunftszeiten |
| `presence_departure` | Regelmäßige Abwesenheitszeiten |
| `window_open_climate` | Fenster offen bei aktiver Heizung |
| `manual_repeat` | Manuelle Aktionen zur selben Stunde |
| `zone_transition` | Zonenübergänge |
| `cover_sun_position` | Beschattung basierend auf Sonnenstand |
| `light_ambiguous` | Mehrdeutige Lichtverhältnisse |

## Integration Points

### HA → Engine
```python
from .pattern_proposal import async_record_observation, SuggestionTrigger

await async_record_observation(
    hass=hass,
    zone_id="zone:wohnbereich",
    trigger=SuggestionTrigger.TEMPERATURE_PATTERN,
    payload={"temperature": 17.5, "climate_entity": "climate.wohnen"},
)
```

### Dashboard → GET /api/copilot_ha/suggestions
```json
GET /api/copilot_ha/suggestions?zone=zone:wohnbereich

[
  {
    "candidate_id": "...",
    "zone_id": "zone:wohnbereich",
    "trigger": "temperature_pattern",
    "confidence": "medium",
    "trigger_label": "Temperatur um 22:00",
    "suggestion_text": "In diesem Raum ist es um 22:00 oft kalt (17.5°C). Heizung auf 20°C vorschlagen?",
    "suggested_action": {"entity_id": "climate.wohnen", "temperature": 20.0},
    "created_at": "2026-03-20T20:00:00Z"
  }
]
```

## Next Steps

- [ ] `copilot_ha/__init__.py` → `async_setup_entry` ruft `async_setup_pattern_proposal` auf
- [ ] REST API Route für `GET /api/copilot_ha/suggestions`
- [ ] Dashboard-JS: SuggestionCards mit Accept/Dismiss
- [ ] `thresholds.yaml` pro Zone
