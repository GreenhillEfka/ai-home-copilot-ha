# PilotSuite v1.0.0-rc2: Integration Manifest

**Target:** RC2 Landing (2026-04-07 01:00 Berlin)
**Lead:** DesignClaw / PilotClaw

## 1. Structural Hardening (v1.0 Standard)
- [ ] **CQRS Implementation:** Schreib-Operationen (Commands) für Habitus-Zonen über `events/bus.py`.
- [ ] **Hexagonal Bridge:** Ports für HA-Entity-States und Web-Queries sauber getrennt.
- [ ] **Federated Math:** Library unter `ml/math/federated.py` verfügbar.

## 2. Legacy & Feature Completion
- [ ] **P1-Batch-1:** Alle 13 Endpunkte (Wetter, Notifications, Energy-Baselines) registriert.
- [ ] **Habit-Sensoren:** HA-Integration für Routine-Predictions aktiv.
- [ ] **Energy Optimizer:** OR-Tools Engine mit Live-HA-State gekoppelt.

## 3. Intelligence & Confidence
- [ ] **Thompson Sampling:** Aktiv für Multi-User Präferenz-Entscheidungen.
- [ ] **Wilson Score:** Confidence-Bounds werden im Backend-UI (Zones) angezeigt.
- [ ] **Ollama-RAG:** Tuning-Parameter (RRR=1, Threshold=0.7) als Default-ENVs.

## 🚀 COMMAND: PILOTSUITE_RC2_READY
Sobald diese Liste grün ist, wird der Tag `v1.0.0-rc2` gesetzt.

**Go. Keine Ausreden. Schlag auf schlag.**
