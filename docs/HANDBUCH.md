# PilotSuite Styx -- Benutzerhandbuch

**Version:** 14.6.5
**Datum:** 2026-03-16
**Sprache:** Deutsch

---

## Inhaltsverzeichnis

1. [Was ist PilotSuite?](#1-was-ist-pilotsuite)
2. [Installation](#2-installation)
3. [Dashboard-Uebersicht (8 Tabs)](#3-dashboard-uebersicht-8-tabs)
4. [Habituszonen](#4-habituszonen)
5. [Musikwolke](#5-musikwolke)
6. [Sprachsteuerung (Styx Chat)](#6-sprachsteuerung-styx-chat)
7. [Neuronales Netzwerk](#7-neuronales-netzwerk)
8. [Stimmungserkennung](#8-stimmungserkennung)
9. [Vorschlagssystem](#9-vorschlagssystem)
10. [Habitus Miner](#10-habitus-miner)
11. [Energiemanagement](#11-energiemanagement)
12. [Tag-System](#12-tag-system)
13. [Services (copilot_ha.*)](#13-services-copilot_ha)
14. [Privacy und Sicherheit](#14-privacy-und-sicherheit)
15. [Fehlerbehebung](#15-fehlerbehebung)
16. [FAQ](#16-faq)

---

## 1. Was ist PilotSuite?

PilotSuite Styx ist eine **lokale KI-Plattform fuer Smart Homes**, die auf Home Assistant aufsetzt. Sie lernt kontinuierlich aus dem Verhalten Ihres Haushalts, erkennt Muster und macht intelligente Vorschlaege -- ohne dass Daten jemals Ihr Zuhause verlassen.

### Zwei Komponenten, ein System

```
+-------------------------------------------------------+
|                   Home Assistant                       |
|                                                        |
|  +-------------------+       +---------------------+  |
|  | PilotSuite HA     |<----->| PilotSuite Core     |  |
|  | (HACS-Integration)|  REST | (Add-on, Port 8909) |  |
|  |                   |  API  |                      |  |
|  | "Sinne + Haende"  |       | "Gehirn + Stimme"   |  |
|  | - Sensoren lesen  |       | - Ollama LLM        |  |
|  | - Entities        |       | - Brain Graph        |  |
|  | - Dashboard       |       | - Habitus Mining     |  |
|  | - Config Flow     |       | - Mood Engine        |  |
|  | - Lovelace Cards  |       | - Neuronales System  |  |
|  +-------------------+       +---------------------+  |
+-------------------------------------------------------+
```

- **PilotSuite HA** (HACS-Integration, `copilot_ha`): Liest Sensordaten, erstellt Entities, steuert Geraete, zeigt Dashboards und Lovelace Cards an. Sie ist der "Thin Client" -- die Sinne und Haende des Systems.
- **PilotSuite Core** (Add-on): Das Backend mit KI-Gehirn. Hier laufen das lokale LLM (Ollama/qwen3), der Brain Graph, die Mood Engine, das Habitus Mining und die neuronale Pipeline. Ohne Core kein Chat und keine KI-Vorschlaege.

### Kernprinzipien

| Prinzip | Bedeutung |
|---------|-----------|
| **Local-first** | Alle Daten und KI-Modelle laufen lokal -- keine Cloud, kein externer API-Call |
| **Privacy-first** | Keine PII-Speicherung, automatische Redaktion, opt-in fuer alle Features |
| **Governance-first** | Vorschlaege statt automatischer Aktionen. Der Mensch entscheidet (Human-in-the-Loop) |

---

## 2. Installation

### Voraussetzungen

- Home Assistant 2024.1.0 oder neuer
- HACS (Home Assistant Community Store) installiert
- Ausreichend Hardware fuer das lokale LLM (empfohlen: 4+ GB RAM frei)

### Schritt 1: Core Add-on installieren

1. In Home Assistant: **Einstellungen --> Add-ons --> Add-on Store --> Drei-Punkte-Menue --> Repositories**
2. Repository-URL hinzufuegen: `https://github.com/GreenhillEfka/pilotsuite-styx-core`
3. Neues Add-on "PilotSuite Core" suchen und **INSTALLIEREN**
4. Konfiguration pruefen (Standard ist in Ordnung)
5. **STARTEN** und "Beim Booten starten" aktivieren
6. Im Log pruefen: `Starting CoPilot Core...` sollte erscheinen

### Schritt 2: HA-Integration installieren (HACS)

1. In HACS: **Integrationen --> Drei-Punkte-Menue --> Benutzerdefinierte Repositories**
2. URL: `https://github.com/GreenhillEfka/pilotsuite-styx-ha`, Kategorie: Integration
3. "PilotSuite" suchen und herunterladen
4. Home Assistant **neu starten**

### Schritt 3: Integration konfigurieren

1. **Einstellungen --> Geraete und Dienste --> Integration hinzufuegen**
2. "PilotSuite" suchen und auswaehlen
3. Der 7-Schritt-Wizard fuehrt durch die Konfiguration:

| Schritt | Inhalt |
|---------|--------|
| 1. Discovery | Auto-Erkennung des Core Add-ons (host + port + token) |
| 2. Zonen | Habitus-Zonen konfigurieren (automatisch aus HA-Areas) |
| 3. Zonen-Entities | Entities den Zonen zuordnen |
| 4. Entities | Globale Entity-Auswahl |
| 5. Features | Features aktivieren (Musikwolke, Energiemanagement, etc.) |
| 6. Netzwerk | UniFi, Webhook, Forwarder-Einstellungen |
| 7. Review | Zusammenfassung und Bestaetigung |

**Hinweis:** Die Auto-Discovery erkennt den Core unter `homeassistant.local:8909` automatisch. Falls die Erkennung fehlschlaegt, kann der Endpoint manuell eingegeben werden.

### Schritt 4: Erste Schritte nach der Installation

1. **Dashboard oeffnen**: PilotSuite erstellt automatisch ein Storage-Mode-Dashboard (kein HA-Neustart noetig)
2. **Sprachassistent**: Unter **Einstellungen --> Sprachassistenten** "PilotSuite" als Conversation Agent auswaehlen
3. **24-48 Stunden warten**: Das System braucht Daten fuer erste Muster und Vorschlaege

---

## 3. Dashboard-Uebersicht (8 Tabs)

Das PilotSuite Dashboard wird automatisch als Storage-Mode-Dashboard erstellt und ist sofort in der Sidebar sichtbar. Es besteht aus 8 Tabs:

### Tab 1: Styx (Neural Interface)

Der Haupt-Tab mit KI-Uebersicht:

- **Neural Interface** (`styx-neural-card`): Interaktives Diagramm des gesamten neuronalen Systems
- **Stimmung** (`styx-mood-card`): Aktuelle Hausstimmung mit Konfidenz-Gauge
- **Brain Graph** (`styx-brain-card`): Visualisierung der Knoten und Kanten des Zustandsgraphen
- **KI-Vorschlaege** (`styx-suggestions-card`): Accept/Reject/Snooze-Aktionen
- **Fehler und Reparatur** (`styx-error-card`): Aktuelle Probleme und Loesungsvorschlaege

### Tab 2: Haushalt

Ganzheitliche Uebersicht ueber Ihren Haushalt:

- **Haushaltsuebersicht** (`styx-household-card`): Wetter, Preise, Alarme, Zonen-Status
- **PilotSuite Status**: Online-Status, Version, API-Zustand, Zonenanzahl
- **Betrieb**: Reload, Forwarder, Dashboards
- **Medien**: Aktive Musik/TV-Player
- **Habitus-Zonen**: Zonen-Karte mit Mood und Neuron-Aktivitaet

### Tab 3: Zonen

Detailansicht aller Habitus-Zonen:

- **Habitus-Regeln** (`styx-habitus-card`): Erkannte Verhaltensregeln
- **Zonen-Karte** (`styx-zone-card`): Interaktive Zonen mit Mood, Neuron-Aktivitaet, Quick Actions
- **Zonen-Entities**: Alle einer Zone zugeordneten Entities

### Tab 4: Automation

Automatisierung und Muster:

- **Vorschlaege** (`styx-suggestions-card`): Offene Automatisierungsvorschlaege
- **Habitus-Regeln**: Erkannte A->B-Muster mit Confidence und Lift
- **Aktions-Buttons**: Brain Sync, Muster Mining, Dashboard aktualisieren

### Tab 5: Energie

Energieverbrauch und -erzeugung:

- **Verbrauch und Erzeugung**: Tageswerte, historische Trends
- **Geraete-Zeitplan**: Optimaler Betriebsplan fuer Grossverbraucher
- **Anomalie-Warnung**: Ungewoehnlicher Verbrauch wird erkannt

### Tab 6: Musik

Musikwolke-Steuerung:

- **Medien-Entities**: Aktive Speaker, Now Playing, Zonen-Status
- **Steuerungs-Buttons**: Alle abspielen, Alle pausieren, Follow starten
- **Zone-Speaker-Mapping**: Zuordnung von Speakern zu Habitus-Zonen

### Tab 7: KI (Neuronen)

Tiefer Einblick in das neuronale System:

- **Brain Graph**: Knoten und Kanten des Zustandsgraphen
- **Mood und Habitus**: Stimmung und erkannte Muster nebeneinander
- **Neuronen und Sensoren**: Context-, State- und Mood-Layer-Entities

### Tab 8: Chat

Direkter Zugang zum KI-Assistenten:

- **Styx Chat** (`styx-chat-card`): Volles Chat-Interface mit Konversationsverlauf

### Dynamische Zonen-Tabs (YAML-Dashboard)

Im YAML-Dashboard werden zusaetzlich **dynamische Tabs fuer jede Habitus-Zone** generiert. Jeder Zonen-Tab zeigt:
- Praesenz-Status und Bewegungsmelder
- Beleuchtung (Lichter, Helligkeit)
- Klima (Temperatur, Luftfeuchtigkeit, CO2)
- Medien (Speaker, TV)
- Rollladen und Fenster/Tueren

---

## 4. Habituszonen

### Was sind Habituszonen?

Habituszonen sind logische Bereiche Ihres Zuhauses, die PilotSuite automatisch oder manuell aus Ihren Home-Assistant-Areas erstellt. Aehnliche Raeume werden intelligent zusammengefasst:

| Zone | Raeume (Beispiel) | Typ |
|------|-------------------|-----|
| Wohnbereich | Wohnzimmer, Esszimmer, Gaestezimmer | area |
| Badbereich | Badezimmer, Toilette, Dusche | area |
| Kochbereich | Kueche, Speisekammer | area |
| Buerobereich | Buero, Homeoffice, Werkstatt | room |
| Gangbereich | Flur, Diele, Eingang, Korridor | area |
| Schlafbereich | Schlafzimmer | room |
| Kinderzimmer | Kinderzimmer, Spielzimmer | room |
| Terrassenbereich | Terrasse, Balkon, Wintergarten | outdoor |
| Aussenbereich | Garten, Garage, Hof | outdoor |
| Kellerbereich | Keller, Waschkueche, Technikraum | area |

### Automatische Einrichtung (ZeroConfig)

Beim ersten Start erkennt PilotSuite automatisch Ihre HA-Areas und erstellt Habituszonen:

1. **Keyword-Matching**: Deutsche und englische Raumbezeichnungen werden erkannt
2. **Fuzzy-Matching**: Tippfehler werden toleriert (Levenshtein-Distanz <= 1)
3. **Smart Aggregation**: Aehnliche Raeume (Bad + Toilette) werden zusammengefasst
4. **Virtuelle Areas werden uebersprungen**: Energie, Netzwerk, Kalender etc.

### Entity-Zuordnung und Rollenerkennung

Jede Entity in einer Zone erhaelt automatisch eine Rolle:

| Rolle | Erkannte Entities |
|-------|-------------------|
| `lights` | light.* |
| `motion` | binary_sensor mit device_class motion/presence/occupancy |
| `media` | media_player.* |
| `heating` | climate.*, fan.* |
| `temperature` | sensor mit device_class temperature |
| `humidity` | sensor mit device_class humidity |
| `brightness` | sensor mit device_class illuminance |
| `cover` | cover.* |
| `door` | binary_sensor mit device_class door |
| `window` | binary_sensor mit device_class window |
| `lock` | lock.* |
| `energy` | sensor mit device_class energy |
| `power` | sensor mit device_class power |

### Neuronale Tags

Aus den Entity-Rollen werden automatisch Neuron-Tags erstellt, die den drei Schichten des neuronalen Systems zugeordnet werden:

```
Entity-Rollen --> Neuron-Tags --> Neuronale Schichten

temperature, humidity, co2, energy, power --> Context Layer (blau)
motion, door, window, lock, cover, heating --> State Layer (gruen)
lights, brightness, media                  --> Mood Layer (rosa)
```

### Zone Automation (Drei Modi)

Jede Habituszone kann in einem von drei Automatisierungsmodi betrieben werden:

| Modus | Symbol | Verhalten |
|-------|--------|-----------|
| **off** | -- | Nur Zustandserfassung, keine Aktionen |
| **learning** | Lupe | Zustand + Mustererkennung (KI lernt Gewohnheiten) |
| **autonomy** | Blitz | Volle Automatisierung (Licht, Musik, Klima reagieren automatisch) |

**Modus setzen:**

```yaml
service: copilot_ha.zone_automation_set_mode
data:
  zone_id: wohnzimmer
  mode: learning
```

### Lichtsteuerung (Autonomy-Modus)

- Automatisches Einschalten bei Praesenz, Ausschalten bei Abwesenheit
- Konfigurierbare Verzoegerungen (Presence Delay, Absence Delay)
- Hysterese gegen Flackern bei Wolkendurchzug
- Aussen-Lux-Kompensation (Helligkeitssensor)

### Musiksteuerung (Autonomy-Modus)

- Auto-Play bei Betreten der Zone
- Follow-Modus zwischen Zonen
- Konfigurierbare Standard-Lautstaerke
- Automatisches Pausieren bei Abwesenheit

---

## 5. Musikwolke

Die **Musikwolke** ist PilotSuites Multiroom-Audiosystem. Es orchestriert Sonos-Speaker (und andere media_player-Entities) zonenbasiert.

### Funktionen

| Funktion | Beschreibung |
|----------|-------------|
| **Gruppen** | Mehrere Zonen spielen synchron die gleiche Musik |
| **Follow-Modus** | Musik folgt einer Person automatisch von Raum zu Raum |
| **Pro-Zone-Lautstaerke** | Jede Zone hat individuelle Lautstaerke (0-100%) |
| **Auto-Play** | Musik startet automatisch beim Betreten einer Zone (optional, im Autonomy-Modus) |

### Follow-Modus im Detail

```
Person betritt Zone A        Musik spielt in Zone A
        |
Person wechselt zu Zone B    Musik folgt zu Zone B
        |                    Zone A wird pausiert
Person wechselt zu Zone C    Musik folgt zu Zone C
        |                    Zone B wird pausiert
Person verlaesst alle Zonen  Alle Zonen werden pausiert
```

Der Follow-Modus nutzt die Praesenz-Erkennung (Bewegungsmelder, Person-Tracking) der Habituszonen.

### Steuerung

**Per Dashboard (Musik-Tab):**
- Play/Pause/Dissolve-Buttons
- Follow Start/Stop-Buttons

**Per HA-Automation:**
```yaml
service: copilot_ha.musikwolke_start_follow
data:
  person_id: person.alice
  source_zone: wohnzimmer
```

**Per Sprachbefehl (Styx Chat):**
- "Spiele Musik im Wohnzimmer"
- "Stoppe die Musik ueberall"
- "Musik leiser im Schlafzimmer"
- "Musik folge mir"

### Verfuegbare Services

| Service | Funktion | Parameter |
|---------|----------|-----------|
| `copilot_ha.musikwolke_create` | Gruppe erstellen | `zone_ids` (Liste) |
| `copilot_ha.musikwolke_dissolve` | Gruppe aufloesen | `zone_ids` (Liste) |
| `copilot_ha.musikwolke_play` | Zone abspielen | `zone_id`, optional `volume_pct` |
| `copilot_ha.musikwolke_pause` | Zone pausieren | `zone_id` |
| `copilot_ha.musikwolke_volume` | Lautstaerke setzen | `zone_id`, `volume_pct` (0-100) |
| `copilot_ha.musikwolke_start_follow` | Follow starten | `person_id`, `source_zone` |
| `copilot_ha.musikwolke_stop_follow` | Follow stoppen | `session_id` |

---

## 6. Sprachsteuerung (Styx Chat)

PilotSuite enthaelt einen vollstaendig lokalen KI-Assistenten:

### Technische Daten

| Eigenschaft | Wert |
|-------------|------|
| **LLM-Modell** | qwen3:0.6b (Standard), qwen3:4b (optional) |
| **Runtime** | Ollama (im Core-Container) |
| **Sprachen** | Deutsch (primaer), Englisch |
| **API** | OpenAI-kompatibel (`/v1/chat/completions`) |
| **HA-Integration** | Conversation Agent ("PilotSuite") |
| **Tool-Calling** | 9+ Tools (Licht, Klima, Szenen, Entities, ...) |
| **Conversation Memory** | Lifelong Learning (erinnert sich an Praeferenzen) |

### Zugriffswege

1. **Dashboard**: Styx Chat Tab (Tab 8)
2. **HA Assist**: Einstellungen --> Sprachassistenten --> PilotSuite auswaehlen
3. **Telegram**: Ueber den integrierten Telegram-Bot (mit Server-seitigem Tool-Calling)
4. **API**: `POST /v1/chat/completions` am Core-Endpoint

### Speech-to-Text / Text-to-Speech

PilotSuite registriert eigene STT- und TTS-Provider in Home Assistant:
- **STT**: Spracheingabe ueber Mikrofon --> Text ueber Core LLM
- **TTS**: Text --> Sprachausgabe ueber Media-Player

```yaml
service: copilot_ha.speak
data:
  text: "Guten Morgen! Die Temperatur betraegt 22 Grad."
  entity_id: media_player.wohnzimmer
  language: de
```

### Beispielbefehle

- "Wie ist die Stimmung im Haus?"
- "Schalte das Licht im Bad aus"
- "Zeige mir den Energieverbrauch"
- "Aktiviere den Kino-Modus"
- "Wer ist gerade zu Hause?"
- "Stelle die Heizung im Schlafzimmer auf 20 Grad"

### Sprachstil

Der Sprachstil (Tone) kann angepasst werden:

```yaml
service: copilot_ha.set_voice_tone
data:
  tone: friendly  # formal, casual, friendly, professional
```

---

## 7. Neuronales Netzwerk

### Architektur-Uebersicht

```
+------------------------------------------------------------------+
|                    Neuronale Pipeline                              |
|                                                                    |
|  HA Events --> Event Ingest --> Brain Graph --> Habitus Miner      |
|                                    |               |               |
|                                Neurons          Patterns           |
|                                    |               |               |
|                                Mood Engine    Vorschlaege          |
|                                    |               |               |
|                              Stimmungs-        Repairs UI          |
|                              erkennung         Dashboard           |
+------------------------------------------------------------------+
```

### Brain Graph

Der Brain Graph ist ein gerichteter, gewichteter Zustandsgraph, der das aktuelle Wissen ueber Ihr Smart Home abbildet:

- **Knoten** (Nodes): Entities, Zonen, Geraete, Personen, Konzepte, Module, Events
- **Kanten** (Edges): in_zone, controls, affects, correlates, triggered_by, observed_with, mentions
- **Kapazitaet**: Bis zu 500 Knoten und 1.500 Kanten (konfigurierbar)
- **Exponentielles Decay**: Veraltete Informationen verlieren automatisch an Relevanz

```
effective_score = score * exp(-lambda * alter_in_stunden)
lambda = ln(2) / halbwertszeit
```

- Knoten-Halbwertszeit: 24 Stunden
- Kanten-Halbwertszeit: 12 Stunden

### Drei Neuronale Schichten

Die Neuronen sind in drei Schichten organisiert:

| Schicht | Farbe | Zweck | Beispiel-Neuronen |
|---------|-------|-------|-------------------|
| **Context** | Blau | Umgebungsdaten | Temperatur, Luftfeuchtigkeit, CO2, Energie, Wetter |
| **State** | Gruen | Physische Zustaende | Praesenz, Bewegung, Tueren, Fenster, Rollladen |
| **Mood** | Rosa | Komfort/Wohlbefinden | Licht, Helligkeit, Medien, Unterhaltung |

### Neuron Manager

Der Neuron Manager orchestriert 12+ Bewertungsneuronen:

- **PresenceNeuron**: Anwesenheitserkennung pro Zone
- **TimeOfDayNeuron**: Tageszeit-Kontext (morning/afternoon/evening/night)
- **LightLevelNeuron**: Beleuchtungsstaerke und Aussenhelligkeit
- **WeatherNeuron**: Wetterdaten (DWD, OpenWeatherMap)
- **EnergyLevelNeuron**: Aktueller Energieverbrauch und PV-Ertrag
- **StressIndexNeuron**: Systembelastung und Anomalien
- **ComfortIndexNeuron**: Gesamtkomfort-Bewertung
- **CameraNeuron**: Kamera-basierte Aktivitaetserkennung
- **UniFiNeuron**: Netzwerk-Praesenz und Geraete-Status

---

## 8. Stimmungserkennung

### 9 Stimmungszustaende

Die Mood Engine erkennt folgende Stimmungszustaende:

| Zustand | Deutsch | Beschreibung |
|---------|---------|-------------|
| **relax** | Entspannung | Niedriger Aktivitaetsgrad, angenehmes Ambiente |
| **focus** | Fokus | Konzentrations-Modus, wenig Ablenkung |
| **active** | Aktivitaet | Hoher Aktivitaetsgrad, mehrere Geraete in Nutzung |
| **sleep** | Schlaf | Nachtmodus, minimale Aktivitaet |
| **away** | Abwesend | Niemand zu Hause |
| **alert** | Alarm | Sicherheitsrelevante Situation |
| **social** | Sozial | Mehrere Personen anwesend, Unterhaltung |
| **recovery** | Erholung | Uebergangsphase, Rueckkehr zur Normalitaet |
| **unknown** | Unbekannt | Nicht genug Daten fuer Klassifikation |

### 3D-Mood-Scoring

Jede Zone wird in drei Dimensionen bewertet:

| Dimension | Wertebereich | Beschreibung |
|-----------|-------------|-------------|
| **Comfort** | 0.0 -- 1.0 | Komfort (Temperatur, Licht, Aktivitaet) |
| **Joy** | 0.0 -- 1.0 | Unterhaltung/Genuss (Musik, TV, soziale Aktivitaet) |
| **Frugality** | 0.0 -- 1.0 | Ressourceneffizienz (Tageszeit, Verbrauchsmuster) |

### Exponential Smoothing

Mood-Werte werden mit Alpha = 0.3 geglaettet, um abrupte Spruenge zu vermeiden:

```
neuer_wert = alter_wert * 0.7 + signal * 0.3
```

### Einfluss auf Vorschlaege

Die Stimmung beeinflusst die Relevanz von Vorschlaegen:
- **Joy > 0.6 und Comfort > 0.7**: Energiespar-Vorschlaege werden unterdrueckt (Frugality < 0.5)
- Ein stimmungsbasierter Multiplikator (0.0 -- 1.0) skaliert die Relevanz jedes Vorschlags

---

## 9. Vorschlagssystem

### Governance-Lifecycle

Vorschlaege durchlaufen einen festen Lebenszyklus:

```
Muster erkannt --> pending --> offered --> accepted / dismissed / snoozed
                                               |
                                          HA-Automation
                                          wird erstellt
```

| Status | Bedeutung |
|--------|-----------|
| **pending** | Muster wurde erkannt, noch nicht angeboten |
| **offered** | Vorschlag wird im Dashboard angezeigt |
| **accepted** | Nutzer hat den Vorschlag angenommen --> Automation wird erstellt |
| **dismissed** | Nutzer hat den Vorschlag abgelehnt |
| **snoozed** | Vorschlag wird fuer X Stunden zurueckgestellt |

### Quellen fuer Vorschlaege

PilotSuite generiert Vorschlaege aus vier Quellen:

| Quelle | Ort | Beschreibung |
|--------|-----|-------------|
| 1. Lokales Habitus Mining | HA-Integration | Association Rule Mining auf lokalen Events |
| 2. Lokale Anomalie-Erkennung | HA-Integration | Ungewoehnlicher Verbrauch, inaktive Geraete |
| 3. Core Habitus Mining | Core Add-on | Erweitertes Mining mit Brain-Graph-Kontext |
| 4. Core Proactive Engine | Core Add-on | Kontextbewusste Vorschlaege bei Zonenwechsel |

### Aktionen im Dashboard

Im Styx-Tab und Automation-Tab koennen Vorschlaege verwaltet werden:

```yaml
# Vorschlag annehmen
service: copilot_ha.suggestion_accept
data:
  suggestion_id: "sug_abc123"

# Vorschlag ablehnen
service: copilot_ha.suggestion_reject
data:
  suggestion_id: "sug_abc123"
  reason: "Nicht relevant"

# Vorschlag zurueckstellen (4 Stunden)
service: copilot_ha.suggestion_snooze
data:
  suggestion_id: "sug_abc123"
  hours: 4
```

---

## 10. Habitus Miner

### Was ist Habitus Mining?

Der Habitus Miner entdeckt Verhaltensregeln aus dem Smart-Home-Event-Strom mittels Association Rule Mining. Er sucht nach A->B-Mustern: "Wenn Event A auftritt, folgt Event B innerhalb eines Zeitfensters."

### Algorithmus

1. **Preprocessing**: Events filtern und deduplizieren
2. **Frequent Events**: Haeufige A- und B-Kandidaten identifizieren
3. **Hit-Counting**: Fuer jedes (A, B, dt)-Tripel zaehlen, wie oft B innerhalb von dt Sekunden nach A auftritt
4. **Quality Metrics**: Confidence, Lift, Leverage und Conviction berechnen
5. **Filtering**: Regeln unter Mindestschwellen verwerfen

### Qualitaetsmetriken

| Metrik | Bedeutung |
|--------|-----------|
| **Confidence** | Wie oft folgt B tatsaechlich auf A? (n(AB) / n(A)) |
| **Confidence LB** | Wilson Score Lower Bound -- konservativ bei kleinen Stichproben |
| **Lift** | Wie stark ist die Korrelation ueber Zufall? (Confidence / P(B)) |
| **Leverage** | Absoluter Unterschied zur Baseline |
| **Conviction** | Abhaengigkeitsgrad der Regel |

### Beispiel

```
Erkanntes Muster:
  A: light.kueche --> on
  B: switch.kaffeemaschine --> on
  Confidence: 0.82 (in 82% der Faelle)
  Lift: 3.4 (3.4x wahrscheinlicher als Zufall)

Vorschlag: "Wenn Sie das Kuechenlicht einschalten, soll die
            Kaffeemaschine automatisch angehen?"
```

### Zone-basiertes Mining

Events werden nach Habituszonen gruppiert. Das ermoeglicht raumspezifische Automatisierungen, z.B.:
- Schlafzimmer: Licht aus --> Rollladen runter
- Wohnzimmer: TV an --> Licht dimmen
- Kueche: Licht an --> Kaffeemaschine an

### Mining manuell starten

```yaml
service: copilot_ha.habitus_mine_rules
data:
  days_back: 7
  min_confidence: 0.5
  min_lift: 1.2
```

---

## 11. Energiemanagement

### Funktionen

| Funktion | Beschreibung |
|----------|-------------|
| **Verbrauchsanalyse** | Tagesverbrauch, Erzeugung, Netto-Bilanz |
| **Geraete-Zeitplan** | Optimierung nach PV-Ertrag und Stromtarif |
| **Anomalie-Erkennung** | Automatische Warnung bei ungewoehnlichem Verbrauch |
| **Energiefluss** | Visualisierung der Energiefluesse |

### Energy Insights

```yaml
service: copilot_ha.energy_insights_get
data:
  hours: 24
```

### Anomalie-Erkennung

```yaml
service: copilot_ha.anomaly_alert_check_and_alert
data:
  device_id: sensor.living_room_temperature
  threshold: 0.7
```

### Mood-Integration

Die Mood Engine beeinflusst Energiespar-Vorschlaege: Wenn der Komfort-Level hoch ist und der Joy-Wert ueber 0.6 liegt, werden Energiespar-Vorschlaege unterdrueckt, um das Wohlbefinden nicht zu stoeren.

---

## 12. Tag-System

Tags kategorisieren und gruppieren Entities zonenuebergreifend:

### Tag-Typen

| Typ | Beispiel | Zweck |
|-----|----------|-------|
| **Zone-Tags** | `area:wohnzimmer` | Entity einer Zone zuordnen |
| **Rollen-Tags** | `licht`, `klima`, `medien` | Funktionale Klassifikation |
| **Neuron-Tags** | `neuron_context_wohnbereich` | Neuronale Schicht-Zuordnung |
| **Custom-Tags** | `sicherheit`, `styx` | Benutzerdefinierte Gruppierung |

### Bidirektionale Synchronisation

Tags werden automatisch zwischen HA (Labels) und Core (Tag System) synchronisiert:

```yaml
# Tag manuell zuweisen
service: copilot_ha.tag_entity
data:
  entity_id: light.wohnzimmer
  tag_ids: "licht,ambient"

# Tags vom Core holen
service: copilot_ha.tag_registry_pull_from_core

# Labels sofort synchronisieren
service: copilot_ha.tag_registry_sync_labels_now
```

---

## 13. Services (copilot_ha.*)

### Uebersicht aller verfuegbaren Services

#### Installation und Setup

| Service | Beschreibung |
|---------|-------------|
| `show_installation_guide` | Installationsanleitung als Benachrichtigung |
| `ping` | Health-Check der Integration |

#### Vorschlagssystem

| Service | Beschreibung |
|---------|-------------|
| `suggestion_accept` | Vorschlag annehmen |
| `suggestion_reject` | Vorschlag ablehnen |
| `suggestion_snooze` | Vorschlag zurueckstellen |

#### Habitus Mining

| Service | Beschreibung |
|---------|-------------|
| `habitus_mine_rules` | Lokales Pattern-Mining starten |
| `habitus_get_rules` | Erkannte Regeln abrufen |
| `habitus_reset_cache` | Mining-Cache leeren |
| `habitus_configure_mining` | Mining-Parameter konfigurieren |
| `trigger_mining` | On-Demand Mining im Core |

#### Musikwolke

| Service | Beschreibung |
|---------|-------------|
| `musikwolke_create` | Gruppe erstellen |
| `musikwolke_dissolve` | Gruppe aufloesen |
| `musikwolke_play` | Zone abspielen |
| `musikwolke_pause` | Zone pausieren |
| `musikwolke_volume` | Lautstaerke setzen |
| `musikwolke_start_follow` | Follow starten |
| `musikwolke_stop_follow` | Follow stoppen |

#### Zone Automation

| Service | Beschreibung |
|---------|-------------|
| `zone_automation_set_mode` | Automatisierungsmodus setzen (off/learning/autonomy) |
| `assign_entity_to_zone` | Entity einer Zone zuordnen |
| `remove_entity_from_zone` | Entity aus Zone entfernen |

#### Sprachsteuerung

| Service | Beschreibung |
|---------|-------------|
| `parse_command` | Sprachbefehl in Intent parsen |
| `speak` | Text via TTS ausgeben |
| `execute_command` | Sprachbefehl parsen und ausfuehren |
| `get_voice_state` | Voice-Status abrufen |
| `set_voice_tone` | Sprachstil setzen |

#### Tag-System

| Service | Beschreibung |
|---------|-------------|
| `tag_entity` | Entity taggen |
| `untag_entity` | Tags von Entity entfernen |
| `tag_registry_upsert_tag` | Tag erstellen/aktualisieren |
| `tag_registry_set_assignment` | Tags einem Subject zuweisen |
| `tag_registry_confirm` | Tag bestaetigen |
| `tag_registry_sync_labels_now` | Labels sofort synchronisieren |
| `tag_registry_pull_from_core` | Tags vom Core holen |

#### Multi-User Praeferenzen (MUPL)

| Service | Beschreibung |
|---------|-------------|
| `mupl_learn_preference` | Praeferenz fuer User lernen |
| `mupl_set_user_priority` | User-Prioritaet setzen |
| `mupl_delete_user_data` | Userdaten loeschen (GDPR) |
| `mupl_export_user_data` | Userdaten exportieren (GDPR) |
| `mupl_detect_active_users` | Aktive User erkennen |
| `mupl_get_aggregated_mood` | Aggregierten Mood abrufen |

#### Energie

| Service | Beschreibung |
|---------|-------------|
| `energy_insights_get` | Energie-Insights abrufen |
| `anomaly_alert_check_and_alert` | Anomalie pruefen und alarmieren |
| `anomaly_alert_clear_history` | Anomalie-Verlauf loeschen |

#### Conversation Memory

| Service | Beschreibung |
|---------|-------------|
| `get_memory_stats` | Speicher-Statistiken abrufen |
| `get_memory_history` | Gespraechsverlauf abrufen |

#### Event Forwarder

| Service | Beschreibung |
|---------|-------------|
| `forwarder_n3_start` | Event-Forwarder starten |
| `forwarder_n3_stop` | Event-Forwarder stoppen |
| `forwarder_n3_stats` | Forwarder-Statistiken |

#### HomeKit Bridge

| Service | Beschreibung |
|---------|-------------|
| `homekit_enable_zone` | HomeKit fuer Zone aktivieren |
| `homekit_disable_zone` | HomeKit fuer Zone deaktivieren |

#### Debug

| Service | Beschreibung |
|---------|-------------|
| `enable_debug` | Debug-Modus aktivieren |
| `toggle_debug` | Debug-Modus umschalten |
| `enable_debug_for` | Debug fuer Entity aktivieren |
| `disable_debug` | Debug deaktivieren |
| `clear_debug_buffer` | Debug-Buffer leeren |
| `clear_error_digest` | Error-Digest leeren |
| `set_debug` | Debug-Modus setzen (legacy) |

#### Ops Runbook

| Service | Beschreibung |
|---------|-------------|
| `ops_runbook_preflight_check` | Preflight-Check ausfuehren |
| `ops_runbook_smoke_test` | Smoke-Test ausfuehren |
| `ops_runbook_execute_action` | Runbook-Aktion ausfuehren |
| `ops_runbook_run_checklist` | Checklist ausfuehren |

---

## 14. Privacy und Sicherheit

### Datenschutz-Grundsaetze

| Prinzip | Umsetzung |
|---------|-----------|
| **Kein Cloud-Upload** | Alle Daten bleiben auf Ihrem Home Assistant |
| **PII-Redaktion** | E-Mail-Adressen, IP-Adressen, Telefonnummern werden automatisch entfernt |
| **Token-Authentifizierung** | Alle API-Aufrufe erfordern einen Auth-Token |
| **GDPR-konform** | Datenexport und -loeschung per Service (`mupl_export_user_data`, `mupl_delete_user_data`) |
| **Retention Policies** | Automatisches Loeschen alter Daten (Mood: 30 Tage, max. 50.000 Eintraege) |
| **Opt-in Features** | Events Forwarder, DevLogs, Multi-User-Learning sind standardmaessig deaktiviert |

### Authentifizierung

PilotSuite verwendet Token-basierte Authentifizierung zwischen HA-Integration und Core:

- **Auto-Discovery**: Token wird beim ersten Setup automatisch vom Core abgerufen (1-Key-Flow)
- **Manuell**: Token kann unter Einstellungen --> Integrationen --> PilotSuite --> Konfigurieren gesetzt werden
- **Header**: `X-Auth-Token` (bei API-Aufrufen)

---

## 15. Fehlerbehebung

### Core Add-on nicht erreichbar

**Symptom:** "PilotSuite Core ist gerade nicht erreichbar"

1. Add-on Status pruefen: **Einstellungen --> Add-ons --> PilotSuite Core** -- laeuft es?
2. Logs pruefen: Add-on Logs auf Fehler ueberpruefen
3. Health-Endpoint testen: `http://homeassistant.local:8909/health` im Browser aufrufen
4. Token pruefen: Unter **Einstellungen --> Integrationen --> PilotSuite --> Konfigurieren** pruefen, ob der Token gesetzt ist

### Auto-Discovery fehlgeschlagen

**Symptom:** Integration findet Core nicht automatisch

1. Sicherstellen, dass das Core Add-on laeuft und auf Port 8909 hoert
2. Falls das Add-on beim HA-Boot noch nicht bereit ist: PilotSuite plant einen automatischen Retry nach 30 Sekunden
3. Manuell konfigurieren: Host = `homeassistant.local`, Port = `8909`
4. Bei Docker-Setups: Eventuell `host.docker.internal` statt `homeassistant.local` verwenden

### Dashboard leer oder fehlt

**Symptom:** Kein PilotSuite-Dashboard in der Sidebar

1. PilotSuite erstellt ein Storage-Mode-Dashboard automatisch -- kein HA-Neustart noetig
2. Browser-Cache leeren (Strg+Shift+R)
3. Pruefen, ob Custom Cards geladen sind: Browser-Konsole auf Fehler pruefen
4. Dashboard manuell regenerieren:

```yaml
service: copilot_ha.refresh_dashboard
```

### Keine Vorschlaege

**Symptom:** Dashboard zeigt keine KI-Vorschlaege

1. **24-48 Stunden warten** -- das System braucht Daten fuer Muster
2. Events Forwarder pruefen: Ist er aktiviert? (`events_forwarder_enabled: true`)
3. Mining manuell starten:

```yaml
service: copilot_ha.habitus_mine_rules
data:
  days_back: 7
```

4. Brain Graph Status pruefen: Haben die Sensoren Daten?

### Musikwolke reagiert nicht

1. Speaker eingeschaltet und im Netzwerk?
2. Media-Player in HA sichtbar und steuerbar?
3. Zone-Speaker-Mapping konfiguriert? (Media Context v2)
4. Musikwolke-Service testen:

```yaml
service: copilot_ha.musikwolke_play
data:
  zone_id: wohnzimmer
```

### Config Entry ID finden

Die Config Entry ID wird fuer einige Services benoetigt:

1. **Einstellungen --> Integrationen --> PilotSuite**
2. Auf die drei Punkte klicken --> **Systeminformationen**
3. Die Entry ID steht unter "Entry ID"

### Debug-Modus aktivieren

```yaml
service: copilot_ha.enable_debug
data:
  log_level: "DEBUG"
```

Logs finden Sie unter: **Einstellungen --> System --> Protokolle** (nach `custom_components.copilot_ha` filtern)

---

## 16. FAQ

### Brauche ich einen Cloud-Account oder ein Abo?

Nein. PilotSuite laeuft vollstaendig lokal. Es gibt keine Cloud-Anbindung, kein Abo, keine externen API-Aufrufe. Alles bleibt auf Ihrem Home Assistant.

### Welche Hardware brauche ich?

PilotSuite laeuft auf jeder Hardware, die Home Assistant unterstuetzt. Fuer den KI-Chat (LLM) werden ca. 4 GB freier RAM empfohlen. Das Standard-Modell (qwen3:0.6b) ist ressourcenschonend; fuer bessere Qualitaet kann qwen3:4b verwendet werden.

### Kann ich PilotSuite mit vorhandenen Automationen nutzen?

Ja. PilotSuite ergaenzt Ihre bestehenden Automationen -- sie werden nicht ersetzt. PilotSuite schlaegt neue Automationen vor, die Sie annehmen oder ablehnen koennen (Governance-first).

### Was passiert mit meinen Daten, wenn ich PilotSuite deinstalliere?

Die Integration und das Add-on koennen sauber deinstalliert werden. Lokale Daten (Brain Graph, Mood History, etc.) liegen im Add-on-Datenverzeichnis (`/data/`) und werden beim Entfernen des Add-ons geloescht.

### Kann ich mehrere Benutzer im Haushalt haben?

Ja. Das Multi-User Preference Learning (MUPL) Modul unterstuetzt mehrere Benutzer mit individuellen Praeferenzen. Jeder Benutzer kann eigene Lichtstaerken, Temperaturen und Lautstaerken haben. Bei Konflikten wird die User-Prioritaet beruecksichtigt.

### Wie oft werden Vorschlaege generiert?

- **Lokales Mining**: Kann manuell gestartet oder automatisch getriggert werden
- **Core Mining**: Laeuft periodisch und bei bestimmten Events
- **Proactive Engine**: Generiert Vorschlaege in Echtzeit bei Zonenwechsel

### Welche Sprachen werden unterstuetzt?

Die Integration und das Dashboard sind auf Deutsch ausgelegt. Der KI-Chat versteht Deutsch und Englisch. Die TTS-Ausgabe unterstuetzt ebenfalls beide Sprachen.

### Wie aktualisiere ich PilotSuite?

1. **HACS**: PilotSuite HA wird ueber HACS aktualisiert (automatische Benachrichtigung bei neuen Versionen)
2. **Add-on Store**: PilotSuite Core wird ueber den Add-on Store aktualisiert
3. **Wichtig**: Beide Komponenten muessen immer auf der gleichen Version sein (Paired Releases)

### Was bedeuten die drei Modi (off/learning/autonomy)?

- **off**: PilotSuite beobachtet nur -- keine Aktionen. Ideal zum Kennenlernen.
- **learning**: PilotSuite beobachtet und lernt Muster. Es werden Vorschlaege generiert, aber keine Aktionen ausgefuehrt. Empfohlen fuer die ersten Wochen.
- **autonomy**: PilotSuite handelt selbststaendig basierend auf gelernten Mustern (Licht, Musik, Klima). Nur fuer Zonen verwenden, in denen Sie dem System vertrauen.

---

**PilotSuite Styx v14.6.5** -- Ihr lokaler KI-Copilot fuer das Smart Home.
Alle Daten bleiben lokal. Alle Entscheidungen bleiben bei Ihnen.

*GitHub: [GreenhillEfka/pilotsuite-styx-ha](https://github.com/GreenhillEfka/pilotsuite-styx-ha) | [GreenhillEfka/pilotsuite-styx-core](https://github.com/GreenhillEfka/pilotsuite-styx-core)*
