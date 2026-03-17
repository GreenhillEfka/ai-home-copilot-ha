# PilotSuite Styx -- Taskliste

**Version:** v14.6.5
**Datum:** 2026-03-16
**Sprache:** Deutsch

---

## Legende

| Status | Bedeutung |
|--------|-----------|
| ERLEDIGT | Aufgabe abgeschlossen und verifiziert |
| OFFEN | Aufgabe geplant, noch nicht begonnen |
| IN ARBEIT | Aufgabe aktuell in Bearbeitung |
| BLOCKIERT | Aufgabe wartet auf Abhaengigkeit |

---

## 1. Erledigte Aufgaben

| Nr | Aufgabe | Version | Datum | Anmerkung |
|----|---------|---------|-------|-----------|
| T-001 | Zone Automation Auth Fix | v14.6.4 | 2026-03-15 | Auth-Token korrekt via `hass.config_entries.async_get_entry()` statt fehlendem dict-key |
| T-002 | suggestion_panel ImportError | v14.6.1 | 2026-03-14 | Import-Fehler im Suggestion Panel behoben |
| T-003 | Core v14.6.3 Deploy | v14.6.3 | 2026-03-14 | Core-Backend erfolgreich deployed und verifiziert |
| T-004 | Config Entry Discovery Retry | v14.6.3 | 2026-03-14 | Verzoegerter Retry wenn Core beim ersten Versuch nicht erreichbar |
| T-005 | Zone Device Assignment | v14.6.5 | 2026-03-16 | Entities korrekt den konfigurierten Zonen zugeordnet |
| T-006 | Dashboard View Switch Dedup | v14.6.5 | 2026-03-16 | Doppelte Dashboard-Views beim Neuaufbau verhindert |
| T-007 | Zone State Sync | v14.6.5 | 2026-03-16 | Zonen-Status zwischen HA und Core synchronisiert |
| T-008 | Zone Dedup | v14.6.5 | 2026-03-16 | Duplikat-Zonen in Konfiguration bereinigt |

---

## 2. Offene Aufgaben

### 2.1 Backend Dashboard Redesign

| Nr | Aufgabe | Prioritaet | Aufwand | Status | Abhaengigkeit |
|----|---------|-----------|---------|--------|---------------|
| T-010 | Dashboard-Architektur mit 8 Tabs planen | Hoch | M | OFFEN | -- |
| T-011 | Tab 1: Styx (KI/Brain) ueberarbeiten | Hoch | L | OFFEN | T-010 |
| T-012 | Tab 2: Haushalt ueberarbeiten | Hoch | L | OFFEN | T-010 |
| T-013 | Tab 3: Energie ueberarbeiten | Mittel | M | OFFEN | T-010 |
| T-014 | Tab 4: Praesenz ueberarbeiten | Mittel | M | OFFEN | T-010 |
| T-015 | Tab 5: Musik ueberarbeiten | Mittel | M | OFFEN | T-010 |
| T-016 | Tabs 6-8: Zonen dynamisch generieren | Hoch | L | OFFEN | T-010 |
| T-017 | Card Generator an neues Layout anpassen | Hoch | M | OFFEN | T-011 bis T-016 |
| T-018 | Dashboard Storage-Mode Migration testen | Hoch | S | OFFEN | T-017 |

Aufwand: S = klein (< 2h), M = mittel (2-4h), L = gross (4-8h)

### 2.2 Neue Core Module

| Nr | Aufgabe | Prioritaet | Aufwand | Status | Abhaengigkeit |
|----|---------|-----------|---------|--------|---------------|
| T-020 | ZWave Modul im Core implementieren | Mittel | L | OFFEN | -- |
| T-021 | Zigbee Modul im Core implementieren | Mittel | L | OFFEN | -- |
| T-022 | Thread Modul im Core implementieren | Niedrig | L | OFFEN | -- |
| T-023 | HomeAssistant Modul im Core implementieren | Mittel | L | OFFEN | -- |
| T-024 | HA-Entity-Plattformen fuer neue Module | Mittel | M | BLOCKIERT | T-020 bis T-023 |

### 2.3 Pipeline und Verdrahtung

| Nr | Aufgabe | Prioritaet | Aufwand | Status | Abhaengigkeit |
|----|---------|-----------|---------|--------|---------------|
| T-030 | Mood Chart Backend-Verdrahtung | Mittel | M | OFFEN | T-011 |
| T-031 | Pipeline End-to-End Verification | Hoch | L | OFFEN | -- |
| T-032 | Suggestion-Pipeline verifizieren (4 Quellen) | Hoch | M | OFFEN | T-031 |

### 2.4 Bereinigung und Wartung

| Nr | Aufgabe | Prioritaet | Aufwand | Status | Abhaengigkeit |
|----|---------|-----------|---------|--------|---------------|
| T-040 | Duplikat-Entities bereinigen (_2 Suffixe) | Mittel | M | OFFEN | -- |
| T-041 | Documentation Update (Handbuch, Roadmap) | Niedrig | M | OFFEN | -- |
| T-042 | Uebersprungene Tests aktivieren (HA: 41, Core: 112) | Niedrig | L | OFFEN | -- |
| T-043 | Test-Coverage erhoehen (Ziel: HA 500+, Core 1800+) | Mittel | L | OFFEN | -- |

---

## 3. Bekannte Issues

| Nr | Issue | Schweregrad | Workaround | Geplante Loesung |
|----|-------|-----------|------------|-------------------|
| I-001 | Config Entry kann beim ersten Boot leer sein | Mittel | Delayed Retry (v14.6.3) laedt Config Entry nach verzoegertem Zeitfenster nach | Monitoring ausbauen, ggf. persistenten Cache einfuehren |
| I-002 | Duplikat-Entities mit _2 Suffix | Niedrig | Manuelle Bereinigung im Entity Registry (Einstellungen -> Geraete & Dienste -> Entities) | T-040: Automatische Erkennung und Bereinigung |
| I-003 | test_list_suggestions ist instabil (Core) | Niedrig | Test ist als known flaky markiert | Timing-Abhaengigkeit im Test beheben |

---

## 4. Checkliste naechstes Release

Vor jedem Release muessen folgende Schritte durchgefuehrt werden:

- [ ] Alle Tests bestanden (HA + Core)
- [ ] Version in allen Dateien synchron gebumpt
  - [ ] HA: `VERSION`, `custom_components/copilot_ha/VERSION`, `manifest.json`
  - [ ] Core: `VERSION`, `copilot_core/VERSION`, `copilot_core/rootfs/usr/src/app/VERSION`, `config.yaml`, `manifest.json`
- [ ] PR erstellt und gemergt (beide Repos)
- [ ] GitHub Release erstellt (beide Repos, gleicher Tag)
- [ ] Deployment auf HA-Instanz verifiziert
  - [ ] `update_entity` aufgerufen
  - [ ] `update/install` ausgefuehrt
  - [ ] `config_entries/reload` ausgefuehrt
- [ ] Funktionstest auf Live-Instanz

---

## 5. Aufgaben-Statistik

| Kategorie | Anzahl |
|----------|--------|
| Erledigt | 8 |
| Offen | 18 |
| Blockiert | 1 |
| Bekannte Issues | 3 |
| **Gesamt** | **30** |

---

*Zuletzt aktualisiert: 2026-03-16*
