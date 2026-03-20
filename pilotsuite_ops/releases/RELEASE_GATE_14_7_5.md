# Release Gate — HA v14.7.5

**Status:** ❌ GATE NOT PASSED  
**Datum:** 2026-03-20  
**Branch:** `pilotsuite-styx-ha-release-prep-v14.7.3`  
**Worktree-Zuordnung:** HA-Release-Prep

---

## 1. Check-Definition: Gekoppeltes Core+HA-Release

Ein Gekoppeltes Release erfordert **alle** nachfolgenden Checks. Kein Check darf FAIL, wenn der Release freigegeben werden soll.

| # | Check | Beschreibung | Automatisiert |
|---|-------|-------------|---------------|
| G1 | **Version-Sync** | HA-`manifest.json` version == Core-`VERSION` file == CHANGELOG-Header beider Repos | ⚠️ Teilweise (CLI-Snapshot) |
| G2 | **Changelog-Kreuzreferenz** | HA-CHANGELOG enthält Core-Version-Referenz und Core-CHANGELOG enthält HA-Version-Referenz | ⚠️ Manuell |
| G3 | **OpenAPI-Path-Count** | Anzahl API-Paths in `openapi.yaml` ist in Core UND HA identisch | ✅ Ja (grep `^  /`) |
| G4 | **Test-Coverage** | Testsuite läuft durch (keine neuen Failures), Mindestanzahl Tests dokumentiert | ⚠️ Manuell |

---

## 2. Check-Ergebnisse für HA v14.7.5

### G1 — Version-Sync ❌ FAIL

| Artefakt | Pfad | Erwartet | Gefunden | Status |
|----------|------|----------|----------|--------|
| HA `manifest.json` | `custom_components/copilot_ha/manifest.json` | `14.7.5` | `14.7.5` | ✅ PASS |
| Core `VERSION` | `copilot_core/VERSION` (prep) | `14.7.5` | `14.7.3` | ❌ FAIL |
| Core CHANGELOG | `CHANGELOG.md` prep | `[v14.7.5]` | existiert nicht | ❌ FAIL |
| Core `VERSION` | `copilot_core/VERSION` (current) | `14.7.5` | `14.7.4` | ❌ FAIL |

**Befund:** HA ist auf 14.7.5, Core (prep und current) noch auf 14.7.3 / 14.7.4. Kein Sync.

> ⚠️ HA-Changelog vermerkt explizit: *"Paired Core v14.7.5 release is still pending"*

---

### G2 — Changelog-Kreuzreferenz ⚠️ PARTIAL (HA-Seite OK, Core-Seite FEHLT)

| Referenz | Erwartet | Gefunden | Status |
|----------|----------|----------|--------|
| HA-CHANGELOG → Core-Version | `HA v14.7.5 <-> Core v14.7.5` | ✅ `HA v14.7.5 test release on current Core baseline v14.7.3` (aber Referenz ist 14.7.3, nicht 14.7.5) | ⚠️ NOTE |
| Core-CHANGELOG → HA-Version | `[v14.7.5]` mit HA-Referenz | ❌ Kein Eintrag für v14.7.5 im Core-CHANGELOG | ❌ FAIL |

**Befund:** HA-Dokumentation weiß, dass Core noch fehlt. Core-Dokumentation enthält keinen v14.7.5-Eintrag.

---

### G3 — OpenAPI-Path-Count ✅ PASS

| Quelle | Path-Count | Status |
|--------|-----------|--------|
| HA prep `docs/openapi.yaml` | **572** | ✅ |
| Core prep `docs/openapi.yaml` | **572** | ✅ |
| Core current `docs/openapi.yaml` | **572** | ✅ |

**Befund:** 572 Paths in allen drei geprüften Specs. Letzter Stand von Core v14.7.4 als korrekt verifiziert dokumentiert (CHANGELOG-Eintrag).

---

### G4 — Test-Coverage ⚠️ NICHT VOLLSTÄNDIG VERIFIZIERT

| Artefakt | Wert | Status |
|----------|------|--------|
| Neue Testfiles in HA v14.7.5 | `test_services_integration.py`, `test_zone_flows_integration.py` | ✅ Listed |
| Testfile-Inventar (prep) | 20 `test_*.py`-Dateien | ✅ Existieren |
| Baseline Core v14.7.3 | 4430 passed, 118 skipped | 📋 Referenzwert |
| Baseline HA v14.7.3 | 522 passed, 41 skipped | 📋 Referenzwert |
| Explizite Test-Run-Ergebnisse für HA v14.7.5 | Nicht dokumentiert | ⚠️ FEHLT |

**Befund:** Neue Tests sind angelegt, aber kein Test-Run-Report (pytest JSON/HTML) für v14.7.5 vorhanden.

---

## 3. Zusammenfassung: Gate-Status

```
╔══════════════════════════════════════════════════════════════╗
║  GATE STATUS: HA v14.7.5                    [  1/4 PASSED ] ║
╠══════════════════════════════════════════════════════════════╣
║  G1  Version-Sync                    [FAIL]                  ║
║       Core prep 14.7.3 ≠ HA prep 14.7.5                       ║
║                                                              ║
║  G2  Changelog-Kreuzreferenz         [FAIL]                  ║
║       Core-CHANGELOG: kein v14.7.5-Eintrag                   ║
║                                                              ║
║  G3  OpenAPI-Path-Count              [PASS]  572 paths       ║
║                                                              ║
║  G4  Test-Coverage                   [INCONCLUSIVE]          ║
║       Neue Tests vorhanden, kein Run-Report                  ║
╚══════════════════════════════════════════════════════════════╝

Blocker:  G1 (Core-VERSION fehlt), G2 (Core-CHANGELOG fehlt)
```

---

## 4. Naechste Schritte (Blocker-Abbau)

| # | Aktion | Verantwortlich |
|---|--------|---------------|
| 1 | Core `VERSION` auf `14.7.5` setzen (prep + current) | Core-Release-Prep |
| 2 | Core `CHANGELOG.md` Eintrag `[v14.7.5]` erstellen mit HA-Referenz | Core-Release-Prep |
| 3 | Core-Pendant-Änderungen für PS-171, PS-136 (Zone-Flows, Contract) verifizieren | Core-Review |
| 4 | pytest-Run für HA v14.7.5 durchführen und Ergebnis dokumentieren | HA-Release-Prep |
| 5 | G1–G4 nach Core-Patch erneut prüfen | PilotClaw |

---

*Erstellt: 2026-03-20 von PilotClaw (Subagent) — Tasklog: PS-140*
