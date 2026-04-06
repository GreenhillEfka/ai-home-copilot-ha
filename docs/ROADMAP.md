# PilotSuite Roadmap

> Zuletzt aktualisiert: März 2026

PilotSuite ist ein Ein-Entwickler-Projekt mit ambitionierten Zielen. Diese Roadmap beschreibt den bisherigen Weg, die aktuelle Entwicklung und die geplante Zukunft. Alle Zeitangaben sind Richtwerte -- Prioritaeten koennen sich je nach Community-Feedback und technischer Machbarkeit verschieben.

---

## Bisherige Releases

### Phase 1 -- Fundament (v0.1 - v0.8)

Die ersten Versionen legten das Fundament fuer das gesamte System:

- **Flask-Backend** als zentrale API-Schicht mit Waitress als Production-Server
- **Brain Graph** zur Modellierung von Zusammenhaengen zwischen Sensoren, Raeumen und Automatisierungen
- **Habitus-System** fuer die Erfassung von Gewohnheiten und Tagesrhythmen
- **Event Pipeline** fuer die Verarbeitung von Home-Assistant-Ereignissen in Echtzeit

Diese Phase definierte die Kernarchitektur: lokal, modular, privacy-first.

### Phase 2 -- Stabilisierung (v1.0 - v2.0)

Der Fokus verschob sich von Features auf Zuverlaessigkeit:

- **Circuit Breakers** fuer HA-Supervisor- und Ollama-Verbindungen (automatische Fehlerisolierung)
- **SQLite WAL-Modus** mit `busy_timeout` fuer zuverlaessigen konkurrierenden Zugriff
- **Config Validation** mit `vol.Range`-Grenzen und sicheren Typ-Konvertierungen (`_safe_int`, `_safe_float`)
- **Request Timing** mit X-Request-ID-Korrelation und Slow-Request-Logging (>2s)

Das System wurde produktionsreif.

### Phase 3 -- Feature-Ausbau (v3.0 - v3.7)

Die grosse Erweiterungsphase brachte die intelligenten Module:

- **Neurons** -- lernfaehige Muster-Erkennung fuer Automatisierungen
- **Mood Engine** -- Stimmungserkennung basierend auf Sensorik, Wetter und Tageszeit
- **MUPL (Multi-User Preference Learning)** -- individuelle Praeferenzen pro Haushaltsmitglied
- **Media Zones** -- raumuebergreifende Mediensteuerung mit Kontext
- **Energy Module** -- Energieverbrauchsanalyse und Optimierungsvorschlaege
- **Waste/Birthday** -- Muellkalender-Integration und Geburtstagserinnerungen

Insgesamt wuchs das System auf 32 Module, 94+ Sensoren und 130+ API-Endpunkte.

### Phase 4a -- Bugfixes (v3.8)

Qualitaetssicherung und Stabilitaet:

- **Sichere Datenzugriffe** -- defensive Programmierung gegen fehlende oder unerwartete Werte
- **Resource Leak Fixes** -- Behebung von Speicher- und Verbindungslecks
- **Prune Logic Fix** -- korrigierte Bereinigung veralteter Daten

### Phase 4b -- Produktionsrelease (v3.9.0)

Der Schritt zur offiziellen Veroeffentlichung:

- **hassfest-Kompatibilitaet** -- Einhaltung aller Home-Assistant-Validierungsregeln
- **Dokumentations-Ueberarbeitung** -- vollstaendige Neufassung der Projektdokumentation
- **Valides HACS-Release** -- korrekte Release-Tags fuer die Home Assistant Community Store Integration

---

## Phase 5 -- Cross-Home Sharing ✅ COMPLETE

> Status: ✅ Abgeschlossen (v12.0.0) -- 31 Endpoints implementiert

### Vision

Haushalte sollen voneinander lernen koennen, ohne private Daten preiszugeben. Wenn hundert Haushalte aehnliche Energiemuster haben, sollte jeder einzelne davon profitieren.

### Implementierte Funktionen

**Notifications API** ✅ (21 Endpoints)
- Vollstaendiges Benachrichtigungssystem mit Send, List, Read, Dismiss, Clear
- Device-Subscriptions mit Push-Token-Support
- Home-Assistant-Integration (Device-Registry, HA Notify Services, Test-Endpoint)
- Statistiken, Digest und Pending-Notifications
- Deduplication und Rate Limiting integriert

**Sharing API** ✅ (16 Endpoints)
- Entity Registry fuer Cross-Home Sharing
- Sync-Service mit WebSocket-Unterstuetzung und Peer-Management
- Discovery-Service fuer mDNS/lokale Peers
- Share/Stop-Share Workflows pro Entity und Home
- Status-Endpoint fuer Registry, Sync und Discovery

**Collective Intelligence / Federated Learning** ✅ (15 Endpoints)
- Kompletter Federated-Learning-Lifecycle (Register, Update, Round, Aggregate)
- Knowledge-Extraktion und -Transfer mit Confidence-Scoring
- State-Persistenz (Save/Load)
- Statistiken, Modell- und Round-History
- Community-getriebene Verbesserungen fuer Automatisierungsvorschlaege

**Privacy-Garantien** ✅
- Strikt opt-in -- nichts wird ohne explizite Zustimmung geteilt
- Vollstaendige Anonymisierung: keine Geraete-IDs, keine Standorte, keine Rohdaten
- Differential Privacy mit konfigurierbarem Epsilon-Budget
- Privacy-Aware Aggregator integriert

**Architektur** ✅
- `sharing/`-Modul im Core Add-on implementiert
- `collective_intelligence/`-Modul mit allen Komponenten
- Peer Discovery ueber mDNS oder optionalen Rendezvous-Server
- Ende-zu-Ende-verschluesselter Transport zwischen Peers
- Lokaler Aggregator fasst eingehende Muster zusammen

### Testabdeckung

- **Notifications API**: 35+ Tests (Endpoints, Dedup, Rate Limiting, Digest, HA Integration)
- **Sharing API**: 25+ Integrationstests (Registry, Sync, Discovery)
- **Collective Intelligence**: 40+ Tests (Service, Federated Rounds, Knowledge Transfer)
- Alle Tests erfolgreich bestanden ✅

---

## Phase 6 -- Advanced ML & Type Hints ✅ COMPLETE

> Status: ✅ Abgeschlossen (v12.0.0) -- 2526 Tests, 98% Pass-Rate

### Type Hints Vervollstaendigung ✅
- **Notifications API** (`api/v1/notifications.py`) -- Vollstaendige Typisierung aller Methoden, Dataclasses und Endpunkte mit `from __future__ import annotations`
- **Sharing API** (`sharing/api.py`) -- Durchgaengige Type Hints fuer alle Endpoints, Helper-Funktionen und Datenstrukturen
- **Collective Intelligence API** (`collective_intelligence/api.py`) -- Durchgaengige Type Hints fuer Federated Learning Endpunkte mit `Tuple[Response, int] | Response` Return Types
- **Konsistenz** -- Einheitlicher Stil ueber alle Phase-5/6-Module hinweg

### Test-Ergebnisse ✅
- **2526 Tests** total
- **2476 passed** (98.0% Pass-Rate)
- **20 failed**, **30 skipped**
- Flask v3.1.3 und NumPy v2.4.2 im Test-Environment
- Alle Integrationstests aktiviert

### Geplante ML-Features (verschoben nach Phase 7)

Die folgenden Advanced-ML-Features wurden in Phase 7 verschoben, da Phase 6 auf Type Hints und Testabdeckung fokussiert war:

- **On-Device Inference** -- TFLite / ONNX Runtime fuer leichtgewichtige ML-Modelle
- **Anomaly Detection** -- Isolation Forest fuer ungewoehnliche Sensormuster
- **Zeitreihen-Prognosen** -- LSTM / Transformer-basierte Vorhersagen
- **Energy Load Shifting** -- PV-Ertragsprognosen und dynamische Stromtarife
- **Personalized Automation Timing** -- Verhaltensbasierte Zeitpunkt-Optimierung

---

## Phase 7 -- Production Readiness & Advanced ML Features (naechste Phase)

> Status: 🔜 Geplant

### Production Readiness

- **Performance-Optimierung** -- Connection Pooling, Cache Tuning, VectorStore-Optimierung
- **Startup-Zeit** -- Lazy Loading selten genutzter Module
- **Monitoring** -- Prometheus-Metriken, Health-Check-Erweiterung
- **Dokumentation** -- OpenAPI-Spec fuer alle Endpoints, vollstaendige API-Referenz
- **Remaining Test Fixes** -- 20 fehlgeschlagene Tests analysieren und beheben

### Advanced ML

- **On-Device Inference** -- TFLite / ONNX Runtime auf Raspberry Pi 4 / Intel NUC (Ziel: <100ms)
- **Anomaly Detection** -- Isolation Forest fuer ploetzliche Energieanstiege, unerwartete Aktivitaeten
- **Zeitreihen-Prognosen** -- LSTM/Transformer fuer Temperatur, Energie, Anwesenheit
- **Energy Load Shifting** -- Waschmaschine, Wallbox, Geschirrspueler automatisch optimieren
- **Personalized Automation Timing** -- "Licht 2 Min vor Ankunft" statt fixer Zeitpunkt

### Herausforderungen

- Ressourcenbeschraenkung: nicht jeder Host hat GPU oder viel RAM
- Modellgroesse vs. Genauigkeit: kompakte Modelle muessen genuegen
- Trainingszeit: inkrementelles Lernen statt vollstaendigem Neutraining

---

## Naechste Prioritaeten (kurz- bis mittelfristig)

Diese Punkte stehen auf der naechsten Arbeitsliste, unabhaengig von den grossen Phasen:

### Dashboard: Styx

- Einheitliches Dashboard, das Brain Graph, Chat und Historie zusammenfuehrt
- Visualisierung der Neuron-Aktivitaet und Mood-Verlauf
- Echtzeit-Updates ueber WebSocket
- Responsives Design fuer Tablet-Wandmontage und Mobile

### Voice Integration

- Tiefere Anbindung an den Home-Assistant Voice Assistant
- Kontextbewusste Antworten (Stimmung, Tageszeit, Raum)
- Proaktive Sprachhinweise bei wichtigen Erkenntnissen
- Unterstuetzung fuer Mehrsprachigkeit (DE/EN als Minimum)

### Kalender: Smart Scheduling

- Intelligente Terminplanung mit Stimmungsbewusstsein
- "Du hast morgen einen vollen Tag -- soll ich den Wecker 15 Minuten frueher stellen?"
- Automatische Anpassung von Beleuchtungsszenen an den Tagesablauf
- Integration mit bestehenden Kalender-Modulen und Mood Engine

### Multi-Home

- Sichere Synchronisation zwischen mehreren Wohnorten (Hauptwohnung, Ferienhaus, Buero)
- Einheitliche Steuerung ueber eine Oberflaeche
- Standortabhaengige Automatisierungen ("Ferienhaus vorheizen, wenn Anreise in 2 Stunden")
- Verschluesselte Kommunikation zwischen den Instanzen

### Performance-Optimierung

- **Connection Pooling** fuer HA-Supervisor- und Ollama-Verbindungen
- **Cache Tuning** fuer haeufig abgefragte Sensordaten und RAG-Ergebnisse
- **VectorStore-Optimierung** -- effizientere Aehnlichkeitssuche bei wachsender Datenbasis
- **Startup-Zeit** reduzieren durch lazy Loading von selten genutzten Modulen

---

## Designprinzipien fuer die Zukunft

Diese Prinzipien gelten fuer alle zukuenftigen Entwicklungen und werden nicht verhandelt:

### Local-First bleibt

PilotSuite laeuft vollstaendig lokal. Keine Cloud-Abhaengigkeit, kein externer Server fuer Kernfunktionen. Das LLM (standardmaessig `qwen3:0.6b`, optional `qwen3:4b` via Ollama) laeuft auf dem gleichen Geraet. Optionale Netzwerkfunktionen (Cross-Home Sharing, Web Search) sind immer opt-in und nie fuer den Basisbetrieb erforderlich.

### Privacy bleibt

Alle Datenverarbeitung findet auf dem Geraet statt. Keine Telemetrie, kein Tracking, keine Daten an Dritte. Wenn kuenftige Features Daten uebertragen (z.B. Federated Learning), dann nur anonymisiert, verschluesselt und mit ausdruecklicher Zustimmung. Der Nutzer behalt immer die volle Kontrolle ueber seine Daten.

### Governance bleibt

PilotSuite schlaegt vor, handelt aber nicht eigenmaechtg. Das 3-Tier-Autonomie-System (active / learning / off) gibt dem Nutzer die Wahl, wie viel Automatisierung erwuenscht ist. Auch im "active"-Modus werden sicherheitsrelevante Aktionen (Tuerschloesser, Alarmanlagen) nie ohne Bestaetigung ausgefuehrt.

### Backward Compatibility

Upgrades sollen reibungslos verlaufen. Datenbank-Migrationen werden automatisch ausgefuehrt. Konfigurationsaenderungen sind abwaertskompatibel. Veraltete APIs erhalten eine Deprecation-Phase, bevor sie entfernt werden. Ziel: `docker pull` und fertig, keine manuellen Schritte noetig.

---

## Mitmachen

PilotSuite ist ein Ein-Entwickler-Projekt, aber Feedback und Ideen aus der Community sind willkommen. Feature Requests und Bug Reports ueber GitHub Issues sind der beste Weg, die Richtung mitzugestalten.

> "Ein Smart Home soll sich anfuehlen wie ein aufmerksamer Mitbewohner -- nicht wie ein IT-Projekt."
