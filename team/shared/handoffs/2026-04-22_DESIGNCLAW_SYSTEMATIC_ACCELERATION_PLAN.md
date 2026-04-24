# DesignClaw support plan — systematic faster Core development without drift

**Stand:** 2026-04-22 22:05 Europe/Berlin
**Owner:** Orakel for queue truth, PilotClaw as Core single writer, HomeClaw as HA single writer
**Role:** support-only acceleration artifact, no second writer path

## Why this plan
Andreas wants all of this at once, correctly:
- tasks worked out before execution
- research used, but only in service of implementation
- functions questioned before integration, then integrated correctly
- seamless autonomous execution when no real question exists
- higher speed without murks
- HA pulled along in parallel where it is a real consumer, not as drift

This plan turns that into one clean operating system.

## Hard operating rules
1. **One active Core slice at a time** on PilotClaw
2. **One active HA slice at a time** on HomeClaw, only when there is a real consumer seam
3. **Every slice starts with a mini packet**:
   - goal
   - exact files
   - exact proof ring
   - exact success signal
4. **Research is mandatory but bounded**:
   - read current seam
   - read adjacent tests/contracts
   - read one relevant doc/handoff
   - then cut code
5. **No reopen of old queue text by assumption**
6. **No topic chatter as substitute for landed code**

## The actual delivery pipeline
For every new slice, use this fixed sequence:

### Phase A — Prepare
- identify the exact function/module seam
- verify current repo truth
- verify current tests/contracts
- write one compact execution packet if the seam is still ambiguous

### Phase B — Build
- modify only the exact seam files
- keep the slice small enough to prove in one run
- no side refactor unless directly required

### Phase C — Prove
- py_compile or equivalent syntax gate
- focused proof ring only
- if green, checkpoint immediately

### Phase D — Hand off / continue
- update queue truth
- name next exact pull
- if a HA consumer seam is now honest, hand one bounded HA slice to HomeClaw

## Speed-up proposals that do not add murk
### 1. Fixed pre-slice packet discipline
Before every Core slice, there must be a 4-line packet:
- exact seam
- exact files
- exact proof ring
- exact success signal

**Impact:** less drift, fewer false starts, faster commits.

### 2. Bounded research rule
Research stays in, but capped:
- max 3 reads before code
- current module
- current tests/contracts
- one supporting doc/handoff

**Impact:** keeps correctness without turning into idle analysis.

### 3. Autonomous continuation by default
If there is no real blocker:
- PilotClaw continues directly to the next named Core slice
- HomeClaw continues directly to the next named HA consumer slice
- Orakel only interrupts for real blocker, milestone, or approval need

**Impact:** less dead air, more continuous shipping.

### 4. HA parallel shadowing, not HA drift
While Core is active, HomeClaw should do only one of two things:
- close a real HA seam already handed off by Core
- prepare the exact next consumer seam behind the active Core work

**Impact:** real parallelism without building random side surfaces.

### 5. Visualization and configuration must ship with the function spine
For every meaningful vertical slice, explicitly ask:
- how is the function made visible to the user
- where is the configuration/admin seam for this function
- which HA/UI/dashboard/consumer surface proves it exists outside the API

This does **not** mean building large side UIs first. It means every real function gets:
- one truthful visualization/consumer path
- one truthful configuration/control path
- both tied to the same canonical module truth

**Impact:** functions do not remain invisible or unconfigurable after backend work lands.

### 6. 6h visible output gate
Every 6h there must be at least one of:
- landed commit
- green focused proof ring
- visible E2E function gain

If not, the current slice is too vague and must be recut.

## Next work, from current file truth
Current ledger truth says:
- Core through `CORE-HARDEN-207` is closed
- next Core backlog candidates are:
  - `HARDEN-208` sensors API
  - `HARDEN-209` state API
  - `AUTO-203-B` notification delivery
- HA has `HA-E2E-303` closed, `HA-559` still in progress

## Recommended serial plan to the next visible release
### Round 1 — finish current HA seam cleanly
**Owner:** HomeClaw
**Task:** close `HA-559`
**Goal:** remove residual HA ambiguity so the shared queue is clean again
**Proof:** exact HA focused ring only

### Round 2 — continue Core hardening where it strengthens the shipped product spine
**Owner:** PilotClaw
**Recommended order:**
1. `HARDEN-208` sensors API
2. `HARDEN-209` state API
3. `AUTO-203-B` notification delivery

**Why this order:**
- sensors + state stabilize the module surfaces that other consumers rely on
- then notification delivery extends the already-real automation vertical slice

### Round 3 — first bigger visible E2E consolidation
**Owner:** PilotClaw
**Goal:** bind the current rule/automation truth into a stronger user-visible product path
**Expected shape:**
- Zone/Habitus state
- Core decision/rule
- notification delivery
- HA-visible consumer confirmation

### Round 4 — HA follow-through in parallel
**Owner:** HomeClaw
**Goal:** mirror only the real consumer seam coming out of Round 3
**Do not:** build speculative dashboards or unrelated config detours

### Round 5 — release candidate gate
Only cut RC if all are true:
- HA active seam green
- Core active seam green
- one visible E2E product function is demonstrably real
- queue truth names the next pull cleanly

## Rough plan until complete end
This is the broad order, then each slice gets detailed by current research before coding:
1. finish open HA cleanup (`HA-559`)
2. stabilize Core module APIs (`HARDEN-208`, `HARDEN-209`)
3. extend automation from A to B on real delivery (`AUTO-203-B`)
4. mirror the resulting consumer seam in HA
5. consolidate one visible end-to-end automation product path
6. then repeat the same pattern for the next strongest vertical slice

## What DesignClaw should do
- stay support-only
- produce mini packets when an exact seam is unclear
- do targeted research before implementation slices
- tighten proof rings and handoffs
- never start a competing writer cadence

## What should stop immediately
- broad repeated status loops
- queue text without exact current seam
- research without a direct coding consumer
- HA parallel work without a real Core consumer handoff
- backend-only landings that leave no truthful visualization/config path behind
- planning documents that do not change the next actual slice

## Success signal
This plan is working if, over the next 24 to 48h, Andreas sees:
- fewer repeated status messages
- more landed code
- more focused green tests
- cleaner queue truth
- at least one stronger visible E2E product gain
