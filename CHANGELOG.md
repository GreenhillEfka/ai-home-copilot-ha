# CHANGELOG

## v7.11.1 (2026-02-28)

### Test Coverage Completion
- **Flask Integration Tests** für alle Phase 5 APIs vervollständigt:
  - Notifications API: 22 Tests (100% grün)
  - Collective Intelligence API: 22 Tests (100% grün)
  - Sharing API: 28 Tests (bereits bestehend)
  - **Gesamt: 95 Tests bestanden** ✅
- **Fixes implementiert**:
  - `get_federated_service()` zu `copilot_core/__init__.py` hinzugefügt
  - Mock-Fix für `test_get_knowledge_base` (JSON-Serialisierung)
  - Test-Assertions an API-Response-Format angepasst
- **Type Hints** vervollständigt:
  - Notifications API: Vollständige Type Hints für alle Endpoints
  - Collective Intelligence API: Vollständige Type Hints für alle Endpoints
  - Return-Typen: `Tuple[Dict[str, Any], int]` für alle Flask-Endpoints

### Code Quality
- Alle 95 Phase 5 Integration Tests laufen grün
- CI/CD-ready für Production-Deployment
- Type-safe Code mit vollständigen Annotations

---

## v7.11.0 (2026-02-28)

### Notifications API Enhancement
- **Push-Notification Templates** hinzugefügt:
  - Wiederverwendbare Template-Strukturen mit Platzhaltern
  - Built-in Templates: Energy Anomaly, Schedule Reminder, Comfort Suggestion, Security Alert
  - Template-Registry mit CRUD-Operationen
  - `send-with-template` Endpoint für template-basierte Notifications
- **Priority Levels** implementiert (low/medium/high/critical):
  - String-based PriorityLevel Enum
  - Abwärtskompatibilität zu legacy int-Priorities (1-4)
  - Konvertierungsfunktionen zwischen Formaten
- **Scheduling-Funktion** für verzögerte Notifications:
  - Scheduler mit konfigurierbarem Check-Interval
  - Unterstützung für absolute Zeitpunkte (deliver_at) und relative Verzögerungen (delay_minutes)
  - Cancel-Funktion für geplante Notifications
  - Background-Thread für automatische Zustellung
- Neue API-Endpoints:
  - `GET/POST /api/v1/notifications/templates` - Templates verwalten
  - `GET/DELETE /api/v1/notifications/templates/<id>` - Template abrufen/löschen
  - `POST /api/v1/notifications/send-with-template` - Template-basierte Notification senden
  - `POST /api/v1/notifications/schedule` - Notification planen
  - `GET /api/v1/notifications/scheduled` - Geplante Notifications abrufen
  - `DELETE /api/v1/notifications/scheduled/<id>` - Geplante Notification stornieren

### Sharing Module Tests
- **Integrationstests** für `/api/v1/sharing/*` Endpoints:
  - Vollständige API-Abdeckung für Registry, Sync und Discovery
  - Cross-Home Sync-Szenarien mit mehreren Homes
  - Entity-Sharing mit multiplen Ziel-Home-IDs
  - Versions-Tracking bei Updates
- **Mock-Tests** für Cross-Home Sync-Szenarien:
  - Multi-Peer-Synchronisation
  - Peer-Version-Kompatibilitätsprüfungen
  - Sync-Log-Tracking
  - Edge-Case-Behandlung (404, 400 Fehler)
- Test-Dateien:
  - `test_sharing_integration.py` - 40+ Tests für API-Integration
  - Erweiterte Mock-Services für realistische Testszenarien

### Performance-Optimierung
- **Database Query Optimization** für Federated Learning Endpoints:
  - QueryOptimizer mit automatischem Caching
  - Pattern-basierte Cache-Invalidierung
  - Query-Statistiken und Performance-Monitoring
  - Konfigurierbare TTL-Werte pro Query
- **Caching** für häufig abgerufene Sharing-Entities:
  - LRU-Cache mit TTL-Unterstützung
  - Spezialisierte Caches für Models, Updates und Rounds
  - Batch-Optimierung: Partial Cache Hits werden automatisch nachgeladen
  - Thread-sichere Implementierung
- Neue Module:
  - `performance/optimization.py` - Zentrale Optimierungskomponenten
  - `LRUCache` - Wiederverwendbare LRU-Cache-Implementierung
  - `FederatedLearningOptimizer` - FL-spezifische Optimierungen
  - `SharingEntityCache` - Sharing-Entity-Caching
- Statistiken und Monitoring:
  - Cache-Hit-Rates
  - Query-Durchlaufzeiten (min/max/avg)
  - Cache-Größen und Auslastung

### Files Changed
- `copilot_core/notifications/templates.py` (neu) - Template & Scheduling Engine
- `copilot_core/api/v1/notifications.py` - Erweitert um Template & Scheduling Endpoints
- `copilot_core/performance/optimization.py` (neu) - Performance-Optimierung
- `tests/test_notifications_templates.py` (neu) - Template & Scheduling Tests
- `tests/test_sharing_integration.py` (neu) - Sharing Integration Tests
- `tests/test_performance_optimization.py` (neu) - Performance Tests

### Tests
- 80+ neue Tests für v7.11.0 Features
- Vollständige Abdeckung der neuen API-Endpoints
- Integrationstests für Cross-Home Szenarien
- Performance-Benchmarks für Caching

---

## v7.10.2 (2026-02-24)
- Version bump to v7.10.2 — sync with main branch merge
- Fixed pyproject package name to `ai_home_copilot_client`
- Resolved import errors in SDK tests
- Synchronized core and HA versions

## v7.10.1 (2026-02-24)
- Auto-release: System integrity checks and minor fixes
- Updated version in config and manifest

## v7.10.0 (2026-02-24)
- Plugin system v1 — base classes, search/llm plugins, React backend API
- Search plugin via SearXNG (local, HTML parser)
- LLM plugin — Ollama/Cloud integration
- Web UI toggle API (`/api/plugins/*`)
- HA manifest.json extended with `searxng_enabled`, `searxng_base_url`

## v7.9.2 (2026-02-24)
- Bugfix: connection pooling in llm_provider
- Feature: SearXNG integration for web search

## v7.9.1 (2026-02-24)
- Added SearXNG search plugin (plugins/search/) for local web search
- Added HA-conform manifest.json with optional searxng config
- Cleaned up dev branches — all releases now go directly to main
- HA hassfest compliant structure

## v7.8.13 (2026-02-24)
- Cross-Home Sharing + Autopilot Runner v0.1.0

## v7.8.12 (2026-02-24)
- Phase 5: NotificationSensor + SceneIntelligenceSensor
- 31 API endpoints registered

## v7.8.11 (2026-02-23)
- Fixed error isolation and connection pooling
- Added unit tests for error boundary and status tracking
