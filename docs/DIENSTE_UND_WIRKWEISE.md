# PilotSuite Styx -- Dienste und Wirkweise

Version: v14.6.5 | Domain: `copilot_ha` | Stand: 2026-03-16

Dieses Dokument beschreibt alle von der PilotSuite HA-Integration registrierten
Services, den Conversation Agent, STT/TTS-Entities und den Webhook-Empfaenger.

---

## Inhaltsverzeichnis

1. [Uebersicht aller Services](#uebersicht-aller-services)
2. [Kategorie: Installation und Betrieb](#kategorie-installation-und-betrieb)
3. [Kategorie: Tag Registry](#kategorie-tag-registry)
4. [Kategorie: Media Context v2](#kategorie-media-context-v2)
5. [Kategorie: Events Forwarder (N3)](#kategorie-events-forwarder-n3)
6. [Kategorie: Ops Runbook](#kategorie-ops-runbook)
7. [Kategorie: Habitus Dashboard](#kategorie-habitus-dashboard)
8. [Kategorie: Multi-User Preference Learning (MUPL)](#kategorie-multi-user-preference-learning-mupl)
9. [Kategorie: Kamera-Kontext](#kategorie-kamera-kontext)
10. [Kategorie: Debug](#kategorie-debug)
11. [Kategorie: UniFi Netzwerk](#kategorie-unifi-netzwerk)
12. [Kategorie: Predictive Automation](#kategorie-predictive-automation)
13. [Kategorie: Anomalie-Erkennung](#kategorie-anomalie-erkennung)
14. [Kategorie: Energie](#kategorie-energie)
15. [Kategorie: Habit Learning](#kategorie-habit-learning)
16. [Kategorie: HomeKit Bridge](#kategorie-homekit-bridge)
17. [Kategorie: Musikwolke und Zonen-Automation](#kategorie-musikwolke-und-zonen-automation)
18. [Kategorie: Conversation Memory](#kategorie-conversation-memory)
19. [Kategorie: Entity-Zonen-Zuordnung](#kategorie-entity-zonen-zuordnung)
20. [Kategorie: Mood Modul](#kategorie-mood-modul)
21. [Conversation Agent (Styx Assist)](#conversation-agent-styx-assist)
22. [Speech-to-Text (STT)](#speech-to-text-stt)
23. [Text-to-Speech (TTS)](#text-to-speech-tts)
24. [Webhook-Empfaenger (Core -> HA)](#webhook-empfaenger-core---ha)

---

## Uebersicht aller Services

Alle Services werden unter der Domain `copilot_ha` registriert. Die
Registrierung erfolgt zentral in `services_setup.py` via
`async_register_all_services()`, die waehrend `async_setup()` aufgerufen wird.

| Registrierungsfunktion                  | Anzahl Services |
|-----------------------------------------|-----------------|
| `_register_installation_guide_service`  | 1               |
| `_register_tag_registry_services`       | 5               |
| `_register_media_context_v2_services`   | 3               |
| `_register_forwarder_n3_services`       | 3               |
| `_register_ops_runbook_services`        | 4               |
| `_register_habitus_dashboard_cards_services` | (delegiert) |
| `_register_mupl_services`              | 5               |
| `_register_camera_context_services`     | 6               |
| `_register_debug_services`             | 2               |
| `_register_unifi_services`             | 2               |
| `_register_predictive_services`         | 1               |
| `_register_anomaly_services`           | 2               |
| `_register_energy_services`            | 1               |
| `_register_habit_learning_services`     | 2               |
| `_register_homekit_services`           | 2               |
| `_register_musikwolke_services`         | 8               |
| `_register_memory_services`            | 2               |
| `_register_entity_centric_services`     | 4               |
| Mood-Modul (pro Entry)                 | 3               |
| FrontendModule (pro Entry)             | 1               |
| Suggestion Panel (pro Entry)           | ~3              |

---

## Kategorie: Installation und Betrieb

### copilot_ha.show_installation_guide

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Zeigt eine vollstaendige Installationsanleitung als HA Persistent Notification an. |
| Parameter | `entry_id` (optional, string) -- Config Entry ID. Ohne Angabe wird der erste Eintrag verwendet. |
| Wirkweise | Liest Host/Port/Token aus der Config Entry, generiert eine Markdown-Anleitung mit 5 Schritten (Core installieren, konfigurieren, HA konfigurieren, Dashboard, Smoke Test) und zeigt sie als Notification an. |

Beispielaufruf:
```yaml
service: copilot_ha.show_installation_guide
data: {}
```

---

## Kategorie: Tag Registry

Governance-Services fuer das Tag-System (v0.1). Tags klassifizieren Entities
nach Funktion (licht, praesenz, klima, etc.) und werden fuer Neuron-Feed und
Zone-Zuordnung verwendet.

### copilot_ha.tag_registry_upsert_tag

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Erstellt oder aktualisiert einen Tag im lokalen Registry. |
| Parameter | `tag_key` (erforderlich), `title` (optional), `icon` (optional), `color` (optional), `status` (optional) |
| Wirkweise | Ruft `async_upsert_tag()` auf, speichert den Tag persistent im HA-Storage. |

### copilot_ha.tag_registry_set_assignment

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Weist einem Subject (Entity/Zone) eine Liste von Tags zu. |
| Parameter | `subject` (erforderlich, string), `tag_keys` (erforderlich, Liste von Strings) |
| Wirkweise | Ruft `async_set_assignment()` auf. |

### copilot_ha.tag_registry_confirm

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Bestaetigt einen vorgeschlagenen Tag (Governance: Human-in-the-Loop). |
| Parameter | `tag_key` (erforderlich) |
| Wirkweise | Ruft `async_confirm_tag()` auf, setzt Tag-Status auf bestaetigt. |

### copilot_ha.tag_registry_sync_labels_now

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Synchronisiert alle Tags sofort mit HA Labels. |
| Parameter | Keine |
| Wirkweise | Ruft `async_sync_labels_now()` auf. |

### copilot_ha.tag_registry_pull_from_core

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Zieht den kompletten Tag-System-Snapshot vom Core Add-on. |
| Parameter | `entry_id` (optional) |
| Wirkweise | Ruft `async_pull_tag_system_snapshot()` auf, holt Tags von der Core API (`/api/v1/tags`) und merged sie lokal. |

---

## Kategorie: Media Context v2

Services fuer die zonenbasierte Medien-Player-Zuordnung.

### copilot_ha.media_context_v2_suggest_zone_mapping

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Generiert Vorschlaege, welche Media Player welchen Zonen zugeordnet werden sollten. |
| Parameter | `entry_id` (erforderlich) |
| Wirkweise | Erstellt einen `MediaContextV2ConfigManager`, ruft `async_get_zone_suggestions()` auf und feuert ein HA-Event `copilot_ha_media_context_v2_zone_suggestions`. |

### copilot_ha.media_context_v2_apply_zone_suggestions

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Wendet die automatisch generierten Zonen-Zuordnungen an. |
| Parameter | `entry_id` (erforderlich) |
| Wirkweise | Ruft `async_apply_zone_suggestions()` auf, persistiert die Zuordnungen. |

### copilot_ha.media_context_v2_clear_overrides

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Loescht manuelle Zonen-Zuordnungs-Overrides. |
| Parameter | `entry_id` (erforderlich) |
| Wirkweise | Ruft `coordinator_v2.clear_manual_overrides()` auf. |

---

## Kategorie: Events Forwarder (N3)

Services zum manuellen Starten, Stoppen und Abfragen des N3 Event Forwarders.
Der regulaere EventsForwarderModule startet automatisch; diese Services steuern
eine separate N3-Instanz.

### copilot_ha.forwarder_n3_start

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Startet den N3 Event Forwarder fuer eine Config Entry. |
| Parameter | `entry_id` (erforderlich) |
| Wirkweise | Erstellt eine `N3EventForwarder`-Instanz mit vordefinierten Domains (light, climate, media_player, binary_sensor, sensor, cover, lock, person, device_tracker, weather), Batch-Size 50, Flush-Intervall 0.5s. |

### copilot_ha.forwarder_n3_stop

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Stoppt den N3 Event Forwarder. |
| Parameter | `entry_id` (erforderlich) |
| Wirkweise | Ruft `async_stop()` auf dem gespeicherten Forwarder auf. |

### copilot_ha.forwarder_n3_stats

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Gibt Statistiken des Forwarders als HA-Event aus. |
| Parameter | `entry_id` (erforderlich) |
| Wirkweise | Ruft `async_get_stats()` auf, feuert `copilot_ha_forwarder_n3_stats`. |

---

## Kategorie: Ops Runbook

Betriebsservices fuer automatisierte Pruef- und Wartungsablaeufe.

### copilot_ha.ops_runbook_preflight_check

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Fuehrt einen Preflight-Check vor Updates/Releases durch. |
| Parameter | Keine |
| Wirkweise | Prueft Konnektivitaet, Version, Konfiguration. |

### copilot_ha.ops_runbook_smoke_test

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Fuehrt einen Smoke-Test nach Installation/Update durch. |
| Parameter | Keine |
| Wirkweise | Testet Basis-Funktionalitaet (API-Erreichbarkeit, Sensor-States). |

### copilot_ha.ops_runbook_execute_action

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Fuehrt eine benannte Runbook-Aktion aus. |
| Parameter | `action` (erforderlich, string) |
| Wirkweise | Delegiert an `async_execute_runbook_action()`. |

### copilot_ha.ops_runbook_run_checklist

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Fuehrt eine benannte Checkliste ab. |
| Parameter | `checklist` (erforderlich, string) |
| Wirkweise | Delegiert an `async_run_checklist()`. |

---

## Kategorie: Habitus Dashboard

### copilot_ha.get_dashboard_patterns (und weitere)

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Stellt Habitus-Pattern-Daten fuer Dashboard-Cards bereit. |
| Wirkweise | Delegiert an `async_setup_habitus_dashboard_cards_services()`. |

---

## Kategorie: Multi-User Preference Learning (MUPL)

DSGVO-konforme, lokal gespeicherte Praeferenz-Lernfunktionen pro Benutzer (v0.8.0).

### copilot_ha.mupl_learn_preference

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Speichert eine gelernte Praeferenz fuer einen Benutzer. |
| Parameter | `user_id` (erforderlich), `preference_type` (erforderlich), `value` (erforderlich, float oder dict), `zone` (optional) |
| Wirkweise | Ruft `mupl.set_preference()` auf. |

### copilot_ha.mupl_set_user_priority

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Setzt die Prioritaet eines Benutzers (0.0 bis 1.0). |
| Parameter | `user_id` (erforderlich), `priority` (erforderlich, float 0.0-1.0) |
| Wirkweise | Bestimmt Gewichtung bei Konflikten zwischen Benutzerpraeferenzen. |

### copilot_ha.mupl_delete_user_data

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Loescht alle Praeferenzdaten eines Benutzers (DSGVO: Recht auf Loeschung). |
| Parameter | `user_id` (erforderlich) |

### copilot_ha.mupl_export_user_data

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Exportiert alle Praeferenzdaten eines Benutzers (DSGVO: Recht auf Datenuebertragbarkeit). |
| Parameter | `user_id` (erforderlich) |
| Wirkweise | Feuert Event `copilot_ha_mupl_user_data_exported` mit den exportierten Daten. |

### copilot_ha.mupl_get_active_conflicts

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Zeigt aktive Konflikte zwischen Benutzerpraeferenzen an. |
| Wirkweise | Nur verfuegbar wenn MUPL-Modul aktiviert. |

---

## Kategorie: Kamera-Kontext

Services fuer die Kamera-Integration (Frigate-Bridge, Bewegungserkennung).

### copilot_ha.camera_trigger_motion

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Meldet ein Bewegungsereignis fuer eine Kamera. |
| Parameter | `camera_id` (erforderlich), `camera_name` (optional), `confidence` (optional, float), `zone` (optional), `thumbnail` (optional) |
| Wirkweise | Ruft `coordinator.async_add_motion_event()` auf, aktualisiert Kamerastatus. |

### copilot_ha.camera_trigger_presence

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Meldet ein Praesenz-Erkennungsereignis. |
| Parameter | `camera_id` (erforderlich), `camera_name` (optional), `presence_type` (optional), `person_name` (optional), `confidence` (optional) |

### copilot_ha.camera_trigger_activity

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Meldet ein Aktivitaetsereignis (z.B. "kochen", "fernsehen"). |
| Parameter | `camera_id` (erforderlich), `camera_name` (optional), `activity_type` (erforderlich), `duration_seconds` (optional), `confidence` (optional) |

### copilot_ha.camera_trigger_zone

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Meldet ein Zonenereignis (Person betritt/verlaesst Kamerazone). |
| Parameter | `camera_id` (erforderlich), `zone_name` (erforderlich), `event_type` (optional, Standard: "entered"), `object_type` (optional) |

### copilot_ha.camera_clear_motion

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Setzt den Bewegungsstatus einer Kamera zurueck. |
| Parameter | `camera_id` (erforderlich) |

### copilot_ha.camera_set_retention

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Setzt die Aufbewahrungsdauer fuer Kameraereignisse. |
| Parameter | `camera_id` (erforderlich), `hours` (erforderlich, int) |

---

## Kategorie: Debug

### copilot_ha.set_debug

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Aktiviert oder deaktiviert den Debug-Modus. |
| Parameter | `enabled` (erforderlich, bool) |
| Wirkweise | Delegiert an `enable_debug` / `disable_debug` Services (aus debug.py). |

### copilot_ha.clear_error_digest

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Leert den Error-Digest-Puffer. |
| Parameter | Keine |

---

## Kategorie: UniFi Netzwerk

### copilot_ha.copilot_ha_unifi_run_diagnostics

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Fuehrt UniFi-Netzwerkdiagnostik durch. |
| Parameter | Keine |
| Wirkweise | Feuert Event `copilot_ha_unifi_diagnostics` mit Ergebnis. |

### copilot_ha.copilot_ha_unifi_get_report

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Generiert einen UniFi-Netzwerkbericht. |
| Parameter | Keine |
| Wirkweise | Feuert Event `copilot_ha_unifi_report` mit Bericht. |

---

## Kategorie: Predictive Automation

### copilot_ha.predictive_automation_suggest_automation

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Erstellt einen manuellen Automatisierungsvorschlag basierend auf einem Pattern. |
| Parameter | `pattern` (erforderlich, string), `confidence` (optional, float), `zone` (optional, string) |
| Wirkweise | Feuert Event `copilot_ha_predictive_suggestion`. |

---

## Kategorie: Anomalie-Erkennung

### copilot_ha.anomaly_alert_check_and_alert

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Prueft eine Entity auf Anomalien (ungewoehnliche Werte). |
| Parameter | `device_id` (erforderlich, Entity-ID), `threshold` (optional, float, Standard: 0.7) |
| Wirkweise | Liest den aktuellen State, feuert Event `copilot_ha_anomaly_check`. |

### copilot_ha.anomaly_alert_clear_history

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Loescht die Anomalie-Historie. |
| Parameter | Keine |

---

## Kategorie: Energie

### copilot_ha.energy_insights_get

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Sammelt Energie-Einsichten fuer ein Geraet oder alle Energie-Entities. |
| Parameter | `device_id` (optional, string), `hours` (optional, int, Standard: 24) |
| Wirkweise | Sammelt bis zu 20 Energie/Power-Sensor-Werte, feuert Event `copilot_ha_energy_insights`. |

---

## Kategorie: Habit Learning

### copilot_ha.habit_learning_learn

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Meldet ein gelerntes Gewohnheitsereignis. |
| Parameter | `device_id` (erforderlich), `event_type` (erforderlich), `device_chain` (optional, Liste) |
| Wirkweise | Speichert im Memory-Puffer (max 1000 Eintraege), feuert Event `copilot_ha_habit_learned`. |

### copilot_ha.habit_learning_predict

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Erstellt eine Vorhersage basierend auf gelernten Gewohnheiten. |
| Parameter | `device_id` (erforderlich), `event_type` (erforderlich), `start_device` (optional) |
| Wirkweise | Frequenzbasierte Vorhersage aus dem Puffer, feuert Event `copilot_ha_habit_prediction`. |

---

## Kategorie: HomeKit Bridge

### copilot_ha.homekit_enable_zone

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Aktiviert eine Habitus-Zone fuer die HomeKit-Bridge. |
| Parameter | `zone_id` (erforderlich), `zone_name` (optional) |
| Wirkweise | Registriert alle Zone-Entities in der HomeKit-Bridge, feuert `copilot_ha_homekit_zone_toggled`. |

### copilot_ha.homekit_disable_zone

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Deaktiviert eine Habitus-Zone in der HomeKit-Bridge. |
| Parameter | `zone_id` (erforderlich) |

---

## Kategorie: Musikwolke und Zonen-Automation

### copilot_ha.musikwolke_create

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Erstellt eine Musikwolke-Gruppe ueber mehrere Zonen (synchronisierte Wiedergabe). |
| Parameter | `zone_ids` (erforderlich, Liste) |
| Wirkweise | Ruft Core API `/api/v1/musikwolke/create` auf. |

### copilot_ha.musikwolke_dissolve

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Loest eine Musikwolke-Gruppe auf. |
| Parameter | `zone_ids` (erforderlich, Liste) |

### copilot_ha.musikwolke_play

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Startet Medienwiedergabe in einer Zone. |
| Parameter | `zone_id` (erforderlich), `volume_pct` (optional, int 0-100) |
| Wirkweise | Ruft Core API `/api/v1/media/zones/{zone_id}/play` auf. |

### copilot_ha.musikwolke_pause

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Pausiert Medienwiedergabe in einer Zone. |
| Parameter | `zone_id` (erforderlich) |

### copilot_ha.musikwolke_volume

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Setzt die Lautstaerke einer Zone. |
| Parameter | `zone_id` (erforderlich), `volume_pct` (erforderlich, int 0-100) |

### copilot_ha.musikwolke_start_follow

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Startet eine Follow-Session: Musik folgt einer Person von Zone zu Zone. |
| Parameter | `person_id` (erforderlich), `source_zone` (erforderlich) |
| Wirkweise | Ruft Core API `/api/v1/media/musikwolke/start` auf. |

### copilot_ha.musikwolke_stop_follow

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Stoppt eine laufende Follow-Session. |
| Parameter | `session_id` (erforderlich) |

### copilot_ha.zone_automation_set_mode

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Setzt den Automationsmodus einer Zone. |
| Parameter | `zone_id` (erforderlich), `mode` (erforderlich, einer von: `off`, `learning`, `autonomy`) |
| Wirkweise | Ruft Core API `/api/v1/zone-automation/zones/{zone_id}/mode` auf. |

Beispielaufruf:
```yaml
service: copilot_ha.zone_automation_set_mode
data:
  zone_id: "wohnbereich"
  mode: "learning"
```

---

## Kategorie: Conversation Memory

### copilot_ha.get_memory_stats

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Holt ConversationMemory-Statistiken vom Core (gelernte Praeferenzen, Thread-Zaehler). |
| Parameter | Keine |
| Wirkweise | Ruft Core API `/api/styx/memory` auf, feuert Event `copilot_ha_memory_stats`. |

### copilot_ha.get_memory_history

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Holt die Gespraechshistorie eines bestimmten Threads. |
| Parameter | `conversation_id` (optional, Standard: ""), `limit` (optional, int 1-100, Standard: 20) |
| Wirkweise | Ruft Core API `/api/styx/memory/history` auf, feuert Event `copilot_ha_memory_history`. |

---

## Kategorie: Entity-Zonen-Zuordnung

### copilot_ha.assign_entity_to_zone

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Weist eine Entity einer Habitus-Zone zu. |
| Parameter | `entity_id` (erforderlich), `zone_id` (erforderlich) |
| Wirkweise | Ruft `async_assign_entity_to_zone()` auf. |

### copilot_ha.remove_entity_from_zone

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Entfernt eine Entity aus ihrer aktuellen Zone. |
| Parameter | `entity_id` (erforderlich) |

### copilot_ha.tag_entity

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Weist einer Entity Tags zu (kommasepariert). |
| Parameter | `entity_id` (erforderlich), `tag_ids` (erforderlich, kommaseparierter String) |
| Wirkweise | Fuegt die Entity zu den angegebenen Tags im EntityTagStore hinzu. |

### copilot_ha.untag_entity

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Entfernt Tags von einer Entity. |
| Parameter | `entity_id` (erforderlich), `tag_ids` (erforderlich, kommaseparierter String) |

---

## Kategorie: Mood Modul

Diese Services werden pro Config Entry registriert (Entry-ID im Servicenamen).

### copilot_ha.mood_orchestrate_zone_{entry_id}

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Fuehrt Mood-Inference und daraus abgeleitete Aktionen fuer eine einzelne Zone durch. |
| Parameter | `zone_name` (erforderlich), `dry_run` (optional, bool), `force_actions` (optional, bool) |
| Wirkweise | Sammelt Sensordaten, ruft Core API `/api/v1/mood/zones/{zone}/orchestrate` auf, fuehrt resultierende HA-Service-Calls lokal aus (wenn nicht dry_run). |

### copilot_ha.mood_orchestrate_all_{entry_id}

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Fuehrt Mood-Orchestrierung fuer alle konfigurierten Zonen durch. |
| Parameter | `dry_run` (optional, bool), `force_actions` (optional, bool) |

### copilot_ha.mood_force_mood_{entry_id}

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Erzwingt einen bestimmten Mood-Zustand fuer eine Zone. |
| Parameter | `zone_name` (erforderlich), `mood_state` (erforderlich), `duration_minutes` (optional, int) |
| Wirkweise | Ruft Core API `/api/v1/mood/zones/{zone}/force_mood` auf. |

---

## Kategorie: Frontend

### copilot_ha.refresh_dashboard

| Eigenschaft | Wert |
|-------------|------|
| Zweck | Generiert das PilotSuite-Dashboard neu (alle 8 Views). |
| Parameter | Keine |
| Wirkweise | Registriert durch das FrontendModule. Reagiert auch automatisch auf Zonen-Aenderungen (debounced). |

---

## Conversation Agent (Styx Assist)

**Klasse:** `StyxConversationAgent` in `conversation.py`

Der Conversation Agent implementiert `AbstractConversationAgent` und wird als
HA Voice Assistant registriert. Nutzer koennen PilotSuite unter
"Einstellungen > Sprachassistenten" als Standard-Agent waehlen.

| Eigenschaft | Wert |
|-------------|------|
| Unterstuetzte Sprachen | `de`, `en` |
| Registrierung | `async_setup_conversation()` waehrend `async_setup_entry()` |
| Core-Endpoint | `POST /v1/chat/completions` |
| Timeout | 90 Sekunden (fuer Ollama auf HA-Hardware) |
| Modell | `pilotsuite` (internes Routing auf qwen3 via Core) |
| Conversation-ID | Wird normalisiert und ueber Sessions beibehalten |

**Ablauf:**

1. Benutzer spricht oder tippt eine Nachricht
2. `async_process()` empfaengt `ConversationInput`
3. Nachricht wird als `{"role": "user", "content": text}` an Core gesendet
4. Core verarbeitet via Ollama LLM (qwen3), nutzt ConversationMemory fuer Kontext
5. Antwort wird als `ConversationResult` mit `IntentResponse` zurueckgegeben

**Fehlerbehandlung:** Bei CopilotApiError oder Timeout wird eine
deutschsprachige Fehlermeldung zurueckgegeben ("PilotSuite Core ist gerade
nicht erreichbar.").

---

## Speech-to-Text (STT)

**Klasse:** `PilotSuiteSTTEntity` in `stt.py`

| Eigenschaft | Wert |
|-------------|------|
| Entity-Name | PilotSuite STT |
| Unterstuetzte Sprachen | de, en, fr, es, it, nl, pt, pl, ru, ja, zh |
| Audio-Format | WAV, PCM, 16-bit, 16000 Hz, Mono |
| Core-Endpoint | `POST /api/v1/styx/stt?language={lang}` |
| Timeout | 30 Sekunden |
| Backend | Whisper via Ollama oder Cloud-Fallback |

**Ablauf:**

1. Audio-Stream wird chunk-weise empfangen und in einen Puffer gesammelt
2. Rohe PCM-Daten werden in einen WAV-Container verpackt
3. WAV-Daten werden an den Core-STT-Endpoint gesendet
4. Transkription wird als `SpeechResult` zurueckgegeben

---

## Text-to-Speech (TTS)

**Klasse:** `PilotSuiteTTSEntity` in `tts.py`

| Eigenschaft | Wert |
|-------------|------|
| Entity-Name | PilotSuite TTS |
| Unterstuetzte Sprachen | de, en, fr, es, it |
| Ausgabeformat | MP3 |
| Core-Endpoint | `POST /api/v1/styx/tts` |
| Timeout | 30 Sekunden |
| Backend | edge-tts (Microsoft Edge TTS) |

**Verfuegbare Stimmen (Auswahl):**

| Sprache | Stimmen |
|---------|---------|
| de | Conrad, Katja, Amala, Ingrid (AT), Leni (CH) |
| en | Guy, Jenny, Ryan (GB), Sonia (GB) |
| fr | Henri, Denise |
| es | Alvaro, Elvira |
| it | Diego, Elsa |

---

## Webhook-Empfaenger (Core -> HA)

**Datei:** `webhook.py`

Der Webhook-Empfaenger wird waehrend `async_setup_entry()` registriert und
empfaengt Push-Events vom Core Add-on in Echtzeit.

### Registrierung

- Webhook-ID wird pro Config Entry generiert und persistent gespeichert
- URL: `https://{ha_url}/api/webhook/{webhook_id}`
- Registriert via `homeassistant.components.webhook.async_register()`

### Authentifizierung

Dreistufig mit Legacy-Transition-Support:

1. **Kanonischer Header:** `X-Auth-Token`
2. **Bearer Token:** `Authorization: Bearer {token}`
3. **Legacy Header:** Konfigurierbar mit Sunset-Datum

Optional: HMAC-Signaturverifikation via Umgebungsvariable
`PILOTSUITE_WEBHOOK_SIGNING_SECRET_PRIMARY` (SHA-256, Nonce-Replay-Schutz).

### Unterstuetzte Event-Typen

| Event-Typ | Wirkweise |
|-----------|-----------|
| `status` | Aktualisiert `ok` und `version` im Coordinator |
| `mood` | Merged Mood-Daten (Stimmung, Konfidenz) in Coordinator, sofortige Entity-Aktualisierung |
| `neuron` | Merged Neuron-States in Coordinator |
| `suggestion` | Feuert `copilot_ha_suggestion_received` HA-Event fuer Suggestion Panel |
| `module_data` | Aktualisiert Smart Home Module (Licht, Helligkeit, Heizung, Bewegung, Praesenz) |
| `zone_update` | Aktualisiert zonenspezifische Daten im Coordinator |
| `anomaly` | Merged in alert_history (max 50), feuert `copilot_ha_anomaly_detected` bei warning/critical |
| `autonomy_executed` | Speichert in autonomy_history (max 50), feuert `copilot_ha_autonomy_executed` |
| `autonomy_failed` | Speichert in autonomy_errors (max 20), feuert `copilot_ha_autonomy_failed` |
| `scene_captured` | Feuert `copilot_ha_scene_captured` |
| `scene_applied` | Feuert `copilot_ha_scene_applied` |
| `module_zone_state_changed` | Aktualisiert pro-Zone/pro-Modul State im Coordinator |

### Envelope-Format

```json
{
  "type": "mood",
  "data": {
    "mood": "gemuetlich",
    "confidence": 0.87
  }
}
```

### Fehlerbehandlung

Strukturierte Fehlerantworten mit Error-Codes:

| Code | HTTP | Beschreibung |
|------|------|-------------|
| `invalid_json` | 400 | Kein gueltiges JSON |
| `missing_type` | 400 | Feld `type` fehlt |
| `unknown_type` | 400 | Unbekannter Event-Typ |
| `invalid_token` | 401 | Token fehlt oder ungueltig |
| `invalid_signature` | 401 | HMAC-Signatur ungueltig |
| `replay_detected` | 401 | Nonce bereits verwendet |
| `rate_limited` | 429 | Rate Limit ueberschritten |
| `payload_too_large` | 413 | Payload zu gross |
