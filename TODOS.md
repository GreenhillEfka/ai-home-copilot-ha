# TODOS.md - PilotSuite Styx

## P0 (Critical)

- [x] Error Isolation – ✅ COMPLETE (v12.0.0+)
  - Circuit Breaker Pattern implementiert (`circuit_breaker.py`)
  - HA Supervisor und Ollama Breaker mit automatischer Recovery
  - Tests: 20/20 passing (`test_circuit_breaker.py`)
  
- [x] Connection Pooling – ✅ COMPLETE (v12.0.0+)
  - aiohttp.ClientSession Pooling (`connection_pool.py`)
  - Configurable pool size (default: 10 connections)
  - Health checks und Metrics
  - Tests: 23/23 passing (`test_connection_pool.py`)

## P1 (Important)

- [ ] Scene Pattern Extraction – aus User-Verhalten (Szenen-Aktivierung) Muster lernen
- [ ] Routine Pattern Extraction – tageszeitbasierte/wochentagsbasierte Rückschlüsse
- [x] Push Notifications – ✅ COMPLETE (Phase 5, v12.0.0)
  - 9 Endpoints (`/api/v1/notifications/*`)
  - Device Subscriptions, HA Integration
  - Tests: 23/23 passing

## P2 (Nice to have)

- [ ] MCP Phase 2 – erweiterte Skills für AI-Clients
- [x] Test Suite Expansion – ✅ 2569 Tests total (98%+ pass rate)
  - Connection Pooling: 23 Tests
  - Circuit Breaker: 20 Tests
  - Phase 5/6 APIs: 76 Tests
  - Full Suite: 2526+ Tests
- [ ] Multi-User Preference Learning – MUPL深化 (bereits v0.8.x integriert, aber erweiterbar)

---

## Notes

*Last updated: 2026-03-02*
*Based on Styx v12.0.0+*

### P0 Implementation Details

**Error Isolation (Circuit Breaker):**
- File: `copilot_core/circuit_breaker.py`
- States: CLOSED → OPEN → HALF_OPEN → CLOSED
- HA Supervisor: 5 failures threshold, 30s recovery
- Ollama: 3 failures threshold, 60s recovery
- Thread-safe implementation

**Connection Pooling:**
- File: `copilot_core/connection_pool.py`
- aiohttp.TCPConnector mit limit=10, limit_per_host=10
- Session reuse statt neuer Connections pro Request
- Health checks alle 60s (configurable)
- Metrics: requests_total, connections_reused, reuse_rate_pct

---
