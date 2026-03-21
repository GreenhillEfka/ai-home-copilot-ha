# UX LANE REVIEW — Reconciliation v14.9.1 Convergence Proposal
**Lane:** Design/UX (Stxy)
**Date:** 2026-03-21
**Based on:** Lovelace Card Audit, Zone-Sorting Duplikat-Befund, ARCHITECTURE.md

---

## UX LANE STATUS: SAUBER ✅

Alle 10 Lovelace Cards in `www/` sind aktiv referenziert. Keine UX-Artefakte müssen entfernt werden.

---

## 1) BLEIBT SAUBER IM RELEASE (v14.9.1)

### Lovelace Cards (`www/`) — alle aktiv ✅
| Card | Refs | Kanonicität |
|------|------|-------------|
| styx-zone-card.js | 5 | ✅ |
| styx-brain-card.js | 5 | ✅ |
| styx-mood-card.js | 5 | ✅ |
| styx-habitus-card.js | 3 | ✅ |
| styx-suggestions-card.js | 5 | ✅ |
| styx-chat-card.js | 5 | ✅ |
| styx-household-card.js | 5 | ✅ |
| styx-neural-card.js | 2 | ✅ |
| styx-error-card.js | 5 | ✅ |
| styx-card-base.js | — | ✅ Base |
| pilotstack-zone-cards.mjs | — | ✅ Build output |

### UX-Spec Artefakte (GitHub, master)
- `UX_SPEC_001_HOLD_SYNC_FEEDBACK.md` — UX-SPEC-001, implementiert in commit `2a50914b` ✅
- `UX_REVIEW_14_8_1.md` — Gate: PASS, 3 Fixes in `391a5efa` ✅

### Zones-Visualisierung
- `zone_card_yaml.md` — Dokumentation ✅

---

## 2) STALE/DUPLIZIERT/OHNE ANBINDUNG

### Zone-Sorting Duplikate (HA Repo) — NICHT produktiv genutzt
| File | Zeilen | Produktions-Refs | Empfehlung |
|------|--------|-----------------|------------|
| `entity_zone_sorter.py` | 184 | **0** (nur Test) | **Bereinigen** — stale |
| `habitus_entity_sorting.py` | 337 | **0** (keine) | **Bereinigen** — orphan |

**Wichtig:** `zone_matcher.py` (Core) ist die korrekte Implementation. Die HA-Files sind duplicates ohne Produktionsnutzung.

### Backup-Datei (bereits gelöscht ✅)
- `www/styx-zone-card.js.bak` — gelöscht commit `1f94fd45` ✅

### TS Build-Source vs JS Output
| File | Status | Anmerkung |
|------|--------|-----------|
| `dashboard/static/cards/*.ts` | ⚠️ | Build-Source → kompiliert zu `pilotstack-zone-cards.mjs` |
| `dashboard/build.mjs` | ⚠️ | Build-Tool, NUR für TS→JS nötig |
| `pilotstack-zone-cards.mjs` in `www/` | ✅ | Korrekt — kompiliertes Bundle |

**Frage:** Wird `build.mjs` + `dashboard/static/cards/` noch aktiv gebaut? Falls nein → TS-Source kann wegfallen wenn das Bundle in `www/` aktuell ist.

---

## 3) RELEASE-AUSSCHLÜSSE (NICHT in v14.9.1)

| Artefakt | Grund |
|----------|-------|
| `dashboard/app.py` (Flask Port 8766) | Nicht dokumentiert, Vermischung |
| `dashboard/widgets/` | Flask-basierte Widgets |
| `dashboard/templates/` | Jinja2-Templates |
| `dashboard/api/` | Flask Blueprints |
| `entity_zone_sorter.py` | Stale, keine Produktions-Refs |
| `habitus_entity_sorting.py` | Orphan, keine Produktions-Refs |
| Neue Features (Zone-Editor Cards) | Erst nach Baseline sauber |

---

## 4) UX LANE: NUR DIESER RELEASE

**Mein Beitrag zu v14.9.1:**
- [x] Lovelace Card Audit → alle 10 aktiv ✅
- [ ] `entity_zone_sorter.py` + `habitus_entity_sorting.py` → PilotClaw-Handoff (stale/orphan)
- [ ] TS Build-System → verifizieren ob aktiv oder Archiv

**Was ich NICHT tue:**
- Keine neuen Features
- Keine UX-Specs ohne klaren Core-Bedarf
- Keine Änderungen an aktiven Lovelace Cards ohne Blocker-Grund

---

## 5) CONVERGENCE VORSCHLAG (UX Lane)

```
UX RELEASE SCOPE v14.9.1:
  ✅ Alle 10 Lovelace Cards in www/ — behalten
  ✅ pilotstack-zone-cards.mjs — behalten
  ✅ zone_card_yaml.md — behalten
  ✅ UX Specs (bereits implementiert) — behalten
  ❌ entity_zone_sorter.py — bereinigen (stale)
  ❌ habitus_entity_sorting.py — bereinigen (orphan)
  ⚠️ dashboard/static/cards/*.ts + build.mjs — klären (falls ungenutzt: bereinigen)
```

**UX braucht keine eigenen Commits in diesem Release.** Nur die Stale-Orphan-Bereinigung durch PilotClaw (die zone-sorting Duplikate sind PilotClaws Task beim squash-merge).

---

*Stxy — UX Lane — 2026-03-21 17:50*
