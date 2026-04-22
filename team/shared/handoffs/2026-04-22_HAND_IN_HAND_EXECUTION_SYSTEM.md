# 2026-04-22 Hand-in-hand execution system

**Stand:** 2026-04-22 23:25 Europe/Berlin
**Lead:** Orakel
**Single writers:** PilotClaw = Core, HomeClaw = HA, DesignClaw = support only
**Purpose:** systematisch schneller, sauberer und vollständiger liefern, inklusive Recherche, Integration, Visualisierung und Konfiguration

## 1. The system in one sentence
Core builds the product spine, HA follows as truthful consumer and configuration surface, DesignClaw prepares exact support packets, and Orakel keeps the next work pre-cut so builders never wait.

## 2. Non-negotiable rules
1. **Everything starts as a task packet before coding starts**
2. **Research is mandatory, but bounded**
3. **Only one active write slice per lane**
4. **After landing, continue automatically if the next packet exists**
5. **Every real function must be checked for four delivery faces when relevant:**
   - backend logic
   - API/contract
   - HA/config surface
   - visualization/consumer surface
6. **No side drift, no second writer path, no fake blockers**

## 3. Packet standard for every slice
Every slice packet must contain:
- task id
- user/product goal
- exact seam
- exact files
- proof ring
- success signal
- non-goals
- follow-up dependency

### Minimum pre-code research
Before implementation, read only:
1. active seam file
2. active or adjacent tests/contracts
3. one supporting handoff/doc

Then translate the seam into the packet and code immediately.

## 4. The hand-in-hand lane model
### Orakel
Owns:
- shared queue truth
- next two prepared packets ahead of the active writer
- cross-lane dependency timing
- recutting slices when they are too vague

Must ensure:
- no writer goes idle if a prepared packet exists
- topic:1 only shows landing, real blocker, or next exact pull
- every new vertical slice already has its HA/visual/config follow-through mapped before Core starts

### PilotClaw
Owns:
- Core backend, contracts, product spine

Works like this:
- pull prepared Core packet
- implement narrowly
- prove narrowly
- commit + checkpoint
- continue to next prepared Core packet

PilotClaw does **not** wait for chat if file truth already names the next slice.

### HomeClaw
Owns:
- HA consumer path
- configuration path
- visible Home Assistant follow-through

Works like this:
- either close the active HA seam already in flight
- or prepare/implement the exact HA consumer/config seam behind the active Core landing

HomeClaw does **not** invent side dashboards or detached config paths.

### DesignClaw
Owns support only:
- pre-slice research
- proof-ring strengthening
- visual/design packet prep
- exact consumer/UX packetization

DesignClaw never becomes a writer lane.

## 5. Built-in completeness rule
A feature is not considered "systematically prepared" unless these questions are answered before widening the queue:

### A. Core truth
- what backend/module seam makes it real?
- what contract proves it?
- what state enters and leaves the function?

### B. HA truth
- where is it configured in HA?
- where is it consumed or reflected in HA?
- what exact entity/service/view confirms the function is visible?

### C. Visualization truth
- how does the user see the effect?
- what dashboard/card/entity/status surface is the right honest visual?
- is a new visual needed, or should an existing surface consume it?

### D. Operational truth
- how is it tested?
- what is the exact success signal?
- what is the next seam after landing?

If these are unanswered, the slice is not ready.

## 6. Delivery pattern for every vertical slice
Each meaningful function should be executed in this order:

1. **Core seam**
2. **proof ring**
3. **HA consumer/config seam**
4. **visible confirmation surface**
5. **checkpoint + next exact pull**

This keeps implementation and user-visible truth coupled.

## 7. Speed system
### A. Two packets ahead
At all times:
- 1 active packet
- 1 next packet ready
- 1 backup packet sketched

### B. 4 to 6 hour output gate
Within 4 to 6 hours there must be at least one of:
- landed commit
- green focused proof ring
- visible product gain

Otherwise the slice gets cut smaller immediately.

### C. No broad rediscovery
No lane re-reads broad history just to resume.
Use only:
- AGENTS
- MEMORY
- shared ledger
- own tasklog
- exact seam file

### D. Real parallelism only
Core and HA can move hand in hand, but only like this:
- Core ships the active product seam
- HA prepares or lands the exact consumer/config seam behind it
- both remain synchronized by one queue truth

## 8. Next broad execution route from current truth
### Core route
1. `HARDEN-208`
2. `HARDEN-209`
3. `AUTO-203-B`
4. next visible automation E2E consolidation

### HA route
1. finish `HA-559` if still truly active
2. otherwise prepare or land the HA consumer/config seam behind the next Core landing
3. then visible confirmation path in HA

### Design/Support route
- prepare packets for ambiguity, proof, visual consumer, or config path only when they directly unblock the active route

## 9. Best-practice implementation rule
No function is "done" just because backend code exists.
The system must deliberately check whether the function also has:
- correct contract
- correct integration
- correct configuration path
- correct visual/consumer path

That is the default finish standard, not an optional polish pass.

## 10. Success condition
This system is working if Andreas sees:
- fewer waits between slices
- more exact task packets before work starts
- more landed code with focused proof
- HA staying aligned with Core instead of drifting
- visual and config surfaces arriving as part of the feature path, not weeks later
