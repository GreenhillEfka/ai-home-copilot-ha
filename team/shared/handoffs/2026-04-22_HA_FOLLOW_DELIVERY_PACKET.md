# 2026-04-22 HA follow delivery packet

**Stand:** 2026-04-22 23:22 Europe/Berlin
**Owner:** HomeClaw
**Support packet:** DesignClaw
**Dependency:** pull only after `CORE-AUTO-203-B` lands.
**Route:** `CORE-AUTO-203-B -> HA-FOLLOW-DELIVERY -> E2E-CONSOLIDATION-01`

## Task id
`HA-FOLLOW-DELIVERY`

## Goal
Use only already-existing Home Assistant surfaces behind the landed Core notification-delivery seam. Make the delivery visible and steerable without inventing a new dashboard family or detached UI.

## Honest existing HA surfaces

### 1) Primary visual confirmation, native HA surface
This surface is built into Home Assistant itself, so there is no HA worktree file that owns the UI.

**Delivery owner files**
- `/config/clawd/team/worktrees/pilotsuite-styx-core-current/addons/pilotsuite/app/copilot_core/proactive_engine.py`
- `/config/clawd/team/worktrees/pilotsuite-styx-core-current/tests/test_core_auto_203_b_notification_delivery_contract.py`

**Why this is the first truthful visible landing**
- `CORE-AUTO-203-B` delivers to `/services/notify/persistent_notification`.
- That means the first honest HA-visible confirmation is the native Home Assistant persistent notification surface.
- No extra Lovelace or custom-card work is required to claim visibility.

### 2) HA-owned status projection, existing integration surface
**Files**
- `/config/clawd/team/worktrees/pilotsuite-styx-ha-current/custom_components/pilotsuite/sensors/notification_sensor.py`
- `/config/clawd/team/worktrees/pilotsuite-styx-ha-current/tests/test_notification_sensor_projection.py`
- `/config/clawd/team/worktrees/pilotsuite-styx-ha-current/custom_components/pilotsuite/__init__.py`

**Why this is honest**
- The sensor is a pure projection shell over the canonical Core APIs:
  - `/api/v1/notifications`
  - `/api/v1/notifications/digest`
- It already exposes a real HA entity surface for pending count, latest items, and digest breakdown.
- `__init__.py` keeps legacy unique-id migration continuity via `copilot_notifications`.

### 3) Existing config and steering surfaces
**Files**
- `/config/clawd/team/worktrees/pilotsuite-styx-ha-current/custom_components/pilotsuite/config_options_flow.py`
- `/config/clawd/team/worktrees/pilotsuite-styx-ha-current/custom_components/pilotsuite/zone_automation_entities.py`
- `/config/clawd/team/worktrees/pilotsuite-styx-ha-current/custom_components/pilotsuite/services.yaml`
- `/config/clawd/team/worktrees/pilotsuite-styx-ha-current/custom_components/pilotsuite/dashboard_wiring.py`
- `/config/clawd/team/worktrees/pilotsuite-styx-ha-current/tests/test_config_options_flow_projection.py`
- `/config/clawd/team/worktrees/pilotsuite-styx-ha-current/tests/test_dashboard_wiring_projection.py`
- `/config/clawd/team/worktrees/pilotsuite-styx-ha-current/tests/test_zone_automation_entities_projection.py`

**Why these are the honest controls**
- `config_options_flow.py` already exposes `automation_modes`, `habitus_zones`, `generate_dashboard`, and `publish_dashboard`.
- `zone_automation_entities.py` already creates per-zone HA select/switch/number controls so automation can be steered from existing HA entity surfaces.
- `services.yaml` already exposes `pilotsuite.zone_automation_set_mode`.
- `dashboard_wiring.py` is existing dashboard wiring infrastructure only, not a new delivery UI.
- There is no dedicated delivery-toggle UI today, so this packet must not invent one.

## Explicit non-surface, do not claim
**File**
- `/config/clawd/team/worktrees/pilotsuite-styx-ha-current/custom_components/pilotsuite/www/styx-household-card.js`

**Reason**
- The file header mentions notifications, but the current implementation does not consume `sensor.pilotsuite_notifications`.
- Therefore this packet must not claim an existing dashboard card for delivery visibility.

## Exact HA follow-through pull
1. Treat the native HA persistent notification as the primary visible confirmation behind `CORE-AUTO-203-B`.
2. If a file-backed HA consumer proof is required, stay on `notification_sensor.py` only.
3. If steering is needed, stay on the already-existing automation mode/config surfaces only.
4. Do not widen into new Lovelace cards, new dashboard tabs, or a delivery-specific config flow in this packet.

## Proof rings
### Core delivery landing
- `python3 -m py_compile addons/pilotsuite/app/copilot_core/proactive_engine.py tests/test_core_auto_203_b_notification_delivery_contract.py`
- `/config/clawd/.venv_smoke_gate/bin/python -m pytest -q tests/test_core_auto_203_b_notification_delivery_contract.py`

### HA visible projection
- `python3 -m py_compile custom_components/pilotsuite/sensors/notification_sensor.py`
- `.venv/bin/python -m pytest -q tests/test_notification_sensor_projection.py`

### HA config / steering surfaces
- `.venv/bin/python -m pytest -q tests/test_config_options_flow_projection.py tests/test_dashboard_wiring_projection.py tests/test_zone_automation_entities_projection.py`

## Success signals
- A real HA persistent notification is the first visible delivery confirmation.
- `sensor.pilotsuite_notifications` stays an honest projection of Core notification truth, not a locally invented status layer.
- Existing operator control remains on automation modes, zone controls, and current config flow surfaces.
- No speculative dashboard work and no detached second UI path are introduced.

## Next exact recommendation
Pull `HA-FOLLOW-DELIVERY` as: native persistent-notification confirmation plus `notification_sensor.py` projection proof, then stop. Only cut a separate follow-up packet if a real requirement appears to surface that entity inside an existing Lovelace entities card or dashboard section.
