# HA TASKBOARD — PilotSuite HA Integration Layer

**Lane:** HomeClaw / HA-Integration  
**Version:** 15.4.0  
**Prinzip:** HA = Integration/Projection. Keine Core-Logik in HA.

---

## Referenzen (führend)

- HA_CONCEPT_DIRECTIVE.md ← Architekturregeln
- PILOTSUITE_EXECUTION_FOUNDATION.md ← Worktree/Repo/Truth
- HA_CORE_CONTRACT_TASKBOARD.md ← HA↔Core Contracts
- /handoffs/ ← Lane-übergreifende Handoffs

---

## HA-Sprint Stand (2026-04-05)

### Abgeschlossen ✅

| # | Task | Commit | Artefakt |
|---|------|--------|---------|
| HA-57 | neurons_14.py deletion | PR #169 | custom_components/copilot_ha/neurons_14.py removed |
| HA-60 | cognitive_sensors + habit_learning_v2 klassifiziert | PR #169 | HA-lokal, kein Core-Eingriff |
| HA-61 | Blueprint-Registry-Drift (H2) | — | 12 Driftfälle dokumentiert |
| HA-65 | Version Bump | PR #170 | manifest.json → 15.4.0 |
| HA-72 | PS-151 Drift Guard | PR #173 | .pre-commit.d/ps151_drift_guard.sh |
| HA-78 | api/__init__.py SyntaxError | PR #174 | _post_json try-block korrekt geschlossen |
| HA-86 | Stale Recovery Docs archiviert | PR #175 | HA_CONCEPT_DIRECTIVE.md + 2 weitere gelöscht |
| HA-87 | HA_CONCEPT_DIRECTIVE.md erstellt | Commit `9668fb92` | docs/HA_CONCEPT_DIRECTIVE.md |
| HA-88 | 3 Sensoren HA-83 Fix | Commit `31d58c04` | appliance/comfort/demand_response graceful |
| HA-89 | README.md v15.4.0 | Commit `22fa9d83` | Version + Status aktualisiert |

### Aktiv 🔄

| # | Task | Next Step | Folgeschritt |
|---|------|---------|-------------|
| HA-90 | TASKBOARD.md erstellen | → dieser Slice | PR → Merger |
| HA-91 | HA-Branch auf main | Nach TASKBOARD-Merge | takeover → main rebasen |
| HA-67 | 26 Core-Dateien → PilotClaw | Handoff-Dokument fertig | PilotClaw移管 |

### Offen 🔴

| # | Task | Abhängigkeit |
|---|------|-------------|
| HA-67 | Core-Dateien移管 (brain_graph, habitus, ml/, kg/, vector, learning_analytics) | PilotClaw |
| HA-92 | 3 Sensoren Core-Endpoints implementieren | PilotClaw: /energy/fingerprints, /comfort, /energy/demand-response/status |
| HA-93 | Zone Sync Fix (B1-B4) | PilotClaw: HubZoneEngine sync |
| HA-94 | Projection-Tests: neuron_dashboard, presence_sensors, predictive_maintenance | HA-lokal |
| HA-95 | HACS Release Shape Fix | HACS-Validierung |

---

## HA↔Core Contract Status

| Contract | HA-Hälfte | Core-Hälfte | Status |
|----------|-----------|-------------|--------|
| INGEST_CONTRACT | ✅ HomeClaw | ✅ PilotClaw | Aktiv |
| ZONE_TRUTH_CONTRACT | 🔴 Zone Sync offen | 🔴 B1-B4 | Blockiert |
| MODULE_CONTRACT | ✅ HomeClaw | ✅ PilotClaw | Aktiv |
| AUTOMATION_NEURON_CONTRACT | 🔴 Offen | 🔴 Offen | Nie begonnen |
| RAG_STYX_CONTRACT | 🔴 Offen | 🔴 Offen | Nie begonnen |
| PROPOSAL_LIFECYCLE_CONTRACT | 🔴 Offen | 🔴 Offen | Nie begonnen |
| DASHBOARD_READMODEL_CONTRACT | 🔴 Offen | 🔴 Offen | Nie begonnen |

---

## Slice-by-Slice (dieser Sprint)

1. ✅ HA_CONCEPT_DIRECTIVE.md
2. ✅ 3 Sensoren HA-83 Fix
3. ✅ README.md v15.4.0
4. 🔄 TASKBOARD.md ← aktuell
5. → HA-Branch → main Rebase
6. → HA-67 Handoff finalisieren
7. → HA-94 Projection-Tests

---

## Nächster exakter Schritt

**TASKBOARD.md commit → PR → Merge → Branch Rebase auf main**

**Direkter Folgeschritt:** HA-Branch cleanup (takeover/ha4-main-truth → main)

---

**Genehmigt:** Andreas Betz  
**Herausgeber:** HomeClaw / openclaw-main  
**Stand:** 2026-04-05 18:15 Europe/Berlin
