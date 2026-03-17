# PilotSuite Styx HA -- Modulbeschreibung

**Version:** 14.6.5 | **Stand:** 2026-03-16

Dieses Dokument beschreibt saemtliche 36 Module des PilotSuite Styx HA-Systems.
Module werden ueber das CopilotRuntime-System geladen und verwaltet.

---

## Inhaltsverzeichnis

1. [Laufzeitsystem (CopilotRuntime)](#laufzeitsystem-copilotruntime)
2. [ModuleRegistry (Core-Backend)](#moduleregistry-core-backend)
3. [Modulkategorien](#modulkategorien)
   - [Wahrnehmung](#1-wahrnehmung)
   - [Neuronen / Brain](#2-neuronen--brain)
   - [Netzwerk](#3-netzwerk)
   - [Intelligence](#4-intelligence)
   - [Kommunikation](#5-kommunikation)
   - [Haushalt](#6-haushalt)
   - [Integration](#7-integration)
   - [System](#8-system)
4. [Standalone-Module](#standalone-module)
5. [Modul-Ladekette](#modul-ladekette)

---

## Laufzeitsystem (CopilotRuntime)

**Datei:** `core/runtime.py`

Das CopilotRuntime ist der zentrale Orchestrierer aller Module.
Pro HA-Instanz existiert genau eine Singleton-Instanz.

```
CopilotRuntime (Singleton)
    |
    +-- ModuleRegistry (core/registry.py)
    |       |-- register(name, factory)
    |       |-- create(name) -> CopilotModule
    |       +-- names() -> list[str]
    |
    +-- _live_modules: dict[entry_id -> dict[name -> CopilotModule]]
    |
    +-- async_setup_entry(entry, modules)
    |       1. Erstellt ModuleContext(hass, entry)
    |       2. Instanziiert jedes Modul via registry.create()
    |       3. Ruft mod.async_setup_entry(ctx) auf
    |       4. Bei Fehler: Rollback aller bereits geladenen Module
    |       5. Retry: nur erfolgreiche Module werden geladen (Graceful Degradation)
    |
    +-- async_unload_entry(entry, modules)
            Entlaedt Module in umgekehrter Reihenfolge.
```

### CopilotModule (Protocol)

**Datei:** `core/module.py`

Minimales Interface fuer alle Module:

| Methode | Beschreibung |
|---------|-------------|
| `name` (property) | Eindeutiger Modulname |
| `async_setup_entry(ctx)` | Initialisierung bei Config-Entry-Setup |
| `async_unload_entry(ctx)` | Aufraumen bei Config-Entry-Entladen |

### ModuleContext (Dataclass)

| Attribut | Typ | Beschreibung |
|----------|-----|-------------|
| `hass` | `HomeAssistant` | HA-Instanz |
| `entry` | `ConfigEntry` | Aktiver Config-Entry |
| `domain` | `str` (property) | = `copilot_ha` |
| `entry_id` | `str` (property) | Config-Entry-ID |


---

## ModuleRegistry (Core-Backend)

**Datei:** `core/module_registry.py`

Unabhaengig vom HA-seitigen `core/registry.py` existiert im Core-Backend ein separates
ModuleRegistry mit SQLite-Persistenz fuer Modul-Zustaende.

### Drei-Stufen-Autonomie

| Zustand | Beschreibung | Datensammlung | Vorschlaege | Auto-Ausfuehrung |
|---------|-------------|:---:|:---:|:---:|
| `active` | Voll operativ | Ja | Ja | Ja (wenn beide Seiten aktiv) |
| `learning` | Beobachtungsmodus | Ja | Ja (manuell) | Nein |
| `off` | Deaktiviert | Nein | Nein | Nein |

### Doppelte Sicherheit (Double-Safety)

Auto-Apply ist NUR moeglich, wenn SOWOHL das Quell-Modul ALS AUCH das Ziel-Modul
im Zustand `active` sind. Dies verhindert unbeabsichtigte autonome Aktionen.

| Methode | Beschreibung |
|---------|-------------|
| `should_auto_apply(source, target)` | True wenn beide active |
| `should_suggest(module_id)` | True wenn active oder learning |
| `should_collect_data(module_id)` | True wenn nicht off |
| `get_suggestion_mode(source, target)` | "auto_apply" / "manual" / "suppress" |


---

## Modulkategorien


### 1. Wahrnehmung

Diese Module erfassen physische Umgebungsdaten pro Habitus-Zone.

#### 1.1 licht_module

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `licht_module` |
| **Python-Pfad** | `.core.modules.licht_module` |
| **Klasse** | `LichtModule` |
| **Pipeline-Position** | Eingang |
| **Zweck** | Erfasst pro Zone: Anzahl eingeschalteter Lichter, Gesamtzahl, Durchschnittshelligkeit, Auto-Modus-Status |
| **Abhaengigkeiten** | Habitus-Zonen (fuer Zone-Entity-Zuordnung) |
| **Erzeugte Entities** | Keine eigenen; liefert Daten an Habitus-Zonen-Aggregation |
| **Konfiguration** | Keine |

#### 1.2 helligkeit_module

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `helligkeit_module` |
| **Python-Pfad** | `.core.modules.helligkeit_module` |
| **Klasse** | `HelligkeitModule` |
| **Pipeline-Position** | Eingang |
| **Zweck** | Erfasst pro Zone: Indoor-/Outdoor-Lux, Lichtbedarf, Defizit-Prozent |
| **Abhaengigkeiten** | Illuminance-Sensoren (z.B. Zigbee-Lichtsensoren) |
| **Erzeugte Entities** | Keine eigenen; liefert Daten an Habitus-Zonen-Aggregation |
| **Konfiguration** | Keine |

#### 1.3 bewegung_module

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `bewegung_module` |
| **Python-Pfad** | `.core.modules.bewegung_module` |
| **Klasse** | `BewegungModule` |
| **Pipeline-Position** | Eingang |
| **Zweck** | Erfasst pro Zone: aktive Bewegungssensoren, Gesamtzahl, letzte Bewegung, Aktualitaet |
| **Abhaengigkeiten** | binary_sensor.* (motion-Entities) |
| **Erzeugte Entities** | Keine eigenen; liefert Daten an Habitus-Zonen-Aggregation |
| **Konfiguration** | Keine |

#### 1.4 praesenz_module

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `praesenz_module` |
| **Python-Pfad** | `.core.modules.praesenz_module` |
| **Klasse** | `PraesenzModule` |
| **Pipeline-Position** | Eingang |
| **Zweck** | Erfasst pro Zone: Belegung, Personenanzahl, anwesende Personen, letzter Eintritt |
| **Abhaengigkeiten** | person.*, device_tracker.* |
| **Erzeugte Entities** | Keine eigenen; liefert Daten an Habitus-Zonen-Aggregation |
| **Konfiguration** | Keine |

#### 1.5 heiz_module

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `heiz_module` |
| **Python-Pfad** | `.core.modules.heiz_module` |
| **Klasse** | `HeizModule` |
| **Pipeline-Position** | Eingang |
| **Zweck** | Erfasst pro Zone: aktuelle/Ziel-Temperatur, Luftfeuchtigkeit, Heizstatus, Eco-Modus, Komfortindex |
| **Abhaengigkeiten** | climate.*, sensor.*_temperature, sensor.*_humidity |
| **Erzeugte Entities** | Keine eigenen; liefert Daten an Habitus-Zonen-Aggregation |
| **Konfiguration** | Keine |


---

### 2. Neuronen / Brain

Module fuer Stimmungsanalyse und Wissensgraph-Synchronisation.

#### 2.1 brain_graph_sync

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `brain_graph_sync` |
| **Python-Pfad** | `.core.modules.brain_graph_sync` |
| **Klasse** | `BrainGraphSyncModule` |
| **Version** | 1.1.0 |
| **Pipeline-Position** | Verarbeitung |
| **Zweck** | Echtzeit-Synchronisation von HA-Entities zum Core Brain Graph. Erstellt Knoten und Beziehungen (Entity-Area, Entity-Zone, Entity-Tags). Batch-Verarbeitung, Event-Deduplizierung mit TTL-Cache. |
| **Abhaengigkeiten** | Core Add-on (/api/v1/graph), BrainGraphSyncService, ModuleConnector |
| **Erzeugte Entities** | Brain-Graph-Sensoren (via brain_graph_sync.py Service) |
| **Konfiguration** | Sync-Intervall (300s), Batch-Groesse (50), aktivierte Domains |

#### 2.2 mood

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `mood` |
| **Python-Pfad** | `.core.modules.mood_module` |
| **Klasse** | `MoodModule` |
| **Version** | 0.2 |
| **Pipeline-Position** | Verarbeitung |
| **Zweck** | Zonen-basierte Stimmungsinferenz aus HA-Sensordaten. Event-getrieben und polling-basiert. Integration mit Character-System fuer gewichtete Stimmungsberechnung. |
| **Abhaengigkeiten** | Zonen-Konfiguration (motion, light, media Entities), CharacterModule, TTLCache |
| **Erzeugte Entities** | `sensor.copilot_ha_mood`, `sensor.copilot_ha_mood_confidence`, `sensor.copilot_ha_neuron_activity` |
| **Konfiguration** | Zonen-Schema (motion_entities, light_entities, media_entities, illuminance_entity), min_dwell_time (600s), action_cooldown (120s), polling_interval (300s) |

#### 2.3 mood_context

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `mood_context` |
| **Python-Pfad** | `.core.modules.mood_context_module` |
| **Klasse** | `MoodContextModule` |
| **Pipeline-Position** | Verarbeitung |
| **Zweck** | Konsument des Core Mood-Service. Pollt Core Mood API und haelt lokalen Cache der Zonen-Stimmungen. Kontextualisiert Automation-Vorschlaege (z.B. keine Energiespar-Vorschlaege waehrend Entertainment). |
| **Abhaengigkeiten** | Core Add-on (Mood API), UserPreferenceModule |
| **Erzeugte Entities** | Keine eigenen; liefert Mood-Kontext an andere Module |
| **Konfiguration** | Polling-Intervall (30s) |

#### 2.4 knowledge_graph_sync

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `knowledge_graph_sync` |
| **Python-Pfad** | `.core.modules.knowledge_graph_sync` |
| **Klasse** | `KnowledgeGraphSyncModule` |
| **Pipeline-Position** | Verarbeitung |
| **Zweck** | Synchronisiert HA-Entities zum Core Knowledge Graph. Erstellt Knoten fuer Entities und Kanten: Entity-Area (BELONGS_TO), Entity-Zone (BELONGS_TO), Entity-Tags (HAS_TAG), Entity-Capabilities (HAS_CAPABILITY), Pattern-Mood (RELATES_TO_MOOD). Inkrementelle Synchronisation, Batch-Verarbeitung. |
| **Abhaengigkeiten** | Core Add-on (KnowledgeGraphClient), Entity Registry, Area Registry, Habitus Zones |
| **Erzeugte Entities** | Keine eigenen |
| **Konfiguration** | Full-Sync-Intervall (3600s), Batch-Groesse (50), Retry-Delay (5s), Max-Retries (3) |


---

### 3. Netzwerk

Module fuer Netzwerk-Diagnostik und Wi-Fi-Monitoring.

#### 3.1 unifi_module

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `unifi_module` |
| **Python-Pfad** | `.core.modules.unifi_module` |
| **Klasse** | `UniFiModule` |
| **Version** | 0.2 |
| **Pipeline-Position** | Eingang |
| **Zweck** | Netzwerk- und Wi-Fi-Diagnostik: WAN-Qualitaet (Verlust, Latenz, Jitter, Ausfaelle), Wi-Fi-Roaming-Analyse (Ping-Pong, klebende Clients), AP/Radio-Health (Retries, Auslastung, DFS), Baselines und Anomalieerkennung, Praesenz-Integration (Client-Standort, Signalstaerke). |
| **Abhaengigkeiten** | UniFi-Controller (via Core Add-on), UnifiContextCoordinator |
| **Erzeugte Entities** | UniFi-spezifische Sensoren und Binary-Sensoren |
| **Konfiguration** | UniFi-Controller-URL, Credentials |

#### 3.2 network

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `network` |
| **Python-Pfad** | `.core.modules.unifi_context_module` |
| **Klasse** | `UnifiContextModule` |
| **Version** | 0.2 |
| **Pipeline-Position** | Eingang / Verarbeitung |
| **Zweck** | Netzwerk-Monitoring-Kontextanbieter. Stellt WAN-Status, Clients, Roaming-Events und Traffic-Baselines bereit. AP-basierte Raumpraesenz-Erkennung. Exportiert Daten fuer andere Module. |
| **Abhaengigkeiten** | Core Add-on (UniFi Neuron), UnifiContextCoordinator |
| **Erzeugte Entities** | `sensor.copilot_ha_wan_*`, `binary_sensor.copilot_ha_unifi_*` |
| **Konfiguration** | Host, Port, Token |


---

### 4. Intelligence

Module fuer maschinelles Lernen, Anomalieerkennung und Kameraintegration.

#### 4.1 ml_context

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `ml_context` |
| **Python-Pfad** | `.core.modules.ml_context_module` |
| **Klasse** | `MLContextModule` |
| **Pipeline-Position** | Verarbeitung / Lernen |
| **Zweck** | Stellt ML-Kontext fuer Neuronen und Sensoren bereit. Unified Interface zu: AnomalyDetector (Echtzeit-Anomalieerkennung), HabitPredictor (zeitbasierte Mustererkennung), EnergyOptimizer (Geraeteenergieoptimierung), MultiUserLearner (Mehrbenutzer-Verhaltenstracking). Mood-Integration: mood-gewichtete Vorhersagen. |
| **Abhaengigkeiten** | MLContext, MoodModule (optional) |
| **Erzeugte Entities** | ML-Sensoren ueber ml_context.py |
| **Konfiguration** | Update-Intervall (60s) |

#### 4.2 camera_context

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `camera_context` |
| **Python-Pfad** | `.core.modules.camera_context_module` |
| **Klasse** | `CameraContextModule` |
| **Pipeline-Position** | Eingang / Verarbeitung |
| **Zweck** | Integriert Kamera-Events mit dem Habitus-Neuralsystem: Motion-Events, Gesichtserkennung, Objekterkennung, Zonen-Events. Privacy-first: nur lokale Verarbeitung, Face-Blurring, konfigurierbare Aufbewahrung. |
| **Abhaengigkeiten** | camera.* Entities, SIGNAL_ACTIVITY_UPDATED |
| **Erzeugte Entities** | Camera-Motion und -Presence Binary-Sensoren |
| **Konfiguration** | Keine |

#### 4.3 energy_context

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `energy_context` |
| **Python-Pfad** | `.core.modules.energy_context_module` |
| **Klasse** | `EnergyContextModule` |
| **Version** | 0.2 |
| **Pipeline-Position** | Eingang / Verarbeitung |
| **Zweck** | Energiemonitoring-Kontextmodul. Stellt Verbrauch, Erzeugung, Anomalien und Load-Shifting-Moeglichkeiten bereit. Berechnet Frugality-Score basierend auf aktuellem Verbrauch vs. Baseline. Integration mit Mood-System (get_frugality_mood_factor). Privacy-first: nur aggregierte Werte. |
| **Abhaengigkeiten** | Core Add-on (Energy API), EnergyContextCoordinator |
| **Erzeugte Entities** | Energy-Insight-Sensoren, Energie-Sensoren |
| **Konfiguration** | Host, Port, Token |

#### 4.4 weather_context

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `weather_context` |
| **Python-Pfad** | `.core.modules.weather_context_module` |
| **Klasse** | `WeatherContextModule` |
| **Pipeline-Position** | Eingang |
| **Zweck** | Wetterdaten-Modul fuer PV-Prognose und Energieoptimierung. Aktuelle Bedingungen, Vorhersagen und PV-basierte Empfehlungen. Privacy-first: nur aggregierte Werte. |
| **Abhaengigkeiten** | Core Add-on (Weather API), WeatherContextCoordinator |
| **Erzeugte Entities** | Weather-Context-Sensoren |
| **Konfiguration** | Host, Port, Token |

#### 4.5 home_alerts

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `home_alerts` |
| **Python-Pfad** | `.core.modules.home_alerts_module` |
| **Klasse** | `HomeAlertsModule` |
| **Pipeline-Position** | Korrelation / Aktion |
| **Zweck** | Ueberwacht kritische Hauszustaende und generiert aktionsrelevante Warnungen: Batterie-Warnungen (< 20%/10%), Klima-Abweichungen (> 2 Grad von Ziel), Praesenz-Aenderungen, System-Alerts (unerreichbare Entities). Persistente Quittierung via HA Storage. Alert-Historie (30 Tage). |
| **Abhaengigkeiten** | Entity Registry, HA Storage |
| **Erzeugte Entities** | `sensor.copilot_ha_home_alerts` |
| **Konfiguration** | Schwellenwerte (Batterie, Klima-Abweichung) |

#### 4.6 frigate_bridge

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `frigate_bridge` |
| **Python-Pfad** | `.core.modules.frigate_bridge` |
| **Klasse** | `FrigateBridgeModule` |
| **Pipeline-Position** | Eingang |
| **Zweck** | Optionale Bruecke fuer Frigate NVR. Entdeckt Frigate-generierte Entities (binary_sensor.*_person, binary_sensor.*_motion, sensor.*_person_count) und leitet Personen-/Bewegungserkennungs-Events an CameraContextModule und das Neuralsystem weiter. Graceful Degradation wenn Frigate nicht installiert. |
| **Abhaengigkeiten** | Frigate NVR (optional), CameraContextModule |
| **Erzeugte Entities** | Keine eigenen |
| **Konfiguration** | Keine (automatische Erkennung) |


---

### 5. Kommunikation

Module fuer Sprachsteuerung, Suche und Persoenlichkeit.

#### 5.1 voice_context

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `voice_context` |
| **Python-Pfad** | `.core.modules.voice_context` |
| **Klasse** | `VoiceContextModule` |
| **Pipeline-Position** | Verarbeitung / Aktion |
| **Zweck** | Sprachsteuerung und TTS fuer PilotSuite. Voice Command Parser, TTS-Ausgabe via HA TTS-Services, Voice State Tracking, Command Templates. Character-System-Integration (voice_tone-bewusste Antworten). Unterstuetzt Stimmungen: formal, friendly, casual, cautious. |
| **Abhaengigkeiten** | HA TTS-Services, CharacterModule |
| **Erzeugte Entities** | `sensor.copilot_ha_voice_context`, `sensor.copilot_ha_voice_prompt` |
| **Konfiguration** | Keine |

#### 5.2 quick_search

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `quick_search` |
| **Python-Pfad** | `.core.modules.quick_search` |
| **Klasse** | `QuickSearchModule` |
| **Pipeline-Position** | Verarbeitung |
| **Zweck** | Entitaets-, Automations- und Service-Suche fuer PilotSuite. Entity Search (Name, State, Domain), Automation Search (Name, Trigger, Action), Service Search (Domain, Service-Name), Quick Actions, Character-System-Integration, Suggestions-Integration. |
| **Abhaengigkeiten** | HA States, Automations, Services |
| **Erzeugte Entities** | Keine eigenen; stellt Such-Services bereit |
| **Konfiguration** | Keine |

#### 5.3 character_module

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `character_module` |
| **Python-Pfad** | `.core.modules.character_module` |
| **Klasse** | `CharacterModule` |
| **Pipeline-Position** | Verarbeitung |
| **Zweck** | Persoenlichkeits-Management fuer PilotSuite. Definiert 5 Charakter-Modi: Assistant (neutral, effizient), Companion (warm, proaktiv), Guardian (sicherheitsfokussiert), Efficiency (optimierungsfokussiert), Relaxed (ruhig, minimal). Persistenz via HA Storage. Integration mit Mood- und Voice-Module. |
| **Abhaengigkeiten** | HA Storage |
| **Erzeugte Entities** | Keine eigenen; liefert Charakter-Konfiguration |
| **Konfiguration** | CharacterMode (assistant/companion/guardian/efficiency/relaxed) |


---

### 6. Haushalt

Module fuer Haushaltserinnerungen und Kalender-Integration.

#### 6.1 waste_reminder

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `waste_reminder` |
| **Python-Pfad** | `.core.modules.waste_reminder_module` |
| **Klasse** | `WasteReminderModule` |
| **Pipeline-Position** | Aktion |
| **Zweck** | Integriert mit hacs_waste_collection_schedule. Automatische Erinnerungen (Abend vorher + Morgen), TTS-Ansagen via proaktive Engine, persistente HA-Benachrichtigungen, LLM-Kontext-Injektion, Weiterleitung des Abfall-Kontexts an Core Add-on. Liest `daysTo`-Attribut der Waste-Sensoren. |
| **Abhaengigkeiten** | waste_collection_schedule (HACS), TTS-Services |
| **Erzeugte Entities** | Keine eigenen; nutzt HA Notifications |
| **Konfiguration** | Keine (automatische Erkennung der Waste-Sensoren) |

#### 6.2 birthday_reminder

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `birthday_reminder` |
| **Python-Pfad** | `.core.modules.birthday_reminder_module` |
| **Klasse** | `BirthdayReminderModule` |
| **Pipeline-Position** | Aktion |
| **Zweck** | Scannt HA-Kalender-Entities nach Geburtstags-Events. Taegliche Morgen-TTS-Ansagen, Liste kommender Geburtstage (14 Tage), LLM-Kontext-Injektion, persistente Benachrichtigungen. Erkennt Schluesselwoerter (Geburtstag, Birthday, Geb.) und extrahiert Name + Alter. Integration mit calendar_context fuer Mood-Gewichtung (soziale Events erhoehen sozialen Mood-Weight). |
| **Abhaengigkeiten** | calendar.* Entities, TTS-Services |
| **Erzeugte Entities** | Keine eigenen |
| **Konfiguration** | Keine |

#### 6.3 calendar_module

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `calendar_module` |
| **Python-Pfad** | `.core.modules.calendar_module` |
| **Klasse** | `CalendarModule` |
| **Version** | 0.1.0 |
| **Pipeline-Position** | Eingang / Verarbeitung |
| **Zweck** | Liest Events aus HA calendar.* Entities: Heute-/Upcoming-Events fuer LLM-Kontext, pro-Haushaltsmitglied-Kalender, event-bewusste proaktive Vorschlaege. |
| **Abhaengigkeiten** | calendar.* Entities |
| **Erzeugte Entities** | Kalender-Sensoren ueber sensors/calendar_sensors.py |
| **Konfiguration** | Keine (automatische Erkennung) |


---

### 7. Integration

Module, die HA mit dem Core Add-on und externen Systemen verbinden.

#### 7.1 events_forwarder

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `events_forwarder` |
| **Python-Pfad** | `.core.modules.events_forwarder` |
| **Klasse** | `EventsForwarderModule` |
| **Pipeline-Position** | Verarbeitung (Datenfluss HA -> Core) |
| **Zweck** | Opt-in HA->Core Event-Forwarder mit Privacy-first Allowlist. Leitet state_changed und call_service Events an Core /api/v1/events weiter. Bounded In-Memory-Queue mit Drop-Oldest-Policy, optionale persistente Queue (HA Storage), Idempotenz mit TTL, Rate-Limiting (Token-Bucket), exponentielles Backoff bei Fehlern, Neuron-Feed-Filter. Nur erlaubte Domains (light, media_player, climate, cover, lock, switch, scene, script). |
| **Abhaengigkeiten** | Core Add-on (/api/v1/events), Habitus Zones, Coordinator/API |
| **Erzeugte Entities** | `sensor.copilot_ha_forwarder_queue_depth`, `sensor.copilot_ha_forwarder_dropped_total`, `sensor.copilot_ha_forwarder_error_streak`, `binary_sensor.copilot_ha_forwarder_connected` |
| **Konfiguration** | `events_forwarder_enabled`, `flush_interval` (1-60s), `max_batch` (1-500), `forward_call_service`, `idempotency_ttl` (0-86400s), `persistent_queue_enabled`, `persistent_queue_max_size`, `include_habitus_zones`, `include_media_players`, `additional_entities` |

#### 7.2 history_backfill

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `history_backfill` |
| **Python-Pfad** | `.core.modules.history_backfill` |
| **Klasse** | `HistoryBackfillModule` |
| **Pipeline-Position** | Eingang (einmalig) |
| **Zweck** | Bootstrappt den Brain Graph aus dem HA Recorder. Holt bei Erst-Setup die State-History der letzten 24 Stunden fuer Allowlist-Entities und sendet sie als Events an Core. Laeuft nur einmal (Completion via HA Storage gespeichert). Verwendet dieselbe Entity-Allowlist wie der Events-Forwarder. |
| **Abhaengigkeiten** | HA Recorder, Events Forwarder (Allowlist), Core Add-on (/api/v1/events) |
| **Erzeugte Entities** | Keine |
| **Konfiguration** | Keine (automatisch bei Erst-Setup) |

#### 7.3 candidate_poller

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `candidate_poller` |
| **Python-Pfad** | `.core.modules.candidate_poller` |
| **Klasse** | `CandidatePollerModule` |
| **Pipeline-Position** | Korrelation |
| **Zweck** | Bruecke zwischen Core API Candidates und HA Repairs UI. Pollt periodisch Core /api/v1/candidates?state=pending und konvertiert jeden Kandidaten in ein HA Repairs Issue via suggest.async_offer_candidate. Synchronisiert Benutzer-Entscheidungen (accepted/dismissed) zurueck zum Core. Rate-Limiting und exponentielles Backoff. |
| **Abhaengigkeiten** | Core Add-on (/api/v1/candidates), CopilotApiClient, suggest.py |
| **Erzeugte Entities** | Keine eigenen; erzeugt HA Repairs Issues |
| **Konfiguration** | Poll-Intervall (5 Minuten Standard) |

#### 7.4 habitus_miner

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `habitus_miner` |
| **Python-Pfad** | `.core.modules.habitus_miner` |
| **Klasse** | `HabitusMinerModule` |
| **Pipeline-Position** | Lernen / Korrelation |
| **Zweck** | A->B Pattern Discovery aus HA-Events. Zonen-basiertes Pattern Mining: sammelt state_changed Events in einem persistenten Puffer (deque, maxlen=1000, HA Storage alle 5 Minuten), entdeckt Verhaltens-Regeln mit Confidence/Lift/Support-Metriken via Core API, erzeugt Automation-Vorschlaege aus Regeln. Zone-Affinity-Mapping ueber Habitus Zones. |
| **Abhaengigkeiten** | Core Add-on (habitus/mine API), Habitus Zones, Coordinator |
| **Erzeugte Entities** | `sensor.copilot_ha_habitus_miner_status`, `sensor.copilot_ha_habitus_miner_rule_count`, `sensor.copilot_ha_habitus_miner_top_rule` |
| **Konfiguration** | `min_confidence` (0.5), `min_lift` (1.2), `max_rules` (100), `buffer_max_size` (1000), `buffer_max_age_hours` (24) |
| **Services** | `habitus_mine_rules`, `habitus_get_rules`, `habitus_reset_cache`, `habitus_configure_mining` |

#### 7.5 entity_tags

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `entity_tags` |
| **Python-Pfad** | `.core.modules.entity_tags_module` |
| **Klasse** | `EntityTagsModule` |
| **Version** | 0.2.0 |
| **Pipeline-Position** | Verarbeitung |
| **Zweck** | Manuelles und automatisches Entity-Tagging. Benutzer koennen eigene Tags zuweisen, jede von Styx interagierte Entity bekommt automatisch den "Styx"-Tag. Tags sichtbar in LLM-Kontext, Sensoren, und querybar von anderen Modulen. |
| **Abhaengigkeiten** | Entity Tags Store |
| **Erzeugte Entities** | Keine eigenen |
| **Konfiguration** | Via Config Flow UI |

#### 7.6 person_tracking

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `person_tracking` |
| **Python-Pfad** | `.core.modules.person_tracking_module` |
| **Klasse** | `PersonTrackingModule` |
| **Pipeline-Position** | Eingang / Verarbeitung |
| **Zweck** | Personen-Tracking via person.* und device_tracker.*. Erfasst Praesenz-Status, Ankunfts-/Abfahrts-Historie, LLM-Kontext. Privacy-first: nur lokale Entity-Daten. Domains: person, device_tracker. States: home, not_home, Zonen-Namen. |
| **Abhaengigkeiten** | person.*, device_tracker.* |
| **Erzeugte Entities** | Keine eigenen; liefert LLM-Kontext |
| **Konfiguration** | Keine |

#### 7.7 scene_module

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `scene_module` |
| **Python-Pfad** | `.core.modules.scene_module` |
| **Klasse** | `SceneModule` |
| **Version** | 0.1.0 |
| **Pipeline-Position** | Aktion |
| **Zweck** | Habitus-Zonen-Szenenverwaltung: aktuelle Zonen-Bedingungen als HA-Szenen speichern, mit Lernen, Vorschlaegen und eingebauten Presets. Erfassbare Domains: light, switch, cover, climate, fan, media_player, input_boolean, input_number, input_select. |
| **Abhaengigkeiten** | Habitus Zones, HA Scene-Service |
| **Erzeugte Entities** | Szenen-Entities ueber HA Szenen-System |
| **Konfiguration** | Keine |

#### 7.8 homekit_bridge

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `homekit_bridge` |
| **Python-Pfad** | `.core.modules.homekit_bridge` |
| **Klasse** | `HomeKitBridgeModule` |
| **Version** | 2.0 |
| **Pipeline-Position** | Aktion |
| **Zweck** | Exponiert Habitus-Zonen-Entities an Apple HomeKit. Pro-Zone HomeKit-Toggle in HA Storage, ruft homekit.reload nach Filter-Aenderungen auf, auto-exponiert neue Zonen, holt Setup-Codes und QR-URLs vom Core Add-on. Dashboard zeigt QR-Code pro Zone. Unterstuetzte Domains: light, switch, cover, climate, fan, lock, media_player, sensor, binary_sensor, input_boolean. |
| **Abhaengigkeiten** | HA HomeKit-Integration, Core Add-on, Habitus Zones |
| **Erzeugte Entities** | HomeKit-Entities ueber homekit_entities.py |
| **Konfiguration** | Pro-Zone-Toggle (HA Storage) |

#### 7.9 media_zones

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `media_zones` |
| **Python-Pfad** | `.core.modules.media_context_module` |
| **Klasse** | `MediaContextModule` |
| **Version** | 0.1 |
| **Pipeline-Position** | Eingang |
| **Zweck** | Leichtgewichtiger, read-only Snapshot konfigurierter Medienplayer (Spotify, Sonos, TV usw.) fuer Mood, Habitus und Entertain Module. Privacy-first: nur entity_id, state, media_type, media_title, area. Keine Album-Art-URLs, keine Wiedergabepositionen, keine Benutzerkonten. |
| **Abhaengigkeiten** | media_player.* Entities |
| **Erzeugte Entities** | Media-Sensoren (Music Active Count, TV Active Count, etc.) |
| **Konfiguration** | `media_music_players`, `media_tv_players` (CSV-Listen oder Listen) |


---

### 8. System

Module fuer Betrieb, Debug, Performance und Frontend-Management.

#### 8.1 legacy

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `legacy` |
| **Python-Pfad** | `.core.modules.legacy` |
| **Klasse** | `LegacyModule` |
| **Pipeline-Position** | Eingang (Kern-Setup) |
| **Zweck** | Bewahrt das bestehende Single-Module-Verhalten. Erstellt den CopilotDataUpdateCoordinator, registriert Webhook, richtet Devlog-Push, HA-Errors-Digest, Media Context (v1+v2) und Seed Adapter ein. Leitet Entity-Plattformen weiter (binary_sensor, sensor, button, text, number, select, switch, stt, tts). Muss als erstes Modul geladen werden. |
| **Abhaengigkeiten** | CopilotDataUpdateCoordinator, Webhook, Core Add-on |
| **Erzeugte Entities** | Alle Basis-Entities ueber Plattform-Forwarding |
| **Konfiguration** | Erbt Config-Entry-Daten |

#### 8.2 performance_scaling

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `performance_scaling` |
| **Python-Pfad** | `.core.modules.performance_scaling` |
| **Klasse** | `PerformanceScalingModule` |
| **Pipeline-Position** | System (Hintergrund) |
| **Zweck** | Performance-Monitoring und Skalierungs-Guardrails. Trackt API-Antwortzeiten (Rolling Window, Perzentile), Speicherverbrauch (/proc/self/status), Entity-Anzahl, Coordinator-Update-Latenz. Alert-Schwellen mit konfigurierbaren Limits. Background-Task prueft alle 60 Sekunden. Integration mit PerformanceGuardrails Rate-Limiting. |
| **Abhaengigkeiten** | PerformanceGuardrails |
| **Erzeugte Entities** | Keine eigenen; Daten abrufbar via get_snapshot() |
| **Konfiguration** | Schwellen: api_response_time_ms (2000), coordinator_update_ms (5000), entity_count_max (200), memory_usage_mb_max (1536), error_rate_percent (5.0) |

#### 8.3 dev_surface

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `dev_surface` |
| **Python-Pfad** | `.core.modules.dev_surface` |
| **Klasse** | `DevSurfaceModule` |
| **Pipeline-Position** | System (Debug) |
| **Zweck** | Entwickler-Oberflaeche mit DevLog-Puffer (800 Events), Error-Digest (50 Recent, Error-Gruppierung, Traceback-Summary), Debug-Modi (off/light/full mit Auto-Timeout), Ping-Service. Privacy-first Redaktion: Emails, JWTs, Bearer-Tokens, URL-Credentials werden automatisch maskiert. |
| **Abhaengigkeiten** | Coordinator |
| **Erzeugte Entities** | Keine eigenen; Daten ueber HA Services abrufbar |
| **Konfiguration** | Debug-Level (off/light/full), Debug-Timeout (max 24h) |
| **Services** | `enable_debug_for`, `disable_debug`, `clear_error_digest`, `set_debug_level`, `clear_all_logs`, `ping` |

#### 8.4 ops_runbook

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `ops_runbook` |
| **Python-Pfad** | `.core.modules.ops_runbook` |
| **Klasse** | `OpsRunbookModule` |
| **Version** | 0.1 |
| **Pipeline-Position** | System |
| **Zweck** | Operations-Runbook mit automatisierten Diagnoseprozeduren. Stellt OpsRunbookStore fuer persistente Runbook-Daten bereit. Erstellt ops_runbook-spezifische Entities. |
| **Abhaengigkeiten** | OpsRunbookStore, ops_runbook.py |
| **Erzeugte Entities** | Ops-Runbook-Entities |
| **Konfiguration** | Keine |

#### 8.5 frontend_module

| Eigenschaft | Wert |
|-------------|------|
| **Registry-Name** | `frontend_module` |
| **Python-Pfad** | `.core.modules.frontend_module` |
| **Klasse** | `FrontendModule` |
| **Pipeline-Position** | System (Frontend) |
| **Zweck** | Dashboard-Lifecycle-Management. Dashboard-Refresh-Service (copilot_ha.refresh_dashboard), View-Toggle-Persistenz (8 Views: styx, haushalt, zonen, automation, energie, musik, ki, chat), automatischer Rebuild bei Habitus-Zonen-Aenderungen (entprellt), SIGNAL_FRONTEND_MODULE_READY fuer Entity-Erzeugung in switch/button Plattformen. |
| **Abhaengigkeiten** | HA Storage, Habitus Zones (Signal), Dashboard-Generator |
| **Erzeugte Entities** | View-Toggle-Switches, Dashboard-Refresh-Button |
| **Konfiguration** | View-Toggles (persistent via HA Storage) |
| **Services** | `refresh_dashboard` |


---

## Standalone-Module

Folgende Module werden NICHT ueber das CopilotModule-Interface geladen,
sondern separat in `__init__.py::async_setup_entry()` initialisiert:

| Modul | Klasse | Beschreibung |
|-------|--------|-------------|
| UserPreferenceModule | `user_preference_module.py` | Benutzer-Praeferenz-Tracking (opt-in via `CONF_USER_PREFERENCE_ENABLED`) |
| MultiUserPreferenceModule | `multi_user_preferences.py` | Multi-User Praeferenz-Lernsystem v0.8.0 (opt-in via `CONF_MUPL_ENABLED`) |
| ZoneDetector | `zone_detector.py` | Proaktive Zonen-Eintritts-Weiterleitung an Core Add-on (v3.1.0) |
| StyxConversationAgent | `conversation.py` | HA Conversation Agent (Proxy zu Core OpenAI-kompatiblem Endpoint) |
| Zone Auto-Setup | `zone_auto_setup.py` | Automatische Habitus-Zonen-Erstellung aus HA-Areas (v14.4.0) |


---

## Modul-Ladekette

Die Module werden in der in `_MODULES` definierten Reihenfolge geladen:

```
1.  legacy                  <-- Kern: Coordinator, Plattformen, Webhook
2.  performance_scaling     <-- System-Monitoring
3.  events_forwarder        <-- HA->Core Event-Bridge
4.  history_backfill        <-- Einmalige History-Befuellung
5.  dev_surface             <-- Debug-Tools + Services
6.  habitus_miner           <-- Pattern Discovery
7.  ops_runbook             <-- Operations-Runbook
8.  unifi_module            <-- UniFi-Diagnostik
9.  brain_graph_sync        <-- Brain-Graph-Synchronisation
10. candidate_poller        <-- Core-Candidates -> HA Repairs
11. media_zones             <-- Medienplayer-Kontext
12. mood                    <-- Stimmungsinferenz
13. mood_context            <-- Core Mood API Konsument
14. energy_context          <-- Energiemonitoring
15. network                 <-- Netzwerk-Kontext
16. weather_context         <-- Wetter/PV-Kontext
17. knowledge_graph_sync    <-- Knowledge-Graph-Sync
18. ml_context              <-- ML Pattern/Anomaly
19. camera_context          <-- Kamera-Integration
20. quick_search            <-- Entity/Service-Suche
21. voice_context           <-- Sprachsteuerung/TTS
22. home_alerts             <-- Kritische Hauszustandswarnungen
23. character_module        <-- Persoenlichkeits-Presets
24. waste_reminder          <-- Muellabfuhr-Erinnerungen
25. birthday_reminder       <-- Geburtstags-Erinnerungen
26. entity_tags             <-- Entity-Tagging
27. person_tracking         <-- Personen-Tracking
28. frigate_bridge          <-- Frigate NVR Bridge
29. scene_module            <-- Zonen-Szenen
30. homekit_bridge          <-- Apple HomeKit Bridge
31. calendar_module         <-- Kalender-Integration
32. licht_module            <-- Zonen-Licht-Tracking
33. helligkeit_module       <-- Zonen-Helligkeit-Tracking
34. heiz_module             <-- Zonen-Klima-Tracking
35. bewegung_module         <-- Zonen-Bewegung-Tracking
36. praesenz_module         <-- Zonen-Praesenz-Tracking
37. frontend_module         <-- Dashboard-Lifecycle
```

Bei Fehler eines Moduls: Rollback aller bereits geladenen Module,
dann Retry nur der erfolgreichen Module (Graceful Degradation).
