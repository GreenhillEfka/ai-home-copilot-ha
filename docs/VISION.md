# PilotSuite Styx -- Vision

**Version:** 14.6.5
**Datum:** 2026-03-16
**Sprache:** Deutsch

---

## PilotSuite als lebenslanger, selbstschaerfender Begleiter

PilotSuite ist nicht einfach eine Smart-Home-Integration. Es ist ein **lebenslanger digitaler Begleiter**, der Ihr Zuhause mit der Zeit immer besser versteht. Anders als klassische Automatisierungssysteme, die starre Regeln ausfuehren, lernt PilotSuite kontinuierlich aus dem Verhalten Ihres Haushalts und passt sich an -- ohne Cloud, ohne Abo, ohne Datenweitergabe.

### Die Kernidee

```
Klassisches Smart Home:          PilotSuite:

Nutzer schreibt Regeln           Nutzer lebt einfach
        |                                |
Regeln werden ausgefuehrt        System beobachtet und lernt
        |                                |
Nutzer passt Regeln an           System schlaegt Verbesserungen vor
        |                                |
(Endlos-Schleife)                Nutzer entscheidet: Ja oder Nein
                                         |
                                 System wird praeziser
                                         |
                                 Haus passt sich dem Nutzer an
                                 (nicht umgekehrt)
```

**Das Ziel:** Ihr Zuhause soll sich Ihnen anpassen -- nicht Sie sich Ihrem Zuhause.

---

## Die Neurale Pipeline

### Vom Sensor zum Vorschlag

Die neurale Pipeline ist das Herzstrueck von PilotSuite. Sie transformiert rohe Sensordaten in intelligente Handlungsvorschlaege -- vollstaendig lokal, in Echtzeit.

```
+---------------------------------------------------------------------+
|                                                                       |
|  Home Assistant                                                       |
|  (4000+ Entities)                                                     |
|       |                                                               |
|       v                                                               |
|  [1] Sensoren und States                                              |
|       |  Licht, Temperatur, Bewegung, Tuer, Fenster, Medien, ...      |
|       v                                                               |
|  [2] Entity Tags                                                      |
|       |  Rolle: licht, klima, praesenz, medien, energie               |
|       |  Zone: wohnbereich, kochbereich, schlafbereich                 |
|       |  Neuron-Layer: context, state, mood                           |
|       v                                                               |
|  [3] Event Ingest (Batch, Dedup, Cooldown)                            |
|       |                                                               |
|       v                                                               |
|  [4] Backend-Sensoren (Neuronen)                                      |
|       |  Context: Temperatur, Wetter, Energie, CO2                    |
|       |  State:   Praesenz, Tueren, Fenster, Rollladen                |
|       |  Mood:    Licht, Helligkeit, Medien                           |
|       v                                                               |
|  [5] Brain Graph                                                      |
|       |  500+ Knoten, 1500+ Kanten                                    |
|       |  Exponentielles Decay (24h Halbwertszeit)                     |
|       |  Beziehungen: in_zone, controls, affects, correlates          |
|       v                                                               |
|  [6] Habitus Miner                                                    |
|       |  Association Rule Mining (A->B Muster)                        |
|       |  Wilson-Confidence, Lift, Leverage                            |
|       |  Zone-basiertes Mining                                        |
|       v                                                               |
|  [7] Mood Engine                                                      |
|       |  3D-Scoring: Comfort x Joy x Frugality                        |
|       |  9 Stimmungszustaende                                         |
|       |  Relevanz-Multiplikator fuer Vorschlaege                      |
|       v                                                               |
|  [8] Vorschlaege (Candidates)                                         |
|       |  Governance-Lifecycle: pending -> offered -> accepted          |
|       |  Human-in-the-Loop: Accept / Reject / Snooze                  |
|       v                                                               |
|  [9] Zurueck an Home Assistant                                        |
|       |  Automation erstellen, Licht/Klima/Medien steuern             |
|       |  Dashboard aktualisieren                                      |
|       |  Conversation Memory: Langzeit-Lernen                         |
|                                                                       |
+---------------------------------------------------------------------+
```

### Der Kreislauf

Die Pipeline ist kein linearer Prozess, sondern ein Kreislauf:

1. **Sensoren** liefern Rohdaten
2. **Tags** klassifizieren und gruppieren
3. **Neuronen** bewerten den Kontext
4. **Brain Graph** bildet Beziehungen ab
5. **Habitus Miner** entdeckt Muster
6. **Mood Engine** bewertet die Stimmung
7. **Vorschlaege** werden generiert
8. **Nutzer entscheidet** (Accept/Reject/Snooze)
9. **Entscheidung fliesst zurueck** in den Brain Graph
10. **Muster werden praeziser** -- der Kreislauf beginnt von vorn

Jede Nutzer-Entscheidung macht das System besser. Jedes "Nein" ist genauso wertvoll wie jedes "Ja".

---

## Universelle Anbindung

PilotSuite ist kein geschlossenes System. Es bietet mehrere standardisierte Schnittstellen, ueber die externe Clients, KI-Assistenten und Tools auf das gesamte Wissen zugreifen koennen.

### Drei API-Ebenen

```
+---------------------------------------------------+
|                PilotSuite Core                      |
|                                                     |
|  +-------------+  +------------------+  +-------+  |
|  | REST API    |  | OpenAI-kompatible|  | MCP   |  |
|  | /api/v1/*   |  | API /v1/*        |  | /mcp  |  |
|  |             |  |                  |  |       |  |
|  | Events      |  | chat/completions |  | Tools |  |
|  | Brain Graph |  | models           |  | Brain |  |
|  | Mood        |  | Tool-Calling     |  | Mood  |  |
|  | Habitus     |  | Streaming        |  | Neuro |  |
|  | Neurons     |  |                  |  |       |  |
|  | Candidates  |  | Kompatibel mit:  |  | JSON  |  |
|  | Zones       |  | - HA Extended    |  | -RPC  |  |
|  | Tags        |  |   OpenAI Conv.   |  | 2.0   |  |
|  | Energy      |  | - OpenAI SDK     |  |       |  |
|  | Dashboard   |  | - OpenClaw       |  |       |  |
|  +-------------+  +------------------+  +-------+  |
+---------------------------------------------------+
```

| Schnittstelle | Endpunkt | Zweck |
|---------------|----------|-------|
| **REST API** | `/api/v1/*` | Vollstaendiger Zugriff auf alle Subsysteme (Events, Graph, Mood, Habitus, Neurons, Zones, Tags) |
| **OpenAI-kompatible API** | `/v1/chat/completions`, `/v1/models` | Chat mit Tool-Calling. Kompatibel mit Extended OpenAI Conversation, OpenAI SDK, OpenClaw |
| **MCP Server** | `/mcp` | Model Context Protocol (JSON-RPC 2.0). Externe KI-Clients (Claude Desktop, OpenClaw) greifen auf Brain Graph, Habitus, Mood, Neurons zu |

### Warum drei APIs?

- **REST API**: Fuer programmatische Integration, Dashboards, Monitoring
- **OpenAI-kompatible API**: Fuer jeden OpenAI-kompatiblen Client -- PilotSuite wird zum lokalen LLM-Backend
- **MCP Server**: Fuer die naechste Generation von KI-Tools, die standardisiert auf Kontextdaten zugreifen wollen

---

## Governance-first: Von Vorschlaegen zu Vertrauen zu Autonomie

### Das Drei-Phasen-Modell

PilotSuite erzwingt keine Automatisierung. Stattdessen baut es schrittweise Vertrauen auf:

```
Phase 1: BEOBACHTUNG (off)
  |  System beobachtet, lernt im Hintergrund
  |  Keine Aktionen, keine Vorschlaege
  |  Nutzer lernt das System kennen
  |
  v
Phase 2: VORSCHLAEGE (learning)
  |  System erkennt Muster und schlaegt vor
  |  Nutzer entscheidet: Accept / Reject / Snooze
  |  Jede Entscheidung verbessert das Modell
  |  Vertrauen waechst mit jeder richtigen Vorhersage
  |
  v
Phase 3: AUTONOMIE (autonomy)
  |  System handelt selbststaendig
  |  Nur fuer Zonen und Aktionen, denen der Nutzer vertraut
  |  Nutzer kann jederzeit zurueck zu Phase 2 wechseln
  |  Transparenz: Jede Aktion ist erklaerbar
```

### Granulare Autonomie

Autonomie ist nicht alles-oder-nichts. Sie ist **pro Zone** und **pro Aktionstyp** konfigurierbar:

| Zone | Licht | Musik | Klima | Rollladen |
|------|-------|-------|-------|-----------|
| Wohnzimmer | autonomy | learning | off | off |
| Schlafzimmer | autonomy | autonomy | learning | off |
| Kueche | learning | off | off | off |
| Buero | autonomy | autonomy | autonomy | learning |

### Erklaerbarkeit

Jeder Vorschlag und jede Aktion ist erklaerbar. Die Explainability Engine generiert natuerlichsprachige Erklaerungen:

> "Vorschlag: Licht im Flur automatisch einschalten bei Bewegung.
> Begruendung: In den letzten 7 Tagen haben Sie 47 Mal das Flurlicht innerhalb von 3 Sekunden nach Bewegungserkennung eingeschaltet (Confidence: 89%, Lift: 4.2x)."

---

## Privacy-first: Alles lokal, keine Cloud

### Technische Garantien

PilotSuite ist architektonisch darauf ausgelegt, dass keine Daten Ihr Zuhause verlassen:

```
+---------------------------------------+
|          Ihr Home Assistant            |
|                                        |
|  +------+    +------+    +----------+ |
|  | HA   |--->| Pilot|--->| SQLite   | |
|  | Core |    | Suite|    | Datenbank| |
|  |      |<---| Core |<---| /data/   | |
|  +------+    +------+    +----------+ |
|                                        |
|  Kein Ausgang ins Internet             |
|  Kein Cloud-API-Call                   |
|  Kein Telemetrie-Upload               |
|  Kein Account, kein Login             |
+---------------------------------------+
```

| Massnahme | Umsetzung |
|-----------|-----------|
| **Lokales LLM** | Ollama laeuft im Docker-Container. Modell: qwen3:0.6b (oder 4b) |
| **Lokale Datenbank** | SQLite (WAL-Modus) unter `/data/`. Keine externe Datenbank |
| **PII-Redaktion** | E-Mail, IP, Telefonnummern werden automatisch aus dem Brain Graph entfernt |
| **Bounded Storage** | Mood: 30 Tage, max. 50.000 Eintraege. Brain Graph: max. 500 Knoten |
| **Opt-in Features** | Event Forwarding, Dev Logs, Multi-User Learning sind standardmaessig AUS |
| **GDPR-Services** | `mupl_export_user_data` und `mupl_delete_user_data` fuer Datenhoheit |

### Cloud-Fallback (optional, opt-in)

Fuer Nutzer, die ein leistungsfaehigeres LLM bevorzugen, existiert ein optionaler Cloud-Fallback:
- Standardmaessig deaktiviert
- Nur fuer den Chat-Endpoint (`/v1/chat/completions`)
- Konfigurierbar ueber Add-on-Optionen (`cloud_api_url`, `cloud_api_key`, `cloud_model`)
- Kein anderes Subsystem (Brain Graph, Habitus, Mood) nutzt Cloud-Dienste

---

## Zukunftsvision: Das Haus passt sich dem Nutzer an

### Heute (v14.6.5)

PilotSuite erkennt Muster, schlaegt Automatisierungen vor und steuert Licht, Musik und Klima zonenbasiert. Der Nutzer hat volle Kontrolle ueber jede Entscheidung.

### Morgen

```
                    Jetzt                          Zukunft
               +-------------+               +------------------+
               |    Nutzer    |               |     Nutzer       |
               |  steuert    |               |   lebt einfach   |
               |  manuell    |               |                  |
               +------+------+               +--------+---------+
                      |                                |
                      v                                v
               +-------------+               +------------------+
               | Smart Home  |               |   PilotSuite     |
               | fuehrt aus  |               |   beobachtet,    |
               |             |               |   lernt,         |
               +-------------+               |   optimiert,     |
                                              |   erklaert       |
                                              +------------------+
```

### Roadmap-Ideen

#### Multi-User-Optimierung

Mehrere Personen im Haushalt haben unterschiedliche Beduerfnisse. PilotSuite lernt individuelle Praeferenzen und loest Konflikte intelligent:

- **Persoenliche Lichtstaerke**: Person A bevorzugt 80%, Person B bevorzugt 40% -- PilotSuite findet den Kompromiss basierend auf Prioritaet und Anwesenheitsstatus
- **Individuelle Musikpraeferenzen**: Morgens Jazz fuer Person A, Podcast fuer Person B
- **Konfliktaufloesung**: Gewichtete Aggregation basierend auf Nutzer-Prioritaeten und Kontext

#### Energieoptimierung

Tiefere Integration mit PV-Anlagen, dynamischen Stromtarifen und Grossverbrauchern:

- **PV-Ertragsprognose**: Waschmaschine und Trockner laufen, wenn die Sonne scheint
- **Tarifsensitive Steuerung**: Grossverbraucher verschieben auf guenstige Stunden
- **Verbrauchsmuster**: "Ihre Heizung laeuft 15% effizienter, wenn Sie die Rollladen um 16:00 schliessen"
- **Autarkie-Maximierung**: Speicher-Management basierend auf Wetter- und Verbrauchsprognose

#### Gesundheitsmonitoring

Nicht-invasive Gesundheitsindikatoren aus vorhandenen Sensoren ableiten:

- **Schlafqualitaet**: Aus Bewegungsdaten, Lichtmuster und Temperaturdaten
- **Aktivitaetslevel**: Wie aktiv ist der Haushalt im Vergleich zum Durchschnitt?
- **Komfort-Trends**: Langzeit-Trends in Temperatur, Luftqualitaet, Lichtmuster
- **Anomalie-Erkennung**: Ungewoehnliche Abweichungen vom normalen Tagesablauf (z.B. fuer aeltere Haushaltsmitglieder)

#### Praediktive Automatisierung

Ueber reaktive Muster hinaus -- PilotSuite sagt voraus, was als naechstes passiert:

- **Ankunftsprognose**: "Person A kommt in ca. 15 Minuten nach Hause -- Heizung und Licht werden vorbereitet"
- **Routine-Erkennung**: "Montags bis freitags stehen Sie um 6:30 auf -- Kaffee und Licht werden vorbereitet"
- **Kontext-Awareness**: "Es wird dunkel und kalt -- Rollladen schliessen und Heizung erhoehen?"

#### Foederiertes Lernen (Collective Intelligence)

Anonymisiertes Lernen ueber Haushalte hinweg -- ohne Daten zu teilen:

- **Pattern Sharing**: Anonymisierte Regeln (nicht Daten) werden geteilt
- **Modell-Aggregation**: Verbesserte Vorhersagemodelle durch kollektives Wissen
- **Privacy Preservation**: Differential Privacy, kein Rueckschluss auf einzelne Haushalte
- **Opt-in**: Vollstaendig freiwillig und jederzeit abschaltbar

#### Integration mit weiteren Oekosystemen

- **Apple HomeKit**: Pro-Zone HomeKit Bridge (bereits implementiert, QR-Code im Dashboard)
- **Matter**: Natives Matter-Protokoll fuer geraetuebergreifende Interoperabilitaet
- **Telegram**: Bot mit Server-seitigem Tool-Calling (bereits implementiert)
- **Frigate**: Kamera-basierte Praesenz und Aktivitaetserkennung (bereits angebunden)
- **UniFi**: Netzwerk-basierte Praesenz und Geraete-Monitoring (bereits integriert)

---

## Zusammenfassung der Vision

```
+-------------------------------------------------------------------+
|                                                                     |
|  PilotSuite Styx -- Die Vision                                     |
|                                                                     |
|  1. LOKAL      Alle Daten, alle Modelle, alles auf Ihrem Geraet   |
|  2. LERNEND    Wird mit jedem Tag besser, nicht schlechter         |
|  3. ERKLAERBAR Jede Entscheidung ist nachvollziehbar               |
|  4. RESPEKTVOLL Schlaegt vor, erzwingt nie                         |
|  5. OFFEN      REST, OpenAI, MCP -- jeder Client kann anbinden    |
|  6. PRIVAT     Keine Cloud, kein Account, keine Telemetrie         |
|  7. LEBENSLANG Selbstschaerfend, je laenger im Einsatz desto      |
|                besser                                               |
|                                                                     |
|  Das Haus lernt seinen Bewohner kennen.                             |
|  Der Bewohner lebt einfach.                                         |
|                                                                     |
+-------------------------------------------------------------------+
```

PilotSuite strebt danach, die Bruecke zwischen "dummen" Smart Homes (die nur ausfuehren, was man ihnen sagt) und wirklich intelligenten Wohnraeumen zu schlagen -- Raeumen, die verstehen, was ihre Bewohner brauchen, und respektvoll darauf reagieren.

Nicht heute. Nicht morgen. Aber mit jedem Tag ein Stueck besser.

---

*PilotSuite Styx v14.6.5 -- Lokal. Lernend. Lebenslang.*
*GitHub: [GreenhillEfka/pilotsuite-styx-ha](https://github.com/GreenhillEfka/pilotsuite-styx-ha) | [GreenhillEfka/pilotsuite-styx-core](https://github.com/GreenhillEfka/pilotsuite-styx-core)*
