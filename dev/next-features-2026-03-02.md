# PilotSuite — Nächste Features & Implementation Plan

**Datum:** 2026-03-02  
**Erstellt von:** @Cowdya (Subagent)  
**Status:** Phase 5 ✅ COMPLETE | Phase 6 ✅ COMPLETE  
**Nächste Phase:** Phase 7 — Production Readiness & Advanced ML

---

## 📋 Executive Summary

### Aktuelle Situation
- **Phase 5 (Cross-Home Sharing)**: ✅ Abgeschlossen (v12.0.0) — 31 Endpoints implementiert, 142 Tests grün
- **Phase 6 (Advanced ML & Type Hints)**: ✅ Abgeschlossen (v12.0.0) — 2526 Tests, 98% Pass-Rate
- **Nächster Meilenstein**: **Phase 7 — Production Readiness & Advanced ML Features**

### Empfohlene Prioritäten für nächste Iteration
1. **Dashboard: Styx** — Einheitliche Visualisierung (HIGH)
2. **Remaining Test Fixes** — 20 fehlgeschlagene Tests analysieren/beheben (HIGH)
3. **On-Device Inference** — TFLite/ONNX für ressourcenschonende ML-Modelle (MEDIUM)
4. **Anomaly Detection** — Isolation Forest für Sensormuster (MEDIUM)
5. **Performance-Optimierung** — Connection Pooling, Cache Tuning (MEDIUM)

---

## 🎯 Nächster Meilenstein: Phase 7

Laut ROADMAP.md ist Phase 7 die nächste geplante Entwicklungsphase:

### Phase 7 — Production Readiness & Advanced ML Features

> **Status:** 🔜 Geplant  
> **Zielversion:** v13.0.0 (MAJOR)

#### Teil 1: Production Readiness

| Feature | Beschreibung | Priorität | Aufwand |
|---------|-------------|-----------|---------|
| **Performance-Optimierung** | Connection Pooling, Cache Tuning, VectorStore-Optimierung | HIGH | 3-5 Tage |
| **Startup-Zeit** | Lazy Loading selten genutzter Module | MEDIUM | 2-3 Tage |
| **Monitoring** | Prometheus-Metriken, Health-Check-Erweiterung | HIGH | 4-6 Tage |
| **Dokumentation** | OpenAPI-Spec für alle Endpoints, vollständige API-Referenz | MEDIUM | 3-4 Tage |
| **Remaining Test Fixes** | 20 fehlgeschlagene Tests analysieren und beheben | HIGH | 2-3 Tage |

#### Teil 2: Advanced ML

| Feature | Beschreibung | Priorität | Aufwand |
|---------|-------------|-----------|---------|
| **On-Device Inference** | TFLite / ONNX Runtime für Raspberry Pi 4 / Intel NUC (Ziel: <100ms) | MEDIUM | 5-7 Tage |
| **Anomaly Detection** | Isolation Forest für ungewöhnliche Sensormuster | HIGH | 4-6 Tage |
| **Zeitreihen-Prognosen** | LSTM/Transformer für Temperatur, Energie, Anwesenheit | MEDIUM | 7-10 Tage |
| **Energy Load Shifting** | Waschmaschine, Wallbox, Geschirrspüler automatisch optimieren | HIGH | 5-8 Tage |
| **Personalized Automation Timing** | Verhaltensbasierte Zeitpunkt-Optimierung | MEDIUM | 4-6 Tage |

---

## 📊 Offene TODOs aus Phase 5/6

### Aus PHASE5_TODO.md
Alle Hauptaufgaben sind abgeschlossen ✅. Keine blockierenden TODOs.

### Aus PHASE6_TODO.md

#### Documentation Updates (Pending)
- [ ] ROADMAP.md mit Phase 6 Fortschritt aktualisieren
- [ ] API-Referenzdokumentation erstellen (OpenAPI/Swagger spec)
- [ ] Anwendungsbeispiele für alle Endpoints hinzufügen
- [ ] Cross-Home Sharing Setup-Guide erstellen
- [ ] Federated Learning Konfigurationsanleitung
- [ ] Troubleshooting-Sektion für häufige Probleme

#### Production Readiness (Pending)
- [ ] Rate Limiting für sensible Endpoints hinzufügen
- [ ] Request Validation/Sanitization implementieren
- [ ] Audit Logging für Sharing-Operationen
- [ ] CORS-Konfiguration für Cross-Origin Requests prüfen
- [ ] Caching für häufig gelesene Entities
- [ ] Pagination für große Entity-Listen
- [ ] Connection Pooling für Sync Service
- [ ] Health Check Endpoints für alle Services
- [ ] Graceful Degradation implementieren
- [ ] Disaster Recovery Procedures dokumentieren

---

## 💡 Vorschläge für nächste Features (priorisiert)

### HIGH Priority — Nächste Sprint (2-3 Wochen)

#### 1. Dashboard: Styx v1.0
**Beschreibung:** Einheitliches Dashboard, das Brain Graph, Chat und Historie zusammenführt.

**Features:**
- Visualisierung der Neuron-Aktivität und Mood-Verlauf
- Echtzeit-Updates über WebSocket
- Responsives Design für Tablet-Wandmontage und Mobile
- Integration mit bestehenden APIs (Notifications, Sharing, Collective Intelligence)

**Technische Umsetzung:**
- Frontend: React/Vue.js mit WebSocket-Client
- Backend: Neue Dashboard-API (`/api/v1/dashboard/*`)
- Datenquellen: Brain Graph, Mood Engine, Event Store

**Aufwand:** 5-7 Tage  
**Dependencies:** Keine  
**Value:** HIGH — Zentrale Visualisierung für alle PilotSuite-Daten

---

#### 2. Remaining Test Fixes (20 failed tests)
**Beschreibung:** Analyse und Behebung der 20 fehlgeschlagenen Tests aus Phase 6.

**Aktueller Stand:**
- Total: 2526 Tests
- Passed: 2476 (98.0%)
- Failed: 20 (0.8%)
- Skipped: 30 (1.2%)

**Vorgehen:**
1. Test-Logs analysieren (`pytest --tb=long`)
2. Root Causes identifizieren (Blueprint-Konflikte, Endpoint-Registration, etc.)
3. Fixes implementieren
4. Regression Tests durchführen

**Aufwand:** 2-3 Tage  
**Dependencies:** Keine  
**Value:** HIGH — 100% Test-Pass-Rate für Production-Release

---

#### 3. Anomaly Detection MVP
**Beschreibung:** Isolation Forest für ungewöhnliche Sensormuster erkennen.

**Use Cases:**
- Energieanstiege (3x höher als üblich für Dienstag 14:00)
- Unerwartete Aktivitäten (Bewegung nachts im Büro)
- Wasserverbrauch (ungewöhnliche Muster = Leck-Erkennung)

**Technische Umsetzung:**
- Bibliothek: `scikit-learn` IsolationForest
- Training: Historische Sensordaten (30 Tage)
- Inference: Echtzeit-Event-Pipeline
- Alerts: Über Notifications API

**API Endpoints:**
```
POST /api/v1/anomaly/detect      — Echtzeit-Analyse
GET  /api/v1/anomaly/history     — Historische Anomalien
POST /api/v1/anomaly/configure   — Schwellwerte konfigurieren
GET  /api/v1/anomaly/stats       — Statistik
```

**Aufwand:** 4-6 Tage  
**Dependencies:** NumPy, scikit-learn  
**Value:** HIGH — Proaktive Problemerkennung

---

### MEDIUM Priority — Folgende Sprints (1-2 Monate)

#### 4. On-Device Inference
**Beschreibung:** TFLite / ONNX Runtime für ressourcenschonende ML-Modelle.

**Ziel:** Inference unter 100ms auf Raspberry Pi 4 / Intel NUC

**Modelle:**
- Mood Prediction (kompakt, <10MB)
- Activity Recognition (mittel, ~25MB)
- Energy Forecast (kompakt, <15MB)

**Technische Umsetzung:**
- ONNX Runtime für universelle Kompatibilität
- TFLite für ARM-Optimierung (Raspberry Pi)
- Model-Quantization (FP32 → INT8)

**Aufwand:** 5-7 Tage  
**Dependencies:** ONNX Runtime, TFLite  
**Value:** MEDIUM — Bessere Performance auf schwacher Hardware

---

#### 5. Energy Load Shifting
**Beschreibung:** Automatische Optimierung von Geräten basierend auf PV-Ertrag und Stromtarifen.

**Geräte:**
- Waschmaschine
- Wallbox (E-Auto)
- Geschirrspüler
- Wärmepumpe / Boiler

**Datenquellen:**
- PV-Ertragsprognose (Wetter-API)
- Dynamische Stromtarife (Tibber/Awattar API)
- Nutzerverhalten (Habitus-System)

**API Endpoints:**
```
POST /api/v1/energy/optimize     — Optimierung berechnen
GET  /api/v1/energy/schedule     — Geplante Aktionen
POST /api/v1/energy/tariff       — Tarif konfigurieren
GET  /api/v1/energy/savings      — Ersparnisse berechnen
```

**Aufwand:** 5-8 Tage  
**Dependencies:** Energie-Modul (bereits vorhanden), externe APIs  
**Value:** HIGH — Kosteneinsparung, Nachhaltigkeit

---

#### 6. Voice Integration Deep Dive
**Beschreibung:** Tiefere Anbindung an Home Assistant Voice Assistant.

**Features:**
- Kontextbewusste Antworten (Stimmung, Tageszeit, Raum)
- Proaktive Sprachhinweise bei wichtigen Erkenntnissen
- Mehrsprachigkeit (DE/EN als Minimum)

**Technische Umsetzung:**
- Integration mit HA Voice Pipeline
- Kontext aus Mood Engine + Brain Graph
- TTS über bestehende TTS-Tools

**Aufwand:** 4-6 Tage  
**Dependencies:** Home Assistant Voice  
**Value:** MEDIUM — Bessere UX

---

#### 7. Kalender: Smart Scheduling
**Beschreibung:** Intelligente Terminplanung mit Stimmungsbewusstsein.

**Features:**
- "Du hast morgen einen vollen Tag — soll ich den Wecker 15 Minuten früher stellen?"
- Automatische Anpassung von Beleuchtungsszenen an Tagesablauf
- Integration mit bestehenden Kalender-Modulen und Mood Engine

**API Endpoints:**
```
GET  /api/v1/calendar/smart      — Intelligente Vorschläge
POST /api/v1/calendar/suggest    — Vorschlag erstellen
GET  /api/v1/calendar/conflicts  — Konflikte erkennen
```

**Aufwand:** 4-6 Tage  
**Dependencies:** Kalender-Modul, Mood Engine  
**Value:** MEDIUM — Proaktive Assistenz

---

#### 8. Multi-Home Synchronisation
**Beschreibung:** Sichere Synchronisation zwischen mehreren Wohnorten.

**Use Cases:**
- Hauptwohnung + Ferienhaus + Büro
- Einheitliche Steuerung über eine Oberfläche
- Standortabhängige Automatisierungen ("Ferienhaus vorheizen")

**Technische Umsetzung:**
- Verschlüsselte Kommunikation zwischen Instanzen
- Sync über bestehendes Sharing-Modul
- Location-Awareness über GPS/Network

**API Endpoints:**
```
POST /api/v1/multihome/register  — Weitere Home-Instanz registrieren
GET  /api/v1/multihome/status    — Sync-Status
POST /api/v1/multihome/sync      — Manuelle Synchronisation
```

**Aufwand:** 6-8 Tage  
**Dependencies:** Sharing API (bereits vorhanden)  
**Value:** MEDIUM — Für Nutzer mit mehreren Immobilien

---

### LOW Priority — Zukünftige Releases (3+ Monate)

| Feature | Beschreibung | Aufwand | Value |
|---------|-------------|---------|-------|
| **Zeitreihen-Prognosen** | LSTM/Transformer für Temperatur, Energie, Anwesenheit | 7-10 Tage | MEDIUM |
| **Personalized Automation Timing** | Verhaltensbasierte Zeitpunkt-Optimierung | 4-6 Tage | MEDIUM |
| **OpenAPI/Swagger Spec** | Vollständige API-Dokumentation | 3-4 Tage | LOW |
| **Audit Logging** | Vollständige Protokollierung aller Aktionen | 3-4 Tage | LOW |
| **Community Beta Testing** | Externe Tester für neue Features | 2-3 Tage | LOW |

---

## 🚀 Implementation-Plan für nächste Iteration

### Sprint 1 (Woche 1-2): Dashboard MVP + Test Fixes

**Ziele:**
- [ ] Styx Dashboard Grundgerüst (React + WebSocket)
- [ ] 20 failed tests analysieren und beheben
- [ ] Dashboard-API Endpoints implementieren

**Deliverables:**
- Funktionierendes Dashboard mit Brain Graph Visualisierung
- 100% Test-Pass-Rate (2526/2526 Tests)
- API-Dokumentation für Dashboard-Endpoints

---

### Sprint 2 (Woche 3-4): Anomaly Detection MVP

**Ziele:**
- [ ] Isolation Forest Integration (scikit-learn)
- [ ] Training-Pipeline für historische Daten
- [ ] Echtzeit-Inference in Event-Pipeline
- [ ] Alert-Integration mit Notifications API

**Deliverables:**
- Anomaly Detection API (4 Endpoints)
- Konfigurierbare Schwellwerte
- Dokumentation und Beispiele

---

### Sprint 3 (Woche 5-6): Energy Load Shifting

**Ziele:**
- [ ] PV-Ertragsprognose (Wetter-API Integration)
- [ ] Dynamische Stromtarife (Tibber/Awattar)
- [ ] Optimierungsalgorithmus für Geräte-Scheduling
- [ ] Nutzer-Feedback-Schleife (Accept/Reject Vorschläge)

**Deliverables:**
- Energy Optimization API (4 Endpoints)
- Integration mit bestehendem Energie-Modul
- Kosteneinsparungs-Berechnung

---

## 📈 Erfolgskriterien

### Für Phase 7 (v13.0.0)

| Kriterium | Ziel | Messung |
|-----------|------|---------|
| **Test-Pass-Rate** | 100% | pytest Ergebnis |
| **Dashboard-Performance** | <2s Ladezeit | Browser DevTools |
| **Anomaly Detection** | <5% False Positives | Test mit historischen Daten |
| **Energy Savings** | 10-15% Kosteneinsparung | Vergleich Vorher/Nachher |
| **Startup-Zeit** | <30s | `time docker-compose up` |
| **API-Response-Zeit** | <100ms (95th Percentile) | Prometheus-Metriken |

---

## 🔧 Technische Schulden & Risiken

### Bekannte Probleme

1. **20 Failed Tests** — Root Cause noch unbekannt
   - Risiko: Production-Release mit bekannten Test-Failures
   - Mitigation: Sprint 1 Priorität

2. **Dokumentation Lücken** — OpenAPI-Spec fehlt für Phase 5/6 APIs
   - Risiko: Schwierige Integration für externe Entwickler
   - Mitigation: Sprint 4 einplanen

3. **Performance auf Raspberry Pi** — ML-Inference kann langsam sein
   - Risiko: User Experience leidet auf schwacher Hardware
   - Mitigation: On-Device Inference mit quantisierten Modellen

### Risiken für Phase 7

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| ML-Modelle zu groß für Pi | MEDIUM | HIGH | Quantization, ONNX Runtime |
| Externe APIs (Tibber, Wetter) instabil | LOW | MEDIUM | Caching, Fallback-Logik |
| Dashboard zu ressourcenintensiv | MEDIUM | MEDIUM | Lazy Loading, Virtual Scrolling |
| Anomaly Detection False Positives | MEDIUM | MEDIUM | Konfigurierbare Schwellwerte, User-Feedback |

---

## 📝 Empfehlungen

### Für nächste Iteration (Sprint 1-2)

1. **Fokus auf Test Fixes** — 100% Pass-Rate ist ein wichtiges Qualitätsmerkmal
2. **Dashboard MVP** — Zeigt den Wert von PilotSuite visuell
3. **Anomaly Detection** — Low-Hanging Fruit mit hohem Nutzwert

### Für Phase 7 Gesamt

1. **Production Readiness vor neuen Features** — Stabilität geht vor Innovation
2. **Dokumentation parallel entwickeln** — Nicht als Nachgedanke behandeln
3. **Community-Feedback einholen** — GitHub Issues für Feature-Priorisierung

---

## 📌 Zusammenfassung

**Nächster Meilenstein:** Phase 7 — Production Readiness & Advanced ML (v13.0.0)

**Top 3 Prioritäten für nächste Iteration:**
1. 🎯 Dashboard: Styx v1.0 (HIGH)
2. 🐛 Remaining Test Fixes (20 failed → 0) (HIGH)
3. 🔍 Anomaly Detection MVP (HIGH)

**Geschätzter Aufwand:** 3-4 Wochen für Sprint 1-2

**Empfohlenes Vorgehen:**
- Sprint 1: Dashboard MVP + Test Fixes
- Sprint 2: Anomaly Detection
- Sprint 3: Energy Load Shifting
- Sprint 4: Dokumentation + OpenAPI-Spec

---

_Erstellt: 2026-03-02 06:25 CET_  
_Autor: @Cowdya (Coding Agent)_  
_Status: Ready for Review by @Clawdya_
