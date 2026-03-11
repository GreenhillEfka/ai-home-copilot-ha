# Release Notes v13.7.0 -- Musikwolke HA Services & Documentation Overhaul

**Datum:** 2026-03-11
**Branch:** main
**Tag:** `v13.7.0`
**HA hassfest:** compliant
**Paired Release:** Core v13.7.0 <-> HA v13.7.0

---

## Ueberblick

PilotSuite v13.7.0 schliesst die **Musikwolke End-to-End Integration** zwischen Core und HA ab und liefert eine vollstaendige Dokumentationsueberarbeitung.

### Highlights

- **8 neue Musikwolke HA-Services** fuer direkte Steuerung aus HA Automations und Dashboard
- **Interaktives Musik-Dashboard** mit Button-Controls statt statischem Markdown
- **14 neue Coordinator-API-Methoden** fuer Musikwolke, Media Follow und Zone Automation
- **Vollstaendige Dokumentation**: Handbuch, Installationsanleitung, Modul-Referenz

---

## Neue HA-Services

| Service | Beschreibung |
|---------|-------------|
| `copilot_ha.musikwolke_create` | Musikwolke-Gruppe erstellen (synchronisierte Wiedergabe) |
| `copilot_ha.musikwolke_dissolve` | Musikwolke-Gruppe aufloesen |
| `copilot_ha.musikwolke_play` | Wiedergabe in einer Zone starten |
| `copilot_ha.musikwolke_pause` | Wiedergabe in einer Zone pausieren |
| `copilot_ha.musikwolke_volume` | Lautstaerke fuer eine Zone setzen (0-100%) |
| `copilot_ha.musikwolke_start_follow` | Follow-Session starten (Musik folgt Person) |
| `copilot_ha.musikwolke_stop_follow` | Follow-Session beenden |
| `copilot_ha.zone_automation_set_mode` | Automatisierungsmodus setzen (off/learning/autonomy) |

### Beispiel: HA Automation

```yaml
automation:
  - alias: "Musikwolke bei Ankunft"
    trigger:
      - platform: state
        entity_id: person.alice
        to: "home"
    action:
      - service: copilot_ha.musikwolke_start_follow
        data:
          person_id: person.alice
          source_zone: wohnzimmer
```

---

## Coordinator-Erweiterungen

14 neue API-Methoden im `CopilotApiClient`:

- `async_get_musikwolke_status()` -- Status aller aktiven Musikwolke-Gruppen
- `async_musikwolke_play/pause/volume` -- Zone-Steuerung
- `async_create_musikwolke/dissolve_musikwolke` -- Gruppen-Management
- `async_start/stop_media_follow` -- Follow-Session-Management
- `async_get_media_follow_sessions()` -- Session-Ueberblick
- `async_set/get_zone_automation_mode` -- Automatisierungsmodus
- `async_get_musikwolke_zone_map()` -- Zone-Speaker-Mapping

---

## Dashboard-Verbesserungen

### Musik-Tab (Tab 5)

- **Play/Pause/Dissolve Buttons**: Direkte Steuerung per Tap
- **Follow Start/Stop Buttons**: Media-Follow per Knopfdruck
- **Zonen-Automatisierung**: Tabellarische Modi-Uebersicht
- **Info-Card**: Erklaerung der Musikwolke-Funktionalitaet

---

## Dokumentation

| Dokument | Beschreibung |
|----------|-------------|
| `docs/HANDBUCH.md` | Deutsches Benutzerhandbuch |
| `docs/INSTALLATIONSANLEITUNG.md` | Schritt-fuer-Schritt Installationsanleitung |
| `docs/MODULE_REFERENCE.md` | Vollstaendige Modul-Referenz |

---

## Upgrade-Hinweise

- **Breaking Changes:** Keine
- **Neue Dependencies:** Keine
- **Migration:** Nicht erforderlich -- Standard HA-Update

---

**PilotSuite v13.7.0** -- Local-first, Privacy-first, Governance-first.
