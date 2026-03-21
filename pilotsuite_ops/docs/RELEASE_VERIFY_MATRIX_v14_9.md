# RELEASE VERIFY MATRIX — pilotsuite-styx-ha v14.9.x (UPDATED)

> **Context:** Reconciliation/Aufräum-Release. Keine Features. Saubere Bestandsaufnahme.
> **Erstellt:** 2026-03-21 14:30 GMT+1
> **Updated:** 2026-03-21 14:45 GMT+1
> **Branch:** `origin/main` @ `2a50914b`
> **Repo:** `pilotsuite-styx-ha`

---

## CRITICAL NEW FINDING (14:45)

### Dashboard/ Flask-Server — Architektur-Verletzung

**Befund:** `dashboard/` (Flask + SocketIO, Port 8766) im HA-Repo ist ein **parallel laufender Flask-Server** neben dem Core Flask-Server (Port 8909). Das ist eine klare Architektur-Verletzung der Andreas-Regel.

| Property | Core (Port 8909) | HA dashboard/ (Port 8766) |
|----------|------------------|----------------------------|
| Stack | Flask + SocketIO + Ollama | Flask + SocketIO |
| Entities/Sensoren | HA-Integration | Direkte HA-API-Aufrufe |
| Brain/Mood/Zone | Komplett | Dupliziert via `zone_data_store` |
| Auth | `apiKeyAuth` / `bearerAuth` | Unknown |
| **Status** | **OFFIZIELL** | **PARALLEL/UNFRIEDRIG** |

**8 duplicate Widget-Dateien** (exakte Kopien):
- `brain_graph.py`, `chat_widget.py`, `optimization.py`, `sensor_overview.py`, `system_status.py`, `zone_summary.py`
- **nur** in `dashboard/widgets/` im HA-Repo, identisch zu Core `dashboard/widgets/`

**Entscheidung nötig:**
- Entweder `dashboard/` in HA als offizielle Visualisierungs-Schicht BEHALTEN (dann Core `dashboard/` als Legacy markieren)
- Oder HA `dashboard/` ENTFERNEN und komplett auf Core (Port 8909) + Lovelace Cards (www/) umstellen

---

## PFAD 1: Syntax & Import — ✅ RELEASEFÄHIG

| Check | Ergebnis | Pfad |
|-------|---------|------|
| Alle 145+ Python-Dateien kompilierbar | ✅ PASS | `custom_components/copilot_ha/**/*.py` |
| JS/TS Lovelace Cards syntaktisch valid | ✅ PASS | `www/styx-*.js` |
| `pilotstack-zone-cards.mjs` syntaktisch valid | ✅ PASS | `www/pilotstack-zone-cards.mjs` |
| 37 Unit Tests (habitus_module + entity_sorting) | ✅ PASS | `tests/test_habitus_module_schema.py`, `tests/test_habitus_entity_sorting.py` |
| contracts_bridge.py | ✅ PASS | `core/contracts_bridge.py` |

---

## PFAD 2: Area→Zone Mapping — ✅ RELEASEFÄHIG (VORBEHALT)

| Check | Ergebnis | Pfad |
|-------|---------|------|
| `area_zone_map.json` existiert und valid | ✅ PASS | `config/area_zone_map.json` |
| 10 Mappings, 3 Aggregation Rules | ✅ PASS | `config/area_zone_map.json` |
| `load_area_zone_map()` | ✅ PASS | `area_zone_registry.py` |
| `sort_entity_to_zone()` Zone-IDs konsistent | ✅ PASS | `habitus_zones_entities_v2.py` |

**Zone-ID-Mismatch (bekannt, notiert):**
- HA `zone_ids`: `wohnbereich`, `badbereich`, `kochbereich`, `gangbereich`, `schlafbereich`, `kellerbereich`, `zimmer_mira`, `zimmer_paul`
- Core `ZoneType`: `LIVING`, `BATH`, `KITCHEN`, `OFFICE`, `HALLWAY`, `BEDROOM`, `ROOM_MIRA`, `ROOM_PAUL`, `TERRACE`, `OUTSIDE`
- Kein Overlap. HA-Keyword-Logik funktioniert HA-intern konsistent.

---

## PFAD 3: Core↔HA API-Verdrahtung — ⚠️ BROKEN

| Check | Ergebnis | Pfad |
|-------|---------|------|
| `habitus_zones_matcher.py` in Core | ❌ **FEHLT** | muss in Core existieren |
| HA importiert `habitus_zones_matcher` | ✅ existiert nicht | `habitus_zones_api.py:17` |
| Runtime: Fallback aktiv → Match-Commands nicht spezifikationsgemäß | ⚠️ UNBEKANNT | nur syntaktisch |

**Critical Blocker:** `habitus_zones_matcher.py` existiert nicht in Core. HA importiert es, schlägt zur Laufzeit fehl → `HAS_ZONE_MATCHER = False`.

---

## PFAD 4: Lovelace Cards / Frontend — ✅ SYNTAX OK, COMMIT-PENDING

| Check | Ergebnis | Pfad |
|-------|---------|------|
| 9 JS Cards syntaktisch valid | ✅ PASS | `www/styx-*.js` |
| `pilotstack-zone-cards.mjs` | ⚠️ 411+ UNCOMMITTED | `www/pilotstack-zone-cards.mjs` |
| `.bak` | ❌ 36KB Backup-Artefakt | `www/styx-zone-card.js.bak` |

---

## PFAD 5: Dashboard/ Flask-Server — ❌ ARCHITEKTUR-VERLETZUNG

| Check | Ergebnis | Pfad |
|-------|---------|------|
| Flask-Server auf Port 8766 | ❌ PARALLEL ZU CORE | `dashboard/app.py` |
| 8 duplicate Widget-Dateien | ❌ DUPLIZIERT Core | `dashboard/widgets/*.py` |
| Zone-Visualisierung in Core `dashboard/` | ⚠️ Legacy? | `core/dashboard/widgets/` |
| Lovelace Cards (www/) | ✅ OFFIZIELL | `www/styx-*.js` |

---

## PFAD 6: Configuration / Config Flow — ✅ SYNTAX OK

| Check | Ergebnis | Pfad |
|-------|---------|------|
| Config Flow 7-Step Wizard | ✅ Syntax OK | `config_flow.py`, `config_wizard_steps.py` |
| Config Schema Builder | ✅ Syntax OK | `config_schema_builders.py` |

---

## ZUSAMMENFASSUNG: FREIGABE-STATUS

```
✅ SYNTAX OK + UNIT TESTS PASS          → release-fähig
✅ AREA→ZONE MAPPING                     → release-fähig (Notierung)
🔴 dashboard/ FLASK PARALLEL-SERVER    → MUSS ENTSCHIEDEN WERDEN
🔴 habitus_zones_matcher.py FEHLT      → MUSS GEFIXT WERDEN
⚠️ PILOTSTACK-ZONE-CARDS.MJS           → UNCOMMITTED (Blocker)
❌ styx-zone-card.js.bak                → MUSS GELÖSCHT WERDEN
```

---

## MUST-FIX vor v14.9.1

1. **`dashboard/` Flask-Server** — Architektur-Entscheidung treffen: behalten (dann Core als Legacy) oder entfernen (komplett auf Core + Lovelace)
2. **`habitus_zones_matcher.py`** — in Core erstellen oder HA-Import auf `zone_matcher.py` umstellen
3. **`pilotstack-zone-cards.mjs`** — committen oder verwerfen (Owner: Stxy)
4. **`styx-zone-card.js.bak`** — löschen

---

## OFFENE ENTSCHEIDUNGEN (AN ANDREAS)

1. **Dashboard/ Flask-Server (Port 8766):** Offizielle HA-Visualisierung oder Legacy/Delete?
2. **`habitus_zones_matcher.py`:** In Core erstellen ODER HA-Import auf existierende `zone_matcher.py` umstellen?
3. **Core Version:** Manifest zeigt `14.8.1`, sollte `14.9.0` sein?

---

## CLEANUP-TASK-VERTEILUNG (VORSCHLAG)

| Agent | Cleanup Task |
|-------|-------------|
| PilotClaw | `habitus_zones_matcher.py` fix in Core |
| PilotClaw | `dashboard/` Architektur-Entscheidung + Umsetzung |
| Stxy | `pilotstack-zone-cards.mjs` commit/verwerfen |
| HomeClaw | `.bak` löschen + Verify-Matrix pflegen |

---

*Erstellt durch: HomeClaw Lane (Runtime/Integration)*
*GitHub-First: Alle Befunde an `origin/main@2a50914b` gebunden*
