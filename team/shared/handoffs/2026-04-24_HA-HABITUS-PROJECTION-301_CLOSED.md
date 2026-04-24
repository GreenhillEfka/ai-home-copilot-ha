# HA-HABITUS-PROJECTION-301 — closed

**Stand:** 2026-04-24 Europe/Berlin
**Owner:** HomeClaw
**Commit:** `e12c3abf` (`feat(ha): project habitus zones from canonical core seam`)

## Landed truth
- `habitus_zone_sensor` now consumes the canonical Core seam:
  - `GET /api/v1/habitus/zones?include_metrics=true`
- the HA sensor remains a pure projection, not a second semantic engine
- the bounded HA slice landed cleanly and the HA worktree is clean after commit

## Exact files
- `custom_components/pilotsuite/sensors/habitus_zone_sensor.py`
- `tests/test_habitus_zone_sensor_projection.py`

## Focused proof
```bash
python3 -m py_compile custom_components/pilotsuite/sensors/habitus_zone_sensor.py
.venv/bin/python -m pytest -q tests/test_habitus_zone_sensor_projection.py
```

## Proof result
- syntax: PASS
- projection proof ring: `21 passed`

## User-visible effect
PilotSuite now has a truthful HA-owned Zone/Habitus overview sensor projected from the canonical Core habitus/zones seam.

## Queue effect
`HA-HABITUS-PROJECTION-301` is closed.
Next exact pull: `TRUTH-RECONCILE-302`.
