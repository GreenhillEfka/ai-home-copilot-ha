# Orakel execution plan — systematic faster Core development with HA pulled along

**Stand:** 2026-04-22 23:10 Europe/Berlin
**Owner:** Orakel for routing and packet readiness
**Single writers:** PilotClaw for Core, HomeClaw for HA
**Support:** DesignClaw on exact unblock only

## Why this plan exists
Andreas wants the same things at once, correctly:
- tasks worked out before execution
- bounded research before integration
- functions questioned before wiring, then integrated correctly
- seamless autonomous continuation when there is no real question
- faster throughput with less murk
- HA pulled along in parallel where it is a real consumer, not as side drift

This plan turns that into one clean operating rule and one queue.

## Binding operating model
### 1. Exact packet before every slice
Every slice starts with one compact execution packet:
- task id
- exact seam
- exact files
- exact proof ring
- success signal
- non-goals / do-not-widen

### 2. Research stays mandatory, but bounded
Before code on a new slice, read only:
1. current seam file
2. current proof/test ring
3. one supporting handoff/doc if needed

Then cut code.

### 3. Hard builder loop
Every builder lane runs:
`exact pull -> implement -> focused proof -> commit -> checkpoint -> next exact pull`

### 4. No idle gaps
If the next exact packet is already ready, the builder continues autonomously.
Stop only for:
- real blocker
- real decision
- missing packet truth

### 5. HA parallel means consumer-follow, not side work
HomeClaw only does one of these:
- close the active HA seam already in flight
- pull the exact HA consumer seam behind the current Core landing

No speculative dashboards, no side configuration drift.

## How we support and accelerate Core now
### A. Keep the next two Core packets prepared ahead of PilotClaw
Orakel keeps:
- active slice packet
- next slice packet
- one prepared backup packet

This removes waiting between landings.

### B. Push all support work behind the active Core seam
DesignClaw only helps when one of these is true:
- the seam is ambiguous
- the proof ring is weak
- a support packet can remove implementation risk immediately

No independent research cadence.

### C. Enforce visible-output cadence
At least every 4 to 6 hours there must be one of:
- landed commit
- green focused proof ring
- visible product gain

If not, the slice is too vague and must be recut smaller.

### D. Use Core-first serial order, with HA shadowing the real consumer path
Core keeps shipping the product spine.
HA stays close enough to prove consumer truth, but never steals the queue head without a real handoff.

## Current truth at planning time
From shared ledger truth:
- Core closed through `CORE-HARDEN-207`
- Current Core backlog head is the next unnamed hardening seam, with candidates:
  - `HARDEN-208` sensors API
  - `HARDEN-209` state API
  - `AUTO-203-B` notification delivery
- HA has `HA-E2E-303` closed and `HA-559` still in progress
- Systematic fast-dev mode is already active and working

## Recommendation
**Recommended path: Option A**

### Option A — best balance of speed and correctness
1. `HARDEN-208` sensors API
2. `HARDEN-209` state API
3. `AUTO-203-B` notification delivery
4. HA consumer follow-through on the real delivery seam
5. one visible end-to-end automation confirmation path

**Why A is best:**
- sensors + state harden the product spine that multiple consumers rely on
- delivery then extends an already-real automation path instead of inventing a new one
- HA parallelization stays honest because it follows a Core-produced seam

### Option B — delivery first
1. `AUTO-203-B`
2. HA follow-through
3. `HARDEN-208`
4. `HARDEN-209`

**Why not recommended first:**
- faster visible motion, but weaker base surfaces underneath
- more risk of re-touching state/sensor seams after the vertical slice

### Option C — HA cleanup first, then Core
1. finish `HA-559`
2. `HARDEN-208`
3. `HARDEN-209`
4. `AUTO-203-B`

**Why not recommended first:**
- clean, but slower on Core throughput
- does not use current Core shipping rhythm as aggressively

## Next exact work now
### PilotClaw — active next pull
**Task:** `HARDEN-208` sensors API
**Goal:** put the current sensor surface under dedicated contract proof
**Packet must name:**
- exact endpoint/module seam
- exact touched files
- exact proof ring
- exact unauthorized + happy-path expectations
- exact next pull after landing

### Orakel — immediate support work
1. prepare `HARDEN-208` packet if still ambiguous
2. prepare `HARDEN-209` packet before `HARDEN-208` lands
3. prepare `AUTO-203-B` packet behind that
4. keep topic:1 result-only

### HomeClaw — parallel shadow work
**Task:** continue `HA-559` only if it is the actual active HA seam.
If `HA-559` is stale, HomeClaw should instead prepare the exact next HA consumer seam that follows the next Core automation/delivery landing.

### DesignClaw — support only
Only act if asked or if one exact unblock packet materially reduces risk for:
- `HARDEN-208`
- `HARDEN-209`
- `AUTO-203-B`

## Broad route until complete end
### Phase 1 — stabilize the Core product spine
- `HARDEN-208` sensors API
- `HARDEN-209` state API

### Phase 2 — extend the live automation vertical slice
- `AUTO-203-B` notification delivery
- validate that the rule/automation path is real and visible

### Phase 3 — HA consumer confirmation on the same truthful path
- HomeClaw mirrors only the exact consumer seam produced by Core
- no speculative side UI

### Phase 4 — first full visible E2E package
Target path:
- Zone/Habitus state
- Core rule/decision
- delivery action
- HA-visible confirmation / consumer state

### Phase 5 — hardening and release gate
- focused regression rings on touched spines
- remove stale ambiguity in queue truth
- name exact remaining gaps only

### Phase 6 — ship-ready closeout
- one clean RC-style checkpoint
- proof summary per active seam
- next backlog head already packetized

## What should stop immediately
- blocker posts caused by stale or isolated truth
- planning without an exact next coding consumer
- research that does not tighten an active seam
- HA side motion without a real Core handoff
- status chatter in place of proof, commit, or next pull

## Success signal
This plan is working if Andreas sees, over the next 24 to 48h:
- more landed code
- cleaner exact-next-pull handoffs
- faster Core cadence with less dead air
- HA following real Core consumer seams
- one visibly stronger E2E automation path, not just local hardening
