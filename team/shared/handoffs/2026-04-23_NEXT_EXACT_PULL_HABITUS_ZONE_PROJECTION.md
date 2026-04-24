# 2026-04-23 Next exact pull — Habitus zone projection

**Stand:** 2026-04-23 Europe/Berlin
**Why now:** `HA-FOLLOW-DELIVERY` is closed, `E2E-CONSOLIDATION-01` is treated as proven in current file truth, and the live HA worktree already contains a bounded dirty seam around `habitus_zone_sensor`. That makes this the cleanest next exact pull to either land or discard fast.

## Current truth
- Core hardening wave is landed through `CORE-HARDEN-215`.
- `HA-FOLLOW-DELIVERY` is file-backed closed.
- `E2E-CONSOLIDATION-01` is treated as green in the ledger.
- HA worktree is not clean:
  - `custom_components/pilotsuite/sensors/habitus_zone_sensor.py`
  - `tests/test_habitus_zone_sensor_projection.py`

## Exact owner
**HomeClaw**

## Exact bounded slice
Bring `habitus_zone_sensor` onto the canonical Core habitus/zones surface and prove it as a pure HA projection.

### Canonical path
`Core /api/v1/habitus/zones -> HA habitus_zone_sensor projection`

### Exact files
- `/config/clawd/team/worktrees/pilotsuite-styx-ha-current/custom_components/pilotsuite/sensors/habitus_zone_sensor.py`
- `/config/clawd/team/worktrees/pilotsuite-styx-ha-current/tests/test_habitus_zone_sensor_projection.py`

## Pull rule
Before code/landing decision:
1. confirm the dirty diff is still bounded to this seam only
2. if bounded, finish it
3. if not bounded, cut it back to this seam only or discard it

Then run:
`exact pull -> focused proof -> commit -> checkpoint`

## Focused proof ring
Run in `/config/clawd/team/worktrees/pilotsuite-styx-ha-current`:

```bash
python3 -m py_compile \
  custom_components/pilotsuite/sensors/habitus_zone_sensor.py

.venv/bin/python -m pytest -q \
  tests/test_habitus_zone_sensor_projection.py
```

## Success signal
This pull is complete only if all of the following are true:
1. `habitus_zone_sensor` consumes the canonical Core habitus/zones endpoint only
2. the sensor remains a projection, not a second semantic engine
3. the proof ring is green
4. the HA worktree is clean after commit
5. ledger/checkpoint truth can state exactly what user-visible zone/habitus overview now exists

## Non-goals
- no new dashboard/card family
- no notification widening
- no new automation family
- no config-flow expansion unless strictly required by this sensor seam
- no speculative Core work

## Honest follow-up after this pull
After this lands or is discarded cleanly, the next likely exact packet should be one of:
1. **interactive delivery follow-up** (ack/action/clear path)
2. **durable delivery semantics** (retry/idempotency/delivery intent)
3. **structured E2E observability** (`trigger -> decision -> delivery -> HA confirmation`)

## Routing effect
- **HomeClaw:** active writer on this pull
- **PilotClaw:** no side work; hold until the next Core seam is cut from fresh truth
- **DesignClaw:** support-only if a bounded visual/config unblock is explicitly needed
- **Orakel:** keep routing/result cards tight; no stale path reopening
