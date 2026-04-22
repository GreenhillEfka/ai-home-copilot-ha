## 2026-04-22 23:44 — CORE-AUTO-203-B notification delivery proof-closeout landed cleanly on the exact proactive seam

**Exact seam:** `addons/pilotsuite/app/copilot_core/proactive_engine.py`
**Proof ring:** `tests/test_core_auto_203_b_notification_delivery_contract.py`

**Focused proof:**
- `python3 -m py_compile addons/pilotsuite/app/copilot_core/proactive_engine.py` → PASS
- `/config/clawd/.venv_smoke_gate/bin/python -m pytest -q tests/test_core_auto_203_b_notification_delivery_contract.py` → `4 passed in 0.08s`

**Success signal reached:**
- delivery stays on the canonical notification seam only
- no-token failure, bearer-auth delivery, request-failure path, and HTTP-failure path are green
- no MQTT widening, no dashboard widening, no second action family was opened

**Checkpoint:**
- active pull `CORE-AUTO-203-B` is closed cleanly on fresh canonical truth
- next exact pull advances to `HA-FOLLOW-DELIVERY`

## 2026-04-22 21:18 — CORE-HARDEN-204 naming (entity adoption API contract)

**Exact seam:** `addons/pilotsuite/app/copilot_core/api/v1/entity_adoption.py`
**Problem:** 11 endpoints (zone entity truth, assignment create/remove, refresh, room↔zone mapping, stats, lookup), 0 dedicated API contract tests, critical zone/entity ownership path

**Proof ring:** `tests/test_entity_adoption_api_contract.py`
- `GET /api/v1/entity-adoption/zones` → 200 + zone list structure
- `GET /api/v1/entity-adoption/zones/<zone_id>/entities` → 200 + entity list structure
- `POST /api/v1/entity-adoption/assign` → 200 + assignment payload
- `DELETE /api/v1/entity-adoption/assign/<assignment_id>` → 200/404 contract path
- `GET /api/v1/entity-adoption/stats` → 200
- Unauthorized requests → 401

**Success signal:**
- `tests/test_entity_adoption_api_contract.py` → ALL PASS
- `python3 -m py_compile addons/pilotsuite/app/copilot_core/api/v1/entity_adoption.py` → PASS

**Queue state:** `CORE-HARDEN-206` proof ring already visible in core worktree (`tests/test_notifications_api_contract.py`, commit `89118bc4`) → `CORE-HARDEN-204` exact next Core pull unless fresh `HA-E2E-303` landing arrives first