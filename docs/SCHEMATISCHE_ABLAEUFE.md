# PilotSuite Styx -- Schematische Ablaeufe

Version: v14.6.5 | Stand: 2026-03-16

Dieses Dokument zeigt die wichtigsten Ablaeufe als ASCII-Diagramme.

---

## Inhaltsverzeichnis

1. [Setup Flow](#1-setup-flow)
2. [Boot Flow](#2-boot-flow)
3. [Event Flow](#3-event-flow)
4. [Suggestion Flow](#4-suggestion-flow)
5. [Chat Flow](#5-chat-flow)
6. [Zone Automation Flow](#6-zone-automation-flow)
7. [Mood Flow](#7-mood-flow)
8. [Dashboard Generation Flow](#8-dashboard-generation-flow)
9. [Discovery und Failover Flow](#9-discovery-und-failover-flow)
10. [Webhook Push Flow](#10-webhook-push-flow)

---

## 1. Setup Flow

Installation -> Config Flow (3 Pfade) -> Discovery -> Token -> Entry

```
+------------------+
|  HACS Install    |
|  PilotSuite HA   |
+--------+---------+
         |
         v
+------------------+
|  Settings >      |
|  Integrations >  |
|  + PilotSuite    |
+--------+---------+
         |
         v
+------------------+
|  Config Flow     |
|  async_step_user |
+--------+---------+
         |
         +---------------------------+---------------------------+
         |                           |                           |
         v                           v                           v
+------------------+  +--------------------+  +-------------------+
|  Zero Config     |  |  Quick Start       |  |  Manual Setup     |
|                  |  |  (Wizard)          |  |                   |
+--------+---------+  +--------+-----------+  +--------+----------+
         |                     |                        |
         |            +--------v-----------+            |
         |            | STEP 1: Discovery  |            |
         |            | (Host/Port Auto)   |            |
         |            +--------+-----------+            |
         |                     |                        |
         |            +--------v-----------+            |
         |            | STEP 2: Zones      |            |
         |            | (HA Areas waehlen) |            |
         |            +--------+-----------+            |
         |                     |                        |
         |            +--------v-----------+            |
         |            | STEP 3: Zone       |            |
         |            |   Entities         |            |
         |            +--------+-----------+            |
         |                     |                        |
         |            +--------v-----------+            |
         |            | STEP 4: Entities   |            |
         |            | (Profil waehlen)   |            |
         |            +--------+-----------+            |
         |                     |                        |
         |            +--------v-----------+            |
         |            | STEP 5: Features   |            |
         |            | (Module an/aus)    |            |
         |            +--------+-----------+            |
         |                     |                        |
         |            +--------v-----------+            |
         |            | STEP 6: Network    |            |
         |            | (Host/Port/Token)  |            |
         |            +--------+-----------+            |
         |                     |                        |
         |            +--------v-----------+            |
         |            | STEP 7: Review     |            |
         |            | (Zusammenfassung)  |            |
         |            +--------+-----------+            |
         |                     |                        |
         +---------------------+------------------------+
                               |
                               v
                  +----------------------------+
                  | discover_reachable_core_   |
                  | endpoint()                 |
                  | (Kandidatenliste proben)   |
                  +-------------+--------------+
                                |
                                v
                  +----------------------------+
                  | fetch_setup_token()        |
                  | GET /api/v1/auth/          |
                  |     setup-token            |
                  +-------------+--------------+
                                |
                                v
                  +----------------------------+
                  | async_create_entry()       |
                  | Title: "Styx - PilotSuite" |
                  | Data: host, port, token    |
                  +----------------------------+
```

---

## 2. Boot Flow

async_setup_entry() -> Migrations -> Discovery -> Module -> Coordinator -> Entities

```
+-------------------------------+
| async_setup_entry(hass, entry)|
+---------------+---------------+
                |
                v
+-------------------------------+
| 1. Migrate Connection Config  |
|    (Legacy Keys entfernen,    |
|     Host/Port normalisieren)  |
+---------------+---------------+
                |
                v
+-------------------------------+
| 2. Discover & Persist         |
|    _discover_and_persist()    |
|    +-- build_candidate_hosts()|
|    +-- /health Probe          |
|    +-- fetch_setup_token()    |
|    +-- Config Entry update    |
|    (Retry nach 30s bei Fehler)|
+---------------+---------------+
                |
                v
+-------------------------------+
| 3. Migrate Entry Identity     |
|    (Device-ID konsolidieren,  |
|     Legacy-Devices aufloesen) |
+---------------+---------------+
                |
                v
+-------------------------------+
| 4. Migrate Legacy Sensor IDs  |
|    (Host:Port -> stabile IDs) |
+---------------+---------------+
                |
                v
+-------------------------------+
| 5. Cleanup Legacy Text        |
|    Entities (obsolete text.*) |
+---------------+---------------+
                |
                v
+-------------------------------+
| 6. Install Blueprints         |
+---------------+---------------+
                |
                v
+-------------------------------+
| 7. CopilotRuntime             |
|    _get_runtime(hass)         |
|    +-- 31 Module registrieren |
|    +-- async_setup_entry()    |
|        fuer jedes Modul       |
|                               |
|    Module:                    |
|    - legacy                   |
|    - performance_scaling      |
|    - events_forwarder         |
|    - history_backfill         |
|    - dev_surface              |
|    - habitus_miner            |
|    - ops_runbook              |
|    - brain_graph_sync         |
|    - candidate_poller         |
|    - media_zones              |
|    - mood                     |
|    - mood_context             |
|    - energy_context           |
|    - weather_context          |
|    - knowledge_graph_sync     |
|    - ml_context               |
|    - camera_context           |
|    - quick_search             |
|    - voice_context            |
|    - home_alerts              |
|    - character_module         |
|    - entity_tags              |
|    - person_tracking          |
|    - scene_module             |
|    - licht_module             |
|    - helligkeit_module        |
|    - heiz_module              |
|    - bewegung_module          |
|    - praesenz_module          |
|    - frontend_module          |
|    - ...                      |
+---------------+---------------+
                |
                v
+-------------------------------+
| 8. coordinator.modules_ready  |
|    = True                     |
+---------------+---------------+
                |
                v
+-------------------------------+
| 9. UserPreferenceModule       |
|    (wenn aktiviert)           |
+---------------+---------------+
                |
                v
+-------------------------------+
| 10. MultiUserPreference       |
|     Module (MUPL v0.8.0)      |
+---------------+---------------+
                |
                v
+-------------------------------+
| 11. ZoneDetector              |
|     (Proaktive Zone-Entry-    |
|      Weiterleitung)           |
+---------------+---------------+
                |
                v
+-------------------------------+
| 12. Zone Auto-Setup           |
|     async_auto_create_        |
|     habitus_zones()           |
|     (HA Areas -> Zonen)       |
+---------------+---------------+
                |
                v
+-------------------------------+
| 13. Webhook registrieren      |
|     async_register_webhook()  |
+---------------+---------------+
                |
                v
+-------------------------------+
| 14. Conversation Agent        |
|     async_setup_conversation()|
+---------------+---------------+
                |
                v
+-------------------------------+
| 15. Suggestion Panel          |
| 16. Lovelace Card Resources   |
| 17. Dashboard Wiring          |
| 18. Storage Dashboard         |
| 19. Onboarding Notification   |
+-------------------------------+
```

---

## 3. Event Flow

HA state_changed -> EventsForwarder -> Batch -> Core /api/v1/events -> Brain Graph

```
+---------------------+
| HA Entity State     |
| aendert sich        |
| (z.B. light.wohn-   |
|  zimmer: off -> on)  |
+----------+----------+
           |
           | state_changed Event
           v
+---------------------+
| async_track_state_  |
| change_event()      |
| (Subscription auf   |
|  alle Allowlist-     |
|  Entities)           |
+----------+----------+
           |
           v
+---------------------+     +--------------------+
| _handle_state()     | --> | Pruefungen:        |
|                     |     | - In Allowlist?    |
|                     |     | - Neuron-Exclusion?|
|                     |     | - State geaendert? |
|                     |     | - Idempotenz-Check |
+----------+----------+     +--------------------+
           |
           | Bestanden
           v
+---------------------+
| Canonical Envelope   |
| erstellen:           |
| {id, ts, type,       |
|  entity_id,          |
|  attributes: {       |
|    domain, zone_ids, |
|    old_state,        |
|    new_state,        |
|    state_attributes, |
|    neuron_tags       |
|  }}                  |
+----------+----------+
           |
           v
+---------------------+
| _enqueue(item)      |
| -> Bounded Queue    |
| (drop-oldest bei    |
|  Ueberlauf)         |
+----------+----------+
           |
           +-------------- Queue >= max_batch? ---> Sofort flushen
           |
           v (sonst)
+---------------------+
| Timer (Standard 5s) |
| async_call_later()  |
+----------+----------+
           |
           v
+---------------------+
| _flush_now()        |
| 1. Rate Limit Check |
| 2. Backoff Check    |
| 3. Items aus Queue  |
|    (max max_batch)  |
+----------+----------+
           |
           v
+---------------------+     +--------------------+
| POST /api/v1/events | --> | Core Add-on:       |
| {"items": [...]}    |     | Brain Graph Ingest  |
+---------------------+     | Pattern Mining      |
                             | Neuron Evaluation   |
                             +--------------------+
```

---

## 4. Suggestion Flow

Brain Graph Patterns -> Habitus Miner -> Candidates -> Webhook -> HA UI -> Accept -> Automation

```
+---------------------+
| Core: Brain Graph   |
| (Events akkumuliert)|
+----------+----------+
           |
           v
+---------------------+
| Frequent Pattern    |
| Mining              |
| (min_support,       |
|  min_confidence)    |
+----------+----------+
           |
           v
+---------------------+
| Habitus Miner       |
| Kandidaten erzeugen |
| - Pattern           |
| - Confidence        |
| - Lift              |
| - Support Count     |
| - Zone Context      |
| - Mood Context      |
+----------+----------+
           |
           v
+---------------------+
| Webhook Push        |
| type: "suggestion"  |
| data: {             |
|   pattern, conf,    |
|   zone_id, ...      |
| }                   |
+----------+----------+
           |
           | HTTP POST /api/webhook/{id}
           v
+---------------------+
| HA: Webhook Handler |
| -> hass.bus.        |
|    async_fire(       |
|    "copilot_ha_     |
|     suggestion_     |
|     received")      |
+----------+----------+
           |
           v
+---------------------+
| Suggestion Panel    |
| (HA Repairs UI /    |
|  Issue Registry)    |
|                     |
| Anzeige:            |
| - Pattern Text      |
| - Konfidenz-Balken  |
| - Zone/Mood Kontext |
| - Risiko-Level      |
+----------+----------+
           |
           v
+----+-----+-----+----+
|    |           |     |
v    v           v     v
Accept  Reject  Snooze  Expire
  |       |       |       |
  v       |       |       |
+-------+ |       |       |
|HA Auto| |       |       |
|mation | |       |       |
|aus    | |       |       |
|Blue-  | |       |       |
|print  | |       |       |
|er-    | |       |       |
|stellen| |       |       |
+-------+ |       |       |
          v       v       v
   Status: rejected/snoozed/expired
   (Pattern gespeichert fuer
    zukuenftige Filterung)
```

---

## 5. Chat Flow

User -> Conversation Agent -> Core /v1/chat/completions -> Ollama LLM -> Response

```
+---------------------+
| Benutzer:           |
| "Mach das Licht im  |
|  Wohnzimmer an"     |
+----------+----------+
           |
           v
+---------------------+
| HA Voice Pipeline   |
| oder Chat-Card      |
+----------+----------+
           |
           v
+---------------------+
| StyxConversation-   |
| Agent.async_process |
| (ConversationInput) |
+----------+----------+
           |
           +-- Coordinator vorhanden?
           |   Nein -> Fehlermeldung
           |
           v
+---------------------+
| conversation_id     |
| normalisieren       |
| (UUID-Format)       |
+----------+----------+
           |
           v
+---------------------+
| coordinator.api.    |
| async_chat_         |
| completions(        |
|   messages=[{       |
|     "role": "user", |
|     "content": text |
|   }],               |
|   conversation_id   |
| )                   |
+----------+----------+
           |
           | POST /v1/chat/completions
           | Timeout: 90s
           v
+---------------------+     +---------------------+
| Core Add-on:        |     | Ollama LLM          |
|                     | --> | Modell: qwen3:0.6b  |
| 1. Conversation-    |     | (oder konfiguriert) |
|    Memory laden     |     |                     |
| 2. System-Prompt    |     | Inferenz auf        |
|    mit HA-Kontext   |     | lokaler Hardware    |
|    zusammenbauen    |     |                     |
| 3. An LLM senden   |     +----------+----------+
| 4. Antwort in       |                |
|    Memory speichern |     <----------+
+----------+----------+
           |
           | Response:
           | {"choices": [{"message": {"content": "..."}}]}
           v
+---------------------+
| Content extrahieren |
+----------+----------+
           |
           v
+---------------------+
| IntentResponse      |
| erstellen           |
| -> speech = reply   |
+----------+----------+
           |
           v
+---------------------+
| ConversationResult  |
| an HA zurueck       |
+---------------------+
```

---

## 6. Zone Automation Flow

Praesenz erkannt -> Zone aktiv -> Licht/Musik steuern -> Follow-Modus

```
+---------------------+
| binary_sensor.      |
| motion_wohnzimmer   |
| State: on           |
+----------+----------+
           |
           v
+---------------------+     +---------------------+
| EventsForwarder     | --> | Core: Brain Graph   |
| state_changed       |     | Event ingest        |
+---------------------+     +----------+----------+
                                        |
                                        v
                             +---------------------+
                             | Zone Automation      |
                             | Engine (Core)        |
                             |                      |
                             | Zone: wohnbereich    |
                             | Mode: learning |     |
                             |       autonomy       |
                             +----------+----------+
                                        |
                     +------------------+------------------+
                     |                                     |
                     v                                     v
          +---------------------+              +---------------------+
          | Licht-Steuerung     |              | Musik-Steuerung     |
          |                     |              |                     |
          | auto_enabled: true  |              | Musikwolke:         |
          | Helligkeit anpassen |              | Zone-Wiedergabe     |
          | basierend auf:      |              | starten/pausieren   |
          | - Tageszeit         |              | basierend auf:      |
          | - Outdoor Lux       |              | - Praesenz          |
          | - Praesenz-Dauer    |              | - Tageszeit         |
          | - Mood-State        |              | - User-Praeferenz   |
          +----------+----------+              +----------+----------+
                     |                                     |
                     v                                     v
          +---------------------+              +---------------------+
          | Webhook Push oder   |              | Webhook Push oder   |
          | HA Service Call     |              | HA Service Call     |
          | light.turn_on       |              | media_player.       |
          | {"brightness": 180} |              |   play_media        |
          +---------------------+              +---------------------+

                     +---------------------+
                     | Follow-Modus:       |
                     |                     |
                     | Person wechselt     |
                     | Zone (device_tracker|
                     | / person.*)         |
                     |         |           |
                     |         v           |
                     | Musikwolke:         |
                     | source_zone ->      |
                     | target_zone         |
                     | (Musik folgt)       |
                     +---------------------+

Zone-Modi:
  off       = Keine Automatisierung
  learning  = Beobachten, Patterns sammeln, Vorschlaege machen
  autonomy  = Eigenstaendig handeln (mit Governance-Grenzen)
```

---

## 7. Mood Flow

Sensor-Daten -> Neuron-Layers -> Softmax -> Mood-State -> Mood-Aktionen

```
+---------------------+     +---------------------+     +---------------------+
| Context Layer       |     | State Layer          |     | Mood Layer           |
|                     |     |                      |     |                      |
| - temperature       |     | - motion             |     | - lights             |
| - humidity          |     | - door               |     | - brightness         |
| - co2               |     | - window             |     | - media              |
| - pressure          |     | - lock               |     | - noise              |
| - energy            |     | - cover              |     |                      |
| - power             |     | - heating            |     |                      |
+----------+----------+     +----------+-----------+     +----------+-----------+
           |                           |                            |
           +---------------------------+----------------------------+
                                       |
                                       v
                          +----------------------------+
                          | Core: Neuron Evaluation    |
                          | POST /api/v1/neurons/      |
                          |       evaluate             |
                          |                            |
                          | Input:                     |
                          | - Entity States            |
                          | - Zeitkontext              |
                          | - Wetter                   |
                          | - Praesenz                 |
                          +-------------+--------------+
                                        |
                                        v
                          +----------------------------+
                          | Gewichtung pro Layer       |
                          |                            |
                          | Context: 0.3               |
                          | State:   0.3               |
                          | Mood:    0.4               |
                          |                            |
                          | (Optional: Character-      |
                          |  Service Modifikation)     |
                          +-------------+--------------+
                                        |
                                        v
                          +----------------------------+
                          | Softmax-Normalisierung     |
                          |                            |
                          | gemuetlich:  0.42          |
                          | entspannt:   0.28          |
                          | konzentriert: 0.15         |
                          | energetisch: 0.10          |
                          | ruhig:       0.05          |
                          +-------------+--------------+
                                        |
                                        v
                          +----------------------------+
                          | Dominanter Mood:           |
                          | "gemuetlich" (conf: 0.42)  |
                          +-------------+--------------+
                                        |
                     +------------------+------------------+
                     |                                     |
                     v                                     v
          +---------------------+              +---------------------+
          | Webhook Push        |              | Coordinator Polling  |
          | type: "mood"        |              | GET /api/v1/neurons/ |
          | data: {             |              |     mood             |
          |   mood: "gemuetlich"|              +----------+----------+
          |   confidence: 0.42  |                         |
          | }                   |                         |
          +----------+----------+                         |
                     |                                    |
                     +------------------------------------+
                                       |
                                       v
                          +----------------------------+
                          | HA Entities aktualisiert:  |
                          | sensor.copilot_ha_mood     |
                          | = "gemuetlich"             |
                          +-------------+--------------+
                                        |
                                        v
                          +----------------------------+
                          | Mood-Aktionen (optional):  |
                          |                            |
                          | MoodModule.                |
                          | _orchestrate_zone()        |
                          |                            |
                          | -> Licht anpassen           |
                          | -> Musik aendern            |
                          | -> Szene anwenden           |
                          +----------------------------+
```

---

## 8. Dashboard Generation Flow

Zonen-Aenderung -> FrontendModule -> card_generator -> Storage Dashboard Update

```
+---------------------+
| Trigger:            |
| - Zonen geaendert   |
|   (SIGNAL_HABITUS_  |
|    ZONES_V2_UPDATED)|
| - Service Call      |
|   refresh_dashboard |
| - async_setup_entry |
|   (erster Start)    |
+----------+----------+
           |
           v
+---------------------+
| FrontendModule      |
| _on_zones_updated() |
| oder                |
| _handle_refresh_    |
|  dashboard()        |
+----------+----------+
           |
           v
+---------------------+
| Debounce (5s)       |
| (Mehrere Zonen-     |
|  Aenderungen        |
|  zusammenfassen)    |
+----------+----------+
           |
           v
+---------------------+
| card_generator.py   |
| Dashboard erzeugen: |
|                     |
| Tab 1: Styx         |
|   - Brain Graph     |
|   - Mood Sensor     |
|   - Chat Card       |
|   - Suggestions     |
|                     |
| Tab 2: Haushalt     |
|   - Praesenz        |
|   - Zonen-Status    |
|   - Wetter          |
|                     |
| Tab 3: Energie      |
|   - Verbrauch       |
|   - Produktion      |
|   - Anomalien       |
|                     |
| Tab 4: Praesenz     |
|   - Pro-Zone-Status |
|   - Automation-Modi |
|                     |
| Tab 5: Musik        |
|   - Sonos/Musikwolke|
|                     |
| Tab 6+: Pro Zone    |
|   - Dynamisch fuer  |
|     jede Habitus-   |
|     Zone            |
+----------+----------+
           |
           v
+---------------------+
| YAML generieren     |
+----------+----------+
           |
           +---------------------------+
           |                           |
           v                           v
+---------------------+     +---------------------+
| Storage Dashboard   |     | YAML Dashboard      |
| (Sofort sichtbar,   |     | (pilotsuite-styx/   |
|  kein HA-Restart)   |     |  pilotsuite_        |
|                     |     |  dashboard_latest.  |
| async_ensure_       |     |  yaml)              |
| storage_dashboard() |     |                     |
| -> WebSocket API    |     | Braucht HA-Restart  |
+---------------------+     | oder manuelles      |
                             | Neuladen            |
                             +---------------------+

View-Toggle-Persistenz:
+---------------------+
| FrontendModule      |
| view_states Store   |
| (.storage/          |
|  copilot_ha.        |
|  frontend_views)    |
|                     |
| {                   |
|   "styx": true,     |
|   "haushalt": true, |
|   "zonen": true,    |
|   "automation": true|
|   "energie": false, |
|   "musik": true,    |
|   "ki": true,       |
|   "chat": true      |
| }                   |
+---------------------+
```

---

## 9. Discovery und Failover Flow

Kandidaten-basierte Endpoint-Erkennung mit Sticky-Session

```
+---------------------+
| Config Entry:       |
| host: ""            |
| port: 8909          |
| token: ""           |
+----------+----------+
           |
           v
+---------------------+
| build_candidate_    |
| hosts()             |
+----------+----------+
           |
           v
+------------------------------------------------------+
| Kandidaten (Reihenfolge = Prioritaet):               |
|                                                      |
|  [1] Konfigurierter Host                             |
|  [2] HA internal_url Hostname                        |
|  [3] HA external_url Hostname                        |
|  [4] 533952f3-copilot-core (Supervisor slug)         |
|  [5] 533952f3_copilot_core (Unterstrich-Variante)    |
|  [6] local-copilot-core                              |
|  [7] homeassistant.local                             |
|  [8] homeassistant                                   |
|  [9] supervisor                                      |
| [10] localhost                                       |
| [11] 127.0.0.1                                       |
| [12] host.docker.internal (optional)                 |
+----------------------------+-------------------------+
                             |
                             v
        Fuer jeden Kandidaten x jeden Port:
+------------------------------------------------------+
|                                                      |
|  +--------+    GET /health    +--------+             |
|  | Kand.1 | ----------------> | Core?  |             |
|  | :8909  |    Timeout 2.5s   |        |             |
|  +--------+                   +---+----+             |
|                                   |                  |
|       HTTP 200 + {"ok": true} ----+-> TREFFER        |
|       Fehler/Timeout -------------+-> Naechster      |
|                                                      |
|  +--------+    GET /health    +--------+             |
|  | Kand.2 | ----------------> | Core?  |             |
|  | :8909  |                   |        |             |
|  +--------+                   +--------+             |
|       ...                                            |
|                                                      |
|  Falls /health fehlschlaegt:                         |
|  Fallback auf GET /api/v1/status                     |
|                                                      |
+------------------------------------------------------+

API-Client Failover (_request_json):
+------------------------------------------------------+
|                                                      |
|  Request an active_base_url:                         |
|                                                      |
|  Erfolg -> Sticky: active_base_url bleibt            |
|                                                      |
|  Fehler -> _should_failover() pruefen:               |
|     Timeout/Netzwerk/404/500+ -> Naechste URL        |
|     401/403 (Auth) -> KEIN Failover, Exception       |
|                                                      |
|  Alle URLs erschoepft -> CopilotApiError             |
|                                                      |
+------------------------------------------------------+
```

---

## 10. Webhook Push Flow

Core -> HA Webhook mit Authentifizierung und strukturierter Fehlerbehandlung

```
+---------------------+
| Core Add-on:        |
| Mood/Neuron/etc.    |
| hat sich geaendert  |
+----------+----------+
           |
           | HTTP POST /api/webhook/{webhook_id}
           | Headers:
           |   X-Auth-Token: {token}
           |   Content-Type: application/json
           |   (optional: X-Webhook-Timestamp,
           |    X-Webhook-Nonce, X-Webhook-Signature)
           | Body: {"type": "mood", "data": {...}}
           |
           v
+---------------------+
| HA Webhook Router   |
| -> _handle()        |
+----------+----------+
           |
           v
+---------------------+
| Auth-Pruefung       |
|                     |
| Token-Quellen:      |
| 1. X-Auth-Token     |
| 2. Authorization:   |
|    Bearer {token}   |
| 3. Legacy Header    |
|    (Transition/     |
|     Sunset Mode)    |
+----------+----------+
           |
           +-- Token ungueltig? -> 401 invalid_token
           |
           v
+---------------------+
| HMAC-Signatur       |
| (wenn aktiviert)    |
|                     |
| Pruefe:             |
| 1. Timestamp TTL    |
| 2. Nonce Replay     |
| 3. HMAC SHA-256     |
+----------+----------+
           |
           +-- Signatur ungueltig? -> 401 invalid_signature
           |
           v
+---------------------+
| Envelope Validierung|
|                     |
| Muss enthalten:     |
| - type (string)     |
| - data (object)     |
+----------+----------+
           |
           +-- Fehlt? -> 400 missing_type/missing_data
           |
           v
+---------------------+
| Event-Typ           |
| normalisieren       |
|                     |
| Legacy-Aliases:     |
| mood_changed -> mood|
| suggestion_new ->   |
|   suggestion        |
| neuron_update ->    |
|   neuron            |
+----------+----------+
           |
           +-- Unbekannt? -> 400 unknown_type
           |
           v
+------------------------------------------------------+
| Typ-spezifische Verarbeitung:                        |
|                                                      |
| mood -----> coordinator.async_set_updated_data(      |
|             {mood, dominant_mood, mood_confidence})   |
|                                                      |
| neuron ---> coordinator.async_set_updated_data(      |
|             {neurons})                               |
|                                                      |
| suggestion -> hass.bus.async_fire(                   |
|               "copilot_ha_suggestion_received",      |
|               {suggestion: data})                    |
|                                                      |
| module_data -> coordinator update +                  |
|                _update_smart_home_modules()           |
|                                                      |
| zone_update -> coordinator zone_updates merge        |
|                                                      |
| anomaly --> coordinator alert_history (max 50) +     |
|             hass.bus.async_fire bei warning/critical  |
|                                                      |
| autonomy_executed -> coordinator history +            |
|                      hass.bus.async_fire              |
|                                                      |
| autonomy_failed -> coordinator errors +               |
|                    hass.bus.async_fire                |
|                                                      |
| scene_captured/applied -> hass.bus.async_fire        |
|                                                      |
| module_zone_state_changed ->                         |
|   coordinator.zone_module_states[zone][module]=state |
|                                                      |
| status --> coordinator {ok, version} merge           |
|                                                      |
+------------------------------------------------------+
           |
           v
+---------------------+
| HTTP 200            |
| {"ok": true}        |
+---------------------+
```

---

## Legende

```
+----------+
| Prozess/ |   Verarbeitungsschritt oder Komponente
| Modul    |
+----------+

----->         Datenfluss (synchron oder asynchron)

- - - ->       Optionaler/bedingter Datenfluss

[Komponente]   Inline-Referenz auf Code-Modul

| Wert |       Tabellenzelle
```
