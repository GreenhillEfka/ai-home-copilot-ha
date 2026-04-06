# Handoff: HA Branch Consolidation — 2026-04-07 00:45

**From:** Orakel (Lead-Orchestration)  
**To:** HomeClaw  
**Priority:** Blocker-Clearing  
**Constraint:** Exactly ONE next step — no meta-discussion, no config/model changes

---

## Current HA Lane State (Verified 2026-04-07 00:45)

### Branch Status
- **Working branch:** `feat/conflict-retry-q2`
- **Status:** 19 commits ahead of `origin/main`
- **Latest commit:** `9abdc1a0` — `feat(ha): add analytics_dashboard_card.py`
- **Previous commits:**
  - `0c5848c4` — `fix(ha): add German translations (de.json)`
  - `49884c4d` — `fix(ha): add missing requests to manifest.json requirements`
  - `0675ec97` — `chore: PilotSuite HA v1.0.0-rc2 — all tasks complete`
  - `b52b908c` — `test(ha): heat_pump_sensor projection contract — 29 cases (HA-159)`

### TASKLOG State
- **Last logged task:** HA-159 (heat_pump_sensor) — ✅ done
- **Next logged task:** HA-160 — `ev_charging_sensor.py` OR `media_sensors.py` Projection-Contract-Tests

### Drift Identified
- **`takeover/ha4-main-truth`** branch exists with different commit history (HA-156 at top: `6e1914f7`)
- **`feat/conflict-retry-q2`** is the active working branch (HA-157 through HA-159 logged here)
- **Risk:** Two parallel HA branches with overlapping but divergent histories

---

## Exact Next Step (HA-160)

**Task:** HA-160 — Continue Projection-Contract-Tests on `feat/conflict-retry-q2`

**Choose ONE sensor from remaining untested:**
1. `ev_charging_sensor.py` — Core-API-based (`/api/v1/regional/ev-charging` or similar)
2. `media_sensors.py` — HA-local (uses `hass.states.async_all("media_player")`)

**Decision Rule:**
- If sensor hits Core API (`_core_base_url()` + HTTP calls) → **Projection-Contract-Test** (same pattern as HA-157/158/159)
- If sensor uses HA-local state only → **Skip** or mark as `HA-local/threshold` (not Core-Projection)

**Required Output:**
1. Test file: `tests/test_<sensor>_projection.py`
2. Commit on `feat/conflict-retry-q2`
3. TASKLOG entry with: Cases count, Contract verification, Suite status (X/Y green), pre-commit status
4. Next exact task (HA-161 candidate)

**Do NOT:**
- Merge/rebase branches without explicit instruction
- Switch to `takeover/ha4-main-truth` unless explicitly told
- Create new branches
- Touch config/model/settings

---

## Branch Consolidation (Deferred)

**Note:** Branch consolidation (`feat/conflict-retry-q2` vs `takeover/ha4-main-truth`) is **not** this step.

**Consolidation will happen when:**
1. All remaining Projection-Contract-Tests are complete (~4 sensors left)
2. HA lane reaches natural pause (all Core-Projection sensors tested)
3. Orakel explicitly triggers consolidation as a separate coordination step

**Until then:** Continue on `feat/conflict-retry-q2` — momentum > perfect history

---

## Success Signal

- HA-160 committed on `feat/conflict-retry-q2`
- TASKLOG updated with evidence (test count, suite status, pre-commit green)
- Next task (HA-161) identified
- No branch switches, no meta-drift, no config changes

---

## Context for Resume

**Pattern (from HA-157/158/159):**
```python
# Contract-Mirror pattern
class <Sensor>Contract:
    # Mirror exact sensor logic: .get(key, default), None guards, type checks
    
@pytest.mark.parametrize(...)
def test_<sensor>_<case>():
    # Verify: native_value, icon, extra_state_attributes, edge cases
    # Global Contract: endpoint verification + no local semantic invention
```

**Test Suite Command:**
```bash
cd /config/clawd/team/worktrees/pilotsuite-styx-ha-current
pytest -q tests/test_<sensor>_projection.py
git add -f tests/test_<sensor>_projection.py  # if tests/ in .gitignore
git commit -m "test(ha): <sensor> projection contract — N cases verifying Core-truth-only projection (HA-160)"
```

**Pre-commit Gate:**
```bash
pre-commit run --all-files  # PS-151 drift guard must pass
```

---

**Timestamp:** 2026-04-07 00:45 Europe/Berlin  
**Orakel Coordination Step:** 15-min cron (b053afd0) — Branch drift identified, single next step given
