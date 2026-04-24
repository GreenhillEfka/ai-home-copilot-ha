# 2026-04-23 Forward execution plan and task derivation

**Stand:** 2026-04-23 Europe/Berlin
**Purpose:** Turn current PilotSuite file truth into the next serial execution plan with concrete tasks, owners, proof rings, and exit criteria.

## Current truth used
- `/config/clawd/team/PILOTSUITE_PROGRESS_LEDGER.md`
- `/config/clawd/team/shared/handoffs/2026-04-23_NEXT_EXACT_PULL_HABITUS_ZONE_PROJECTION.md`
- `/config/clawd/team/shared/handoffs/2026-04-23_AEGIS_E2E_CONSOLIDATION_01_PROOF_GATE_PACKET.md`
- `/config/clawd/team/shared/handoffs/2026-04-22_PILOTSUITE_STATE_OF_THE_ART_AND_CONCEPT_REVIEW.md`

## Honest current state
### Landed
- Core hardening wave is landed through `CORE-HARDEN-216` in ledger truth.
- `HA-FOLLOW-DELIVERY` is file-backed closed.
- `E2E-CONSOLIDATION-01` is treated as proven in current ledger truth.

### Still messy / needs reconciliation
- HA worktree contains a bounded dirty seam around `habitus_zone_sensor`.
- Ledger truth is not fully cleanly synchronized:
  - duplicate HARDEN entries
  - stale `CORE — CURRENT HEAD`
  - `E2E-CONSOLIDATION-01` is marked green, but its closeout packaging is thinner than ideal

### Planning consequence
The next work should not be guessed from old slices. It should proceed in this order:
1. finish or discard the live bounded HA dirty seam fast
2. reconcile file truth after that landing
3. cut the next meaningful feature packet on the delivery system
4. keep the chain serial and proof-backed

---

# Forward sequence

## Packet 1 — HA-HABITUS-PROJECTION-301
**Status:** ready now
**Owner:** HomeClaw
**Why first:** this is the only live bounded dirty seam already present in the HA worktree, so it is the cheapest honest next landing.

### Goal
Project canonical Core habitus/zones truth into a clean HA-owned zone overview sensor.

### Exact path
`Core /api/v1/habitus/zones -> HA habitus_zone_sensor projection`

### Files
- `custom_components/pilotsuite/sensors/habitus_zone_sensor.py`
- `tests/test_habitus_zone_sensor_projection.py`

### Proof ring
```bash
python3 -m py_compile custom_components/pilotsuite/sensors/habitus_zone_sensor.py
.venv/bin/python -m pytest -q tests/test_habitus_zone_sensor_projection.py
```

### Done means
- canonical endpoint only
- projection only, no second semantic engine
- proof ring green
- HA worktree clean after commit
- short checkpoint card says what user-visible zone/habitus truth now exists

### Non-goals
- no dashboard family
- no notification widening
- no config-flow expansion unless strictly required

---

## Packet 2 — TRUTH-RECONCILE-302
**Status:** immediately after Packet 1
**Owner:** Orakel
**Support:** Hermes
**Why now:** after the next landing we need one clean shared truth base before cutting more feature work.

### Goal
Reconcile ledger + closeout truth so the next queue is based on one trustworthy current state.

### Tasks
1. fix stale `CORE — CURRENT` section in ledger
2. remove duplicate HARDEN rows / duplicate entries
3. add explicit note for current HA worktree landing or discard result
4. either:
   - add a thin `E2E-CONSOLIDATION-01` closed packet, or
   - add a ledger note that points to the exact proof artifact that closed it

### Artifacts
- `team/PILOTSUITE_PROGRESS_LEDGER.md`
- one closeout/checkpoint artifact if needed

### Done means
- one current shared truth file can be trusted again for routing
- next exact pull can be cut without ambiguity

### Non-goals
- no reopening old product work
- no re-litigating already landed seams

---

## Packet 3 — DELIVERY-INTERACTIVE-303
**Status:** next feature packet after truth reconciliation
**Primary owner:** PilotClaw for Core seam
**Secondary owner:** HomeClaw for HA seam
**Why next:** the state-of-the-art review says the current system is sound, but the most valuable next strengthening is interactive delivery rather than more random hardening.

### Goal
Upgrade one-way delivery into one bounded interactive household-visible loop.

### Canonical user-visible object
`zone-driven household prompt that can be acknowledged or cleared`

### Scope
Build exactly one interaction family:
- acknowledgment
**or**
- actionable button response

Recommendation: start with **acknowledgment** because it is smaller and gives truthful closed-loop confirmation fastest.

### Split tasks
#### 303-A Core delivery interaction contract
**Owner:** PilotClaw
- define response token / correlation shape
- define success / timeout / cancel semantics
- add contract tests for acknowledge path

#### 303-B HA consumer interaction path
**Owner:** HomeClaw
- surface the interaction through existing HA-native surfaces only
- bind response back to the canonical Core delivery seam
- prove visible confirmation of acknowledged state

### Proof shape
Must prove:
`trigger -> delivery -> user acknowledgment -> visible confirmed state`

### Non-goals
- no multi-action menu
- no new dashboard/card family unless unavoidable
- no unrelated automation expansion

---

## Packet 4 — DELIVERY-DURABILITY-304
**Status:** after interactive delivery lands
**Primary owner:** PilotClaw
**Why here:** once interaction exists, reliability semantics become worth formalizing.

### Goal
Move delivery from pure side-effect toward durable intent semantics.

### Questions this packet must make answerable
- what delivery intent was created?
- was it attempted?
- did it succeed / fail / timeout?
- can retry happen safely?
- can duplicate delivery be recognized safely?

### Expected shape
A bounded contract around:
- delivery intent record/object
- explicit outcome categories
- idempotent handling rules for retries

### Non-goals
- no broker expansion
- no queue system rewrite
- no infra detour

---

## Packet 5 — E2E-OBSERVABILITY-305
**Status:** after durability packet
**Owners:** PilotClaw + HomeClaw, each on own seam
**Why last in this run:** it becomes most valuable after interaction and durability semantics exist.

### Goal
Expose one machine-checkable proof chain for a real automation path.

### Required checkpoint chain
- trigger observed
- decision/rule applied
- delivery attempted
- HA-visible confirmation observed

### Output expectation
One small structured status/proof artifact, not prose-only reporting.

### Non-goals
- no full telemetry platform build
- no generic tracing detour across the whole stack

---

# Derived task board

## Ready now
### T1 — land or discard current HA habitus projection seam
- **Packet:** `HA-HABITUS-PROJECTION-301`
- **Owner:** HomeClaw
- **State:** ready

## Next after T1
### T2 — reconcile ledger and closeout truth
- **Packet:** `TRUTH-RECONCILE-302`
- **Owner:** Orakel
- **State:** queued

## Next feature wave
### T3 — define bounded interactive acknowledgment loop
- **Packet:** `DELIVERY-INTERACTIVE-303-A`
- **Owner:** PilotClaw
- **State:** queued

### T4 — bind HA-visible acknowledgment confirmation
- **Packet:** `DELIVERY-INTERACTIVE-303-B`
- **Owner:** HomeClaw
- **State:** queued behind T3 exact seam

### T5 — durable delivery intent and retry discipline
- **Packet:** `DELIVERY-DURABILITY-304`
- **Owner:** PilotClaw
- **State:** queued

### T6 — structured E2E checkpoint proof artifact
- **Packet:** `E2E-OBSERVABILITY-305`
- **Owners:** PilotClaw + HomeClaw
- **State:** queued

## Support-only tasks
### S1 — visual/config review only if requested by active packet
- **Owner:** DesignClaw
- **Rule:** no independent feature lane

### S2 — proof/research gate only for the active packet
- **Owner:** Aegis
- **Rule:** no routing changes

### S3 — status/release packaging only on real movement
- **Owner:** Hermes
- **Rule:** no duplicate chatter

---

# Autonomous routing rule from here
- only one active product packet at a time
- every packet needs: owner, files, proof ring, done signal, non-goals
- no new packet starts before the prior packet is landed or explicitly discarded
- Orakel keeps one prepared next pull ahead of the active writer
- `topic:1` remains: landed truth / real blocker / next exact pull only

---

# Immediate recommended next action
**Pull now:** `HA-HABITUS-PROJECTION-301`

If it lands cleanly:
- immediately do `TRUTH-RECONCILE-302`
- then cut and execute `DELIVERY-INTERACTIVE-303-A`

If it does not stay bounded:
- discard it cleanly
- do `TRUTH-RECONCILE-302`
- then cut `DELIVERY-INTERACTIVE-303-A` as the next active packet
