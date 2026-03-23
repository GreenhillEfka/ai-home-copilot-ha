# HA Restore Handoff

**Ownership split:** HomeClaw has holistic autonomous ownership of `pilotsuite-styx-ha` and the final say for HA/HACS. Route Core/Add-on questions to PilotClaw.

## What is now clear
- The canonical boundary has been restored and is bound by `/config/clawd/team/PILOTSUITE_APPROVED_CONCEPTS_2026-03-23.md`: **HA/HACS delivers raw runtime reality / UX / execution; Core owns semantic truth; Core `homeassistant` is the connection module; Habitus zones are the config/policy layer; RAG / Proposals / Action Intents consume the same Core truth.**
- The live Core currently reachable from this host is **`15.0.4`**.
- Live Core exposes both:
  - `POST /api/v1/zone-automation/ensure-zones`
  - `POST /api/v1/zone-automation/sync-definitions`
  Both return **401 without auth**, so the routes exist.
- Live Core `GET /api/v1/zone-automation/module-schemas` works and returns **7 module schemas**.
- Live Core `GET /api/v1/zone-automation/dashboard` still reports **0 zones**.
- A direct repo-level HA failure path is confirmed in Configure/Reconfigure: `config_flow.py` used `merge_config_data(...)` without importing it.
- A direct repo-level HA failure path is confirmed in zone auto-setup: `zone_auto_setup.py` used `validate_mapping(...)` without importing it, which matches the live `Failed to auto-create Habitus Zones` log.
- `area_zone_registry.py` blocking file I/O on the async setup path is also confirmed and now has an async helper path in the working tree.
- `button_update_check.py` should be treated as a preserved prior fix, not the main current blocker.
- Current RAM/OOM suspicion looks weak (~43.9% RAM used, ~17.7 GB free).

## What that means
The old diagnosis “`/sync-definitions` is missing in Core” is no longer the right blocker for the current runtime.

The top HA-side restore priority is now:
- verify the live HA runtime actually includes the `config_flow.py` / `zone_auto_setup.py` hotfixes,
- verify Configure/Reconfigure and auto-setup stop failing,
- then confirm authenticated HA→Core zone sync.

Secondary follow-up questions remain:
- whether any remaining `config_options_flow.py` errors are separate from the now-confirmed `config_flow.py` path,
- whether `Knowledge Graph sync: No API client available` is expected degraded wiring or a real integration drift.

## Changes made in this pass
- Wrote `docs/HA_CONCEPT_DIRECTIVE.md`
- Wrote `docs/RECOVERY_RESTORE_STATUS.md`
- Updated `TASKBOARD.md`
- Fixed zone payload normalization in:
  - `custom_components/copilot_ha/agent_scripts/health_check.py`
  - `custom_components/copilot_ha/agent_scripts/fixer.py`

## Important caution
The repo working tree is dirty. In particular, working-tree `custom_components/copilot_ha/manifest.json` drops `homeassistant`, `icon`, and `hacs`, while `HEAD` still contains them.

Do **not** release from the dirty tree without reviewing that drift.

## Best next action on the live system
1. Verify the running HA integration actually includes the `config_flow.py` import hotfix, the `zone_auto_setup.py` import hotfix, and the async area→zone loader path.
2. Reload/restart the HA `copilot_ha` integration.
3. Watch logs for Configure/Reconfigure, `Failed to auto-create Habitus Zones`, `_first_zone_sync()`, and `ensure-zones` / `sync-definitions` calls.
4. Re-check Core dashboard for non-zero zones.
5. Only if zones still remain 0, inspect auth/load failure paths and any remaining `config_options_flow.py` traceback instead of reopening the old “route missing” theory.
