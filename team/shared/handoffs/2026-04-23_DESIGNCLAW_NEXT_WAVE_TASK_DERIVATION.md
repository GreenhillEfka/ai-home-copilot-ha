# 2026-04-23 DesignClaw support packet — next wave task derivation from fresh truth

**Stand:** 2026-04-23 Europe/Berlin
**Role:** support-only planning packet
**Truth base:**
- `/config/clawd/team/PILOTSUITE_PROGRESS_LEDGER.md`
- `/config/clawd/team/shared/handoffs/2026-04-22_ACCELERATION_NEXT_SLICE_SEQUENCE.md`
- `/config/clawd/team/shared/handoffs/2026-04-22_HAND_IN_HAND_FEATURE_SYSTEM.md`
- `/config/clawd/team/shared/handoffs/2026-04-23_NEXT_EXACT_PULL_HABITUS_ZONE_PROJECTION.md`

## Fresh state
Already closed on fresh file truth:
- `CORE-AUTO-203-B` ✅
- `HA-FOLLOW-DELIVERY` ✅
- `E2E-CONSOLIDATION-01` ✅
- Core hardening wave through `CORE-HARDEN-216` ✅

So the job now is **not** to reopen that chain.
The job is to cut the next clean feature wave from current truth.

## Recommended next wave

### Task 1 — `HA-HABITUS-ZONE-PROJECTION-01`
**Owner:** HomeClaw
**Why first:** this is the cleanest already-bounded dirty seam in fresh truth and it extends the just-proven automation/delivery path into a clearer user-visible overview without inventing a new family.

**Exact seam:**
`Core /api/v1/habitus/zones -> HA habitus_zone_sensor projection`

**Exact files:**
- `team/worktrees/pilotsuite-styx-ha-current/custom_components/pilotsuite/sensors/habitus_zone_sensor.py`
- `team/worktrees/pilotsuite-styx-ha-current/tests/test_habitus_zone_sensor_projection.py`

**Proof ring:**
- `python3 -m py_compile custom_components/pilotsuite/sensors/habitus_zone_sensor.py`
- `.venv/bin/python -m pytest -q tests/test_habitus_zone_sensor_projection.py`

**Success signal:**
- sensor consumes canonical Core habitus/zones truth only
- stays pure projection, not a second semantic engine
- proof ring green
- HA worktree clean after commit

**Non-goals:**
- no dashboard family widening
- no config-flow widening unless strictly required
- no speculative Core side work

---

### Task 2 — `CORE-DELIVERY-SEMANTICS-01`
**Owner:** PilotClaw
**When:** only after Task 1 lands or is cleanly discarded
**Why second:** after truthful delivery + HA confirmation, the next strongest Core improvement is delivery quality, not a new random module. Tighten the already-shipped automation vertical.

**Goal:** make notification delivery more durable and explicit.

**Task shape:**
- retries / idempotency / delivery intent only if current seam truth supports it
- no widening into MQTT or new action families
- keep it on the canonical proactive delivery seam

**Packet must define before code:**
- exact delivery semantic being added
- exact target files
- exact proof ring
- exact success signal
- explicit non-goals

**Required bundle questions:**
- what user-visible behavior improves
- where HA can observe the improved delivery state
- whether config/control is needed now or later

---

### Task 3 — `E2E-OBSERVABILITY-01`
**Owner:** PilotClaw + HomeClaw on own seams
**When:** after Task 2 or if Task 2 is discarded from fresh truth
**Why third:** Andreas explicitly wants to see what is implemented, how it is working, and how functions are represented. The clean next step is a truthful observability path for the feature system.

**Target shape:**
`trigger -> decision -> delivery -> HA confirmation -> visible projection`

**Bundle parts:**
- Core event/status truth
- HA visible confirmation/projection
- optional config/control if the path needs enable/disable or filtering

**Success signal:**
- one bounded path makes the automation feature inspectable end to end
- status/reporting can point to real function state, not only proof logs

---

## Derived execution order
1. `HA-HABITUS-ZONE-PROJECTION-01`
2. `CORE-DELIVERY-SEMANTICS-01`
3. `E2E-OBSERVABILITY-01`

This preserves the current hand-in-hand rule:
- one active HA slice
- then one active Core slice
- then one bundle-style E2E slice

## Rough continuation after that
Once the above wave is done, the next feature wave should be selected by the same bundle logic:
1. exact backend truth
2. exact consumer/visualization truth
3. exact config/control truth
4. focused proof ring

Strong candidate families after this wave:
- interactive delivery follow-up (ack/action/clear)
- energy/forecast consumer vertical
- voice/context visible confirmation vertical

## What should be posted in topic:1 from this wave
Only:
- landed item
- real blocker
- next exact pull

Not:
- repeated old chain summaries
- broad planning commentary
- status without new file-backed truth

## Compact operator version
**Next exact pull:** `HA-HABITUS-ZONE-PROJECTION-01`

**Then:**
- `CORE-DELIVERY-SEMANTICS-01`
- `E2E-OBSERVABILITY-01`

That is the cleanest next wave from fresh file truth.