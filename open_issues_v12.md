# Offene Issues — PilotSuite v12 (Iteration 1440)

**Stand:** 2026-03-02  
**Review:** Security API Review  
**Gesamtanzahl:** 13 Issues (0 P0, 0 P1, 5 P2, 8 P3)

---

## P0 — Critical (Blocker) 🔴

**Keine P0 Issues gefunden.** ✅

---

## P1 — High Severity (Must Fix Before Release) 🔴

**Alle P1 Issues behoben!** ✅

### P1-01: WebSocket Authentication Missing
**Status:** ✅ **COMPLETE** (2026-03-02)  
**Component:** WebSocket Handler  
**Files:** 
- `copilot_core/websocket_handler.py`
- `copilot_core/api/v1/websocket_neuron.py`
- `copilot_core/api/security.py`

**Implementierung:**
- Token-Validierung in `handle_connect()` implementiert
- Token wird akzeptiert via:
  1. SocketIO auth dict: `{'token': '...'}`
  2. Query-Parameter: `?token=xxx`
  3. Header: `X-Auth-Token`
- Ungültige/fehlende Tokens werden abgelehnt (`return False`)
- Failed connection attempts werden geloggt
- Alle 11 WebSocket-Auth-Tests bestehen ✅

**Tests:**
- `tests/security/test_websocket_auth.py`: 11/11 Tests ✅
- Token validation from query param ✅
- Token validation from header ✅
- Rejects missing token ✅
- Rejects invalid token ✅
- Admin token requirements ✅

---

### P1-02: Neuron State Override Without Authorization
**Status:** ✅ **COMPLETE** (2026-03-02)  
**Component:** Neuron API  
**File:** `copilot_core/api/v1/neurons.py`

**Implementierung:**
- `require_admin_token()` in `copilot_core/api/security.py` implementiert
- State/Context Overrides erfordern Admin-Token
- Standard-Evaluation funktioniert mit normalem Token
- 403 für nicht-autorisierte Override-Versuche
- Override-Versuche werden geloggt

**Code-Stellen:**
- Zeile 184-194: State Override Protection
- Zeile 195-205: Context Override Protection
- Zeile 244: Update Neuron States Protection
- Zeile 381-392: Additional Override Points

**Tests:**
- `tests/security/test_websocket_auth.py::TestAdminTokenRequirement`: 5/5 Tests ✅
- `tests/security/test_input_validation.py`: 13/13 Tests ✅
- Gesamt: 24/24 Security-Tests ✅

---

## P2 — Medium Severity (Should Fix) 🟡

### P2-01: Missing Zone ID Input Sanitization
**Status:** ⚠️ OPEN  
**Component:** Media Zones API  
**File:** `copilot_core/api/v1/media_zones.py`

**Beschreibung:**
Zone ID path parameters used directly without validation/sanitization in multiple endpoints.

**Risk:** Path traversal, injection attacks  
**Fix:** Add regex validation: `^[a-zA-Z0-9_-]+$`  
**Estimate:** 1 hour  
**Endpoints Affected:** 15

---

### P2-02: Missing Rate Limiting on Proactive Endpoints
**Status:** ⚠️ OPEN  
**Component:** Media Zones API  
**File:** `copilot_core/api/v1/media_zones.py`

**Beschreibung:**
Proactive suggestion endpoints (`/proactive/zone-entry`, `/proactive/deliver`) lack rate limiting.

**Risk:** DoS via suggestion flooding, notification spam  
**Fix:** Apply rate limiting decorator from `api/rate_limit.py`  
**Estimate:** 2 hours  
**Endpoints Affected:** 4

---

### P2-03: Missing Neuron ID Validation
**Status:** ⚠️ OPEN  
**Component:** Neuron API  
**File:** `copilot_core/api/v1/neurons.py`

**Beschreibung:**
Neuron ID path parameters not validated for format or length.

**Risk:** Injection, unexpected behavior  
**Fix:** Validate format: `^[a-z_]+\.[a-z_]+$` or `^[a-z_]+$`  
**Estimate:** 1 hour  
**Endpoints Affected:** 3

---

### P2-04: Unbounded Mood History Query
**Status:** ⚠️ OPEN  
**Component:** Neuron API  
**File:** `copilot_core/api/v1/neurons.py`

**Beschreibung:**
`get_mood_history()` limit parameter only client-capped, no server-side maximum.

**Risk:** Performance degradation, potential DoS  
**Fix:** Add server-side cap: `limit = min(int(request.args.get("limit", "10")), 100)`  
**Estimate:** 30 minutes  
**Endpoints Affected:** 1

---

### P2-05: Missing WebSocket Room Name Validation
**Status:** ⚠️ OPEN  
**Component:** WebSocket Handler  
**File:** `copilot_core/api/v1/websocket_neuron.py`

**Beschreibung:**
Room names in `handle_join()` and `handle_subscribe()` not validated.

**Risk:** Injection, unauthorized room access  
**Fix:** Validate: `^[a-zA-Z0-9_-]+$` and max length 50  
**Estimate:** 1 hour  
**Endpoints Affected:** 2

---

## P3 — Low Severity (Nice to Have) 🟢

### P3-01: Verbose Error Messages
**Status:** ℹ️ OPEN  
**Component:** Multiple APIs  
**Files:** Various

**Beschreibung:**
Some error responses include full exception strings, potentially revealing internal structure.

**Risk:** Minor information disclosure  
**Fix:** Use generic error messages, log details server-side  
**Estimate:** 2 hours  
**Occurrences:** ~8 endpoints

---

### P3-02: Missing Failed Authentication Logging
**Status:** ℹ️ OPEN  
**Component:** Security Module  
**File:** `copilot_core/api/security.py`

**Beschreibung:**
Failed authentication attempts not logged, making brute force detection difficult.

**Risk:** Harder to detect attacks  
**Fix:** Add warning log in `validate_token()` on failure  
**Estimate:** 1 hour

---

### P3-03: Token Stored Unencrypted
**Status:** ℹ️ OPEN  
**Component:** Security Module  
**File:** `copilot_core/api/security.py`

**Beschreibung:**
Auth token stored in plaintext in `/data/options.json`.

**Risk:** If filesystem compromised, token exposed  
**Fix:** Consider encryption at rest or secrets manager  
**Estimate:** 1-2 days (requires infrastructure changes)

---

### P3-04: No Token Rotation Mechanism
**Status:** ℹ️ OPEN  
**Component:** Security Module  
**File:** `copilot_core/api/security.py`

**Beschreibung:**
Tokens have no expiration or rotation mechanism.

**Risk:** Long-lived tokens increase compromise window  
**Fix:** Add token expiry (e.g., 90 days) with rotation  
**Estimate:** 1 day

---

### P3-05: Missing Pagination on List Endpoints
**Status:** ℹ️ OPEN  
**Component:** Dashboard Cards API  
**File:** `copilot_core/api/v1/habitus_dashboard_cards.py`

**Beschreibung:**
`/rules` endpoint lacks pagination for large rule sets.

**Risk:** Performance issues with many rules  
**Fix:** Add offset/limit pagination  
**Estimate:** 2 hours

---

### P3-06: XSS Risk in Dashboard Card Generation
**Status:** ℹ️ OPEN  
**Component:** Dashboard Cards API  
**File:** `copilot_core/api/v1/habitus_dashboard_cards.py`

**Beschreibung:**
User-controlled data embedded in card templates without explicit escaping.

**Risk:** XSS if rules contain malicious scripts (requires frontend exploitation)  
**Fix:** Ensure frontend escapes all dynamic content  
**Estimate:** 2 hours (backend + frontend)

---

### P3-07: No Message Size Limits for WebSocket Events
**Status:** ℹ️ OPEN  
**Component:** WebSocket Handler  
**File:** `copilot_core/websocket_handler.py`

**Beschreibung:**
No validation on event payload size.

**Risk:** Large payloads could cause memory issues  
**Fix:** Add size check (e.g., max 10KB per event)  
**Estimate:** 1 hour

---

### P3-08: Hardcoded Time Windows in Dashboard Patterns
**Status:** ℹ️ OPEN  
**Component:** Dashboard Cards API  
**File:** `copilot_core/api/v1/habitus_dashboard_cards.py`

**Beschreibung:**
Fixed time windows ["24h", "7 days", "30 days"] not configurable.

**Risk:** Not a security issue, limits flexibility  
**Fix:** Make configurable via options.json  
**Estimate:** 2 hours

---

## Summary by Component

| Component | P1 | P2 | P3 | Total |
|-----------|----|----|----|-------|
| WebSocket Handler | 1 | 1 | 1 | 3 |
| Neuron API | 1 | 2 | 0 | 3 |
| Media Zones API | 0 | 2 | 0 | 2 |
| Dashboard Cards API | 0 | 0 | 3 | 3 |
| Security Module | 0 | 0 | 2 | 2 |
| General/Multiple | 0 | 0 | 2 | 2 |
| **TOTAL** | **2** | **5** | **8** | **15** |

---

## Action Plan

### Before v12.0 Release (Mandatory)
- [ ] **P1-01:** WebSocket Authentication
- [ ] **P1-02:** Neuron State Override Authorization

### v12.0.1 Patch (Week 2-3)
- [ ] **P2-01:** Zone ID Sanitization
- [ ] **P2-02:** Rate Limiting on Proactive Endpoints
- [ ] **P2-03:** Neuron ID Validation
- [ ] **P2-04:** Mood History Limit Cap
- [ ] **P2-05:** WebSocket Room Validation
- [ ] **P3-01:** Error Message Sanitization
- [ ] **P3-02:** Failed Auth Logging

### v12.1.0 Minor (Month 2)
- [ ] **P3-03:** Token Encryption at Rest
- [ ] **P3-04:** Token Rotation Mechanism
- [ ] **P3-05:** Pagination on List Endpoints
- [ ] **P3-06:** XSS Prevention (Frontend)
- [ ] **P3-07:** WebSocket Message Size Limits
- [ ] **P3-08:** Configurable Time Windows

---

## Testing Requirements

### Security Tests (Before Release)
- [ ] Verify WebSocket auth rejects unauthenticated connections
- [ ] Verify neuron state overrides require admin token
- [ ] Verify zone ID injection attempts rejected
- [ ] Verify rate limiting triggers on proactive endpoints
- [ ] Verify failed auth attempts logged (after P3-02 fix)

### Regression Tests
- [ ] All existing API tests pass
- [ ] WebSocket connections work with valid auth
- [ ] Normal neuron evaluation works without admin token
- [ ] Dashboard cards render correctly

---

## Contact

**Security Review Lead:** @groky  
**Questions:** WhatsApp +4917623565849  
**Next Review:** After P1 fixes implemented

---

*Last Updated: 2026-03-01 14:50 CET*
