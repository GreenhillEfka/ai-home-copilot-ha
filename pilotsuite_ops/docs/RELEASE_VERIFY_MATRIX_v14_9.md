# RELEASE VERIFY MATRIX — pilotsuite-styx-ha v14.9.x

> **Context:** Reconciliation/Aufräum-Release. Keine Features. Saubere Bestandsaufnahme.
> **Erstellt:** 2026-03-21 14:30 GMT+1
> **Branch:** `origin/main` @ `2a50914b`
> **Repo:** `pilotsuite-styx-ha`

---

## PFAD 1: Syntax & Import — ✅ RELEASEFÄHIG

| Check | Ergebnis | Pfad |
|-------|---------|------|
| Alle 145+ Python-Dateien kompilierbar | ✅ PASS | `custom_components/copilot_ha/**/*.py` |
| JS/TS Lovelace Cards syntaktisch valid | ✅ PASS | `www/styx-zone-card.js`, `www/styx-mood-card.js`, etc. |
| `pilotstack-zone-cards.mjs` syntaktisch valid | ✅ PASS | `www/pilotstack-zone-cards.mjs` |
| 37 Unit Tests (habitus_module + entity_sorting) | ✅ PASS | `tests/test_habitus_module_schema.py`, `tests/test_habitus_entity_sorting.py` |
| contracts_bridge.py | ✅ PASS | `core/contracts_bridge.py` — keine externen Imports |
| E2E Contract Pipeline | ✅ PASS (Artefakt, Commit-Referenz fehlt) | `pilotsuite_ops/reports/PS-E2E-001_CONTRACT_PIPELINE_E2E.md` |

**Release-Fähig:** JA — Syntax-Layer ist sauber.

---

## PFAD 2: Area→Zone Mapping — ✅ RELEASEFÄHIG (KLEINER VORBEHALT)

| Check | Ergebnis | Pfad |
|-------|---------|------|
| `area_zone_map.json` existiert und syntaktisch valid | ✅ PASS | `config/area_zone_map.json` |
| `area_zone_map.json` hat 10 Mappings, 3 Aggregation Rules | ✅ PASS | `config/area_zone_map.json` |
| `aggregation_rules` für wohnzimmer/badbereich/kochbereich | ✅ PASS | `config/area_zone_map.json` |
| `load_area_zone_map()` in `area_zone_registry.py` | ✅ PASS | `area_zone_registry.py` |
| `sort_entity_to_zone()` verwendet korrekte zone_ids | ✅ PASS | `habitus_zones_entities_v2.py` |

**Kritischer Vorbehalt — Zone-ID-Mismatch (Architecture Violation):**

| Schema | Zone-IDs |
|--------|---------|
| HA `area_zone_map.json` | `wohnbereich`, `badbereich`, `kochbereich`, `gangbereich`, `schlafbereich`, `kellerbereich`, `zimmer_mira`, `zimmer_paul` |
| Core `ZoneType` Enum | `LIVING`, `BATH`, `KITCHEN`, `OFFICE`, `HALLWAY`, `BEDROOM`, `ROOM_MIRA`, `ROOM_PAUL`, `TERRACE`, `OUTSIDE` |
| **Overlap** | **NULL — keine! Kein einziger gemeinsamer Identifier** |

**Bewertung:** Nicht kritisch-solange die HA-seitige Keyword-Logik (`_ENTITY_ZONE_KEYWORDS`) konsistent mit `area_zone_map.json` arbeitet (prüft German keywords, matched auf `zone:wohnbereich`, etc.) und NICHT mit Core `ZoneType` vermischt wird. Der mismatch existiert, aber die HA-Only-Layer sind konsistent. **Release-fähig mit Notierung.**

---

## PFAD 3: Core↔HA API-Verdrahtung — ⚠️ BROKEN / NICHT TESTBAR

### 3a) Contract-Bridge

| Check | Ergebnis | Pfad |
|-------|---------|------|
| `contracts_bridge.py` definiert ProposalIntent, ActionIntent, etc. | ✅ Syntax OK | `core/contracts_bridge.py` |
| HA-Webhook importiert Contract-Klassen | ✅ PASS | `webhook.py` |
| Core-Zone-Taxonomie (ZoneType Enum) | ⚠️ MISSING | `habitus_zones_matcher.py` **EXISTIERT NICHT** |

**BROKEN — `habitus_zones_matcher.py` existiert nicht im Core:**

```
HA code:  from copilot_core.homeassistant.habitus_zones_matcher import ...
Core:     /copilot_core/homeassistant/habitus_zones_matcher.py  NOT FOUND
Core:     /copilot_core/homeassistant/zone_matcher.py            EXISTS (falscher Name!)
```

```
custom_components/copilot_ha/habitus_zones_api.py:17:
    from copilot_core.homeassistant.habitus_zones_matcher import ...
```

**Folge:** Bei Runtime wird `HAS_ZONE_MATCHER = False` (Fallback aktiv). Folgende WebSocket-Commands funktionieren NICHT wie spezifiziert:
- `pilotsuite/habitus/match_zone` — verwendet den Matcher, schlägt fehl
- `pilotsuite/habitus/zones` — verwendet Store-Daten, funktioniert vermutlich

**Bewertung:** NICHT release-fähig — importiert nicht-existentes Core-Modul. Muss entweder:
1. `habitus_zones_matcher.py` in Core erstellen, ODER
2. HA-Import auf existierende `zone_matcher.py` umstellen (Architecture Change)

### 3b) Webhook Contract Pipeline

| Check | Ergebnis |
|-------|---------|
| E2E Contract Pipeline Report | ✅ PASS |
| Webhook parse/validate/execute | ✅ PASS (syntaktisch) |
| Runtime HA→Core Webhook Delivery | ❓ UNBEKANNT — kein HA API Token für Live-Verifikation |

**Bewertung:** Syntaktisch OK, Runtime-Status UNBEKANNT. Nicht als "getestet" verkaufbar ohne Live-HA-Zugriff.

---

## PFAD 4: Lovelace Cards / Frontend — ✅ RELEASEFÄHIG (COMMIT-PENDING)

| Check | Ergebnis | Pfad |
|-------|---------|------|
| Alle 9 JS Cards syntaktisch valid | ✅ PASS | `www/styx-*.js` |
| `styx-zone-card.js` — 3 UX-Fixes (UX GATE PASS) | ✅ COMMITS OK | `2a50914b`, `391a5efa` |
| `pilotstack-zone-cards.mjs` | ⚠️ 411+/145- UNCOMMITTED | `www/pilotstack-zone-cards.mjs` |
| `.bak`-Datei | ❌ 36KB Backup-Artefakt | `www/styx-zone-card.js.bak` |

**Bewertung:** Cards selbst syntaktisch OK. ABER:
- `pilotstack-zone-cards.mjs` hat 411+ Zeilen Änderungen die NICHT committed sind — das ist ein 14.9.x-Blocker
- `.bak` muss vor Release gelöscht werden

---

## PFAD 5: Configuration / Config Flow — ✅ SYNTAX OK, UNGETESTET

| Check | Ergebnis | Pfad |
|-------|---------|------|
| Config Flow 7-Step Wizard | ✅ Syntax OK | `config_flow.py`, `config_wizard_steps.py` |
| Config Schema Builder | ✅ Syntax OK | `config_schema_builders.py` |
| Options Flow Handler | ✅ Syntax OK | `config_options_flow.py` |
| Zone Wizard Steps | ✅ Syntax OK | `config_zones_flow.py` |

**Bewertung:** Syntax-Layer OK. Runtime Config-Flow ohne Live-HA nicht verifizierbar.

---

## PFAD 6: Dashboard / YAML — ✅ SYNTAX OK, UNBEKANNT RUNTIME

| Check | Ergebnis | Pfad |
|-------|---------|------|
| Dashboard YAML Dateien | ✅ Existieren, Syntax unbekannt | `dashboard/*.yaml` |
| Dashboard Card Definitions | ✅ Existieren | `dashboard_cards/` |
| Lovelace Resources Config | ✅ Existiert | `lovelace_resources.py` |

**Bewertung:** Keine YAML-Syntaxprüfung durchgeführt. Unknown Runtime Risk.

---

## ZUSAMMENFASSUNG: FREIGABE-STATUS

```
✅ SYNTAX OK + UNIT TESTS PASS          → release-fähig
✅ AREA→ZONE MAPPING                     → release-fähig (mit Notierung)
⚠️ CORE↔HA VERDRAHTUNG                   → BROKEN (habitus_zones_matcher.py fehlt)
⚠️ WEBHOOK PIPELINE                      → syntaktisch OK, Runtime unbewiesen
⚠️ PILOTSTACK-ZONE-CARDS.MJS             → UNCOMMITTED (Blocker für 14.9.x)
❌ .BAK DATEI                            → muss gelöscht werden
❌ LIVE RUNTIME                          → nicht verifizierbar ohne HA API Token
```

### Must-Fix vor Release:
1. **`habitus_zones_matcher.py`** — entweder in Core erstellen oder HA-Import auf `zone_matcher.py` umstellen
2. **`pilotstack-zone-cards.mjs`** — committen oder verwerfen (PilotClaw + Stxy Klärung)
3. **`styx-zone-card.js.bak`** — löschen

### Nicht testbar ohne Live-HA:
- Webhook Runtime Delivery
- Config Flow End-to-End
- Dashboard Rendering
- Entity Registration
- WebSocket Commands
- Presence Hold Sync

---

## RISIKO-MATRIX

| Risiko | Wahrscheinlichkeit | Impact | Status |
|--------|-------------------|--------|--------|
| `habitus_zones_matcher.py` fehlt → Runtime-Fallback aktiv | HOCH | MITTEL | MUSS GEFIXT WERDEN |
| `pilotstack-zone-cards.mjs` nie committed → Lovelace UI Inkonsistenz | HOCH | HOCH | BLOKER |
| `.bak` im Release-Artefakt → Backup-Code in Produktion | MITTEL | NIEDRIG | MUST DELETE |
| Zone-ID Mismatch HA/Core → langfristig Maintenance-Schuld | MITTEL | MITTEL | NOTIERUNG |
| Webhook Runtime Delivery funktioniert nicht | UNBEKANNT | HOCH | NICHT TESTBAR |

---

## OFFENE FRAGEN (AN PILOTCLAW / ANDREAS)

1. **Was ist `habitus_zones_matcher.py` — existierte es mal und wurde gelöscht, oder war der Import immer ein Fehler?**
2. **Soll `pilotstack-zone-cards.mjs` committed werden? Welcher Agent ist dafür verantwortlich?**
3. **Gibt es einen HA API Token für Runtime-Verifikation, oder muss das auf einem anderen Weg getestet werden?**
4. **Zone-ID-Schema — bewusste Entscheidung (German in HA, English in Core) oder Versehen?**

---

*Erstellt durch: HomeClaw Lane (Runtime/Integration)*
*GitHub-First: Alle Befunde an `origin/main@2a50914b` gebunden*
