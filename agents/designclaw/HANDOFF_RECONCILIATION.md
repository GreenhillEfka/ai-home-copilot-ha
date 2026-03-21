# RECONCILIATION RELEASE — HA Cleanup Handoff
**For:** HomeClaw / PilotClaw
**Date:** 2026-03-21
**Status:** READY FOR HANDOFF

---

## 1. `dashboard/` — Entfernen aus HA-Repo

### Was nicht dokumentiert ist und entfernt werden muss

```
dashboard/
├── app.py                      ❌ Flask Server (Port 8766), nicht Architektur
├── config.py                   ❌ Flask Config
├── build.mjs                   ❌ Build Tooling (ESBuild)
├── package.json                ❌ 
├── package-lock.json          ❌
├── node_modules/               ❌
├── api/                        ❌ Flask Blueprints
│   ├── __init__.py
│   ├── v1/__init__.py
│   ├── v1/dashboard.py
│   └── v1/widget_positions.py
├── widgets/                    ❌ Flask Widgets
│   ├── __init__.py
│   ├── zone_summary.py         ❌ Zone-Management-Logik
│   ├── brain_graph.py
│   ├── chat_widget.py
│   ├── optimization.py
│   ├── plugin_registry.py
│   ├── sensor_overview.py
│   └── system_status.py
├── templates/                  ❌ Jinja2 Templates
│   ├── index.html
│   ├── dashboard.html
│   ├── zone_card.html
│   └── widgets/
│       ├── brain_graph.html
│       ├── chat_widget.html
│       ├── sensor_overview.html
│       ├── system_status.html
│       └── zone_summary.html
└── static/
    ├── js/
    │   ├── zone_cards.js      ❌ (→ www/ verschieben als Lovelace Card)
    │   ├── dashboard.js
    │   ├── websocket.js
    │   ├── drag_drop.js
    │   ├── accessibility.js
    │   ├── ui_state_components.js
    │   └── README_UI_STATE*.md
    ├── utils/
    │   ├── card-form-helper.ts
    │   ├── card-registration.ts
    │   ├── editor-schema-validation.ts
    │   └── zone-editor-api-client.ts
    ├── editors/
    │   └── module-config-editor.ts
    ├── css/
    │   ├── style.css
    │   ├── dashboard.css
    │   ├── ui_state_components.css
    │   └── accessibility.css
    └── cards/
        ├── index.ts           ⚠️ (Build-Input → pilotstack-zone-cards.mjs)
        ├── styx-zone-creator-card.ts
        ├── habitus-brain-card.ts
        └── zone-module-editor-card.ts
```

### Was dokumentiert ist und begründet werden muss

```
dashboard/
├── card_generator.py            ⚠️ Kompiliert Lovelace YAML Cards
├── pilotsuite_dashboard_v13.yaml ⚠️ YAML Dashboard
├── DRAG_DROP_README.md          ⚠️ Dokumentation
├── OPTIMIZATIONS.md             ⚠️ Dokumentation
├── RAG_SEARCH_CARD.md           ⚠️ Dokumentation
└── ZONE_CARDS_README.md        ⚠️ Dokumentation
```

**Frage:** Wird `card_generator.py` noch aktiv verwendet? Wenn nicht → auch entfernen.

### Zone-Cards-Logik die noch lebt

`widgets/zone_summary.py` enthält `_handlePresenceHold()` + `_updateHoldPills()` — diese Funktionalität muss als Lovelace Card in `www/` existieren bevor `widgets/` fällt.

### Build-Problem

`build.mjs` → `pilotstack-zone-cards.mjs` (kompiliert TS Cards). Wenn `dashboard/static/cards/` entfernt wird, muss das Build-System angepasst werden:
- Option A: TS-Sourcen nach `www/` verschieben + Build-Config anpassen
- Option B: `pilotstack-zone-cards.mjs` direkt in `www/` belassen und nie wieder bauen

---

## 2. `www/styx-zone-card.js.bak` — GELÖSCHT ✅

Commit `1f94fd45` — bereits erledigt.

---

## 3. `pilotsuite_core/` v13.10.0 — Archiv

**Befund:** Separate, ältere HA-Integration (legacy). Wird nur als Fallback-Entity-Name verwendet (`sensor.pilotsuite_core_api_v1` als Fallback zu `sensor.copilot_ha_core_api_v1`).

**Frage:** Soll das archiviert werden (z.B. in ein `legacy/` Verzeichnis) oder bleibt es als Fallback?

---

## 4. CHANGELOG / RELEASE NOTIZEN

In `copilot_ha/CHANGELOG.md` fehlen die letzten Releases:
- v14.8.1
- v14.9.0

→ Muss ergänzt werden.

---

## 5. Nächste Schritte (wer macht was)

| Task | Owner | Status |
|------|-------|--------|
| `dashboard/` Flask/Widgets/Templates entfernen | HomeClaw oder PilotClaw | OFFEN |
| `card_generator.py` + YAML Dashboard prüfen | Wer auch immer | OFFEN |
| TS Card-Sourcen nach `www/` verschieben oder löschen | Design/UX (Stxy) | OFFEN |
| `pilotsuite_core/` archivieren oder belassen | PilotClaw | OFFEN |
| CHANGELOG ergänzen | PilotClaw | OFFEN |
| `build.mjs` + `package*.json` entfernen | HomeClaw | OFFEN |

---

*Stxy — Design/UX Lane — 2026-03-21*
