# Release v13.7.0 — Zone Dashboard, Smart Home Module, Musikwolke HA Services

**Datum:** 2026-03-12
**Branch:** main
**Tag:** `v13.7.0`
**HA hassfest:** compliant
**Paired Release:** Core v13.7.0 <-> HA v13.7.0

---

## Ueberblick

PilotSuite HA v13.7.0 ist ein Major-Feature-Release mit drei Schwerpunkten:

1. **Zone Dashboard** — Angereichert mit Controls, Playlists, Notifications, Birthdays, Todos
2. **5 neue PilotSuite HA Module** — Licht, Helligkeit, Heiz, Bewegung, Praesenz
3. **Musikwolke HA Services** — 8 neue Services fuer direkte Steuerung aus HA Automations

---

## Neue Features

### 5 PilotSuite Smart Home Module
- Licht, Helligkeit, Heiz, Bewegung, Praesenz als eigenstaendige HA-Module
- Beispiel-Dashboard mit realen Entities
- Integration in Zone Dashboard

### Zone Dashboard Erweiterungen
- Habituszonen-IDs synchron mit Core
- Reichere Datenstruktur mit Controls, Musik, Playlists
- Notifications, Birthdays, Todos pro Zone

### 8 Musikwolke HA-Services

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

### Coordinator-Erweiterungen
- 14 neue API-Methoden im `CopilotApiClient`
- Musikwolke, Media Follow und Zone Automation vollstaendig angebunden

### Interaktives Musik-Dashboard
- Play/Pause/Dissolve Buttons mit direkter Steuerung
- Follow Start/Stop per Knopfdruck
- Tabellarische Modi-Uebersicht

---

## Bug Fixes

- Fehlender `asyncio`-Import und Auth-Header-Alignment in API Client
- Warning Logs fuer fehlenden Coordinator in Musikwolke Service Handlers
- Ungebundene Variable `e` in coordinator.py Musikwolke-Methoden

---

## Dokumentation

| Dokument | Beschreibung |
|----------|-------------|
| `docs/HANDBUCH.md` | Deutsches Benutzerhandbuch |
| `docs/INSTALLATIONSANLEITUNG.md` | Installationsanleitung |
| `docs/MODULE_REFERENCE.md` | Vollstaendige Modul-Referenz |

---

## Upgrade-Hinweise

- **Breaking Changes:** Keine
- **Neue Dependencies:** Keine
- **Migration:** Standard HA-Update (HACS → Update)

---

## Statistiken

- **49 Dateien geaendert** (+5.565 / -613 Zeilen)
- **Neue Tests:** test_card_generator_modules.py, test_pilotsuite_modules.py

---

**PilotSuite v13.7.0** — Local-first, Privacy-first, Governance-first.
