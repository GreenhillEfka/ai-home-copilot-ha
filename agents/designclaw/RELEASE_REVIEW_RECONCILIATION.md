# UX RELEASE REVIEW — Reconciliation Release
**Reviewer:** Stxy (Design/UX Lane)
**Date:** 2026-03-21
**Commit:** draft — pending team review

---

## 1. Executive Summary

**Reconciliation-Bedarf:** HOCH
**Schätzung:** 2-3 Tage Cleanup-Arbeit (geschätzter Aufwand)

Die HA-Integration enthält einen eigenständigen Flask-Dashboard-Server (`dashboard/app.py`, Port 8766), der nicht dokumentiert ist und Zone-Management-Logik dupliziert. Ebenfalls: veraltete Backup-Dateien und ein dupliziertes Lovelace Card Bundle.

---

## 2. Architektur-Status

### Korrekter Datenfluss (laut Doku)
```
HA (Entities/Sensoren/Events)
  → coordinator.py → Core API (Port 8909)
                        ↓
           Core Brain/Intelligence/Automation
                        ↓
           Zurück an HA: Zone-Zustand, Suggestions
                        ↓
           Lovelace Cards in www/ (Visualisierung)
```

### Was korrekt ist ✅
| Artefakt | Status |
|-----------|--------|
| `custom_components/copilot_ha/coordinator.py` | ✅ Korrekt — HA↔Core Brücke |
| `custom_components/copilot_ha/www/*.js` | ✅ Lovelace Cards — Visualisierung |
| `custom_components/copilot_ha/sensors/` | ✅ HA Sensoren |

### Was Vermischung ist ❌
| Artefakt | Problem |
|----------|---------|
| `dashboard/app.py` (Port 8766) | Eigenständiger Flask-Server, nicht dokumentiert |
| `dashboard/widgets/` | Flask-basierte Zone-Widgets, dupliziert Core-Logik |
| `dashboard/templates/` | Jinja2-Templates für Flask, nicht Lovelace |
| `dashboard/api/` | Flask Blueprints, unnötig |

---

## 3. Befund: `dashboard/` Ordner im HA-Repo

### Nicht dokumentiert in CLAUDE.md

Die CLAUDE.md des HA-Repos listet nur:
- `dashboard/pilotsuite_dashboard_v*.yaml` — YAML Dashboard
- `dashboard/card_generator.py` — YAML Card Generierung

Was **zusätzlich** existiert aber **nicht dokumentiert** ist:
- `app.py`, `config.py`, `build.mjs`, `package.json`
- `node_modules/`
- `static/` (JS/CSS/TS)
- `widgets/` (Python Flask Widgets)
- `templates/` (Jinja2 Templates)
- `api/` (Flask Blueprints)

### Zone-Management-Logik in Flask-Widgets

`widgets/zone_summary.py` enthält:
- `_handlePresenceHold()` — Presence Hold State Management
- `_updateHoldPills()` — UI-Rendering
- SocketIO für Live-Updates

**Das ist Management-Logik,不应该 in HA.** Es gehört nach Core oder als Lovelace Card in `www/`.

---

## 4. Befund: Backup-Dateien

| Datei | Größe | Aktion |
|-------|-------|--------|
| `www/styx-zone-card.js.bak` | 1082 Zeilen | **LÖSCHEN** |
| `styx-zone-card.js` (aktuell) | ??? | Prüfen ob Änderungen seit letztem Commit |

---

## 5. Befund: Kompiliertes Bundle

| Datei | Status |
|-------|--------|
| `www/pilotstack-zone-cards.mjs` | Prüfen — ist das Build-Output? |

---

## 6. Offene Fragen (Team-Abstimmung nötig)

1. **Wer übernimmt `dashboard/` Cleanup?** HomeClaw/PilotClaw?
2. **Zone-Management in Core:** Ist die komplette Logik (Presence Hold, Zone Summary) sauber in Core und nur als Lovelace Cards in HA visualisiert?
3. **`pilotsuite_core/` (v13.10.0):** Wird es noch referenziert oder ist es ein verwaistes Archiv?

---

## 7. Release-Empfehlung

### Für nächsten Release (v14.9.x)

**Verschieben/Entfernen:**
- [ ] `dashboard/app.py` → Aus HA-Repo entfernen (oder nach Core verschieben wenn gewollt)
- [ ] `dashboard/widgets/` → Aus HA-Repo entfernen
- [ ] `dashboard/templates/` → Aus HA-Repo entfernen
- [ ] `dashboard/api/` → Aus HA-Repo entfernen
- [ ] `dashboard/node_modules/` → Aus HA-Repo entfernen
- [ ] `dashboard/package*.json` → Aus HA-Repo entfernen wenn nicht mehr verwendet
- [ ] `www/styx-zone-card.js.bak` → Löschen

**Behalten (wenn dokumentiert und gewollt):**
- [ ] `dashboard/pilotsuite_dashboard_v*.yaml` → Prüfen ob verwendet
- [ ] `dashboard/card_generator.py` → Prüfen ob verwendet

**Klären:**
- [ ] `pilotsuite_core/` v13.10.0 → Archivieren oder entfernen
- [ ] `www/pilotstack-zone-cards.mjs` → Zweck klären

---

## 8.序列ierte Assets

Nach dem Cleanup müssen folgende Assets sauber funktionieren:
1. Lovelace Cards in `www/` → müssen alle Zone/Presence-Hold/Suggestion-Features abdecken
2. HA Sensoren → müssen Core-Zustand korrekt spiegeln
3. `coordinator.py` → muss die einzige Bridge sein

---

## 9. Abhängigkeiten

- PilotClaw: `dashboard/` Cleanup koordinieren
- HomeClaw: Zone-Management-Logik in Core prüfen (ist alles in Lovelace Cards visualisiert?)
- Stxy: Lovelace Cards aufräumen (`www/`), Backup löschen

---

*Stxy — Design/UX Lane — 2026-03-21 14:35*
