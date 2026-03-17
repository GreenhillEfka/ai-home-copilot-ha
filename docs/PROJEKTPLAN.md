# PilotSuite Styx -- Projektplan

**Version:** v14.6.5
**Datum:** 2026-03-16
**Sprache:** Deutsch

---

## 1. Projektuebersicht

PilotSuite Styx ist eine lokale KI-Plattform fuer Smart Homes auf Basis von Home Assistant. Das Projekt folgt einer Dual-Repo-Architektur:

| Repository | Rolle | Metapher | Technologie |
|-----------|-------|----------|-------------|
| **pilotsuite-styx-ha** | HACS Integration | Sinne + Haende | Python, JS/TS, Lovelace Cards |
| **pilotsuite-styx-core** | Supervisor Add-on | Gehirn + Stimme | Python, Flask, Ollama LLM, SQLite |

### Kernprinzipien

| Prinzip | Bedeutung |
|---------|-----------|
| Local-first | Alle Daten und KI-Modelle laufen lokal -- keine Cloud |
| Privacy-first | Keine PII-Speicherung, opt-in fuer alle Features |
| Governance-first | Vorschlaege statt automatischer Aktionen (Human-in-the-Loop) |
| Thin Client | HA-Integration ist duenn, alle Logik lebt im Core |

### Kommunikation

```
Home Assistant <--> copilot_ha (HA Integration) <--> PilotSuite Core (Port 8909)
                         |                                  |
                    Sensoren/Buttons                  Flask REST-API
                    Dashboard (Storage-Mode)           Brain Graph
                    9 Lovelace Cards                   LLM / Neurons
                    Config Flow (7 Steps)              Zone Automation
                    Event Forwarding                   Musikwolke
```

Kommunikationswege: REST API (HA->Core), Webhook Push (Core->HA), Polling (120s Fallback).

---

## 2. Meilensteine -- Bisherige Entwicklung

### Phase 1 -- Fundament (v0.1 - v0.8)

- Flask-Backend als zentrale API-Schicht mit Waitress
- Brain Graph zur Modellierung von Zusammenhaengen
- Habitus-System fuer Gewohnheiten und Tagesrhythmen
- Event Pipeline fuer HA-Ereignisverarbeitung in Echtzeit

### Phase 2 -- Stabilisierung (v1.0 - v2.0)

- Circuit Breakers fuer HA-Supervisor- und Ollama-Verbindungen
- SQLite WAL-Modus mit busy_timeout
- Config Validation mit vol.Range und sicheren Typ-Konvertierungen
- Request Timing mit X-Request-ID-Korrelation

### Phase 3 -- Feature-Ausbau (v3.0 - v3.7)

- Neurons (lernfaehige Muster-Erkennung)
- Mood Engine (Stimmungserkennung)
- MUPL (Multi-User Preference Learning)
- Media Zones, Energy Module, Waste/Birthday
- Ergebnis: 32 Module, 94+ Sensoren, 130+ API-Endpunkte

### Phase 4 -- Bugfixes und Produktionsrelease (v3.8 - v3.9)

- Sichere Datenzugriffe, Resource Leak Fixes
- hassfest-Kompatibilitaet
- Valides HACS-Release

### Phase 5 -- Cross-Home Sharing (v12.0.0)

- Notifications API (21 Endpoints)
- Sharing API (16 Endpoints)
- Collective Intelligence / Federated Learning (15 Endpoints)
- Privacy-Garantien: Differential Privacy, Anonymisierung, opt-in

### Phase 6 -- Advanced ML und Type Hints (v12.0.0)

- Durchgaengige Type Hints in allen Phase-5/6-Modulen
- 2526 Tests, 98% Pass-Rate

### Phase 7-14 -- Iterative Verbesserungen (v12.x - v14.6.5)

- CopilotRuntime + ModuleRegistry Plugin-System
- Config Flow als 7-Step Wizard
- Storage-Mode Dashboard (sofort sichtbar ohne HA-Restart)
- 9 Lovelace Custom Cards
- 9 Habitus-Zonen mit 141 gemappten Entities
- Zone Automation, Musikwolke, Praesenz-Tracking
- ZeroConfig Discovery fuer Core-Verbindung

---

## 3. Aktuelle Phase: End-to-End Pipeline Wiring (v14.6.x)

Die aktuelle Entwicklungsphase konzentriert sich auf die Verdrahtung aller Module zu einer funktionierenden End-to-End-Pipeline:

| Schwerpunkt | Status | Beschreibung |
|------------|--------|-------------|
| Zone Automation Fix | Erledigt (v14.6.4) | Auth-Token korrekt an Core-API weitergeben |
| Config Entry Persistence | Erledigt (v14.6.5) | Config Entry ueberlebt HA-Neustarts zuverlaessig |
| Zone Device Assignment | Erledigt (v14.6.5) | Entities korrekt den Zonen zugeordnet |
| Dashboard View Switch Dedup | Erledigt (v14.6.5) | Keine doppelten Views beim Dashboard-Neuaufbau |
| Zone State Sync | Erledigt (v14.6.5) | Zonen-Status zwischen HA und Core synchronisiert |
| Zone Dedup | Erledigt (v14.6.5) | Duplikat-Zonen bereinigt |

---

## 4. Naechste Schritte

### 4.1 Backend Dashboard Redesign (Phase 2)

Neugestaltung des Styx-Dashboards im Core-Backend mit 8 Tabs:

| Tab | Inhalt |
|-----|--------|
| 1. Styx (KI/Brain) | Brain Graph, Stimmung, KI-Vorschlaege |
| 2. Haushalt | Praesenz, Habitus-Zonen, Modi |
| 3. Energie | Verbrauch, Erzeugung, Sankey, Anomalien |
| 4. Praesenz | Zonen-Praesenz, Automatisierungs-Modi |
| 5. Musik | Musikwolke, Sonos, Follow-Modus |
| 6-8. Zonen | Dynamische Tabs pro Habitus-Zone |

### 4.2 Neue Core Module

| Modul | Zweck |
|-------|-------|
| ZWave | Z-Wave Geraete-Integration und Statuserfassung |
| Zigbee | Zigbee Netzwerk-Monitoring und Geraeteverwaltung |
| Thread | Thread/Matter Protokoll-Unterstuetzung |
| HomeAssistant | Tiefere HA-System-Integration (Supervisor, Add-ons) |

### 4.3 Pipeline-Verifikation

- End-to-End Test der gesamten Daten-Pipeline (Event -> Core -> Neuron -> Suggestion -> Dashboard)
- Verifizierung aller 4 Suggestion-Quellen (2 lokal, 2 Core-abhaengig)
- Mood Chart Backend-Verdrahtung

### 4.4 Multi-User Learning

- MUPL-System produktionsreif machen
- Individuelle Praeferenzen pro Haushaltsmitglied (aktuell 7 Personen konfiguriert)
- Personalized Automation Timing

---

## 5. Qualitaetsziele

| Metrik | Ist-Stand | Ziel |
|--------|-----------|------|
| Tests HA | 387 passed | 500+ |
| Tests Core | 1793 passed | 1800+ |
| Skipped HA | 41 | < 30 |
| Skipped Core | 112 | < 80 |
| Known Flaky | 1 (test_list_suggestions) | 0 |
| Config Entry Stability | Verbessert (v14.6.5) | 100% zuverlaessig |
| Duplikat-Entities | Vorhanden (_2 Suffixe) | 0 |

---

## 6. Release-Prozess

### Paired Releases

Beide Repos werden immer parallel released. Versionen muessen synchron sein.

### Versionsdateien

| Repository | Dateien |
|-----------|---------|
| HA | `VERSION`, `custom_components/copilot_ha/VERSION`, `custom_components/copilot_ha/manifest.json` |
| Core | `VERSION`, `copilot_core/VERSION`, `copilot_core/rootfs/usr/src/app/VERSION`, `copilot_core/config.yaml`, `copilot_core/manifest.json` |

### Deployment-Pipeline

1. Code pushen auf `claude/*` Branch
2. PR erstellen und mergen in `main`
3. GitHub Release erstellen (Tag = Version)
4. Auf HA-Instanz: `update_entity` aufrufen
5. Warten bis Update erkannt
6. `update/install` ausfuehren
7. `config_entries/reload` zum Aktivieren

### Branching

- `main` -- geschuetzt, nur ueber PR-Merge
- `claude/*` -- Entwicklungsbranches, direkt pushbar

---

## 7. Technische Rahmenbedingungen

| Parameter | Wert |
|-----------|------|
| Python | 3.14.3 |
| HA Mindestversion | 2024.1.0 |
| Domain | copilot_ha |
| Core Port | 8909 |
| LLM | Ollama (Port 11435 intern im Core-Container) |
| Entities | 4520 (HA-Instanz gesamt) |
| Areas | 47 |
| Personen | 7 |
| Habitus-Zonen | 9 |
| Entity-Rollen | 12 |
| Gemappte Entities | 141 |
| Lovelace Cards | 9 Custom Cards |

---

*Zuletzt aktualisiert: 2026-03-16*
