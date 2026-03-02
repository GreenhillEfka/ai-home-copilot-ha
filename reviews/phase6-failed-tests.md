# Phase 6 - Fehlgeschlagene Tests Analyse

**Datum:** 2026-03-02  
**Gesamtanzahl FAILED:** 371 Tests  
**Gesamtanzahl PASSED:** 2888 Tests  
**Gesamtlaufzeit:** ~63 Sekunden

## Hauptfehlerursachen (Priorisiert)

### P0: Auth-Mocking in Test-Fixtures (KRITISCH)
**Betroffene Tests:** ~100+ Tests  
**Fehlerbild:** `assert 403 == 200` oder `TypeError: unsupported operand types(s) for hmac.compare_digest`

**Ursache:** Tests mocken `_validate_token` statt `require_admin_token` oder `validate_token` aus dem security-Modul. Dadurch schlagen Auth-Checks fehl.

**Betroffene Dateien:**
- `tests/test_neurons_api.py` ✅ **FIXED**
- `tests/test_auth_security.py`
- `tests/test_websocket_auth.py`
- `tests/test_neuron_auth.py`
- `tests/test_neuron_visualization.py`

**Lösung:** Mocking muss `security.require_admin_token` und `security.validate_token` patchen, NICHT modul-interne Funktionen.

---

### P0: Fehlende Endpoints (404 Errors)
**Betroffene Tests:** ~150+ Integrationstests  
**Fehler:** `assert 404 == 200`

**Ursache:** Tests erwarten Endpoints, die nicht implementiert oder nicht im Blueprint registriert sind.

**Betroffene Endpoints:**
- `/api/llm/*` - LLM Provider API (nicht implementiert)
- `/api/rag/*` - RAG Search API (teilweise implementiert)
- `/api/v1/neurons/*` - Neuron API (implementiert, aber Auth-Probleme)
- `/api/v1/notifications/*` - Notifications API (implementiert)
- `/api/v1/zones/*` - Zone Editor API (implementiert)

**Lösung:** 
1. Fehlende Endpoints implementieren ODER
2. Tests als "skip" markieren bis Implementierung erfolgt

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

## Zusammenfassung der Fix-Prioritäten

| Priorität | Kategorie | Anzahl Tests | Status |
|-----------|-----------|--------------|--------|
| P0 | Auth-Mocking (neurons_api) | 31 | ✅ FIXED |
| P0 | Auth-Mocking (restliche) | ~70 | TODO |
| P0 | Fehlende Endpoints | ~150 | TODO |
| P1 | Import Errors | ~5 | TODO |
| P1 | Cache Implementation | ~5 | TODO |
| P2 | Zone Editor/API | ~50 | TODO |
| P2 | Notifications | ~30 | TODO |
| P2 | RAG Search | ~40 | TODO |

## Nächste Schritte

1. ✅ **test_neurons_api.py Auth-Mocking fixed** - Patch security.require_admin_token
2. **Auth-Mocking in anderen Dateien fixen** - Gleiches Pattern anwenden
3. **Fehlende Endpoints identifizieren** - Skip-Marker für nicht-implementierte Features
4. **Cache-Interface reparieren** - get_habitus_cache exportieren
