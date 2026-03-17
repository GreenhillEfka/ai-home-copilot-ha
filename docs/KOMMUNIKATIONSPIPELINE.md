# PilotSuite Styx -- Kommunikationspipeline

Version: v14.6.5 | Stand: 2026-03-16

Dieses Dokument beschreibt die gesamte Kommunikationsarchitektur zwischen der
Home Assistant Integration (copilot_ha) und dem PilotSuite Core Add-on.

---

## Inhaltsverzeichnis

1. [Architektur-Ueberblick](#architektur-ueberblick)
2. [Discovery-Mechanismus](#discovery-mechanismus)
3. [Token-Beschaffung (1-Key-Flow)](#token-beschaffung-1-key-flow)
4. [API-Client und Failover](#api-client-und-failover)
5. [Coordinator und Hybrid-Refresh](#coordinator-und-hybrid-refresh)
6. [Events Forwarder (HA -> Core)](#events-forwarder-ha---core)
7. [Webhook Push (Core -> HA)](#webhook-push-core---ha)
8. [Zone Automation Synchronisation](#zone-automation-synchronisation)
9. [Habitus Mining Pipeline](#habitus-mining-pipeline)
10. [Neuron Pipeline](#neuron-pipeline)
11. [Chat Pipeline](#chat-pipeline)
12. [Smart Home Module Pipeline](#smart-home-module-pipeline)

---

## Architektur-Ueberblick

Die PilotSuite verwendet ein hybrides Kommunikationsmodell mit drei Kanaelen:

```
    HA Integration (copilot_ha)              Core Add-on (copilot_core)
    ===========================              ==========================

    [EventsForwarder] ------- POST /api/v1/events -------> [Brain Graph]
    [Coordinator]     ------- GET  /health, /api/v1/* ----> [REST API]
    [Webhook Handler] <------ POST /api/webhook/{id} ------ [Webhook Push]

    Kanal 1: HA -> Core (Events Forwarding)     ~0.5s Batches
    Kanal 2: HA -> Core (Polling)               120s Intervall
    Kanal 3: Core -> HA (Webhook Push)          Echtzeit
```

**Prinzip "Thin Client":** Die HA-Integration ist ausschliesslich fuer
Sensorik (Entity-States lesen), Aktorik (HA-Service-Calls ausfuehren) und
Darstellung (Dashboard, Entities) zustaendig. Jegliche Logik, Inferenz und
Mustererkennung findet im Core Add-on statt.

---

## Discovery-Mechanismus

**Datei:** `config_helpers.py`, Funktion `discover_reachable_core_endpoint()`

### Ablauf

1. Host und Port aus Config Entry lesen (oder Defaults verwenden)
2. Host/Port normalisieren via `normalize_host_port()` (unterstuetzt URLs, IP:Port, Hostnamen)
3. Kandidatenliste erstellen via `build_candidate_hosts()`:

```
Kandidatenreihenfolge:
  1. Konfigurierter Host (z.B. "192.168.30.18")
  2. HA internal_url Hostname (aus hass.config)
  3. HA external_url Hostname (aus hass.config)
  4. "533952f3-copilot-core"    (Supervisor slug, Bindestrich-Form)
  5. "533952f3_copilot_core"    (Supervisor slug, Unterstrich-Form)
  6. "local-copilot-core"       (Lokaler Addon-Name)
  7. "homeassistant.local"      (mDNS)
  8. "homeassistant"            (Docker DNS)
  9. "supervisor"               (Supervisor-Netzwerk)
 10. "localhost"
 11. "127.0.0.1"
 12. "host.docker.internal"     (nur wenn konfiguriert)
```

4. Port-Kandidaten: Konfigurierter Port + Default-Port (8909) falls abweichend
5. Fuer jede Host/Port-Kombination: HTTP GET auf zwei Probe-Pfade probieren:
   - `/health` (unauthentifiziert, bevorzugt)
   - `/api/v1/status` (Fallback)
6. Erfolgskriterium: HTTP 200, Content-Type JSON, Payload `{"ok": true}`
7. Erster Treffer wird zurueckgegeben und persistent gespeichert

### Retry-Mechanismus

Falls die initiale Discovery waehrend `async_setup_entry()` fehlschlaegt
(Core noch nicht gestartet), wird ein verzoegerter Retry nach 30 Sekunden
via `async_call_later()` geplant.

### Timeout

Jeder Probe hat ein Timeout von 2.5 Sekunden (konfigurierbar via `timeout_s`).

---

## Token-Beschaffung (1-Key-Flow)

**Datei:** `config_helpers.py`, Funktion `fetch_setup_token()`

### Ablauf

1. Base-URL aus Host/Port konstruieren
2. HTTP GET auf `{base_url}/api/v1/auth/setup-token`
3. Timeout: 3.0 Sekunden
4. Erwartete Antwort:

```json
{
  "ok": true,
  "token": "auto-generated-setup-token-abc123..."
}
```

5. Token wird extrahiert, gekuerzt geloggt und zurueckgegeben
6. Bei Fehler (HTTP != 200, Timeout, Netzwerkfehler): Leerer String

### Anwendung

Der 1-Key-Flow wird an drei Stellen verwendet:

1. **Zero Config:** Waehrend `async_step_zero_config()` im Config Flow
2. **Manual Setup:** Falls Token-Feld leer gelassen wird
3. **async_setup_entry:** Bei fehlendem Token nach Discovery

---

## API-Client und Failover

**Datei:** `coordinator.py`, Klasse `CopilotApiClient`

### Architektur

Der API-Client erbt von `SharedCopilotApiClient` und ergaenzt Endpoint-Failover.
Bei Erstellung erhaelt er eine Liste von Base-URLs (aus der Kandidatenliste).

### Failover-Logik in `_request_json()`

```
Fuer jeden base_url in self._base_urls:
    1. URL zusammenbauen: {base_url}{path}
    2. HTTP-Request senden (Method, Headers, Payload, Timeout)
    3. Bei Erfolg (HTTP < 400):
       - JSON parsen
       - Active-Base-URL aktualisieren (Sticky)
       - Ergebnis zurueckgeben
    4. Bei Fehler:
       - Pruefen ob Failover sinnvoll ist
       - Ja: Naechsten Kandidaten versuchen
       - Nein: Exception werfen
```

### Failover-Entscheidung (`_should_failover()`)

Failover wird ausgeloest bei:

| Fehlertyp | Failover? |
|-----------|-----------|
| Timeout | Ja |
| Client Error (Netzwerk) | Ja |
| Unerwarteter Content-Type | Ja |
| Ungueltiges JSON | Ja |
| HTTP 404, 405, 408, 429 | Ja |
| HTTP >= 500 | Ja |
| HTTP 401, 403 (Auth-Fehler) | Nein (Token-Problem, nicht Endpoint) |

### Timeout-Stufen

| Endpoint-Kategorie | Timeout |
|--------------------|---------|
| Standard REST (health, mood, neurons) | 10 Sekunden |
| Audio (STT, TTS) | 30 Sekunden |
| Chat Completions | 90 Sekunden |

### Hilfsmethoden

| Methode | Funktion |
|---------|----------|
| `_safe_get()` | GET mit Fehlerbehandlung, gibt Default-Wert bei Fehler zurueck |
| `_safe_post()` | POST mit Fehlerbehandlung, gibt `{"ok": false}` bei Fehler zurueck |
| `async_get()` | Einfacher GET-Wrapper |
| `async_post()` | Einfacher POST-Wrapper |
| `async_put()` | Einfacher PUT-Wrapper |

---

## Coordinator und Hybrid-Refresh

**Datei:** `coordinator.py`, Klasse `CopilotDataUpdateCoordinator`

### Initialisierung

1. Host/Port/Token aus merged Config Entry lesen
2. Kandidaten-URLs erstellen (alle Host/Port-Kombinationen)
3. `CopilotApiClient` mit Kandidatenliste initialisieren
4. Update-Intervall: 120 Sekunden (Fallback-Polling)

### Refresh-Zyklus (`_async_update_data()`)

Bei jedem Refresh (alle 120s oder nach Webhook-Trigger):

```
1. Status abrufen: GET /health + GET /version
2. Mood abrufen: GET /api/v1/neurons/mood
3. Neuron-States abrufen: GET /api/v1/neurons
4. Habit-Learning-Daten aus ML-Context sammeln
5. Smart Home Module Dashboard: GET /api/v1/modules/dashboard
6. Module-Daten in HA-Module-Stubs schreiben (Licht, Helligkeit, Heiz, Bewegung, Praesenz)
7. Anomalie-Status: GET /api/v1/anomaly/history?limit=50&level=low
8. Autonomie-Dashboard: GET /api/v1/autonomy/dashboard
9. Zone Health: GET /api/v1/zone/health
10. Zone Automation Dashboard: GET /api/v1/zone-automation/dashboard
11. Zone-State-Sync: Core automation_mode -> HA Zone-State (active/idle)
12. Einmalig: Zone Automation Sync (ensure-zones)
13. Einmalig: Habitus Config Sync
14. Webhook-Daten konservieren (autonomy_history, zone_module_states)
```

### Retry-Strategie

3 Versuche mit exponentiellem Backoff (1s, 2s). Bei Erschoepfung aller
Versuche wird `UpdateFailed` geworfen, was den Coordinator in den
Unavailable-Zustand versetzt.

### Hybrid-Modus

```
Webhook Push (Echtzeit)                  Polling (120s Fallback)
========================                 =======================
Core sendet Event                        Coordinator pollt /health, /mood, etc.
  |                                        |
  v                                        v
Webhook Handler empfaengt               _async_update_data() laeuft
  |                                        |
  v                                        v
coordinator.async_set_updated_data()    Ergebnis-Dict wird zurueckgegeben
  |                                        |
  v                                        v
Entities werden sofort aktualisiert     Entities werden aktualisiert
```

Der Webhook Push liefert Echtzeit-Updates fuer:
- Mood-Aenderungen
- Neuron-State-Updates
- Neue Vorschlaege (Suggestions)
- Modul-Daten
- Zonen-Updates
- Anomalien
- Autonomie-Aktionen

Das 120s-Polling dient als Sicherheitsnetz, falls Webhooks ausfallen.

---

## Events Forwarder (HA -> Core)

**Datei:** `core/modules/events_forwarder.py`, Klasse `EventsForwarderModule`

### Zweck

Leitet relevante HA state_changed Events (und optional call_service Events)
an den Core weiter, wo sie in den Brain Graph eingespeist werden.

### Entity-Allowlist

Die weiterzuleitenden Entities werden dreistufig bestimmt:

1. **Habitus-Zone-Entities:** Alle Entities aus konfigurierten Zonen
2. **Media-Player:** Konfigurierte Musik- und TV-Player
3. **Zusaetzliche Entities:** Manuell konfigurierte Entity-IDs

### Event-Verarbeitung

```
HA Event: state_changed
    |
    v
_handle_state(event)
    |
    +-- Entity in Allowlist? Nein -> Verwerfen
    |
    +-- Entity in Neuron-Exclusion-Set? Ja -> Verwerfen
    |
    +-- old_state == new_state? Ja -> Verwerfen
    |
    +-- Idempotenz-Check: Bereits gesehen (TTL)? Ja -> Verwerfen
    |
    v
Canonical Event Envelope erstellen:
  {
    "id": "state_changed:{context_id}",
    "ts": "2026-03-16T10:30:00Z",
    "type": "state_changed",
    "source": "home_assistant",
    "entity_id": "light.wohnzimmer",
    "attributes": {
      "domain": "light",
      "zone_ids": ["zone:wohnbereich"],
      "old_state": "off",
      "new_state": "on",
      "state_attributes": {"brightness": 255},
      "neuron_tags": ["neuron_mood_wohnbereich"]
    }
  }
    |
    v
_enqueue(item) -> Bounded Queue (max_size konfigurierbar)
    |
    +-- Queue voll? -> drop-oldest Policy (dropped_total zaehlen)
    |
    +-- Queue-Groesse >= max_batch? -> Sofort flushen
    |
    +-- Sonst: Timer-gesteuerter Flush (Standard: 5s)
```

### Flush-Vorgang

```
_flush_now()
    |
    +-- Rate Limit pruefen (Token Bucket: 10 Tokens, 5/s Refill)
    |      Ueberschritten? -> Spaeter erneut versuchen
    |
    +-- Backoff pruefen (exponentiell, max 60s)
    |
    +-- Max max_batch Items aus Queue nehmen
    |
    +-- POST /api/v1/events mit {"items": [...]}
    |
    +-- Erfolg: Zaehler aktualisieren, Backoff zuruecksetzen
    |
    +-- Fehler: Items vorne wieder einreihen, Backoff erhoehen
    |            Retry nach Backoff-Delay planen
```

### Privacy-First Attribute

Nur eine kleine Whitelist von State-Attributen wird weitergeleitet:

| Domain | Erlaubte Attribute |
|--------|--------------------|
| `light` | brightness, color_temp, hs_color |
| `media_player` | volume_level |
| Alle anderen | Keine |

### call_service Forwarding

Optional aktivierbar. Nur sichere Domains werden weitergeleitet:

**Erlaubt:** light, media_player, climate, cover, lock, switch, scene, script

**Blockiert:** notify, rest_command, shell_command, tts

Nur Aufrufe, die mindestens eine Habitus-Zone-Entity betreffen, werden
weitergeleitet. Service-Daten werden bis auf Entity-IDs gestripped.

### Persistente Queue

Optional aktivierbar. Speichert ungesendete Events im HA-Storage
(`.storage/copilot_ha.events_forwarder.{entry_id}`) fuer Ueberlebenschancen
bei HA-Neustarts.

---

## Webhook Push (Core -> HA)

**Datei:** `webhook.py`

### Registrierung

1. Webhook-ID wird generiert oder aus Config Entry gelesen
2. `webhook.async_register()` registriert den Handler
3. URL wird via `webhook.async_generate_url()` generiert
4. Core muss die Webhook-URL kennen (wird bei Registrierung uebermittelt)

### Verarbeitungskette

```
HTTP POST /api/webhook/{webhook_id}
    |
    v
Token-Validierung (3 Quellen: Canonical, Bearer, Legacy)
    |
    v
Optional: HMAC-Signatur-Validierung
    |
    v
JSON-Body parsen
    |
    v
Envelope validieren: type (string), data (object)
    |
    v
Event-Typ normalisieren (Legacy-Aliases mappen)
    |
    v
Typ-spezifischer Handler:
    - mood:     coordinator.async_set_updated_data({mood, dominant_mood, ...})
    - neuron:   coordinator.async_set_updated_data({neurons})
    - suggestion: hass.bus.async_fire("copilot_ha_suggestion_received")
    - module_data: coordinator + _update_smart_home_modules()
    - zone_update: coordinator.async_set_updated_data({zone_updates})
    - anomaly:  coordinator + hass.bus.async_fire("copilot_ha_anomaly_detected")
    - autonomy_executed: coordinator + hass.bus.async_fire()
    - autonomy_failed:   coordinator + hass.bus.async_fire()
    - scene_captured: hass.bus.async_fire()
    - scene_applied:  hass.bus.async_fire()
    - module_zone_state_changed: coordinator zone_module_states update
    - status:   coordinator ok/version update
    |
    v
HTTP 200 {"ok": true}
```

### HMAC-Signaturverifikation (optional)

Aktiviert durch Umgebungsvariable `PILOTSUITE_WEBHOOK_SIGNING_SECRET_PRIMARY`.

```
Signatur-Input = "{timestamp}.{nonce}." + body_bytes
Erwarteter Digest = HMAC-SHA256(secret, Signatur-Input)
Vergleich = hmac.compare_digest(erwartet, empfangen)
```

Zusaetzliche Schutzmassnahmen:
- Timestamp-TTL (Standard: 300s, konfigurierbar 1-86400s)
- Nonce-Replay-Erkennung (In-Memory-Cache, max 10000 Eintraege)
- Dual-Secret-Support (Primary + Secondary fuer nahtlosen Schluesselwechsel)

---

## Zone Automation Synchronisation

### HA Zonen -> Core

```
async_setup_entry()
    |
    v
Zone Auto-Setup: HA Areas -> aggregate_areas_to_habitus_zones()
    |
    +-- 10 Zonen-Templates (Wohnbereich, Badbereich, Kochbereich, ...)
    +-- Keyword-Matching mit Fuzzy-Toleranz (Levenshtein <= 1)
    +-- Aggregation: Mehrere HA-Areas -> 1 logische Zone
    +-- Entity-Rollen-Erkennung (motion, lights, temperature, ...)
    +-- Neuron-Tags erstellen (context/state/mood pro Zone)
    |
    v
Coordinator erster Refresh:
    |
    v
async_ensure_zone_automation_zones(zone_ids)
    |
    v
POST /api/v1/zone-automation/ensure-zones
    {"zone_ids": ["wohnbereich", "badbereich", ...]}
    |
    v
Core erstellt fehlende Zone-Konfigurationen automatisch
```

### Core -> HA Zone-State-Sync

```
Coordinator Refresh (alle 120s):
    |
    v
GET /api/v1/zone-automation/dashboard
    |
    v
Fuer jede Core-Zone:
    automation_mode != "off" -> Zone-State = "active"
    automation_mode == "off" -> Zone-State = "idle"
    |
    v
async_set_zone_state(hass, entry_id, zone_id, state)
```

---

## Habitus Mining Pipeline

### Gesamtablauf

```
1. Events sammeln (EventsForwarder)
   HA state_changed/call_service -> POST /api/v1/events -> Core Brain Graph

2. Pattern Mining (Core, periodisch)
   Brain Graph -> Frequent Pattern Mining -> Kandidaten
   (min_support, min_confidence konfigurierbar)

3. Kandidaten vorschlagen (Core -> HA via Webhook)
   Webhook type=suggestion -> hass.bus.async_fire("copilot_ha_suggestion_received")

4. Suggestion Panel (HA UI)
   Suggestion -> HA Repairs UI (Issue Registry)
   Benutzer: Accept / Reject / Snooze

5. Automation erstellen (bei Accept)
   Blueprint-URL -> HA Automation erstellen
   Pattern wird als "bestaetigt" markiert
```

### Suggestion-Datenstruktur

```
Suggestion:
  - suggestion_id: Eindeutige ID
  - pattern: "light.kitchen:on -> switch.coffee:on"
  - confidence: 0.87
  - lift: 2.3
  - support: 42 (Beobachtungen)
  - source: habitus | seed | zone_mining | calendar
  - zone_id: "zone:kochbereich"
  - mood_type: "gemuetlich"
  - risk_level: medium
  - status: pending | accepted | rejected | snoozed | expired
```

### Habitus Config Sync

Beim ersten Coordinator-Refresh werden HA-seitige Habitus-Konfigurationsparameter
an Core uebermittelt:

```
POST /api/v1/habitus/config
{
  "min_support": ...,
  "min_confidence": ...,
  "context_features": ...,
  "auto_mine_interval_s": ...,
  "auto_mine_event_threshold": ...
}
```

---

## Neuron Pipeline

### Architektur im Core

```
Entity-States (via Events Forwarder)
    |
    v
Neuron-Layer-Klassifizierung:
    |
    +-- Context Layer: Temperatur, Luftfeuchte, CO2, Druck, Energie, Leistung
    |                  (Hintergrund-Umgebungsdaten)
    |
    +-- State Layer:   Bewegung, Tueren, Fenster, Schloesser, Jalousien, Heizung
    |                  (Physische Zustaende, binaere Sensoren)
    |
    +-- Mood Layer:    Lichter, Helligkeit, Media, Laerm
    |                  (Komfort- und Emotionssignale)
    |
    v
Neuron-Evaluation: POST /api/v1/neurons/evaluate
    {
      "states": { entity_id: {state, attributes} },
      "time": {...},
      "weather": {...},
      "presence": {...}
    }
    |
    v
Softmax-Normalisierung -> Mood-State
    |
    v
Mood-Daten: GET /api/v1/neurons/mood
    {
      "mood": "gemuetlich",
      "confidence": 0.87,
      "layers": {
        "context": {...},
        "state": {...},
        "mood": {...}
      }
    }
```

### Neuron-Tags (HA-seitig)

Waehrend der Zone Auto-Setup werden automatisch Neuron-Tags erstellt:

```
neuron_context_{zone_id}: Entities fuer Context-Layer
neuron_state_{zone_id}:   Entities fuer State-Layer
neuron_mood_{zone_id}:    Entities fuer Mood-Layer
```

Tags werden im EntityTagStore persistiert und dienen dem EventsForwarder
zur Anreicherung von Event-Envelopes (`neuron_tags` Feld).

### Evaluation-Trigger

1. **State-Change-Event:** MoodModule trackt konfigurierte Entities, bei Aenderung wird `_orchestrate_all_zones()` aufgerufen
2. **Polling-Fallback:** MoodModule pollt alle 300s (konfigurierbar)
3. **Coordinator Refresh:** Alle 120s werden Neuron-States per GET abgerufen
4. **Webhook Push:** Core kann Neuron-Updates jederzeit pushen

---

## Chat Pipeline

### Ablauf

```
Benutzer: Sprache oder Text
    |
    v
HA Conversation Agent (StyxConversationAgent)
    |
    +-- conversation_id normalisieren
    +-- Sprache bestimmen (de/en)
    |
    v
coordinator.api.async_chat_completions(
    messages=[{"role": "user", "content": text}],
    conversation_id=conversation_id
)
    |
    v
POST /v1/chat/completions  (Timeout: 90s)
    {
      "model": "pilotsuite",
      "messages": [{"role": "user", "content": "..."}],
      "conversation_id": "..."
    }
    |
    v
Core: Ollama LLM (qwen3:0.6b oder konfiguriertes Modell)
    +-- ConversationMemory fuer Kontext laden
    +-- System-Prompt mit HA-Kontext (Entities, Zonen, Mood)
    +-- LLM-Inferenz
    +-- Antwort in ConversationMemory speichern
    |
    v
Response: {"choices": [{"message": {"content": "..."}}]}
    |
    v
ConversationResult mit IntentResponse an HA zurueck
```

### Fehlerbehandlung

| Fehler | Reaktion |
|--------|----------|
| CopilotApiError | Deutsche Fehlermeldung: "PilotSuite Core ist gerade nicht erreichbar." |
| TimeoutError | "Request to PilotSuite Core timed out." |
| Sonstiger Fehler | "Could not reach PilotSuite Core." |

---

## Smart Home Module Pipeline

### Module im Core

5 Smart Home Module aggregieren Entity-States zonenweise:

| Modul | Daten |
|-------|-------|
| `licht` | Lichter an/aus, Gesamtzahl, durchschnittliche Helligkeit, Auto-Modus |
| `helligkeit` | Indoor/Outdoor Lux, Lichtbedarf, Defizit-Prozent |
| `heiz` | Klima-Daten pro Zone |
| `bewegung` | Bewegungserkennung pro Zone |
| `praesenz` | Praesenz-Erkennung pro Zone |

### Datenfluss

```
Core: Aggregiert Modul-Daten aus Brain Graph
    |
    v
Kanal A: Coordinator Polling (GET /api/v1/modules/dashboard)
Kanal B: Webhook Push (type=module_data)
    |
    v
_update_smart_home_modules(module_data)
    |
    +-- Fuer jedes Modul (licht, helligkeit, heiz, bewegung, praesenz):
    |     1. Entry-Store nach Modul-Instanz suchen
    |     2. Zone Automation Dashboard laden
    |     3. Pro Zone: update_zone() mit zonenspezifischen Daten aufrufen
    |
    v
HA Entity-States werden aktualisiert
```

### Zusaetzlich: Zone Automation Detail

Fuer tiefere Einsichten:
- `GET /api/v1/zone-automation/dashboard` -- Alle Zonen mit Licht/Musik/Praesenz
- `GET /api/v1/modules/zones/{zone_id}` -- Detailansicht pro Zone
- `GET /api/v1/zone/aggregates/{zone_id}` -- Device-Class-Aggregation pro Zone
- `GET /api/v1/zone/health` -- Zone-Gesundheitsuebersicht
