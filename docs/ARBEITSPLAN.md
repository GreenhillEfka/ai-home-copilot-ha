# PilotSuite Styx -- Arbeitsplan

**Version:** v14.6.5
**Datum:** 2026-03-16
**Sprache:** Deutsch

---

## 1. Sprint-Uebersicht

| Sprint | Version | Zeitraum | Schwerpunkt |
|--------|---------|----------|-------------|
| S1 (abgeschlossen) | v14.6.0 - v14.6.3 | Bis 2026-03-14 | Core Deploy, Suggestion Fix, Discovery Retry |
| S2 (abgeschlossen) | v14.6.4 | 2026-03-15 | Zone Automation Auth Fix |
| S3 (abgeschlossen) | v14.6.5 | 2026-03-16 | Config Entry, Zone Dedup, Dashboard Dedup |
| S4 (geplant) | v14.7.x | Naechster Sprint | Backend Dashboard Redesign |
| S5 (geplant) | v14.8.x | Danach | Neue Core Module, Pipeline-Test |

---

## 2. Abgeschlossene Arbeiten (v14.6.x Serie)

### S1: Grundlagen und Stabilisierung (v14.6.0 - v14.6.3)

| Aufgabe | Version | Beschreibung |
|---------|---------|-------------|
| suggestion_panel ImportError | v14.6.1 | Import-Fehler im Suggestion Panel behoben |
| Core v14.6.3 Deploy | v14.6.3 | Core-Backend erfolgreich deployed und verifiziert |
| Config Entry Discovery Retry | v14.6.3 | Verzoegerter Retry bei fehlender Core-Verbindung |

### S2: Zone Automation (v14.6.4)

| Aufgabe | Version | Beschreibung |
|---------|---------|-------------|
| Zone Automation Auth Fix | v14.6.4 | Auth-Token wird korrekt an Core-API uebergeben. `hass.config_entries.async_get_entry()` statt fehlendem dict-key |

### S3: Stabilitaet und Bereinigung (v14.6.5)

| Aufgabe | Version | Beschreibung |
|---------|---------|-------------|
| Config Entry Persistence | v14.6.5 | Config Entry ueberlebt HA-Neustarts zuverlaessig |
| Zone Device Assignment | v14.6.5 | Entities korrekt den konfigurierten Zonen zugeordnet |
| Dashboard View Switch Dedup | v14.6.5 | Doppelte Views beim Dashboard-Neuaufbau verhindert |
| Zone State Sync | v14.6.5 | Zonen-Status korrekt zwischen HA und Core synchronisiert |
| Zone Dedup | v14.6.5 | Duplikat-Zonen in Konfiguration und Entities bereinigt |

---

## 3. Geplante Arbeiten

### S4: Backend Dashboard Redesign (v14.7.x)

Neugestaltung des Styx-Dashboards mit 8 Tabs im Storage-Mode.

| Nr | Aufgabe | Prioritaet | Aufwand | Abhaengigkeit |
|----|---------|-----------|---------|---------------|
| 4.1 | Dashboard-Architektur planen (8 Tabs) | Hoch | M | -- |
| 4.2 | Tab 1: Styx (KI/Brain) ueberarbeiten | Hoch | L | 4.1 |
| 4.3 | Tab 2: Haushalt ueberarbeiten | Hoch | L | 4.1 |
| 4.4 | Tab 3: Energie ueberarbeiten | Mittel | M | 4.1 |
| 4.5 | Tab 4: Praesenz ueberarbeiten | Mittel | M | 4.1 |
| 4.6 | Tab 5: Musik ueberarbeiten | Mittel | M | 4.1 |
| 4.7 | Tabs 6-8: Zonen-Tabs dynamisch generieren | Hoch | L | 4.1 |
| 4.8 | Card Generator an neues Layout anpassen | Hoch | M | 4.2-4.7 |
| 4.9 | Mood Chart Verdrahtung (Frontend -> Core API) | Mittel | M | 4.2 |
| 4.10 | Dashboard Storage-Mode Migration testen | Hoch | S | 4.8 |

Aufwand: S = klein (< 2h), M = mittel (2-4h), L = gross (4-8h)

### S5: Neue Core Module und Pipeline (v14.8.x)

| Nr | Aufgabe | Prioritaet | Aufwand | Abhaengigkeit |
|----|---------|-----------|---------|---------------|
| 5.1 | ZWave Modul (Core) | Mittel | L | -- |
| 5.2 | Zigbee Modul (Core) | Mittel | L | -- |
| 5.3 | Thread Modul (Core) | Niedrig | L | -- |
| 5.4 | HomeAssistant Modul (Core) | Mittel | L | -- |
| 5.5 | HA-Integration: Entity-Plattformen fuer neue Module | Mittel | M | 5.1-5.4 |
| 5.6 | Pipeline End-to-End Test | Hoch | L | -- |
| 5.7 | Suggestion-Pipeline verifizieren (4 Quellen) | Hoch | M | 5.6 |
| 5.8 | Duplikat-Entities bereinigen (_2 Suffixe) | Mittel | M | -- |
| 5.9 | Dokumentation aktualisieren | Niedrig | M | 5.1-5.8 |

### S6: Multi-User und Optimierung (spaeter)

| Nr | Aufgabe | Prioritaet | Aufwand | Abhaengigkeit |
|----|---------|-----------|---------|---------------|
| 6.1 | MUPL produktionsreif machen | Mittel | L | 5.6 |
| 6.2 | Personalized Automation Timing | Niedrig | L | 6.1 |
| 6.3 | Performance-Optimierung (Connection Pooling, Cache) | Mittel | L | -- |
| 6.4 | Test-Coverage erhoehen (HA: 500+, Core: 1800+) | Mittel | L | -- |
| 6.5 | Skipped Tests reduzieren | Niedrig | M | -- |

---

## 4. Abhaengigkeiten

### Abhaengigkeitsgraph

```
Config Entry Persistence (erledigt)
    |
    v
Zone Device Assignment (erledigt) ---> Zone State Sync (erledigt)
    |                                       |
    v                                       v
Zone Dedup (erledigt)              Dashboard View Switch Dedup (erledigt)
                                            |
                                            v
                                   Backend Dashboard Redesign (S4)
                                            |
                            +---------------+---------------+
                            |               |               |
                            v               v               v
                    Mood Chart        Neue Core Module   Pipeline E2E Test
                    Verdrahtung       (ZWave, Zigbee,     (S5.6)
                    (S4.9)            Thread, HA)              |
                                       (S5.1-5.4)             v
                                            |          Suggestion-Pipeline
                                            v          Verifikation (S5.7)
                                    HA Entity-Plattformen
                                    fuer neue Module (S5.5)
```

### Repo-uebergreifende Abhaengigkeiten

| HA-Repo Aufgabe | Core-Repo Abhaengigkeit |
|-----------------|------------------------|
| Dashboard Redesign (S4) | Styx Dashboard Template in Core |
| Mood Chart Verdrahtung (S4.9) | Mood API Endpoints in Core |
| Neue Modul-Entities (S5.5) | Neue Module in Core (S5.1-5.4) |
| Pipeline E2E Test (S5.6) | Alle Core API Endpoints funktional |
| MUPL produktionsreif (S6.1) | MUPL-Service in Core |

### Paired Release Abhaengigkeiten

Jede Aenderung an der REST-API oder am Webhook-Protokoll erfordert ein Paired Release beider Repos. Versionsnummern muessen synchron sein.

---

## 5. Risiken und Massnahmen

| Risiko | Wahrscheinlichkeit | Auswirkung | Massnahme |
|--------|-------------------|------------|-----------|
| Config Entry leer nach erstem Boot | Mittel | Mittel | Delayed Retry implementiert (v14.6.3), Monitoring |
| Duplikat-Entities (_2 Suffixe) | Hoch | Niedrig | Manuelle Bereinigung im Entity Registry |
| Core nicht erreichbar | Mittel | Hoch | Discovery Retry, Circuit Breaker, Polling Fallback |
| Dashboard-Konflikte bei Update | Niedrig | Mittel | Storage-Mode statt YAML, Dedup-Logik |
| Python 3.14 Breaking Changes | Niedrig | Hoch | Regex-Fixes, asyncio.run() statt get_event_loop() |

---

## 6. Test-Strategie

### Aktueller Stand

| Metrik | HA-Repo | Core-Repo |
|--------|---------|-----------|
| Tests gesamt | 387+ | 1793+ |
| Bestanden | 387 | 1793 |
| Fehlgeschlagen | 0 | 0 |
| Uebersprungen | 41 | 112 |
| Bekannt instabil | -- | 1 (test_list_suggestions) |

### Testausfuehrung

```bash
# HA-Repo
.venv/bin/python -m pytest tests/ \
  --ignore=tests/test_anomaly_detector.py \
  --ignore=tests/test_card_generator.py \
  -v --tb=short -q

# Core-Repo
PYTHONPATH=copilot_core/rootfs/usr/src/app \
  .venv/bin/python -m pytest copilot_core/rootfs/usr/src/app/tests \
  -v --tb=short -x
```

### Ziel-Coverage

- HA: Von 387 auf 500+ Tests (neue Module, Dashboard, Pipeline)
- Core: Von 1793 auf 1800+ Tests (neue Module, Stabilisierung)
- Uebersprungene Tests: Schrittweise aktivieren und fixen

---

*Zuletzt aktualisiert: 2026-03-16*
