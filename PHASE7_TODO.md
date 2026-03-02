# Phase 7 — Production Readiness & Advanced ML

**Erstellt:** 2026-03-02 11:00  
**Status:** 🔜 Ready für Implementation  
**Priorität:** P1 (Production Readiness) → P2 (Advanced ML)

---

## 📊 Current Status

| Komponente | Status | Version | Notes |
|------------|--------|---------|-------|
| Phase 5 (Cross-Home Sharing) | ✅ COMPLETE | v12.11.0 | 31 Endpoints, 217+ Tests |
| Phase 6 (Advanced ML + Type Hints) | ✅ COMPLETE | v12.11.0 | 2526 Tests, 98% Pass-Rate |
| Phase 7 (Production Readiness) | 🔜 PLANNED | - | Diese Datei |

---

## 🎯 Phase 7 Tasks

### P1: Production Readiness

#### 1. Performance-Optimierung
- [ ] **Connection Pooling** für HA-Supervisor + Ollama
  - File: `copilot_core/connections.py` (neu) oder `core_setup.py` erweitern
  - Ziel: Wiederverwendung statt Neuverbindung pro Request
- [ ] **Cache Tuning** für häufige Anfragen
  - File: `copilot_core/cache.py` oder bestehendes Caching erweitern
  - Ziel: Sensor-Daten, RAG-Ergebnisse cachen (TTL-basiert)
- [ ] **VectorStore-Optimierung** bei wachsender Datenbasis
  - File: `copilot_core/vectorstore.py` oder `brain_graph.py`
  - Ziel: Effizientere Ähnlichkeitssuche (Indexierung, Chunking)

#### 2. Startup-Zeit reduzieren
- [ ] **Lazy Loading** für selten genutzte Module
  - File: `copilot_core/core_setup.py`
  - Ziel: Module erst bei Bedarf importieren/initialisieren
- [ ] **Init-Profiling** durchführen
  - Script: `scripts/profile_startup.py` (neu)
  - Ziel: Bottlenecks identifizieren (welche Module brauchen am längsten?)

#### 3. Monitoring erweitern
- [ ] **Prometheus-Metriken** für alle Phase 5/6 Endpoints
  - File: `copilot_core/metrics.py` (neu) oder `api/v1/metrics.py`
  - Endpoints: Request-Count, Latency, Error-Rate pro Endpoint
- [ ] **Health-Check** um Performance-Metriken ergänzen
  - File: `copilot_core/api/v1/health.py`
  - Ziel: CPU, RAM, Connection-Pool-Status, Cache-Hit-Rate

#### 4. Dokumentation
- [ ] **OpenAPI-Spec** für alle 130+ Endpoints generieren
  - Tool: `flask-openapi3` oder `apispec`
  - Output: `docs/openapi.json` + `docs/api-reference.md`
- [ ] **Vollständige API-Referenz** schreiben
  - File: `docs/API_REFERENCE.md`
  - Ziel: Alle Endpoints mit Request/Response-Beispielen

#### 5. Test-Fixes
- [ ] **20 fehlgeschlagene Tests** aus Phase 6 analysieren
  - Command: `pytest tests/ -q --tb=short | grep FAILED`
  - Output: `reviews/phase6-failed-tests.md` (neu)
- [ ] **Beheben** vor Production-Release
  - Priorität: P1 (blockiert v13.0.0)

---

### P2: Advanced ML Features

#### 1. On-Device Inference
- [ ] **TFLite / ONNX Runtime** für Raspberry Pi 4 / Intel NUC
  - File: `copilot_core/ml/on_device.py` (neu)
  - Modelle: Mood, Neurons, Anomaly Detection
  - Ziel: <100ms Inference-Zeit
- [ ] **Modell-Konvertierung** (PyTorch → TFLite/ONNX)
  - Script: `scripts/convert_models.py` (neu)

#### 2. Anomaly Detection
- [ ] **Isolation Forest** für Energie-Anstiege, unerwartete Aktivitäten
  - File: `copilot_core/ml/anomaly.py` (neu)
  - Features: Energieverbrauch, Sensor-Muster, Anwesenheit
  - Ziel: Echtzeit-Erkennung (<1s Latency)

#### 3. Zeitreihen-Prognosen
- [ ] **LSTM/Transformer** für Temperatur, Energie, Anwesenheit
  - File: `copilot_core/ml/timeseries.py` (neu)
  - Features: Historische Daten (7-30 Tage), Wetter, Tageszeit
  - Ziel: 1-24h Vorhersagen mit <10% MAPE

#### 4. Energy Load Shifting
- [ ] **PV-Ertragsprognosen** + dynamische Stromtarife
  - File: `copilot_core/modules/energy_load.py` (neu)
  - Integration: Energy Module erweitern
  - Geräte: Waschmaschine, Wallbox, Geschirrspüler
  - Ziel: Automatische Optimierung (Kosten -20%)

#### 5. Personalized Automation Timing
- [ ] **Verhaltensbasierte Zeitpunkt-Optimierung**
  - File: `copilot_core/ml/automation_timing.py` (neu)
  - Features: Historische Automation-Auslösungen, Anwesenheit, Mood
  - Ziel: "Licht 2 Min vor Ankunft" statt fixer Zeitpunkt

---

## 📈 Metriken & Ziele

### Performance-Ziele
| Metrik | Aktuell | Ziel | Messung |
|--------|---------|------|---------|
| Startup-Zeit | TBD | <5s | `scripts/profile_startup.py` |
| Request-Latency (P95) | TBD | <200ms | Prometheus-Metriken |
| Cache-Hit-Rate | TBD | >80% | Health-Endpoint |
| Connection-Pool-Effizienz | 0% (kein Pooling) | >90% | Custom-Metrik |

### ML-Ziele
| Feature | Ziel-Latenz | Ziel-Genauigkeit | Plattform |
|---------|-------------|------------------|-----------|
| On-Device Inference | <100ms | >90% (vs. Cloud) | Pi 4 / NUC |
| Anomaly Detection | <1s | >85% Precision | Pi 4 / NUC |
| Zeitreihen-Prognose | <500ms | <10% MAPE | Pi 4 / NUC |
| Energy Load Shifting | <100ms | -20% Kosten | Pi 4 / NUC |

---

## 🧪 Test-Plan

### P1 Tests
- [ ] Performance-Tests für Connection Pooling (Last-Test mit 1000 Requests)
- [ ] Cache-Hit-Rate-Tests (Simulation häufiger Anfragen)
- [ ] Startup-Profiling (Vergleich vor/nach Lazy Loading)
- [ ] OpenAPI-Spec-Validierung (alle Endpoints dokumentiert?)
- [ ] Health-Endpoint-Tests (neue Metriken vorhanden?)

### P2 Tests
- [ ] On-Device Inference-Tests (Latenz <100ms?)
- [ ] Anomaly Detection-Tests (Precision/Recall >85%?)
- [ ] Zeitreihen-Prognose-Tests (MAPE <10%?)
- [ ] Energy Load Shifting-Tests (Kostenersparnis messbar?)
- [ ] Automation Timing-Tests (User-Akzeptanz?)

---

## 📦 Release-Plan

### v12.12.0 (P1 — Production Readiness)
- Connection Pooling
- Cache Tuning
- Startup-Optimierung
- Monitoring-Erweiterung
- OpenAPI-Spec
- 20 Test-Fixes

### v13.0.0 (P2 — Advanced ML)
- On-Device Inference
- Anomaly Detection
- Zeitreihen-Prognosen
- Energy Load Shifting
- Personalized Automation Timing

---

## 🔗 Dependencies

- **Phase 5:** ✅ Abgeschlossen (v12.11.0)
- **Phase 6:** ✅ Abgeschlossen (v12.11.0)
- **Phase 7 P1:** 🔜 Ready (diese Datei)
- **Phase 7 P2:** ⏳ Wartet auf P1-Abschluss

---

## 📝 Notes

- **Ressourcen-Beschränkung:** Nicht jeder Host hat GPU oder viel RAM
- **Modellgröße vs. Genauigkeit:** Kompakte Modelle müssen genügen
- **Trainingszeit:** Inkrementelles Lernen statt vollständigem Neutraining
- **Local-First:** Alle ML-Features müssen lokal laufen (keine Cloud-Dependency)

---

**Nächste Iteration:** 2026-03-02 11:20 (automatisch via Cron)  
**Verantwortlich:** @styx (Koordination), @cowdya (Implementation), @groky (Review)
