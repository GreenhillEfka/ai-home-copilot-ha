# PilotSuite HA — Modul-Referenz

**Version:** 13.7.0
**Datum:** 2026-03-11

---

## Uebersicht

Die PilotSuite HA Integration besteht aus 145+ Python-Modulen. Diese Referenz dokumentiert die wichtigsten Komponenten.

---

## Core Infrastruktur

| Modul | Datei | Beschreibung |
|-------|-------|-------------|
| Init | `__init__.py` | Integration Entry Point, Platform-Setup |
| Coordinator | `coordinator.py` | DataUpdateCoordinator mit API-Client und Failover |
| API Client | `api.py` | Basis-HTTP-Client fuer Core-Kommunikation |
| Constants | `const.py` | Domain, Konfigurationsschluessel, Defaults |
| Connection | `connection_config.py` | Core-Verbindungsaufloesung (Entry -> Env -> Default) |
| Core Endpoint | `core_endpoint.py` | URL-Builder mit Kandidaten-Erkennung |
| Entity Base | `entity.py` | CopilotStyxEntity Basisklasse |

### CopilotDataUpdateCoordinator

Zentraler Coordinator mit:
- **API-Failover**: Mehrere Kandidaten-URLs, automatischer Wechsel bei Fehler
- **Retry-Logik**: 3 Versuche mit exponentiellem Backoff
- **Hybrid-Polling**: 120s Fallback + Webhook-Push fuer Echtzeit
- **Camera State Management**: Motion, Presence, Activity, Zone Events

### API-Methoden

| Methode | Beschreibung |
|---------|-------------|
| `async_get_status()` | Health + Version Check |
| `async_get_mood()` | Aktuelle Hausstimmung |
| `async_get_neurons()` | Neuronenzustaende |
| `async_get_zone_automation()` | Zone Automation Dashboard |
| `async_get_sonos_summary()` | Sonos Speaker Status |
| `async_get_sonos_favorites()` | Sonos Favoriten |
| `async_sonos_action()` | Sonos Aktion ausfuehren |
| `async_sync_tags_to_core()` | Tags an Core senden |
| `async_get_core_tags()` | Tags von Core laden |
| `async_get_presence()` | Praesenz-Daten |
| `async_get_light_intelligence()` | Licht-Intelligenz |
| `async_chat_completions()` | LLM Chat |
| `async_stt()` | Speech-to-Text |
| `async_tts()` | Text-to-Speech |
| `async_evaluate_neurons()` | Neuronale Auswertung |

### Musikwolke-Methoden (v13.7.0)

| Methode | Beschreibung |
|---------|-------------|
| `async_get_musikwolke_status()` | Status aktiver Gruppen |
| `async_musikwolke_play(zone_id, volume)` | Zone abspielen |
| `async_musikwolke_pause(zone_id)` | Zone pausieren |
| `async_musikwolke_volume(zone_id, pct)` | Lautstaerke setzen |
| `async_create_musikwolke(zone_ids)` | Gruppe erstellen |
| `async_dissolve_musikwolke(zone_ids)` | Gruppe aufloesen |
| `async_start_media_follow(person, zone)` | Follow starten |
| `async_stop_media_follow(session_id)` | Follow stoppen |
| `async_get_media_follow_sessions()` | Sessions auflisten |
| `async_set_zone_automation_mode(zone, mode)` | Modus setzen |
| `async_get_zone_automation_mode(zone)` | Modus abfragen |
| `async_get_musikwolke_zone_map()` | Zone-Speaker-Mapping |

---

## Entity-Plattformen

### Sensoren (sensor.py)

| Entity | Beschreibung |
|--------|-------------|
| `sensor.copilot_ha_mood` | Aktuelle Hausstimmung |
| `sensor.copilot_ha_brain_graph_nodes` | Anzahl Brain Graph Knoten |
| `sensor.copilot_ha_suggestions` | Aktive KI-Vorschlaege |
| `sensor.copilot_ha_predictive_automation` | Praediktive Automatisierung |
| `sensor.pilotsuite_media_follow` | Musikwolke Follow-Status |
| `sensor.pilotsuite_presence_intelligence` | Praesenz-Intelligenz |
| `sensor.pilotsuite_light_intelligence` | Licht-Intelligenz |
| `sensor.pilotsuite_energy_consumption` | Energieverbrauch |
| `sensor.pilotsuite_energy_production` | Energieerzeugung |
| `sensor.pilotsuite_habitus_zones` | Zonen-Uebersicht |
| `sensor.pilotsuite_zone_modes` | Aktive Zonen-Modi |

### Binaer-Sensoren (binary_sensor.py)

| Entity | Beschreibung |
|--------|-------------|
| `binary_sensor.pilotsuite_zone_presence_overview` | Gesamt-Praesenz |
| `binary_sensor.pilotsuite_zone_presence_<zone_id>` | Pro-Zone Praesenz |

### Buttons (button.py + button_*.py)

~20 Button-Module fuer verschiedene Aktionen:
- Debug-Buttons, Graph-Refresh, Camera-Controls
- Demo-Buttons fuer Vorschau-Funktionen
- Brain Sync Trigger

### Switches (switch.py)

Automation-Toggles fuer Features ein-/ausschalten.

### Conversation (conversation.py)

HA Conversation Agent "Styx Assist" fuer Sprachsteuerung und Chat.

### STT / TTS (stt.py, tts.py)

Speech-to-Text und Text-to-Speech via Core LLM/Ollama.

### Camera (camera.py)

Brain Graph Visualisierung als Kamera-Entity.

---

## Services (services_setup.py)

### Musikwolke Services (v13.7.0)

| Service | Parameter |
|---------|-----------|
| `musikwolke_create` | `zone_ids: list` |
| `musikwolke_dissolve` | `zone_ids: list` |
| `musikwolke_play` | `zone_id: str`, `volume_pct?: int` |
| `musikwolke_pause` | `zone_id: str` |
| `musikwolke_volume` | `zone_id: str`, `volume_pct: int` |
| `musikwolke_start_follow` | `person_id: str`, `source_zone: str` |
| `musikwolke_stop_follow` | `session_id: str` |
| `zone_automation_set_mode` | `zone_id: str`, `mode: off\|learning\|autonomy` |

### Tag Registry Services

| Service | Parameter |
|---------|-----------|
| `tag_registry_upsert_tag` | `tag_key`, `title?`, `icon?`, `color?`, `status?` |
| `tag_registry_set_assignment` | `subject`, `tag_keys` |
| `tag_registry_confirm` | `tag_key` |
| `tag_registry_sync_labels_now` | (keine) |
| `tag_registry_pull_from_core` | `entry_id?` |

### Media Context v2 Services

| Service | Parameter |
|---------|-----------|
| `media_context_v2_suggest_zone_mapping` | `entry_id` |
| `media_context_v2_apply_zone_suggestions` | `entry_id` |
| `media_context_v2_clear_overrides` | `entry_id` |

### Habitus Miner Services

| Service | Parameter |
|---------|-----------|
| `habitus_mine_rules` | `days_back?`, `domains?`, `min_confidence?`, `min_lift?` |
| `habitus_get_rules` | `limit?`, `domain_filter?`, `min_score?` |
| `habitus_reset_cache` | (keine) |
| `habitus_configure_mining` | `auto_mining_enabled?`, `buffer_max_size?` |

### MUPL (Multi-User Preference Learning)

| Service | Parameter |
|---------|-----------|
| `mupl_learn_preference` | `user_id`, `preference_type`, `value`, `zone?` |
| `mupl_set_user_priority` | `user_id`, `priority` |
| `mupl_delete_user_data` | `user_id` |
| `mupl_export_user_data` | `user_id` |
| `mupl_detect_active_users` | (keine) |
| `mupl_get_aggregated_mood` | `user_ids?` |

### Voice Services

| Service | Parameter |
|---------|-----------|
| `parse_command` | `text` |
| `speak` | `text`, `entity_id?`, `language?` |
| `execute_command` | `text` |
| `get_voice_state` | (keine) |
| `set_voice_tone` | `tone` |

### Weitere Services

- **Debug**: `enable_debug`, `toggle_debug`, `clear_debug_buffer`, `set_debug`, `ping`
- **Ops Runbook**: `ops_runbook_preflight_check`, `ops_runbook_smoke_test`, `ops_runbook_execute_action`
- **N3 Forwarder**: `forwarder_n3_start`, `forwarder_n3_stop`, `forwarder_n3_stats`
- **Suggestion Panel**: `suggestion_accept`, `suggestion_reject`, `suggestion_snooze`
- **HomeKit**: `homekit_enable_zone`, `homekit_disable_zone`
- **Energy**: `energy_insights_get`
- **Anomaly**: `anomaly_alert_check_and_alert`, `anomaly_alert_clear_history`
- **Habit Learning**: `habit_learning_learn`, `habit_learning_predict`
- **Predictive**: `predictive_automation_suggest_automation`

---

## Config Flow

7-Step Wizard fuer Ersteinrichtung:

1. **DISCOVERY**: Core Add-on automatisch erkennen
2. **ZONES**: Habitus-Zonen definieren
3. **ZONE_ENTITIES**: Entities den Zonen zuweisen
4. **ENTITIES**: Globale Entity-Konfiguration
5. **FEATURES**: Feature-Toggles
6. **NETWORK**: Verbindungseinstellungen
7. **REVIEW**: Zusammenfassung und Bestaetigung

---

## Dashboard (card_generator.py)

Generiert ein 6-Tab Lovelace-Dashboard:

| Tab | Inhalt | Funktion |
|-----|--------|----------|
| Styx | Brain Graph, Mood, Chat, Suggestions | KI-Uebersicht |
| Haushalt | Praesenz, Zonen, Modi | Haushalts-Status |
| Energie | Verbrauch, Zeitplan, Sankey, Anomalien | Energie-Management |
| Praesenz | Pro-Zone Praesenz, Modi-Statistik | Praesenz-Detail |
| Musik | Sonos, Musikwolke-Controls, Follow | Musik-Steuerung |
| Zone-* | Per-Zone: Licht, Klima, Medien | Zone-Detail |

---

## CopilotRuntime + ModuleRegistry (core/)

Plugin-System fuer modulare Erweiterungen:

```python
runtime = CopilotRuntime.get(hass)
await runtime.async_setup_entry(entry, ["brain_sync", "event_forwarder", ...])
```

- **CopilotModule**: Basisklasse mit `async_setup_entry()` / `async_unload_entry()`
- **ModuleContext**: `(hass, entry)` Wrapper
- **Graceful Degradation**: Fehlgeschlagene Module werden uebersprungen

---

**PilotSuite Styx HA** -- Modul-Referenz v13.7.0
