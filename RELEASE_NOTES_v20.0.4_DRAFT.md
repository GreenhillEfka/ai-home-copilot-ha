# PilotSuite HA v20.0.4 Release Notes (Draft)

> Draft status: hold before publish until release validation blockers are resolved.

## Highlights
- Version sync with PilotSuite Core v20.0.4
- HACS/Home Assistant metadata aligned to `pilotsuite` and `20.0.4`
- Config flow includes token-based Core authentication
- Auto-fetch support for setup token from Core (`/api/v1/auth/setup-token`)
- Expanded Lovelace card bundle for PilotSuite dashboards

## What changed
- Home Assistant package metadata updated for the v20.0.4 release line
- Config flow keeps support for Zero Config, Quick Start, Manual Setup, and reconfigure paths
- Token-auth validation checks Core reachability through `/api/v1/status`
- Dashboard/card assets remain bundled under `www/pilotsuite/`

## Validation summary
### Verified
- `custom_components/pilotsuite/config_flow.py` is present in the active v20.0.4 worktree
- Token helper test passed:
  - setup token can be auto-fetched
  - bearer token is sent as `Authorization: Bearer <token>`
  - invalid token path returns HTTP 401 and is surfaced as auth failure
- Targeted repo tests passed:
  - `tests/test_metadata_parity_projection.py`
  - `tests/test_automation_suggestion_sensor_projection.py`
  - `tests/test_hub_dashboard_sensor_projection.py`
  - `tests/test_neuron_dashboard_sensors_projection.py`
  - Result: `64 passed`

### Release blockers to resolve before publish
- Lovelace card count is **11 shipped JS cards**, not 9:
  - `action_executor_card.js`
  - `device_link_card.js`
  - `event_bus_card.js`
  - `habitus_zone_card.js`
  - `intent_manager_card.js`
  - `learning_memory_card.js`
  - `predictive_card.js`
  - `presence_entity_card.js`
  - `room_context_card.js`
  - `rule_optimizer_card.js`
  - `state_bridge_card.js`
- Internal domain constant is still legacy in `custom_components/pilotsuite/const.py`:
  - `DOMAIN = "copilot_ha"`
  - manifest domain is `pilotsuite`
  - this mismatch should be fixed before release/tagging

## Upgrade notes
- If you are upgrading from older `copilot_ha` builds, review dashboards, automations, and entity references for legacy names
- Re-run integration setup or reconfigure if Core host, port, or token changed

## Recommended publish note
This release should only be published after the `const.py` domain mismatch is corrected and the public card-count wording is updated from 9 to 11.
