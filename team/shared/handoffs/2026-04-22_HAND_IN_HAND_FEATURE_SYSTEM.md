# 2026-04-22 Hand-in-hand feature system

**Stand:** 2026-04-22 23:24 Europe/Berlin
**Trigger:** Andreas wants a system that is faster, more systematic, pre-worked, researched, best-practice driven, hand in hand across lanes, and that ensures visualization plus configuration are available for shipped functions.

## Goal
From now on, PilotSuite work should not behave like isolated code slices.
It should behave like one coordinated feature system where every real function is driven through:
1. Core truth
2. HA / consumer truth
3. visualization truth
4. configuration truth
5. focused proof
6. exact next pull

## The new unit of work: feature packet bundle
Every meaningful feature gets a **bundle**, not just one isolated code task.

### Bundle lanes
For each feature, Orakel prepares up to three linked packets:
- **Core packet** — backend seam, contracts, domain truth
- **Consumer/Visualization packet** — dashboard / card / visible status / notification surface
- **Configuration packet** — editor / setup / flow / settings / HA exposure

### Bundle rule
A feature is only considered **complete** when the honest required members of the bundle are done.
Not every feature needs all three, but the bundle must explicitly say which are required and which are not.

## Mandatory feature questions before execution
Before starting a new feature or hardening slice, answer these briefly in the packet:
1. What exact user-visible function is this for?
2. What exact backend seam owns the truth?
3. What exact visible consumer shows it?
4. What exact configuration surface lets it be controlled?
5. What proof ring demonstrates the seam is real?
6. What is explicitly out of scope for this slice?

If one of these has no answer, the packet is incomplete.

## Delivery lifecycle
Every feature now moves through this lifecycle:

### 1. Research
Read only what is necessary:
- active seam file
- active proof/tests
- one relevant doc/handoff
- one adjacent consumer or config file if the feature touches usability

### 2. Packetize
Orakel writes the exact packet bundle:
- task id
- seam owner
- target files
- proof ring
- success signal
- linked follow-up packet(s) for visualization/config if required

### 3. Core landing
PilotClaw or HomeClaw lands the owning backend seam.

### 4. Consumer landing
If the feature requires visibility, the next exact pull must land the visible consumer.

### 5. Configuration landing
If the feature requires user control, the next exact pull must land the config/setup surface.

### 6. E2E check
A bounded proof confirms that the feature is not only coded, but usable.

### 7. Queue continuation
The next packet bundle is already prepared before the current bundle ends.

## Lane responsibilities
### Orakel
- owns bundle design and queue truth
- keeps one active bundle and the next two bundles prepared
- ensures backend, visualization, and config implications are named up front
- cuts stale or vague slices smaller
- escalates only on real blocker, real decision, or milestone

### PilotClaw
- single Core writer
- lands the backend truth and exact Core hardening slices
- does not widen into HA/config/dashboard work unless the packet explicitly owns that seam

### HomeClaw
- single HA/config/consumer writer on HA-owned surfaces
- lands HA consumer or configuration packets behind the active Core seam
- does not invent side work beyond the bundle

### DesignClaw
- support-only
- sharpens visualization packet quality, config ergonomics, and proof expectations on exact request
- never becomes a second implementation writer

## New done definition
A task is only marked **done** when all required bundle elements are done.

### Done examples
- **backend-only hardening:** contract green + no required consumer/config follow-up
- **user-facing feature:** backend green + visible consumer green + config surface green (if needed)
- **automation feature:** backend rule/delivery green + HA-visible result green + configuration path green if the user needs to steer it

## Speed rules that still protect quality
1. Keep research bounded
2. Keep packets exact
3. Keep one active Core slice at a time
4. Keep one active HA follow-up at a time
5. Keep the next two bundles prepared
6. Never treat status chatter as progress
7. If a feature lacks visibility or configurability and it should have them, create the missing follow-up packet immediately

## Immediate application to current queue
### Active Core chain
- `CORE-HARDEN-209` (freshly landed on current truth)
- `CORE-AUTO-203-B`
- `HA-FOLLOW-DELIVERY`
- `E2E-CONSOLIDATION-01`

### Bundle interpretation now
- `CORE-AUTO-203-B` owns the backend delivery truth
- `HA-FOLLOW-DELIVERY` owns the visible consumer truth
- if delivery needs steering or enable/disable control, the next exact config packet must be cut immediately after the delivery seam is proven

## Standing rule for future work
Whenever a new function is proposed, Orakel must decide up front:
- backend only
- backend + visualization
- backend + configuration
- backend + visualization + configuration

That choice must be written into the packet before execution starts.

## Success signal
This system is working when Andreas sees:
- faster landings
- cleaner handoffs
- fewer missing consumer/config gaps after backend work
- more features that are not just implemented, but actually visible and controllable
