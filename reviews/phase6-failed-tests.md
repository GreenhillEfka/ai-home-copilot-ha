# Phase 6 - Fehlgeschlagene Tests Analyse

**Datum:** 2026-03-02  
**Gesamtanzahl FAILED:** ~280 Tests

## Hauptfehlerursachen (Priorisiert)

### P0: Falsches Mocking in Test-Fixtures (KRITISCH)
**Betroffene Tests:** ~200+ Integrationstests  
**Fehlerbild:** `AssertionError: assert <MagicMock name='mock.Flask().test_client()...'> == 200`

**Ursache:** Tests verwenden `mock.Flask()` und `mock.test_client()` statt der echten Flask-App. Dadurch werden alle Response-Objekte zu MagicMock-Objekten, die keine echten status_code Werte haben.

**Betroffene Dateien:**
- `tests/integration/test_api_auth_integration.py`
- `tests/integration/test_llm_provider_integration.py`
- `tests/integration/test_mcp_server_integration.py`
- `tests/integration/test_neural_network_integration.py`
- `tests/integration/test_notification_system_integration.py`
- `tests/integration/test_rag_search_integration.py`
- `tests/integration/test_system_health_integration.py`
- `tests/test_auth_security.py`
- `tests/test_websocket_auth.py`
- `tests/test_notifications_flask_integration.py`
- `tests/test_zone_dashboard.py`
- `tests/test_zone_editor.py`
- `tests/test_zone_editor_api.py`

**Lösung:** Test-Fixtures müssen die echte Flask-App verwenden, nicht mocken.

---

### P0: Security Module - TypeError bei hmac.compare_digest
**Betroffene Tests:**
- `tests/test_auth_security.py::TestSecurityModule::test_validate_token_rejects_wrong_token`
- `tests/test_auth_security.py::TestSecurityModule::test_validate_token_with_bearer_token`
- `tests/test_auth_security.py::TestSecurityModule::test_validate_token_with_x_auth_token_header`
- `tests/test_auth_security.py::TestWebSocketSecurity::*`

**Fehler:** `TypeError: unsupported operand types(s) or combination of types: 'MagicMock' and 'str'`

**Ursache:** In `copilot_core/api/security.py:95` und `:164` wird `header_token` oder `query_token` als MagicMock übergeben, weil das Request-Objekt gemockt ist.

**Lösung:** Request-Mocks müssen korrekte String-Werte für Token-Header zurückgeben.

---

### P0: Fehlende Endpoints (404 Errors)
**Betroffene Tests:**
- `tests/test_anomaly_detection.py::TestAnomalyAPI::test_detect_endpoint`
- `tests/test_anomaly_detection.py::TestAnomalyAPI::test_model_status_endpoint`
- `tests/test_anomaly_detection.py::TestAnomalyAPI::test_sensor_health_endpoint`

**Fehler:** `assert 404 == 200`

**Ursache:** Endpoints sind nicht im Blueprint registriert oder Blueprint ist nicht korrekt eingebunden.

---

### P1: Import Errors
**Betroffene Tests:**
- `tests/test_cache_integration.py::TestHabitusCacheIntegration::test_habitus_cache_import`

**Fehler:** `ImportError: cannot import name 'get_habitus_cache' from 'copilot_core.cache'`

**Ursache:** Funktion existiert nicht im `__init__.py` oder wurde umbenannt.

---

### P1: KeyError in Cache Stats
**Betroffene Tests:**
- `tests/test_cache_integration.py::TestSensorCacheIntegration::test_sensor_cache_flow`

**Fehler:** `KeyError: 'size'`

**Ursache:** Cache-Stats-Dictionary hat keinen 'size' Schlüssel.

---

### P1: Fehlende Attribute/Methoden
**Betroffene Tests:**
- `tests/test_cache_integration.py::TestRAGCacheIntegration::test_bm25_cache_methods`

**Fehler:** `assert hasattr(bm25, '_get_cache_key')` ist False

**Ursache:** BM25SqliteIndex hat die Methode `_get_cache_key` nicht implementiert.

---

### P2: Transaction Log Tests - AttributeError
**Betroffene Tests:**
- `tests/test_log_fixer_tx.py::*`

**Fehler:** `AttributeError` in Transaction-Log-Tests

---

### P2: Neuron Auth Tests
**Betroffene Tests:** ~10 Tests in `test_neuron_auth.py`

**Fehler:** Authorization-Checks schlagen fehl, Endpoints geben falsche Status-Codes zurück.

---

### P2: Neuron Visualization Tests
**Betroffene Tests:** ~15 Tests in `test_neuron_visualization.py`

**Fehler:** Unauthorized/Authorized Tests schlagen fehl.

---

### P2: Neurons API Tests
**Betroffene Tests:** ~20 Tests in `test_neurons_api.py`

**Fehler:** Various AssertionErrors bei Response-Checks.

---

### P2: RAG Hybrid API Tests
**Betroffene Tests:** ~30 Tests in `test_rag_hybrid_api.py`

**Fehler:** Endpoints geben falsche Status-Codes oder Missing Keys.

---

### P2: RAG Hybrid Search Tests
**Betroffene Tests:** ~20 Tests in `test_rag_hybrid_search.py`

---

### P2: Role Delegation API Tests
**Betroffene Tests:** ~15 Tests in `test_role_delegation_api.py`

---

### P2: Notifications Flask Integration Tests
**Betroffene Tests:** ~30 Tests in `test_notifications_flask_integration.py`

---

### P2: Zone Dashboard Tests
**Betroffene Tests:** ~40 Tests in `test_zone_dashboard.py`

---

### P2: Zone Editor Tests
**Betroffene Tests:** ~30 Tests in `test_zone_editor.py` und `test_zone_editor_api.py`

---

## Zusammenfassung der Fix-Prioritäten

| Priorität | Kategorie | Anzahl Tests | Aufwand |
|-----------|-----------|--------------|---------|
| P0 | Mocking-Fixtures | ~200 | Hoch |
| P0 | Security Module | ~10 | Mittel |
| P0 | Fehlende Endpoints | ~3 | Niedrig |
| P1 | Import Errors | ~5 | Niedrig |
| P1 | Cache Implementation | ~5 | Mittel |
| P2 | Auth/Authorization | ~30 | Mittel |
| P2 | API Endpoint Tests | ~50 | Mittel |

## Nächste Schritte

1. **Test-Fixtures reparieren** - Echte Flask-App statt mock.Flask() verwenden
2. **Security Module fixen** - Korrekte Token-Extraktion aus Requests
3. **Fehlende Endpoints registrieren** - Anomaly Detection Blueprint
4. **Cache-Interface komplettieren** - get_habitus_cache exportieren, _get_cache_key implementieren
