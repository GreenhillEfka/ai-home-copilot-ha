# 2026-04-22 PilotSuite state-of-the-art and concept review

**Stand:** 2026-04-22 23:42 Europe/Berlin
**Purpose:** Check the current PilotSuite direction against current web-visible best practice and derive direct execution consequences, not loose research chatter.
**Fresh local truth used:**
- `/config/clawd/team/PILOTSUITE_PROGRESS_LEDGER.md`
- `/config/clawd/team/shared/handoffs/2026-04-22_HAND_IN_HAND_FEATURE_SYSTEM.md`
- `/config/clawd/team/shared/handoffs/2026-04-22_STATUS_RELEASE_AND_SUPPORT_AGENT_SYSTEM.md`
- `/config/clawd/team/shared/handoffs/2026-04-22_ACCELERATION_NEXT_SLICE_SEQUENCE.md`

## Current PilotSuite concept being evaluated
PilotSuite is currently moving toward a coordinated smart-home execution system with:
- exact backend seams in Core
- exact HA-visible consumer follow-up
- configuration/control follow-up where needed
- bounded proof rings
- strict serial execution
- clean release/status reporting
- support-only review/research/status agents around single-writer builder lanes

Active forward chain on fresh truth:
`CORE-AUTO-203-B -> HA-FOLLOW-DELIVERY -> E2E-CONSOLIDATION-01`

---

## External findings and direct implications

### 1. Home Assistant direction is moving toward device context + collective intelligence, not isolated entities
**Source:** Home Assistant Roadmap 2025, `https://www.home-assistant.io/blog/2025/05/09/roadmap-2025h1/`

### Relevant finding
Home Assistant is explicitly pushing toward:
- device context, not just raw entities
- community-derived intelligence
- better default automations
- better dashboards
- more conversational and proactive behavior

### Consequence for PilotSuite
This **supports** the new hand-in-hand bundle rule strongly.
PilotSuite is directionally aligned when it treats a feature as:
- backend truth
- visible consumer truth
- configuration/control truth

### Improvement to adopt explicitly
For every real feature packet, keep naming the owning object in user terms, not only API terms.
Example shape:
- not only `notification delivery path`
- but also `which household-visible device/zone/use-case is being improved`

### Concrete recommendation
For `E2E-CONSOLIDATION-01`, define one canonical user-visible object/system path, for example:
- `zone condition -> rule decision -> delivery -> HA-visible confirmation`
- and bind it to a real device/room/user-facing scenario

---

### 2. Agent systems should stay deterministic where the workflow is known
**Source:** Google Cloud Architecture, `https://docs.cloud.google.com/architecture/choose-design-pattern-agentic-ai-system`

### Relevant finding
Google's current pattern guidance says:
- use deterministic sequential workflows where the path is known
- use multi-agent coordinator/hierarchical/swarm patterns only when ambiguity really requires it
- keep human-in-the-loop at important checkpoints
- revisit architecture as the task shape changes

### Consequence for PilotSuite
This **supports** Andreas' strict serial execution and exact-pull system.
For the current PilotSuite work, a deterministic sequence is the right default.
The current active chain is not an argument for more free-form swarm behavior.

### Improvement to adopt explicitly
Keep multi-agent use limited to:
- status packaging
- visualization/config review
- proof/research gate support

Do **not** let support agents route or rewrite the active product path.

### Concrete recommendation
Keep the current structure:
- Orakel = queue/packet steward
- PilotClaw = Core writer
- HomeClaw = HA writer
- support agents = bounded review/support only

This is state-of-the-art-aligned for a predictable delivery chain.

---

### 3. Notification delivery should be interactive, contextual, and safely repeatable
**Sources:**
- Home Assistant actionable notifications docs, `https://companion.home-assistant.io/docs/notifications/actionable-notifications/`
- Home Assistant automation modes docs, `https://www.home-assistant.io/docs/automation/modes/`

### Relevant finding
Modern HA notification practice favors:
- actionable notifications, not dead-end alerts
- unique action IDs per notification run to avoid collisions
- explicit waits, clear handling, and timeout/cancel paths
- careful automation mode choice (`queued` or `parallel` where overlapping runs are valid)

### Consequence for PilotSuite
This is highly relevant to `CORE-AUTO-203-B` and `HA-FOLLOW-DELIVERY`.
If PilotSuite lands delivery only as a one-way notification send, it risks stopping short of current best practice.

### Improvement to adopt explicitly
After the delivery seam is proven, the first HA-visible consumer should preferably include at least one of these:
- acknowledgment path
- action button path
- visible state/history confirmation
- timeout/clearing behavior

### Concrete recommendation
For `HA-FOLLOW-DELIVERY`, prefer a consumer seam that includes:
1. visible confirmation the notification was generated/sent
2. optional actionable response or acknowledgment route
3. explicit automation mode choice documented (`queued` vs `parallel` vs `single`)

If interactivity is not in this slice, mark it explicitly as the next config/control packet.

---

### 4. Reliable delivery architecture still wants an outbox/idempotency mindset
**Source:** Microservices.io transactional outbox pattern, `https://microservices.io/patterns/data/transactional-outbox.html`

### Relevant finding
Reliable event/delivery systems should not depend on a fragile dual-write pattern.
Best practice is:
- commit state change and delivery intent together
- relay delivery separately
- preserve ordering where needed
- make consumers idempotent because relays can publish more than once

### Consequence for PilotSuite
Even if PilotSuite is not building a large distributed broker system right now, the conceptual lesson still applies:
notification delivery should be modeled as a durable intent, not only a fire-and-forget side effect.

### Improvement to adopt explicitly
When shaping `CORE-AUTO-203-B`, prefer seams that make these questions answerable:
- what exact delivery intent was created?
- was it attempted?
- was it confirmed/failed?
- can retry happen safely?
- can a duplicate be recognized safely?

### Concrete recommendation
Do not widen the current slice, but add one explicit architectural rule behind it:
- future notification/delivery work should move toward **durable delivery intent + idempotent consumer handling**

If not now, cut this as the first follow-up hardening packet after visible E2E proof.

---

### 5. Agentic systems need observability at trace/tool/decision level
**Source:** OpenTelemetry AI Agent Observability, `https://opentelemetry.io/blog/2025/ai-agent-observability/`

### Relevant finding
Current best practice is moving toward standardized traces, metrics, and logs for:
- tool usage
- task execution
- reasoning path visibility
- evaluation/feedback loops

### Consequence for PilotSuite
This supports the new status/release system, but goes one level deeper:
clean human-facing cards are necessary, but they are not enough for system diagnosis.

### Improvement to adopt explicitly
PilotSuite should progressively expose internal proof in a machine-checkable way for:
- notification delivery attempts
- HA consumer confirmation
- E2E flow checkpoints
- failure categories

### Concrete recommendation
For `E2E-CONSOLIDATION-01`, define a small traceable checkpoint set:
- trigger observed
- decision/rule applied
- delivery attempted
- HA-visible confirmation observed

This can remain simple at first, but it should be structured, not prose-only.

---

## Concept-level judgment

## What is already aligned with current practice
- strict serial execution for predictable delivery
- exact packetization
- hand-in-hand backend/consumer/config thinking
- support agents kept away from second-writer drift
- bounded proof rings
- checkpoint/release visibility

## What still needs strengthening
1. **object/context framing**
   - features should map to real household objects/use cases, not only endpoints
2. **interactive delivery model**
   - notifications should trend toward acknowledge/action/confirm flows, not only send flows
3. **durable delivery semantics**
   - move over time from side-effect send to durable delivery intent + retry/idempotency discipline
4. **structured observability**
   - make E2E proof machine-checkable via explicit checkpoints/events/status, not only tests and prose
5. **retrieval resilience**
   - memory/research support should not rely on embeddings alone; add lexical/manual fallback when semantic retrieval is degraded

---

## Direct execution consequences for the current chain

### `CORE-AUTO-203-B`
Keep the slice bounded, but design it so the next steps are not blocked:
- preserve the canonical notification seam only
- ensure failure categories are explicit
- leave room for delivery-attempt state, retry safety, and acknowledgment follow-up

### `HA-FOLLOW-DELIVERY`
Prefer the first consumer seam that gives visible user truth, ideally one of:
- send confirmation/status
- actionable acknowledgment
- dashboard/history confirmation tied to the delivery seam

### `E2E-CONSOLIDATION-01`
Make the first visible automation path explicitly prove:
- real trigger/context
- real rule/decision
- real delivery
- real HA-visible confirmation

And bind it to one named real-world use case, not a generic backend claim.

---

## Recommended next support packets
1. **AUTO-203-B follow-up review note**
   - exact recommendation for durable intent / idempotency-ready shaping
2. **HA-FOLLOW-DELIVERY consumer choice packet**
   - choose between acknowledgment card, actionable notification loop, or dashboard/history confirmation
3. **E2E-CONSOLIDATION-01 proof map**
   - explicit 4-step checkpoint proof structure
4. **Memory-search resilience packet**
   - lexical/manual fallback when embedding path times out

---

## Bottom line
PilotSuite's current updated approach is **directionally strong and more modern than the earlier isolated-slice mode**.
The biggest improvements now are not a total conceptual reset, but tightening around:
- real user/device context
- interactive notification handling
- durable delivery semantics
- structured observability
- resilient fallback for memory/research paths

That means: **stay on the current execution plan, but shape the next packets with these constraints built in.**
