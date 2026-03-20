# PilotSuite Release Gate — Master Index

**Zweck:** Canonicales Dokument für alle gekoppelten Core+HA-Releases. Pro Release wird ein eigenes `RELEASE_GATE_<version>.md` erstellt und hier referenziert.

---

## Release-Check-Definitionen (G1–G4)

Für jedes **gekoppelte Core+HA-Release** müssen alle Checks PASS sein, bevor der Release freigegeben wird.

| # | Check | Was geprüft wird | Automatisiert |
|---|-------|-----------------|---------------|
| **G1** | Version-Sync | HA `manifest.json` version == Core `VERSION` file == CHANGELOG-Header in beiden Repos | ⚠️ CLI-Snapshot (grep/cat) |
| **G2** | Changelog-Kreuzreferenz | HA-CHANGELOG referenziert Core-Version; Core-CHANGELOG referenziert HA-Version (bidirektional) | ⚠️ Manuell |
| **G3** | OpenAPI-Path-Count | Anzahl API-Paths (`grep "^  /" openapi.yaml`) in Core UND HA identisch | ✅ Ja |
| **G4** | Test-Coverage | pytest-Run ohne neue Failures; Baseline dokumentiert; Zuwachs an Testfiles pro Release gebucht | ⚠️ Manuell |

**Gate-Logik:** G1–G4 = AND-Verknüpft. Ein einzelner FAIL-Status ist ein Release-Blocker.

---

## Release-Historie

| Version | HA-Status | Core-Status | G1 | G2 | G3 | G4 | Gate | Dokument |
|---------|-----------|-------------|----|----|----|----|------|----------|
| **14.7.5** | ❌ FAIL | ❌ FAIL (pending) | FAIL | FAIL | PASS | INCONCLUSIVE | ❌ | `RELEASE_GATE_14_7_5.md` |
| 14.7.4 | ✅ PASS | ✅ PASS | PASS | PASS | PASS | PASS | ✅ | (Core-Changelog dokumentiert) |
| 14.7.3 | ✅ PASS | ✅ PASS | PASS | PASS | PASS | PASS | ✅ | (Core-Changelog dokumentiert) |
| 14.6.1 | ✅ PASS | ✅ PASS | PASS | PASS | PASS | PASS | ✅ | (Core-Changelog dokumentiert) |

---

## HA v14.7.5 — Aktuelle Blockers

```
G1 FAIL — Core prep VERSION = 14.7.3, sollte 14.7.5 sein
G2 FAIL — Core CHANGELOG enthält keinen [v14.7.5]-Eintrag
G3 PASS — 572 Paths in HA prep, Core prep und Core current identisch
G4 INCONCLUSIVE — Neue Tests (test_services_integration.py, test_zone_flows_integration.py)
                 vorhanden, aber kein pytest-Run dokumentiert
```

→ Siehe `RELEASE_GATE_14_7_5.md` für vollständige Analyse.

---

## Workflow: Vor jedem Release

1. **Core-Release-Prep** setzt `VERSION` + schreibt CHANGELOG `[v<version>]`
2. **HA-Release-Prep** setzt `manifest.json` + schreibt HA-CHANGELOG mit Core-Referenz
3. PilotClaw führt G1–G4 Checks durch
4. Ergebnis in `RELEASE_GATE_<version>.md` und Update dieses Index in `RELEASE_GATE.md`
5. Gate PASS → Freigabe. Gate FAIL → Blocker-eskalation.

---

*Letztes Update: 2026-03-20 — PilotClaw Subagent — Task PS-140*
