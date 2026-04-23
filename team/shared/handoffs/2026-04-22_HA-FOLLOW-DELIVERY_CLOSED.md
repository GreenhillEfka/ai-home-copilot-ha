# HA-FOLLOW-DELIVERY — bounded consumer seam behind CORE-AUTO-203-B

**Stand:** 2026-04-22 23:42 Europe/Berlin
**Owner:** HomeClaw
**Bounded slice:** notification_sensor.py + native HA surfaces only

---

## CORE-AUTO-203-B delivery seam (landed)

**Commit:** `a8d0a7e7` (already in Core HEAD `21f8a2de`)
**File:** `addons/pilotsuite/app/copilot_core/proactive_engine.py`
**Delivery target:** `POST http://supervisor/services/notify/persistent_notification`
**Contract tests:** `tests/test_core_auto_203_b_notification_delivery_contract.py` → **4 passed**

Core liefert proaktive Notifications via HA Supervisor API → native HA persistent notification surface.

---

## HA consumer surfaces (existing, no new code)

### 1) Native HA persistent notification (no HA worktree file owns this)
First visible delivery confirmation is native HA persistent notification.
No Lovelace card, no custom dashboard work.

### 2) notification_sensor.py projection
**File:** `custom_components/pilotsuite/sensors/notification_sensor.py`
**Endpoints consumed:**
- `GET /api/v1/notifications?limit=10` → `pending_count`, `latest[]`
- `GET /api/v1/notifications/digest?hours=24` → `digest_count`, `by_source`, `by_priority`

**Proof:** `.venv/bin/python -m pytest -q tests/test_notification_sensor_projection.py tests/test_config_options_flow_projection.py tests/test_dashboard_wiring_projection.py tests/test_zone_automation_entities_projection.py` → **52 passed**
**Syntax:** `python3 -m py_compile custom_components/pilotsuite/sensors/notification_sensor.py` → **PASS**

### 3) Automation mode / zone control surfaces (existing, no new code)
- `config_options_flow.py` → `automation_modes`, `habitus_zones`
- `zone_automation_entities.py` → per-zone HA select/switch/number controls
- `services.yaml` → `pilotsuite.zone_automation_set_mode`

**Steering confirmation:** existing operator controls are sufficient, no new delivery-toggle UI.

---

## Proof summary

| Surface | Command | Result |
|---------|---------|--------|
| notification_sensor.py syntax | `python3 -m py_compile custom_components/pilotsuite/sensors/notification_sensor.py` | PASS |
| HA follow proof ring | `.venv/bin/python -m pytest -q tests/test_notification_sensor_projection.py tests/test_config_options_flow_projection.py tests/test_dashboard_wiring_projection.py tests/test_zone_automation_entities_projection.py` | 52 passed |
| Core delivery contract | `/config/clawd/.venv_smoke_gate/bin/python -m pytest -q tests/test_core_auto_203_b_notification_delivery_contract.py` | 4 passed |
| Core proactive_engine syntax | `python3 -m py_compile addons/pilotsuite/app/copilot_core/proactive_engine.py` | PASS |

---

## Honest non-surfaces (do not claim)
- `www/styx-housecard.js` — does not consume `sensor.pilotsuite_notifications`
- No new Lovelace card, no new dashboard tab, no delivery-specific config flow

---

## Queue position
`HA-FOLLOW-DELIVERY` closed. Next exact pull is `E2E-CONSOLIDATION-01` (PilotClaw + HomeClaw on own seams).
HomeClaw holds for next Andreas decision.
