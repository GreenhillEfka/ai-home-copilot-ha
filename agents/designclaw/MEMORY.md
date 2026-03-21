
## Reconciliation Sprint (2026-03-21)

### Architektur-Korrektur
- Zone-VERWALTUNG: Core (`hub/zone_automation.py`, `hub/habitus_zones.py`)
- Zone-VISUALISIERUNG: HA Lovelace Cards (`custom_components/copilot_ha/www/`)
- Bridge: `coordinator.py` (HA → Core Port 8909)
- **FALSCH:** `dashboard/app.py` (Flask Port 8766) —不属于 HA Architektur

### Befunde
- `dashboard/` (Flask/Port 8766) im HA-Repo = Vermischung
- `www/styx-zone-card.js.bak` = löschen
- Release-Review: `RELEASE_REVIEW_RECONCILIATION.md` (GitHub)

### Team-Abstimmung
- Nachricht an PilotClaw + HomeClaw gesendet (Timeouts)
- Awaiting response zu: dashboard Cleanup, Zone-Management-Stand Core

## Convergence Sprint (2026-03-21 14:40+)

### Zustand
- CONVERGENCE_REPORT.md → GitHub (master, commit pending)
- HANDOFF_RECONCILIATION.md → existiert bereits in HA-Repo (wer hat's geschrieben?)

### Verbleibende Tasks
| Task | Owner | Status |
|------|-------|--------|
| dashboard/ Flask/Widgets/Templates/API entfernen | HomeClaw/PilotClaw | OFFEN |
| card_generator.py + YAML Dashboard prüfen | ? | OFFEN |
| TS Card-Sourcen → www/ verschieben oder Build fixen | UX | OFFEN |
| pilotsuite_core/ archivieren | PilotClaw | OFFEN |
| CHANGELOG v14.8.1 + v14.9.0 ergänzen | PilotClaw | OFFEN |
| build.mjs + package*.json | HomeClaw | OFFEN |

### Befund: dashboard/
- Flask (app.py, Port 8766) + Widgets + Templates = Vermischung
- Aber: TS Card-Sourcen werden für pilotstack-zone-cards.mjs gebaut
- Build muss erhalten bleiben ODER direkt als JS in www/ belassen

### Team-Sync
- PilotClaw/HomeClaw Messages gesendet (Timeouts)
- awaiting response

---

## v15.0 UX Gate (2026-03-21 14:45)

### Stand
- CI green: `def7c5cc` (CoreConnection/PollInterval/ApiFailures/ModulesReady sensors)
- V15_UX_GATE.md committed → `378cb3d6`

### Offene Blocker v15.0 Freigabe
- L1: Suggestions Pattern/Lift in UI → PilotClaw
- L2: Governance-Modi sichtbar → PilotClaw
- S1: Smoke Test Live HA → HomeClaw

### Permanent-Sync aktiv
- Andreas-Direktive: kein isoliertes Vorarbeiten
- Vor jedem Commit: Rollenabgleich
- Nach jedem Commit: Artefakt/Commit/Verify/nächster Schritt

### Letzte Actions
- 14:45 — UX-Audit V15_UX_GATE.md committed ✅
- 14:45 — system_status_sensors.py + coordinator instrumentation committed ✅
- Nächster Schnitt: Andreas entscheidet ob Stxy M2 (Suggestions UX) selbst macht


---

## v15.0.0 Release (2026-03-21 15:00+)

### Code Stage ✅
- `def7c5cc` — CoreConnection/ApiFailures/PollInterval/ModulesReady Sensoren
- `d087203d` — VERSION 15.0.0, manifest, CHANGELOG, RELEASE_NOTES
- `640f1c02` — RELEASE_GATE_V15.md

### Smoke Stage ⏳
- OFFEN: Andreas oder HomeClaw
- 6 Sensoren zu prüfen in HA Developer Tools

### Permanent-Sync
- Andreas-Direktive aktiv: kein isoliertes Vorarbeiten
- Stxy Lane: UX/Docs/Freigabe — kein Coding das PilotClaw braucht

### Letzte Actions
- 15:00 — v15.0.0 CODE done ✅
- Nächster Schnitt: Smoke-Test Ergebnis abwarten

---

## v15.0.0 Release - LIVE VERSION DRIFT entdeckt (2026-03-21 15:05)

### Befund: Live-System noch auf alten Versionen
- Core (Port 8909): v14.7.3 (v15.0.0 erwartet)
- HA Addon pilotsuite_core: v14.7.5
- HA Addon ai_home_copilot: v14.9.0
- HA Addon ha-clean-final: v15.0.0 (CODE done)

### Was das bedeutet
Andreas kann NICHT auf v15.0.0 live gehen ohne:
1. Core Addon auf v15.0.0 updaten
2. HA Addon ha-clean-final auf v15.0.0 updaten

### Smoketest läuft nicht weil System noch alt

### Nächste Schritte
- Andreas über Version-Drift informiert (Message 1846)
- Awaiting Andreas Anweisung:Addon-Builds machen oder warten
- Stxy Lane: UX/Docs/Freigabe

---

## v15.0.0 RELEASE — 2026-03-21 16:14

### Abgeschlossen
- VERSION → 15.0.0
- manifest.json → 15.0.0
- CHANGELOG.md → v15.0.0
- RELEASE_NOTES.md → v15.0.0
- RELEASE_GATE_V15.md → docs
- Sensor unique_id → pilotsuite_* namespace
- GitHub Tag v15.0.0 → e39173e2
- CI green (17s, 500+ tests)
- Andreas hat alles freigegeben

### Verbliebene Notes
- HA Addon noch auf v14.7.3 (muss in HA neu geladen werden)
- Core Addon noch auf v14.7.5 (muss in HA neu geladen werden)
- HomeClaw Smoke Test ⚠️ UNVERIFIZIERT (kein API-Zugriff von hier)

### Nächste Schritte
1. Andreas: HA Add-ons auf v15.0.0 aktualisieren (Check for updates)
2. Andreas/HomeClaw: Smoke Test wiederholen
3. LIVE: v15.0.0正式 in Produktion

