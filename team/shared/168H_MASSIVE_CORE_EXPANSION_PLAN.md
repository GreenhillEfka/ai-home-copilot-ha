# 168H MASSIVE CORE EXPANSION PLAN — ANDREAS-AUFTRAG

## 🎯 ZIELSETZUNG
Basierend auf dem Andreas-Auftrag (Core, Robustheit, Intelligence, Voice, UI, MCP) wird dieser Plan die massive Erweiterung des Core-Systems in 168 Stunden durchführen. Alle Agenten arbeiten an Slices 160–300. Der Plan ist verbindlich und dient als Kanonische Wahrheit für alle Ausführungen.

---

## 🧩 KERNKOMPONENTEN (ANDREAS-AUFTRAG)

### 1. Core Expansion
- **Primärwahrheit**: `/config/clawd/team/worktrees/pilotsuite-styx-core-current`
- **Runtime-Wiring**: `rootfs/usr/src/app/...`
- **API-Hierarchie**: Worktree → Runtime → Registry → OpenAPI → Legacy-Doku
- **Aufgabe**: Erweiterung der Core-Funktionalität um neuronale Zustandslogik, Habitus-Zonen, und semantische Normalisierung.

### 2. Robustheit
- **State Consistency Checks** (P2-007)
- **Event Propagation Systematics** (P2-006)
- **Testbasis**: Aktuell grün mit 9 passed Tests (Stand H2)
- **Driftfälle**: 44 offene Driftfälle aus H2-Reconciliation

### 3. Intelligence
- **LSTM Forecasting** für Zeitreihen-Vorhersage
- **OR-Tools Scheduling Optimizer** (P2-002)
- **Knowledge Graphs** mit Entity-Relation-Entity und Temporal Reasoning
- **Federated Learning** für privacy-preserving Multi-User Learning

### 4. Voice
- **Sota_media_alarm.py** konsolidiert (C-026)
- **Musikwolke Engine** überarbeitet (C-025)
- **Sonnenwecker Modul** eigenständig (C-024)

### 5. UI
- **HA/Core-Schluss**: Visualisierung der Core-Wahrheit in Dashboards und Habitus-Zonen UI
- **UX/Ops**: Integration von HA/HACS-Entitäten und Events in Core-Modul

### 6. MCP
- **Neuron-Auth-Contract** (C-027)
- **Contract-Tests** für Neuron-Auth (C-028)
- **Unified Anomaly Framework** für HomeClaw

---

## 🗓️ SPRINTS (SLICES 160–300)

### Sprint 1: Core & Robustheit (Slice 160–180)
- **Lead**: openclaw-main
- **Aufgaben**:
  - Implementierung der neuronalen Zustandslogik
  - Korrektur der Event-Propagation-Systematik
  - Behebung der 44 Driftfälle aus H2-Reconciliation

### Sprint 2: Intelligence & Voice (Slice 181–220)
- **Lead**: intelligence-agent
- **Aufgaben**:
  - Integration von LSTM Forecasting und OR-Tools Scheduling
  - Überarbeitung der Musikwolke Engine
  - Konsolidierung des Sonnenweckers

### Sprint 3: UI & MCP (Slice 221–260)
- **Lead**: ui-agent
- **Aufgaben**:
  - Visualisierung der Core-Wahrheit in Dashboards
  - Implementierung des Neuron-Auth-Contracts
  - Erstellung der Contract-Tests

### Sprint 4: Unified Anomaly Framework (Slice 261–300)
- **Lead**: anomaly-agent
- **Aufgaben**:
  - Entwicklung des Unified Anomaly Frameworks für HomeClaw
  - Integration in Core- und HA-Module
  - Test und Validierung des Frameworks

---

## 📢 INFORMATIONSFLUSS
Alle Leads werden unmittelbar über ihre bindenden Sprints informiert. Die Fortschritte werden in `PILOTSUITE_PROGRESS_LEDGER.md` festgehalten, um eine unmittelbare Weiterführung durch jeden Agenten zu ermöglichen.

---

## 🛠️ IMPLEMENTIERUNG DES UNIFIED ANOMALY FRAMEWORKS
Das Unified Anomaly Framework wird gemäß den Empfehlungen implementiert. Es umfasst:
- Erkennung von Anomalien in Echtzeit
- Automatische Benachrichtigung der zuständigen Leads
- Logging und Reporting der Anomalien
- Integration in bestehende Systeme (Core, HA, MCP)

---

## 📌 CONTINUITY-REGEL
Relevanter Fortschritt darf nicht nur im Chat stehen; er muss in `PILOTSUITE_PROGRESS_LEDGER.md` so festgehalten werden, dass jeder Agent unmittelbar wieder übernehmen kann.