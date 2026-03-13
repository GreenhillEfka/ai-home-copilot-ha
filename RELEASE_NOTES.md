# Release v13.9.0 — Offizielles Release mit allen Beitraegen

**Datum:** 2026-03-13
**Branch:** main
**Tag:** `v13.9.0`
**HA hassfest:** compliant
**Paired Release:** Core v13.9.0 <-> HA v13.9.0

---

## Ueberblick

PilotSuite HA v13.9.0 ist das konsolidierte offizielle Release, das **alle Entwicklungen seit v13.5.8** zusammenfasst. Die HA-Integration wurde umfassend erweitert mit neuen Services, Modulen, Dashboard-Features und verbesserter Core-Kommunikation.

---

## Highlights

### 1. 8 Musikwolke HA-Services
Direkte Steuerung aller Musikwolke-Funktionen aus HA Automations:
| Service | Beschreibung |
|---------|-------------|
| `copilot_ha.musikwolke_create` | Musikwolke-Gruppe erstellen |
| `copilot_ha.musikwolke_dissolve` | Musikwolke-Gruppe aufloesen |
| `copilot_ha.musikwolke_play` | Wiedergabe starten |
| `copilot_ha.musikwolke_pause` | Wiedergabe pausieren |
| `copilot_ha.musikwolke_volume` | Lautstaerke setzen (0-100%) |
| `copilot_ha.musikwolke_start_follow` | Follow-Session starten |
| `copilot_ha.musikwolke_stop_follow` | Follow-Session beenden |
| `copilot_ha.zone_automation_set_mode` | Automatisierungsmodus setzen |

### 2. 5 PilotSuite HA Module
- Licht, Helligkeit, Heiz, Bewegung, Praesenz als eigenstaendige HA-Module
- Beispiel-Dashboard mit realen Entities
- Integration in Zone Dashboard

### 3. Living BrainGraph Dashboard
- Pulsierender BrainGraph mit Echtzeit-Visualisierung
- Neurale Cross-Dependencies sichtbar
- Automation Repair direkt aus dem Dashboard

### 4. Core<->HA Kommunikations-Pipeline
- Vollstaendige bidirektionale Kommunikation verdrahtet
- Webhook Receiver fuer zone_update Events (Echtzeit)
- Memory API Client, Services und Coordinator Wiring
- 14 neue Coordinator-API-Methoden

### 5. Zone Dashboard Erweiterungen
- Habituszonen-IDs synchron mit Core
- Reichere Datenstruktur mit Controls, Musik, Playlists
- Notifications, Birthdays, Todos pro Zone
- Bidirektionale Tag-Synchronisierung mit Core

### 6. Code-Qualitaet & Hardening
- Button Base Class fuer alle Button-Entities
- Lovelace Card Base fuer wiederverwendbare Custom Cards
- Coordinator API Cleanup mit `_safe_get`/`_safe_post` Wrappers
- Zentralisierte Coordinator Timeouts
- 6 tote Button-Dateien mit doppelten unique_ids entfernt
- 13 vergessene Sensoren verdrahtet
- Translations korrigiert

---

## Bug Fixes

- Fehlender `asyncio`-Import und Auth-Header-Alignment in API Client
- Warning Logs fuer fehlenden Coordinator in Musikwolke Service Handlers
- Ungebundene Variable `e` in coordinator.py
- Edge Cases, Type Safety und Automation Hardening
- CrossDependencySensor Registration und Edge Count
- Decision-Sync Retry Queue fuer Offline-Core-Resilienz
- Module Lifecycle, SQLite Safety, Nonce Cache Cleanup

---

## Upgrade-Hinweise

- **Breaking Changes:** Keine
- **Neue Dependencies:** Keine
- **Migration:** Standard HA-Update (HACS -> Update)
- **Mindestversion Core:** v13.9.0
- **Mindestversion HA:** 2024.1.0

---

## Statistiken

| Metrik | Wert |
|--------|------|
| Commits seit v13.5.8 | 28+ |
| Neue/Geaenderte Dateien | 50+ |
| HA-Services (neu) | 8 |
| Coordinator-Methoden (neu) | 14 |
| HA-Module (neu) | 5 |
| Sensoren (gesamt) | 94+ |
| Dashboard Cards | 15+ |

---

**PilotSuite v13.9.0** — Local-first, Privacy-first, Governance-first.
