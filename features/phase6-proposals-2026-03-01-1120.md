# Phase 6 Feature Proposals — Nächste Iteration

**Erstellt:** 2026-03-01 11:20 CET  
**Analyse durch:** @cowdya (Subagent)  
**Session:** cowdya-phase6-planning  
**Basis:** docs/ROADMAP.md, PHASE6_TODO.md, VISION.md, PROJEKTPLAN.md, dev_summary_2026-03-01_0740.md

---

## 📊 Zusammenfassung der Analyse

### Aktueller Status (v11.3.0 / v7.12.4)

| Phase | Status | Version | Details |
|-------|--------|---------|---------|
| Phase 5 — Cross-Home Sharing | ✅ COMPLETE | v7.26.0 | 31 Endpoints (Notifications, Sharing, Federated Learning) |
| Phase 6 — Advanced ML & Type Hints | ✅ COMPLETE | v7.12.4 | Type Hints 100%, Test-Coverage 98.0% |
| Phase 7 — RAG Enhancement | 🟡 GEPLANT | — | Nächste Priorität laut PHASE6_TODO.md |
| Phase 9 — Advanced ML | 🔵 BEGONNEN | — | Anomaly Detection teilweise, Energy Load Shifting in Arbeit |

### Offene TODOs aus PHASE6_TODO.md

1. **RAG Hybrid Search Integration** — HIGH Priority, 2-3 Tage
2. **Push Notification Integration** — HIGH Priority, 1-2 Tage
3. **Test Coverage Improvements** — MEDIUM, Ziel: >90% für Phase-6-Module
4. **Documentation** — MEDIUM (OpenAPI/Swagger, Usage Examples)

---

## 🎯 Priorisierte Features für Nächste Iteration

### Feature 1: RAG Hybrid Search API

**Priorität:** 🔴 HIGH  
**Schätzung:** 2-3 Iterationen (4-6 Tage)  
**Phase:** 7 — RAG Enhancement & Push Integration

#### Beschreibung

Kombiniert lexikalische Suche (BM25) mit semantischer Vektorsuche für präzisere RAG-Ergebnisse. Aktuelle Implementierung nutzt nur Vector Search, was bei spezifischen Fachbegriffen oder exakten Phrasen suboptimal ist.

**Use Cases:**
- "Welche Automatisierung regelt die Heizung im Bad?" → BM25 findet "Heizung", "Bad", Vector findet semantisch ähnliche Patterns
- "Energieverbrauch letzte Woche" → Exakte Phrasen-Matching + semantischer Kontext
- "Wann wurde das letzte Mal die Waschmaschine benutzt?" → Zeitliche + semantische Kombination

#### API-Endpoints

```python
# Neuer Endpoint
POST /api/v1/rag/hybrid-search
{
    "query": "string (required)",
    "top_k": "int (default: 10)",
    "bm25_weight": "float (default: 0.5, range: 0.0-1.0)",
    "vector_weight": "float (default: 0.5, range: 0.0-1.0)",
    "filters": {
        "date_from": "ISO8601 (optional)",
        "date_to": "ISO8601 (optional)",
        "categories": ["array of strings (optional)"],
        "min_score": "float (optional, default: 0.3)"
    },
    "multi_query": "boolean (optional, default: false)",
    "re_rank": "boolean (optional, default: true)"
}

Response:
{
    "results": [
        {
            "id": "string",
            "content": "string",
            "score": "float (combined)",
            "bm25_score": "float",
            "vector_score": "float",
            "metadata": {...},
            "highlights": ["array of matched phrases"]
        }
    ],
    "query_time_ms": "int",
    "total_candidates": "int"
}
```

**Bestehende Endpoints (Erweiterung):**
- `GET /api/v1/rag/search` → Parameter `hybrid=true` hinzufügen
- `POST /api/v1/rag/query` → Hybrid-Option im Request-Body

#### Test-Anforderungen

**Unit Tests:**
- [ ] BM25-Scoring-Algorithmentest mit bekannten Suchbegriffen
- [ ] Vector-Similarity-Test mit Embedding-Vergleich
- [ ] Hybrid-Scoring-Gewichtung (0.0/1.0, 0.5/0.5, 1.0/0.0)
- [ ] Re-Ranking-Logik-Validierung
- [ ] Filter-Logik (Datum, Kategorien, Score-Threshold)

**Integration Tests:**
- [ ] End-to-End Hybrid Search mit realem VectorStore
- [ ] Performance-Test: Response-Zeit <100ms bei 10k Documents
- [ ] Multi-Query-Modus (Query-Expansion)
- [ ] Edge Cases: Leere Ergebnisse, Sonderzeichen, sehr lange Queries

**Regression Tests:**
- [ ] Bestehende Vector-Search-Endpoints weiterhin funktional
- [ ] Abwärtskompatibilität (hybrid=false als Default)

**Test-Dateien:**
- `copilot_core/tests/rag/test_hybrid_search.py` (neu, ~40 Tests)
- `copilot_core/tests/rag/test_bm25.py` (neu, ~15 Tests)
- `copilot_core/tests/rag/test_reranking.py` (neu, ~10 Tests)

#### Geschätzter Aufwand

| Aufgabe | Iterationen | Tage |
|---------|-------------|------|
| BM25-Implementation (falls nicht vorhanden) | 1 | 1-2 |
| Hybrid-Scoring-Logik | 1 | 1 |
| API-Endpoint + Request-Validation | 1 | 0.5 |
| Re-Ranking-Algorithmus | 1 | 1 |
| Tests (Unit + Integration) | 1 | 1-2 |
| Dokumentation + Examples | 0.5 | 0.5 |
| **Gesamt** | **5.5** | **5-7** |

**Risiken:**
- BM25-Implementation könnte aufwändiger sein als erwartet (abhängig von existierendem Code)
- Performance-Optimierung bei großen Document-Mengen
- Gewichtungstuning erfordert empirische Tests mit realen Queries

---

### Feature 2: Push Notification Integration mit HomeAssistant

**Priorität:** 🟠 HIGH  
**Schätzung:** 1-2 Iterationen (2-4 Tage)  
**Phase:** 7 — RAG Enhancement & Push Integration

#### Beschreibung

Integration der bestehenden Notifications-API mit HomeAssistant's `mobile_app` Notify-Service für native Push-Benachrichtigungen auf iOS/Android-Geräten. Aktuell existiert nur Telegram-Integration.

**Use Cases:**
- "Energieverbrauch 3x höher als üblich" → Push an alle Haushaltsmitglieder
- "Fenster im Bad seit 30 Minuten offen" → Kontextspezifische Benachrichtigung
- "Waschmaschine fertig" → Media-Zone-Event als Push
- "Anomalie erkannt: Wasserverbrauch außerhalb der Norm" → Kritische Alerts

#### API-Endpoints

```python
# Neuer Endpoint für HA Notify-Integration
POST /api/v1/notifications/notify-mobile
{
    "message": "string (required)",
    "title": "string (optional)",
    "target_devices": ["array of device_ids (optional, default: all)"],
    "priority": "string (optional: low, normal, high, critical)",
    "category": "string (optional: info, warning, critical, automation)",
    "data": {
        "click_action": "string (URL oder deep link)",
        "icon": "string (mdi:icon-name)",
        "color": "string (hex color)",
        "vibration_pattern": "string",
        "sound": "string",
        "sticky": "boolean (default: false)",
        "group": "string (notification grouping)"
    },
    "automation_trigger": {
        "enabled": "boolean (default: false)",
        "event_type": "string (HA event type)",
        "payload_template": "object (Jinja2 template)"
    }
}

Response:
{
    "sent_to": ["array of device_ids"],
    "failed": ["array of device_ids with error"],
    "notification_id": "string",
    "timestamp": "ISO8601"
}

# Device Management
GET /api/v1/notifications/devices
Response: {
    "devices": [
        {
            "device_id": "string",
            "platform": "ios|android",
            "name": "string",
            "registered_at": "ISO8601",
            "last_seen": "ISO8601",
            "push_enabled": "boolean"
        }
    ]
}

DELETE /api/v1/notifications/devices/{device_id}
Response: { "success": "boolean", "message": "string" }
```

**Bestehende Endpoints (Erweiterung):**
- `POST /api/v1/notifications/send` → Parameter `channel: "mobile" | "telegram" | "all"`
- `GET /api/v1/notifications/status` → Mobile-Device-Status integrieren

#### Test-Anforderungen

**Unit Tests:**
- [ ] Notify-Service-Adapter (HA mobile_app API Call)
- [ ] Device-Token-Management (Speichern, Aktualisieren, Löschen)
- [ ] Priority-Mapping (critical → high-priority APNS/FCM)
- [ ] Template-Rendering für Automation-Payloads
- [ ] Error-Handling bei ungültigen Device-IDs

**Integration Tests:**
- [ ] End-to-End Push-Versand an Test-Devices (iOS + Android)
- [ ] Device-Registrierung via HA mobile_app Webhook
- [ ] Automation-Trigger (Event → Push)
- [ ] Rate-Limiting (max. N Pushes pro Stunde pro Device)
- [ ] Deduplication (gleiche Nachricht innerhalb von X Minuten)

**Regression Tests:**
- [ ] Bestehende Telegram-Notifications weiterhin funktional
- [ ] Notifications-API bleibt abwärtskompatibel

**Test-Dateien:**
- `copilot_core/tests/notifications/test_mobile_push.py` (neu, ~30 Tests)
- `copilot_core/tests/notifications/test_device_registry.py` (neu, ~15 Tests)
- `copilot_core/tests/notifications/test_automation_trigger.py` (neu, ~10 Tests)

#### Geschätzter Aufwand

| Aufgabe | Iterationen | Tage |
|---------|-------------|------|
| HA mobile_app API-Adapter | 1 | 1 |
| Device-Registry + Token-Storage | 1 | 0.5-1 |
| Push-Payload-Builder (iOS/Android) | 1 | 1 |
| Automation-Trigger-Integration | 0.5 | 0.5 |
| Tests (Unit + Integration) | 1 | 1-2 |
| Dokumentation + Setup-Guide | 0.5 | 0.5 |
| **Gesamt** | **5** | **4-6** |

**Risiken:**
- HA mobile_app API könnte sich als komplexer erweisen (Webhook-Auth, Token-Rotation)
- iOS/Android-spezifische Payload-Unterschiede
- Rate-Limiting und Deduplication erfordern sorgfältige Implementierung

---

### Feature 3: Multi-Turn Conversations mit Persistentem Gedächtnis

**Priorität:** 🟡 MEDIUM  
**Schätzung:** 2-3 Iterationen (4-6 Tage)  
**Phase:** 10 — Enhanced Intelligence (vorziehen auf Phase 7/8)

#### Beschreibung

Erweiterung des Conversation Memory über einzelne Sessions hinweg. Nutzer können sich auf frühere Gespräche beziehen, und der Assistant erinnert sich an Präferenzen, Entscheidungen und wiederkehrende Themen.

**Use Cases:**
- "Wie war der Energieverbrauch letzte Woche?" → "Du hast am Dienstag nach dem Verbrauch gefragt, er lag bei 12.5 kWh"
- "Schalte das Licht wie gestern Abend" → Referenz auf frühere Automatisierung
- "Was hast du mir über die Heizung empfohlen?" → Recall früherer Empfehlungen mit Evidenz
- "Ignoriere meine letzte Anfrage" → Kontext-Management

#### API-Endpoints

```python
# Erweiterung bestehender Conversation-Endpoints
POST /api/v1/conversation/message
{
    "message": "string (required)",
    "session_id": "string (optional, auto-generated if omitted)",
    "context": {
        "include_history": "boolean (default: true)",
        "history_depth": "int (default: 10, messages)",
        "include_brain_graph": "boolean (default: true)",
        "include_mood": "boolean (default: true)",
        "include_habitus": "boolean (default: true)"
    },
    "memory": {
        "long_term": "boolean (default: true)",
        "topics": ["array of strings (optional, filter by topic)"],
        "time_range": {
            "from": "ISO8601 (optional)",
            "to": "ISO8601 (optional)"
        }
    }
}

Response:
{
    "response": "string",
    "session_id": "string",
    "context_used": {
        "brain_nodes": "int",
        "mood_state": "string",
        "habitus_patterns": "int",
        "memory_fragments": "int"
    },
    "sources": [
        {
            "type": "brain_graph|memory|habitus|mood",
            "relevance": "float",
            "snippet": "string"
        }
    ]
}

# Memory Management
GET /api/v1/conversation/memory
{
    "session_id": "string (optional, all if omitted)",
    "topic": "string (optional)",
    "limit": "int (default: 50)"
}

Response: {
    "memories": [
        {
            "id": "string",
            "session_id": "string",
            "topic": "string",
            "content": "string",
            "timestamp": "ISO8601",
            "importance": "float (0.0-1.0)"
        }
    ]
}

DELETE /api/v1/conversation/memory/{memory_id}
Response: { "success": "boolean" }

POST /api/v1/conversation/memory/{memory_id}/importance
{
    "importance": "float (0.0-1.0)"
}
Response: { "success": "boolean", "new_importance": "float" }
```

**Bestehende Endpoints (Erweiterung):**
- `POST /api/v1/conversation/chat` → Session-Persistenz hinzufügen
- `GET /api/v1/conversation/history` → Long-Term-Memory integrieren

#### Test-Anforderungen

**Unit Tests:**
- [ ] Memory-Storage (SQLite mit RAG-Integration)
- [ ] Session-Management (Create, Resume, Close)
- [ ] Topic-Extraction aus Conversations
- [ ] Importance-Scoring-Algorithmus
- [ ] Memory-Retrieval mit Filtering (Zeit, Topic, Relevance)

**Integration Tests:**
- [ ] Multi-Turn-Conversation über mehrere Sessions
- [ ] Context-Retrieval aus Brain Graph + Memory
- [ ] RAG-Pipeline mit Memory-Fragments
- [ ] Performance: Memory-Lookup <50ms
- [ ] Edge Cases: Sehr lange Conversations, viele Sessions

**Regression Tests:**
- [ ] Bestehende Single-Turn-Conversations weiterhin funktional
- [ ] Conversation-API bleibt abwärtskompatibel

**Test-Dateien:**
- `copilot_core/tests/conversation/test_multi_turn.py` (neu, ~35 Tests)
- `copilot_core/tests/conversation/test_memory.py` (neu, ~25 Tests)
- `copilot_core/tests/conversation/test_session_management.py` (neu, ~15 Tests)

#### Geschätzter Aufwand

| Aufgabe | Iterationen | Tage |
|---------|-------------|------|
| Memory-Storage-Schema (SQLite) | 1 | 1 |
| Session-Management-Service | 1 | 1 |
| Topic-Extraction + Importance-Scoring | 1 | 1-2 |
| Memory-Retrieval-Integration mit RAG | 1 | 1 |
| API-Endpoints + Validation | 1 | 0.5 |
| Tests (Unit + Integration) | 1 | 1-2 |
| Dokumentation + Examples | 0.5 | 0.5 |
| **Gesamt** | **6.5** | **6-8** |

**Risiken:**
- Memory-Storage könnte bei vielen Conversations groß werden (Pruning-Strategie nötig)
- Topic-Extraction erfordert NLP-Modell (lokal vs. Cloud-Abwägung)
- Privacy-Aspekte: Nutzer müssen Memory löschen können (DSGVO-Konformität)

---

## 📈 Vergleich der Features

| Kriterium | RAG Hybrid Search | Push Notifications | Multi-Turn Conversations |
|-----------|-------------------|--------------------|---------------------------|
| **Priorität** | HIGH | HIGH | MEDIUM |
| **Aufwand** | 5-7 Tage | 4-6 Tage | 6-8 Tage |
| **Iterationen** | 5-6 | 4-5 | 6-7 |
| **Nutzerwert** | Hoch (bessere Suche) | Hoch (mobile Alerts) | Mittel-Hoch (UX) |
| **Techn. Risiko** | Mittel | Mittel | Mittel-Hoch |
| **Abhängigkeiten** | VectorStore (vorh.) | HA mobile_app | RAG, Brain Graph |
| **Test-Coverage-Ziel** | 90%+ | 90%+ | 90%+ |

---

## 🎯 Empfehlung für Nächste Iteration

### Iteration 1 (v11.4.0 / v7.13.0 — MINOR)

**Fokus:** RAG Hybrid Search API  
**Dauer:** 1 Woche (5-7 Tage)  
**Begründung:**
- Höchste Priorität laut PHASE6_TODO.md
- Baut auf existierender RAG-Infrastruktur auf
- Klarer, abgegrenzter Scope
- Gutes Preis-Leistungs-Verhältnis

**Deliverables:**
1. `/api/v1/rag/hybrid-search` Endpoint
2. BM25 + Vector Search mit konfigurierbarer Gewichtung
3. Re-Ranking-Logik
4. Vollständige Testsuite (65+ Tests)
5. API-Dokumentation mit Beispielen

---

### Iteration 2 (v11.5.0 / v7.14.0 — MINOR)

**Fokus:** Push Notification Integration  
**Dauer:** 1 Woche (4-6 Tage)  
**Begründung:**
- Ebenfalls HIGH Priority laut PHASE6_TODO.md
- Schließt Lücke zwischen Core-Notifications und HA-mobile-Devices
- Ermöglicht kritische Alerts ohne Telegram-Zwang

**Deliverables:**
1. `/api/v1/notifications/notify-mobile` Endpoint
2. Device-Registry mit Token-Management
3. Automation-Trigger-Integration
4. Vollständige Testsuite (55+ Tests)
5. Setup-Guide für HA mobile_app

---

### Iteration 3 (v12.0.0 / v8.0.0 — MAJOR)

**Fokus:** Multi-Turn Conversations  
**Dauer:** 1-2 Wochen (6-8 Tage)  
**Begründung:**
- MEDIUM Priority, aber hoher UX-Wert
- Erfordert tiefere Integration (RAG + Brain Graph + Memory)
- Major-Release wegen API-Erweiterungen

**Deliverables:**
1. Session-Persistenz über Conversations hinweg
2. Long-Term-Memory mit Topic-Extraction
3. Memory-Management-API (CRUD + Importance)
4. Vollständige Testsuite (75+ Tests)
5. Conversation-Guide mit Use Cases

---

## 📝 Nächste Schritte

1. **Sofort:** Blueprint Registration Fixes (v11.4.0 PATCH, 20 failing tests → 0)
2. **Diese Woche:** RAG Hybrid Search API implementieren (Iteration 1)
3. **Nächste Woche:** Push Notification Integration (Iteration 2)
4. **Nach Review:** Multi-Turn Conversations planen (Iteration 3)

---

**Analyse abgeschlossen.** ✅  
**Output:** `/config/.openclaw/workspace/features/phase6-proposals-2026-03-01-1120.md`
