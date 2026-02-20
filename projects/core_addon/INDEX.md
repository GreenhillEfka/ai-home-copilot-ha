# Core Add-on - Entwicklungs-Index

## 🎯 Status: v0.4.15 (Sync mit HA Integration v0.7.3) - 2026-02-15 00:48

---

## ✅ Completed Neurons & Modules

| Module | Tests | Docs | Status |
|--------|-------|------|--------|
| **Brain Graph v2** (model/store/service/render/api) | ✅ | ✅ | ✅ Done |
| **Mood Neuron** (service/api) | ✅ | ✅ | ✅ Done |
| **Energy Neuron** (service/api) | ✅ | ✅ | ✅ Done |
| **Media Context** | - | - | ✅ Done |
| **UniFi Neuron** (service/api) | ✅ | ✅ | ✅ Done |
| **Tag System** (registry/assignments/api) | ✅ | ✅ | ✅ Done |
| **Dev Surface** (models/service/api) | ✅ | ✅ | ✅ Done |
| **Log Fixer TX** (operations/transaction_log/recovery) | ✅ | ✅ | ✅ Done |
| **Event Ingest** (processor/store/api) | ✅ | ✅ | ✅ Done |
| **System Health** (service/api) | ✅ | ✅ | ✅ Done |
| **Habitus Miner** (miner/service/api) | ✅ | ✅ | ✅ Done |
| **Candidates** (store/api) | ✅ | ✅ | ✅ Done |

---

## 🔧 Recently Fixed (2026-02-14)

### Habitus Miner Bug Fixes
- **Bug**: `edge.updated_at` → `edge.updated_at_ms` (5 occurrences in miner.py)
  - Sort, filter, session splitting, and timestamp extraction all used wrong attribute
  - Would have caused `AttributeError` at runtime
- **Bug**: `HabitusService._create_candidate_from_pattern` called `self.candidate_store.create_candidate()` (non-existent method)
  - Fixed to use `self.candidate_store.add_candidate(pattern_id, evidence, metadata)` + `get_candidate()`
- **Tests**: Added 17 comprehensive tests in `tests/test_habitus.py`
  - PatternEvidence serialization
  - Sequence extraction (empty, filter, lookback, debounce, session split)
  - Pattern discovery (A→B, self-skip, delta window)
  - Evidence calculation
  - End-to-end mine pipeline
  - HabitusService (throttle, force, candidate creation, dedup, stats)

---

## 📝 Todo / Backlog

| Task | Priority | Status |
|------|----------|--------|
| **Performance Scaling** - Optimize for large graphs (>500 nodes) | Low | Planned |
| **Security/Privacy Audit** - Review PII redaction coverage | Low | Planned |

## ✅ Recently Completed (v0.4.15)

| Task | Status | Date |
|------|--------|------|
| **Habitus Zones v2** - Zone-aware pattern mining | ✅ Done | 2026-02-14 |
| **Graph Candidates Bridge** - Link graph patterns to candidate lifecycle | ✅ Done | 2026-02-14 |
| **SystemHealth/UniFi/Energy Neurons** | ✅ Done | 2026-02-14 |
| **Tag System v0.2** - Decision Matrix + HA Labels | ✅ Done | 2026-02-14 |

---

## 📊 Test Coverage

```
tests/test_brain_graph_model.py    ✅
tests/test_brain_graph_service.py  ✅
tests/test_brain_graph_store.py    ✅
tests/test_dev_surface.py          ✅
tests/test_dev_surface_simple.py   ✅
tests/test_e2e_pipeline.py         ✅
tests/test_energy.py               ✅
tests/test_event_processor.py      ✅
tests/test_event_store.py          ✅
tests/test_habitus.py              ✅ (NEW - 17 tests)
tests/test_log_fixer_tx.py         ✅
tests/test_system_health.py        ✅
tests/test_tag_api.py              ✅
tests/test_tag_assignment_store.py ✅
tests/test_tag_registry.py         ✅
tests/test_tags_v2.py              ✅
tests/test_unifi.py                ✅
```

---

## 🔄 Sync mit HA Integration

Siehe: `/config/.openclaw/workspace/projects/ai_home_copilot/INDEX.md`

Aktueller Sync: v0.4.15 (Core) ↔ v0.7.3 (HA Integration) ✅

Beide Repos sind vollständig synchronisiert mit Habitus Zones v2.

---

*Letzte Aktualisierung: 2026-02-15 00:48*
