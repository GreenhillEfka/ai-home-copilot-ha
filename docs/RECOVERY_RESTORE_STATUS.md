# PilotSuite HA/HACS Recovery Restore Status

**Updated:** 2026-03-23 Europe/Berlin
**Owner lane:** HomeClaw / DesignClaw restore support
**Repo:** `pilotsuite-styx-ha`
**Authority split:** HomeClaw has holistic autonomous ownership of the HA repo and final say for HA/HACS; Core/Add-on questions route to PilotClaw.

## TL;DR

- The intended architecture has been recovered and is now additionally constrained by the approved overall concept bundle at `/config/clawd/team/PILOTSUITE_APPROVED_CONCEPTS_2026-03-23.md`.
- Binding model: **HA/HACS provides raw runtime reality / UX / execution; Core/Add-on is the semantic truth layer; Core `homeassistant` is the connection module; Habitus zones are config/policy for domain modules; RAG / Proposals / Action Intents must consume the same Core truth.**
- The HA lane has two newly confirmed direct repo-level bug paths: missing `merge_config_data(...)` import in `config_flow.py` and missing `validate_mapping(...)` import in `zone_auto_setup.py`.
- Live log `Failed to auto-create Habitus Zones` now has a concrete HA-side code-path match in that missing `validate_mapping(...)` import.
- The intended architecture remains: **HA/HACS is the acquisition + visualization layer; Core/Add-on is the semantic and zone-automation truth layer.**
- Repo `HEAD` publishes **HA/HACS `15.0.17`**, but live Core measured from this host is **`15.0.4`**.
- Live Core now exposes both **`/api/v1/zone-automation/ensure-zones`** and **`/api/v1/zone-automation/sync-definitions`**. Both return **401 without auth**, which proves the routes exist. The earlier “sync-definitions is missing” diagnosis is therefore **stale for the current runtime**.
- Live Core also exposes **`/api/v1/zone-automation/module-schemas`** successfully with **7 modules / 39 fields**.
- Live log evidence currently points much more strongly at **HA-side config/auto-setup code-path failures** than at RAM pressure: current RAM/OOM suspicion looks weak (~43.9% RAM used, ~17.7 GB free).
- `Knowledge Graph sync: No API client available` remains a real warning, but currently looks **secondary** to the config/reconfigure and zone-auto-setup failures.
- The remaining restore problem is **not route absence**. The remaining restore problem is that **HA has not successfully completed authenticated zone sync into Core**, or HA has not reloaded cleanly enough for `_first_zone_sync()` to run against the current Core runtime.
- The working tree is **dirty** with uncommitted startup/HACS-related edits. Do **not** treat the working tree as release truth.

---

## Evidence reviewed

### Markdown sources read from the current repo
- `TASKBOARD.md`
- `.learnings/LEARNINGS.md`
- `CORE_ENDPOINT_STATUS.md`
- `FRONTEND_ZONE_CHAIN.md`
- `RELEASE_LOCK.md`
- `addons/pilot-agent/README.md`
- `agents/designclaw/RELEASE_REVIEW_SUMMARY.md`
- `agents/designclaw/SLICE4_REVIEW.md`
- `agents/designclaw/SLICE5_REVIEW.md`
- `custom_components/copilot_ha/CHANGELOG.md`
- `custom_components/copilot_ha/agent_scripts/README.md`
- `custom_components/copilot_ha/www/zone_card_yaml.md`
- `docs/FRONTEND_ZONE_CHAIN.md`
- `docs/agent/HA_AGENT_COMMUNICATION.md`
- `memory/2026-03-21.md`
- `pilotsuite_ops/docs/SENSOR_AUDIT_PHASE2.md`

### Recovered deleted context used to preserve intent
- deleted `docs/ARCHITECTURE_CONCEPT.md`
- deleted `docs/KOMMUNIKATIONSPIPELINE.md`
- deleted `pilotsuite_ops/docs/PS-089_E2E_ZONE_MAPPING.md`
- deleted `pilotsuite_ops/docs/MODUL_PER_ZONE_SCHEMA.md`
- deleted `pilotsuite_ops/docs/CONTRACT_VERIFY_MODULES_ZONES.md`
- cleanup commits `04452adb` and `67d37b48`

### Live measurements taken during this recovery
```bash
curl http://localhost:8909/health
# -> version 15.0.4

curl http://localhost:8909/api/v1/zone-automation/dashboard
# -> ok, total_zones 0

curl http://localhost:8909/api/v1/zone-automation/module-schemas
# -> ok, 7 module schemas

curl -X POST http://localhost:8909/api/v1/zone-automation/ensure-zones
# -> 401

curl -X POST http://localhost:8909/api/v1/zone-automation/sync-definitions
# -> 401
```

Interpretation: Core is alive, zone-automation routes exist, but no zones are currently present in Core.

### Additional live log signals folded into this status
- `config_flow.py` / Configure/Reconfigure errors are now a top HA-side restore priority because the repo-level `merge_config_data(...)` NameError path is directly confirmed.
- `config_options_flow.py` also appears in live error reports, but that remains a **follow-up verification target** rather than the primary proven root cause.
- `Failed to auto-create Habitus Zones` is now materially explained by the missing `validate_mapping(...)` import in `zone_auto_setup.py`.
- `area_zone_registry.py` blocking file I/O is a real async-path quality problem and aligns with the observed blocking-I/O warnings.
- `button_update_check.py` should be treated differently: the VERSION-read warning class appears to have already been addressed by the earlier async executor path and should mainly be protected from regression.
- `Knowledge Graph sync: No API client available` remains visible, but currently reads more like runtime wiring drift / optional capability absence than the primary cause of Configure/Reconfigure 500s.
- Current memory measurements make RAM/OOM a weak explanation for the live failures.

---

## Recovered intended HA ↔ Core communication path

## 1) Canonical boundary
Recovered from `memory/2026-03-21.md` and deleted architecture docs:

- **HA/HACS** delivers Home Assistant entities, events, areas, and context.
- **Core** owns zone management logic, semantic normalization, module schemas, Brain/Neuron processing, and automation truth.
- **HA** visualizes Core truth back into sensors, cards, and controls.

This means the target state is **not** “HA does everything locally.” The target state is:

**HA areas/entities → HA zone store/sensors → Core zone automation sync → Core dashboard/module truth → HA cards/services**

## 2) Actual sync path still present in code
From `custom_components/copilot_ha/coordinator.py`:

- `_first_zone_sync()` reads zones from `habitus_zones_store_v2`
- strips `zone:` prefixes for Core compatibility
- `POST /api/v1/zone-automation/ensure-zones`
- builds full zone payloads including:
  - `zone_id`
  - `name_de`
  - `zone_type`
  - `entity_ids`
  - role-based `entities`
  - `floor`, `priority`, `tags`
  - HA area metadata
- `POST /api/v1/zone-automation/sync-definitions`

So the HA repo still contains the intended bootstrap + full-definition sync behavior.

## 3) Module configuration path is intact
From `coordinator.py` + `zone_automation_entities.py`:

- HA fetches `GET /api/v1/zone-automation/module-schemas`
- HA creates schema-driven entities for per-zone module config
- live Core currently returns module schemas successfully

This means the **module lane is conceptually intact**; it is waiting on zone sync/runtime alignment.

## 4) Frontend/UI path is intact enough to recover
From `habitus_zones_entities_v2.py` and `www/styx-zone-card.js`:

- `sensor.copilot_ha_habitus_zones` exposes zone lists for Lovelace
- `sensor.copilot_ha_habitus_zones_v2_modules` exposes per-zone module configs
- `styx-zone-card.js` reads the dedicated `v2_modules` sensor first
- presence hold flows via HA service `copilot_ha.set_zone_presence_hold` to Core endpoint `/api/v1/presence/zone/presence/{zone_id}/hold`

This is enough to keep the UI thin and Core-backed once sync is healthy again.

---

## What recent recovery attempts got wrong

### 1) Over-cleanup deleted memory, not just clutter
Commit `04452adb` removed a huge amount of repo context: root docs, tests, HACS metadata, README, operations docs, agent handoffs, and architecture material. Commit `67d37b48` removed additional docs including zone-mapping/contract context.

**Impact:** later recovery work had less evidence and started rediscovering already-made decisions.

### 2) Live version drift was mistaken for contract truth
Older docs correctly observed a runtime where `/sync-definitions` appeared absent. That was then treated like an architectural fact, which triggered:
- a temporary pivot to `ensure-zones`-only sync
- more discussion about alternate paths
- avoidable confusion over whether canonical sync should exist

**Current evidence:** on the live Core reachable now, `sync-definitions` exists. The problem is no longer route absence.

### 3) HACS packaging was broken by removing root `hacs.json`
`CHANGELOG.md` shows the repo removed `hacs.json` at `v15.0.3`, then later restored it at `v15.0.14` because HACS versioned installs broke.

**Meaning:** “cleanup” accidentally removed required release packaging metadata.

### 4) The working tree currently reintroduces HACS risk
`HEAD` manifest contains:
- `homeassistant`
- `hacs: "integration"`
- `icon`

But the **working tree** has those keys removed again in `custom_components/copilot_ha/manifest.json`.

**Meaning:** if the dirty working tree were committed/released as-is, HACS compatibility could regress again.

### 5) Reporting repeatedly mixed HA and Core lanes
The learnings/memory files are clear:
- HA/HACS version
- Core/Add-on version
- git/main state
- live/runtime verification
must be reported separately.

When these got mixed, recovery conversations drifted into false conclusions.

### 6) Recovery tooling drifted from actual payload shapes
`custom_components/copilot_ha/agent_scripts/health_check.py` and `fixer.py` assumed zone payloads were always dict-shaped, but current dashboard/sensor data can be list-shaped. That makes restore tooling noisy or misleading.

I fixed that normalization in this pass so the scripts compare zone IDs more reliably.

---

## Current blockers

### Blocker A — Configure/Reconfigure and auto-setup failures are HA-side priority one
The strongest current HA-side failure candidates are now repo-backed, not speculative:
- `config_flow.py` had a direct `merge_config_data(...)` NameError path in Configure/Reconfigure
- `zone_auto_setup.py` had a direct `validate_mapping(...)` NameError path matching `Failed to auto-create Habitus Zones`
- `area_zone_registry.py` had blocking file I/O on an async startup-adjacent path

The first live-system question is therefore whether the running HA integration actually includes these hotfixes and whether any remaining `config_options_flow.py` tracebacks are separate.

### Blocker B — Core still has 0 zones
Measured live:
- `/health` works
- `/module-schemas` works
- `/zone-automation/dashboard` works
- dashboard reports `total_zones: 0`

This means Core is up, but HA has not successfully seeded or resynced zone definitions.

### Blocker C — authenticated HA-triggered sync is still unverified
I could verify unauthenticated Core routes from this subagent, but I do **not** have a supervisor/HA token in this environment, so I could not directly confirm:
- current HA sensor state
- whether `_first_zone_sync()` ran after the latest runtime change
- whether HA logs show auth or load failures
- whether Configure/Reconfigure and OptionsFlow are now clean in the live runtime

### Blocker D — live Core is behind repo/release head
Repo truth: HA/HACS `15.0.17`
Live Core truth measured here: `15.0.4`

That gap may not be fatal for zone sync, but it means old recovery notes about versions must be treated carefully.

### Blocker E — working tree is not clean
Uncommitted changes currently exist in:
- `custom_components/copilot_ha/__init__.py`
- `custom_components/copilot_ha/core/runtime.py`
- `custom_components/copilot_ha/habitus_zones_api.py`
- `custom_components/copilot_ha/manifest.json`
- plus docs/taskboard changes from this recovery pass

Do not release from this working tree without an explicit cleanup decision.

---

## Small repo changes made in this recovery pass

### Documentation created
- `docs/HA_CONCEPT_DIRECTIVE.md`
- `docs/RECOVERY_RESTORE_STATUS.md`
- `docs/HA_RESTORE_HANDOFF.md`

### Taskboard updated
- `TASKBOARD.md` now includes concrete restore status and next steps

### Small tooling fix applied
- `custom_components/copilot_ha/agent_scripts/health_check.py`
- `custom_components/copilot_ha/agent_scripts/fixer.py`

Change made: zone sync checks now normalize both list-shaped and dict-shaped zone payloads before comparing HA/Core zone IDs.

Validation:
```bash
python3 -m py_compile \
  custom_components/copilot_ha/agent_scripts/health_check.py \
  custom_components/copilot_ha/agent_scripts/fixer.py
```

---

## Smallest safe next steps

### 1. Freeze the conceptual boundary
Treat `docs/HA_CONCEPT_DIRECTIVE.md` as the recovery baseline.

### 2. Do not release from the current dirty tree
Especially do not publish the current working-tree `manifest.json` changes without deliberate review.

### 3. Verify the hotfixed HA-side failure paths in the live runtime
Before broader theory work, confirm the running HA integration actually includes:
- the `config_flow.py` `merge_config_data(...)` import fix
- the `zone_auto_setup.py` `validate_mapping(...)` import fix
- the async area→zone loader path

### 4. Force one clean HA-side reload/sync cycle
From the HA/live side:
- reload or restart the `copilot_ha` integration
- ensure `_first_zone_sync()` runs
- watch logs for Configure/Reconfigure, `Failed to auto-create Habitus Zones`, `ensure-zones`, and `sync-definitions`

### 5. Verify the contract immediately after reload
Minimum checks:
- Configure/Reconfigure no longer throws HTTP 500
- HA logs no longer emit `Failed to auto-create Habitus Zones`
- HA sensor `sensor.copilot_ha_habitus_zones` exists and has zones
- Core `GET /api/v1/zone-automation/dashboard` shows non-zero zones
- Core `POST /api/v1/zone-automation/sync-definitions` is no longer just theoretically present, but actually being reached by HA

### 6. If zones are still 0, debug the real failure — not the old one
Look for:
- HA integration load failure
- any remaining `config_options_flow.py` traceback distinct from the fixed `config_flow.py` path
- missing/invalid auth token between HA and Core
- baseline coordinator not coming up cleanly
- `_first_zone_sync()` not being triggered

Do **not** revert again to an HA-only workaround unless the authenticated sync path is proven broken in the current runtime.

### 7. After zone sync is healthy, validate UX end-to-end
- `sensor.copilot_ha_habitus_zones_v2_modules`
- module chips in `styx-zone-card.js`
- presence-hold service path
- module override config flow step

### 8. Clean reporting after recovery
Use the four-lane truth model in every report:
- HA/HACS version
- Core/Add-on version
- git state
- live verified state

---

## Recovery conclusion

The repo still contains the intended HA ↔ Core design. What was lost was mostly **clarity**, not the core path itself.

The fastest safe route back is:
1. preserve the restored architecture boundary,
2. stop treating old route-missing notes as current truth,
3. verify the live HA runtime includes the config-flow / zone-auto-setup hotfixes,
4. run one clean authenticated HA→Core sync cycle,
5. verify zones appear in Core,
6. only then continue UI/module polish.
