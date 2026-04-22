# 2026-04-22 HA follow delivery packet

**Stand:** 2026-04-22 23:32 Europe/Berlin
**Owner:** HomeClaw
**Trigger:** `HA-GATE-CHECK` determined that `HA-559` is stale historical truth and must not be reopened.
**Dependency:** pull only after `CORE-AUTO-203-B` lands.

## Task id
`HA-FOLLOW-DELIVERY`

## User/product goal
Mirror the real Core notification-delivery landing in one truthful HA-visible consumer seam, so delivery status is visible in Home Assistant on the existing notification surface instead of inventing a new side UI.

## Exact seam
Existing HA notification consumer/projection path only.

## Exact files
- `/config/clawd/team/worktrees/pilotsuite-styx-ha-current/custom_components/pilotsuite/sensors/notification_sensor.py`
- `/config/clawd/team/worktrees/pilotsuite-styx-ha-current/tests/test_notification_sensor_projection.py`

## Why this seam
- It already consumes the canonical Core notification APIs:
  - `/api/v1/notifications`
  - `/api/v1/notifications/digest`
- It is already a truthful HA-visible surface for pending notifications and digest breakdown.
- It matches the allowed `HA-FOLLOW-DELIVERY` shape from the bound sequence: visible notification confirmation / exact status projection tied to the landed delivery seam.

## Focused proof ring
- `python3 -m py_compile custom_components/pilotsuite-styx-ha-current/custom_components/pilotsuite/sensors/notification_sensor.py`
- `.venv/bin/python -m pytest -q tests/test_notification_sensor_projection.py`

## Success signal
- The HA-visible notification surface consumes the post-`CORE-AUTO-203-B` delivery seam honestly.
- No new dashboard family or detached UI path is introduced.
- Notification count/latest/digest projection stays green on the canonical consumer path.

## Non-goals
- do not reopen `HA-559`
- no speculative dashboard work
- no unrelated configuration flow edits
- no second HA side path

## Next exact pull after landing
`E2E-CONSOLIDATION-01`
