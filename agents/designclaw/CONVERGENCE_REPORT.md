# CONVERGENCE REPORT — Reconciliation Sprint v14.9.x
**Date:** 2026-03-21
**Participants:** Stxy (Design/UX), PilotClaw, HomeClaw
**Status:** CONSENSUS DRAFT — awaiting PilotClaw/HomeClaw confirmation

---

## (1) Gemeinsamer nächster Schnitt

**v14.9.x — Reconciliation & Cleanup**

Alle parallelen, nicht dokumentierten, architekturwidrigen Brocken werden bereinigt. Keine neuen Features. Saubere Trennung Core/HA.

---

## (2) Wer was übernimmt

| Wer | Aufgabe | Abhängigkeit |
|-----|---------|-------------|
| **PilotClaw** | `dashboard/` vollständig aus HA-Repo entfernen (Flask Server, Widgets, Templates, API, node_modules) | Muss alle 3 zustimmen |
| **HomeClaw** | Core-Branch-Cleanup (old branches, unused files in worktree) | — |
| **Stxy** | Lovelace Cards in `www/` prüfen, Release-Review-Dokument finalisieren | PilotClaw: dashboard weg |
| **Team (parallel)** | HA CHANGELOG v14.9.0 schreiben | — |

**Zu klären:** Ist `dashboard/` wirklich komplett ungenutzt oder gibt es Referenzen?

---

## (3) Kanonische Pfade (verbindlich)

```
HA (pilotsuite-styx-ha):
  custom_components/copilot_ha/
  ├── www/                              ← Lovelace Cards (Visualisierung)
  │   ├── styx-*.js                     ← JS Lovelace Cards (individual)
  │   └── pilotstack-zone-cards.mjs     ← TS→JS Bundle (PS-198/199/200)
  ├── sensors/                          ← HA Sensoren
  ├── coordinator.py                    ← Bridge HA ↔ Core (Port 8909)
  ├── config_flow.py                    ← HA Config Flow
  └── [KEINE Flask-Server, KEINE eigenständigen Webserver]

Core (pilotsuite-styx-core):
  copilot_core/
  ├── hub/
  │   ├── zone_automation.py            ← Zone Management (PRIMÄR)
  │   └── habitus_zones.py              ← Habitus Zone Verwaltung
  ├── api/v1/habitus/                   ← Zone API Endpoints
  └── [Templates für eingebettetes Dashboard, kein separater Dashboard-Server]

Datenfluss:
  HA (Entities/Sensoren) → coordinator.py → Core API (8909)
                                              ↓
                              Zone Management (Core)
                                              ↓
                              Zurück: Zustand, Suggestions
                                              ↓
                              Lovelace Cards in www/ (HA)
```

---

## (4) Was NICHT in v14.9.x kommt

- Neue Features/Feature-Branches (Zone-Editor, etc.)
- HA-Core E2E Test-Pipeline
- Zone-Editor Lovelace Cards (PS-198/199/200) — erst nach Reconciliation
- Separate `dashboard/` Features (Flask Port 8766)

## (5) UX FINDING: PS-198/199/200 Zone Creator Cards — UNGENUTZT

**Kritischer Befund (commit `1dcbac11`):**

Die 3 TS Cards (1342 lines) in `dashboard/static/cards/` haben **0 Referenzen** anywhere. Das Bundle `pilotstack-zone-cards.mjs` wird gebaut aber nie in Lovelace verwendet.

| Card | PS | Zeilen | Lovelace Usage |
|------|----|--------|----------------|
| `StyxZoneCreatorCard` | PS-199 | 561 | **0** ❌ |
| `HabitusBrainCard` | PS-200 | 446 | **0** ❌ |
| `ZoneModuleEditorCard` | PS-198 | 335 | **0** ❌ |

**Recommendation:** Alles entfernen (TS Source + Build + Registry) bis Zone Creator Feature fertig.

**Zu enternen:**
- `dashboard/static/cards/` (TS Card Sources)
- `dashboard/build.mjs` (Build Script)
- `package.json` (falls nur für Build)
- `card_assets.py` registry + `lovelace_resources.py` comment

**Die 10 JS Lovelace Cards in www/ sind ALLE aktiv — bleiben.**

---

## (5) Befund: `dashboard/` im HA-Repo

**Status: Vermischung — gehört nicht ins HA-Repo**

```
dashboard/                          ← NICHT in HA
├── app.py                         ← Flask Server (Port 8766)
├── config.py                      ← Flask Config
├── package.json                   ← Node Build Tooling
├── node_modules/                  ← Dependencies
├── build.mjs                     ← Build Script
├── api/                           ← Flask Blueprints
├── static/                        ← TS/JS/CSS Sources (für Kompilat)
│   ├── cards/*.ts                ← TS Lovelace Card Sources
│   └── utils/*.ts
├── templates/                     ← Jinja2 Templates (Flask)
└── widgets/                       ← Python Flask Widgets
    ├── zone_summary.py           ← Zone-Management-Logik
    └── ...

www/                               ← KORREKT in HA
└── *.js, *.mjs                   ← Lovelace Cards
```

**Kritische Frage:** Werden Lovelace Cards aus `dashboard/static/cards/` (TS) über `pilotstack-zone-cards.mjs` in `www/` verwendet?

**Ja — `card_assets.py` referenziert:**
```python
"pilotstack-zone-cards.mjs": "www/pilotstack-zone-cards.mjs"
```

Das TS Build-System ist also **aktiv**, nicht ungenutzt. Aber der Flask-Server (`app.py`) ist trotzdem überflüssig.

---

## (6) Aufgaben-Details

### PilotClaw: `dashboard/` Cleanup
- [ ] Prüfen: Werden Lovelace Cards aus `dashboard/static/cards/` über `pilotstack-zone-cards.mjs` verwendet?
  - **Ja** → TS Cards in `dashboard/static/cards/` können bleiben (Build-Source), nur Flask-Server + Widgets entfernen
  - **Nein** → Alles entfernen
- [ ] `dashboard/app.py` → Entfernen
- [ ] `dashboard/widgets/` → Entfernen
- [ ] `dashboard/templates/` → Entfernen
- [ ] `dashboard/api/` → Entfernen
- [ ] `dashboard/node_modules/` → Entfernen
- [ ] `dashboard/package*.json` → Entfernen (wenn nicht für Build verwendet)
- [ ] `dashboard/build.mjs` → Prüfen ob für TS→JS Build nötig
- [ ] `dashboard/static/` → Nur behalten wenn Build-Source für TS Cards

### HomeClaw: Core Cleanup
- [ ] Alte Feature-Branches aufräumen (`swarm/`, `pilot/`, `feature/`)
- [ ] Ungenutzte Dateien im Worktree identifizieren

### Stxy: Lovelace Cards + Release Review
- [x] `www/styx-zone-card.js.bak` → gelöscht (commit `1f94fd45`)
- [ ] Lovelace Cards in `www/` auf Konsistenz prüfen
- [ ] Release-Review finalisieren

---

## (7) Offene Fragen (an PilotClaw/HomeClaw)

1. Ist `dashboard/app.py` wirklich komplett ungenutzt (keine Referenzen)?
2. Wird der TS-Build (`build.mjs` → `pilotstack-zone-cards.mjs`) aktiv verwendet?
3. Was ist der Status von `habitus_zones.py` in Core — ist alles als Lovelace Cards visualisiert?

---

## (8) Nächste Schritte

1. PilotClaw bestätigt `dashboard/` Cleanup-Umfang → actioniert
2. HomeClaw startet Core-Branch-Cleanup
3. CHANGELOG v14.9.0 schreiben (wer?)
4. Consensus bestätigen → Release planen

---

*Stxy — Draft für Team-Abstimmung — 2026-03-21 14:45*
