# Research-to-Implementation Tracker

**Created:** 2026-04-07 00:00 Europe/Berlin
**Purpose:** Track all research-derived tasks from implementation to completion

---

## 📚 RESEARCH SOURCES

| Source | Date | Topics Covered |
|--------|------|----------------|
| `AI_HOME_COPILOT_DEEP_RESEARCH_REPORT.md` | 2026-02-15 | Module Analysis, Neurons, Dashboard, Tests |
| `perplexity_research_2026-02-16.md` | 2026-02-16 | 5 Tracks: AI/ML, Presence, Energy, KG, Multi-User |
| `research_2026-02-17.md` | 2026-02-17 | SOTA Research (5 Prioritäten) |
| `DEEP_RESEARCH_PARALLEL.md` | 2026-03-xx | 5 Parallel Tracks (Architecture, Vector, Bayesian, Integration, UX) |
| `research_integration_map.md` | 2026-03-26 | Integration Status |
| `orakel.md` (Pull-Loop Logs) | 2026-03-24-29 | P0-103 Recovery (80h+ Blockade) |
| **Orakel Hourly SotA Research #1** | **2026-04-07** | **OR-Tools Scheduler (P2-002)** |

---

## ✅ COMPLETED IMPLEMENTATIONS

| ID | Task | Research Source | Commit | LOC | Status |
|----|------|-----------------|--------|-----|--------|
| **P1-002** | LSTM Energy Forecasting | perplexity_2026-02-16 | `C-011` | ~200 | ✅ Done |
| **P1-004** | TFLite/ONNX Runtime | research_2026-02-17 | `C-012` | ~150 | ✅ Done |
| **P2-002** | OR-Tools Scheduler | **Orakel Research #1** | **`5d220f7c`** | **400** | **✅ Just Done!** |
| **C-021** | Symbiose HA-Core Stack | MEMORY.md | 2026-04-06 | 5000+ | ✅ Done |
| **C-024** | Sonnenwecker Module | MEMORY.md | 2026-04-06 | ~200 | ✅ Done |
| **C-027** | Neuron-Auth Contract | MEMORY.md | 2026-04-06 | ~300 | ✅ Done |
| **E1-E3** | Event Ordering (WAL, Versioned State) | MEMORY.md | 2026-04-06 | ~600 | ✅ Done |

---

## 🔄 IN PROGRESS

| ID | Task | Research Source | Progress | Next Step |
|----|------|-----------------|----------|-----------|
| **P1-001** | Bayesian Presence Detection | perplexity_2026-02-16 | 50% | Wilson Score implementieren |
| **P1-005** | Knowledge Graph Schema | perplexity_2026-02-16 | 30% | Neo4j/NetworkX Integration |
| **P1-006** | Voice: Whisper/Piper | research_2026-02-17 | 70% | E2E Testing |
| **P1-007** | Brain Graph Store Tests | DEEP_RESEARCH_REPORT | 0% | Tests schreiben |
| **P1-008** | Tag System Tests | DEEP_RESEARCH_REPORT | 0% | Tests schreiben |

---

## ❌ OPEN (Prioritized)

### P0 - Security/Stability

| ID | Task | Research Source | Why Critical |
|----|------|-----------------|--------------|
| **P0-001** | Security Fix: Token Auth | research_2026-02-17 | Security baseline |
| **P0-002** | Vector Store Tests (19 failures) | DEEP_RESEARCH_REPORT | API stability |

### P1 - Core Features

| ID | Task | Research Source | Why Important |
|----|------|-----------------|---------------|
| **P1-003** | Multi-User Preference Learning | perplexity_2026-02-16 | Personalization |
| **P1-004** | TFLite/ONNX Integration | research_2026-02-17 | Edge ML |
| **P1-005** | Knowledge Graph Schema | perplexity_2026-02-16 | Semantic reasoning |

### P2 - Optimization

| ID | Task | Research Source | ROI |
|----|------|-----------------|-----|
| **P2-001** | Multi-Sensor Fusion | perplexity_2026-02-16 | High |
| **P2-003** | HNSW Vector Optimization | DEEP_RESEARCH_PARALLEL | Medium |
| **P2-004** | Wilson Score Interval | DEEP_RESEARCH_PARALLEL | Medium |
| **P2-005** | Thompson Sampling | DEEP_RESEARCH_PARALLEL | Medium |

### P3 - UX/Dashboard

| ID | Task | Research Source | User Impact |
|----|------|-----------------|-------------|
| **P3-001** | ReactBoard Integration (404 Fix) | DEEP_RESEARCH_REPORT | High |
| **P3-002** | WebSocket für Echtzeit-Updates | DEEP_RESEARCH_REPORT | High |
| **P3-003** | Interaktive Graph-Visualisierung | DEEP_RESEARCH_REPORT | Medium |

---

## 🔬 ORAKEL RESEARCH RECOMMENDATIONS

### Research #1 (2026-04-07): OR-Tools Scheduler

**Status:** ✅ **IMPLEMENTED** (`5d220f7c`)

**Recommendations:**
1. ✅ Separate Forecast → Optimization Pipeline
2. ✅ Start with 3 High-Value Device Classes (EV, Heat Pump, Battery)
3. ✅ Rolling 24-Hour Horizon with 15-Minute Slots

**Open Questions for Discussion:**

**Q1 — Constraint Priority:**
> Should comfort constraints be modeled as hard constraints (never violated) or soft constraints (penalized in objective function)?

**Current Implementation:** Configurable per device (ConstraintType.HARD vs SOFT)

**Q2 — Data Contract:**
> What is the canonical interface between LSTM Forecaster and OR-Tools Scheduler?

**Current Implementation:** `ForecastData` dataclass with load/solar/price/carbon arrays

**Q3 — Execution Authority:**
> Should the scheduler write directly to HA entities, or produce a schedule proposal that requires user confirmation?

**Current Implementation:** `SchedulerIntegration` supports both modes (confirmation required for first N runs)

---

## 📊 IMPLEMENTATION STATISTICS

| Metric | Value |
|--------|-------|
| **Total Research Tasks** | 34+ |
| **Completed** | 10+ |
| **In Progress** | 5 |
| **Open** | 19+ |
| **Research-Driven LOC** | ~7,000+ |
| **Commits from Research** | 50+ |

---

## 🎯 NEXT RESEARCH IMPLEMENTATIONS

Based on research priority and ROI:

1. **P1-001: Bayesian Presence** — Wilson Score + Bayesian Fusion
2. **P1-005: Knowledge Graph** — Neo4j/NetworkX integration
3. **P2-001: Multi-Sensor Fusion** — 3+ sensor types
4. **P3-002: WebSocket Real-Time** — Live dashboard updates
5. **P0-002: Vector Store Tests** — Fix 19 failing tests

---

## 🤔 DISCUSSION NEEDED

### Critical Questions for @all:

1. **Old vs. New Code Gap:**
   - Old codebase had >100,000 LOC
   - New codebase has ~18,000 LOC
   - **Question:** What features from old code are missing?

2. **Research Priority:**
   - 34 research tasks identified
   - Resources limited
   - **Question:** Which 5 tasks are must-have for v1.0.0?

3. **Integration Testing:**
   - 0 new tests in current codebase
   - Old tests exist in archive/
   - **Question:** Test strategy for v1.0.0?

4. **HACS Requirements:**
   - HACS validation needed for community distribution
   - **Question:** HACS submission timeline?

---

*Last Updated: 2026-04-07 00:05 Europe/Berlin*
*Next Research Review: On-demand*
