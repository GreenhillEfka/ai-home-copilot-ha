# 2026-04-22 Core acceleration execution plan

**Stand:** 2026-04-22 22:20 Europe/Berlin
**Lead:** Orakel
**Writers:** PilotClaw = Core only, HomeClaw = HA only
**Intent:** schneller, systematischer, vorbereiteter, autonomer Durchsatz ohne Drift

## 1. What changes now
Ab jetzt gilt nicht nur "mehr Tempo", sondern dieser konkrete Modus:

1. next task is prepared before current task ends
2. research is bounded and mandatory before code
3. implementation slices stay small and provable
4. after landing, the next prepared slice starts automatically unless there is a real blocker or real decision
5. HA runs parallel only as truthful consumer/support path behind the active Core seam

## 2. Exact build loop
Every slice follows exactly:
- prepare
- implement
- focused proof
- commit
- checkpoint
- next exact pull

### Prepare means exactly
For each new slice, the owner must pin:
- task id
- exact seam
- exact files
- exact proof ring
- exact success signal
- non-goals

### Research rule
Before coding, read only:
- current implementation seam
- current adjacent tests/contracts
- one relevant handoff/doc if needed

No broad context sweeps.

## 3. Core support model
### Orakel
- keeps the next two Core slices prepared ahead of PilotClaw
- only surfaces landing, real blocker, or next exact pull into topic:1
- cuts/recuts a slice if 6h pass without a landing, a green focused proof ring, or a visible function gain

### PilotClaw
- remains the single Core writer
- keeps moving autonomously from one prepared Core slice to the next
- does not stop for status synthesis when code/proof can continue

### HomeClaw
- remains the single HA writer
- runs only the real HA seam that mirrors or consumes the active Core output
- in parallel may prepare the next HA consumer seam, but may not open a speculative side path

### DesignClaw
- support only
- prepares mini packets, proof rings, edge-case research, and consumer checks on exact request
- never becomes a second writer

## 4. Current truthful queue from file truth
### Core already closed
- HARDEN-204 ✅
- HARDEN-205 ✅
- HARDEN-206 ✅
- HARDEN-207 ✅

### HA current
- HA-E2E-303 ✅
- HA-559 in progress

### Current next Core candidates from ledger
1. HARDEN-208 — sensors API
2. HARDEN-209 — state API
3. AUTO-203-B — notification delivery

## 5. Recommended execution order until the next real end-to-end release gain
### Phase A — clean open HA state
**Owner:** HomeClaw
**Task:** HA-559
**Goal:** close the remaining HA ambiguity so Core and HA queue truth are both clean
**Output:** landing or real blocker only

### Phase B — stabilize Core read/write surfaces
**Owner:** PilotClaw
**Order:**
1. HARDEN-208 — sensors API
2. HARDEN-209 — state API

**Why first:**
- these seams are shared foundations for user-visible consumers
- they reduce later breakage when the next E2E path is widened

### Phase C — strengthen the already-real automation vertical
**Owner:** PilotClaw
**Task:** AUTO-203-B — notification delivery
**Goal:** extend the current Zone/Habitus -> rule -> notification chain into a stronger delivery contract

### Phase D — HA follow-through on the same product seam
**Owner:** HomeClaw
**Goal:** mirror only the real consumer seam created by Phase C
**Examples:** visible notification confirmation, status projection, or exact dashboard/automation consumer bind
**Do not:** build unrelated config or dashboard detours

### Phase E — first explicit E2E consolidation gate
**Owners:** PilotClaw + HomeClaw, each on own seam
**Goal:** one truthful visible product path:
- Zone/Habitus state
- Core decision/rule
- notification delivery
- HA-visible confirmation

### Phase F — continue the same pattern to completion
After the first stronger E2E vertical lands:
1. choose next strongest vertical slice
2. prepare 2 exact next packets ahead
3. run Core first, HA consumer second
4. prove each slice narrowly
5. only then widen again

## 6. Rough roadmap until the current spine is "complete enough"
1. close HA-559
2. land HARDEN-208
3. land HARDEN-209
4. land AUTO-203-B
5. land the HA consumer seam for that vertical
6. prove one visible automation E2E chain end to end
7. then repeat for the next strongest vertical, likely state/consumer or energy/notification depending on the freshest proof-backed seam

## 7. Fast-throughput rules
- no idle gap between slices when a prepared packet exists
- no repeated status loops
- no fake blockers without file checks
- no second writer path
- no research without a direct coding consumer
- no HA parallelism unless it is tied to the active Core seam

## 8. Success signal for Andreas
This plan is working when the next 24-48h show:
- more commits
- more focused green proof rings
- cleaner next-pull truth
- fewer interruptions
- one stronger visible automation E2E gain
