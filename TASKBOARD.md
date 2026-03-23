# PilotSuite HA/HACS Taskboard

## Directive (2026-03-22)
- **Owner:** HomeClaw
- **Restore support:** DesignClaw
- **Scope:** `pilotsuite-styx-ha`
- **Authority:** HomeClaw has holistic autonomous ownership of this HA repo and the final say for Home Assistant / HACS.
- **Routing split (reaffirmed by Andreas, 2026-03-22):** HA/HACS direction and implementation questions route to **HomeClaw**. Core/Add-on direction and implementation questions route to **PilotClaw**.

## Current mission
Bring the HA/HACS lane back to a coherent state where:
- the intended HA ↔ Core architecture is explicit again,
- deleted docs do not erase prior design intent,
- HA can sync zones/modules into Core cleanly,
- HACS packaging truth is not regressed during recovery.

---

## Restore status snapshot

### Architecture / intent
- [x] Read surviving repo markdown context and recovered deleted architectural context from git history.
- [x] Reconstructed the canonical boundary: **HA/HACS = HA adapter + visualization layer; Core = semantic + zone-automation truth layer.**
- [x] Wrote `docs/HA_CONCEPT_DIRECTIVE.md` as the restored baseline.

### Live/Core evidence
- [x] Verified live Core health from this host: `/health` returns **`15.0.4`**.
- [x] Verified live Core route existence:
  - `POST /api/v1/zone-automation/ensure-zones` → **401** without auth
  - `POST /api/v1/zone-automation/sync-definitions` → **401** without auth
  - `GET /api/v1/zone-automation/module-schemas` → **200**
- [x] Verified live Core dashboard currently reports **0 zones**.
- [x] Conclusion updated: the current blocker is **not** “missing `/sync-definitions` route”; it is failed/unverified authenticated HA→Core sync and/or HA integration reload/runtime state.

### Recovery docs / handoff
- [x] Wrote `docs/RECOVERY_RESTORE_STATUS.md`
- [x] Wrote `docs/HA_RESTORE_HANDOFF.md`
- [x] Updated this taskboard with concrete restore steps/status

### Small safe support changes
- [x] Fixed zone payload normalization in:
  - `custom_components/copilot_ha/agent_scripts/health_check.py`
  - `custom_components/copilot_ha/agent_scripts/fixer.py`
- [x] Validated those script edits with `python3 -m py_compile`

### Still open
- [ ] Confirm HA integration is loading/reloading cleanly in the live HA runtime
- [ ] Confirm Configure/Reconfigure now opens cleanly in the live HA runtime after the `merge_config_data(...)` import hotfix
- [ ] Confirm whether any remaining `config_options_flow.py` tracebacks are separate from the now-confirmed `config_flow.py` NameError path
- [ ] Confirm `_first_zone_sync()` is actually firing after reload
- [ ] Confirm Core dashboard moves from `0 zones` to non-zero after HA-triggered sync
- [ ] Confirm HACS metadata drift in working-tree `manifest.json` is resolved before any release action

### Newly confirmed live/runtime issues (2026-03-23)
- [x] Confirmed direct Configure/Reconfigure failure path: `config_flow.py` used `merge_config_data(...)` without importing it.
- [x] Confirmed direct zone auto-setup failure path: `zone_auto_setup.py` used `validate_mapping(...)` without importing it.
- [x] Live log `Failed to auto-create Habitus Zones` now has a concrete HA-side code-path match in that missing `validate_mapping(...)` import.
- [x] Confirmed area→zone mapping file read sat on an async startup path; async loader helper added for the auto-setup path.
- [~] `button_update_check.py` blocking VERSION-read issue appears already covered by an earlier repo fix and should be preserved, not regressed.
- [~] `config_options_flow.py` still appears in live error reports, but the directly confirmed repo-level failure is presently in `config_flow.py`; treat OptionsFlow as adjacent follow-up, not yet the primary proven cause.
- [~] `Knowledge Graph sync: No API client available` is a real runtime warning, but currently looks secondary to the HA config/auto-setup failures.
- [x] RAM/OOM is currently a weak hypothesis (~43.9% RAM used, ~17.7 GB free) and should stay deprioritized behind the HA code-path failures above.

---

## Critical findings to preserve

1. **Deleted docs did not delete the architecture.**
   Recovered deleted material still supports the same boundary: two surfaces, one contract.

2. **Old recovery notes about `/sync-definitions` being missing are stale for the current runtime.**
   Current live Core exposes the route.

3. **Live runtime and repo/release truth are different lanes.**
   - Repo `HEAD` / HA package version: `15.0.17`
   - Live Core measured now: `15.0.4`
   - Live zone dashboard: `0 zones`

4. **The working tree is dirty and must not be treated as release truth.**
   In particular, working-tree `custom_components/copilot_ha/manifest.json` currently drops keys that `HEAD` still contains (`icon`, `homeassistant`, `hacs`).

5. **Recent cleanup/reconciliation removed too much context.**
   Commits `04452adb` and `67d37b48` removed docs/tests/ops material that later recovery needed.

---

## Concrete next restore steps

1. **Keep the concept boundary fixed.**
   Use `docs/HA_CONCEPT_DIRECTIVE.md` as binding restore guidance.

2. **Do not publish from the dirty tree.**
   Review or isolate current uncommitted edits before any HACS release work.

3. **Verify the hotfixed HA-side failure paths first.**
   Confirm the live HA runtime is actually running code with:
   - the `config_flow.py` `merge_config_data(...)` import fix
   - the `zone_auto_setup.py` `validate_mapping(...)` import fix
   - the async area→zone loader path for startup

4. **Run one clean HA-side reload/sync cycle.**
   Reload/restart the `copilot_ha` integration so `_first_zone_sync()` can run against the current Core runtime.

5. **Verify the real contract after reload.**
   Minimum checks:
   - Configure/Reconfigure no longer throws HTTP 500
   - HA logs no longer emit `Failed to auto-create Habitus Zones`
   - `sensor.copilot_ha_habitus_zones` exists and contains zones
   - HA logs show `ensure-zones` and `sync-definitions` being attempted
   - Core dashboard shows non-zero zones

6. **If Core still shows 0 zones, debug the actual current failure.**
   Focus on:
   - HA integration load failure
   - any remaining `config_options_flow.py` traceback distinct from the fixed `config_flow.py` path
   - auth/token mismatch between HA and Core
   - baseline coordinator missing after runtime setup
   - `_first_zone_sync()` not executing

7. **Only after zone sync works, verify UI/module behavior.**
   - `sensor.copilot_ha_habitus_zones_v2_modules`
   - zone card module chips
   - presence-hold service path
   - module config flow step

8. **Keep reporting lanes separate in every follow-up.**
   Always report:
   - HA/HACS version
   - Core/Add-on version
   - git/repo state
   - live verified state

---

## Required artifacts
- [x] `docs/HA_CONCEPT_DIRECTIVE.md`
- [x] `docs/RECOVERY_RESTORE_STATUS.md`
- [x] `docs/HA_RESTORE_HANDOFF.md`
- [x] `TASKBOARD.md` updated with concrete restore status

## Success signal
This lane is back on track when:
- the architecture boundary is no longer in dispute,
- HA performs a clean authenticated sync into Core,
- Core dashboard shows non-zero zones,
- HACS packaging truth is preserved,
- status updates stop mixing HA, Core, git, and live runtime lanes.
