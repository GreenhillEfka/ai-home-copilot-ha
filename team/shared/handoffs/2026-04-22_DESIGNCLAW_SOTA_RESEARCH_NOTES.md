# DesignClaw support research — state of the art checks for PilotSuite concept and implementation

**Stand:** 2026-04-22 23:28 Europe/Berlin
**Method:** targeted Ollama-backed web search across HA architecture, graph visualization, workflow automation, and config/control patterns
**Role:** support-only external research notes for current execution model

## Main takeaways

### 1. Event-driven entity/state architecture remains the right base
External references around Home Assistant and state-machine-driven automations reinforce:
- canonical entity state as source of truth
- event-driven transitions instead of duplicated polling logic
- bounded automations built as explicit state transitions, not sprawling script chains

**Implication for PilotSuite:**
Keep Habituts/Zones/Neuron state on one truthful canonical state path and make automations consume that path, not alternate projections.

## 2. Graph/neuron visualization should stay tied to canonical backend truth
Current graph visualization guidance consistently favors:
- one canonical graph payload
- interactive consumer on top of that payload
- avoid separate visualization-only data models
- keep live topology and inspection surfaces on the same truth source

**Implication for PilotSuite:**
Neuronen-/Brain-System should continue using one truthful snapshot/live seam. UI should visualize canonical graph truth, not maintain a second front-end graph model.

## 3. Automation slices should be triads, not backend-only landings
Workflow automation guidance is very consistent on production hardening:
- event input
- rule/decision engine
- delivery/action/notification output
plus:
- idempotency
- retries/error handling
- observability on delivery success/failure

**Implication for PilotSuite:**
A function is not really done at backend rule evaluation. Each meaningful slice should land as a triad:
1. backend logic
2. consumer/visualization surface
3. config/control surface

## 4. Config and feature control should be explicit, not mixed implicitly into behavior
Modern config/control references distinguish clearly between:
- feature visibility/enablement
- runtime configuration values
- per-surface or per-tenant overrides

**Implication for PilotSuite:**
Do not bury module behavior in ad hoc defaults. Keep function config explicit and bind it to the same canonical module truth used by backend and consumer surfaces.

## 5. Faster execution without quality loss comes from narrower proofable slices
Across sources, the repeatable pattern is:
- small provable slices
- event-driven contracts
- explicit API/contracts/tests
- focused checkpointing
- no broad speculative side work

**Implication for PilotSuite:**
The current move toward exact seam + exact proof ring + direct autonomous continuation is aligned with state of the art and should be pushed harder, not relaxed.

## Concrete improvements to fold into the current PilotSuite approach
1. Every new vertical slice must name:
   - canonical state source
   - rule/decision seam
   - delivery/visualization seam
   - config/control seam
2. No backend-only completion claim for major functions
3. Add delivery/result observability on automation outputs where possible
4. Keep graph/neuron visualization pinned to canonical graph payload
5. Keep HA parallelism consumer-only behind landed Core truth

## Most relevant external themes checked
- Home Assistant state machine / state management / developer state docs
- interactive graph visualization patterns (GraphScope / Reagraph / Sigma-style guidance)
- workflow automation production patterns (event-driven delivery, retries, observability)
- config / feature-flag / remote-config separation patterns

## Practical conclusion
PilotSuite's broad direction is still sound, but the strongest improvement is this:
**treat every important function as a full product vertical, not just a backend seam**.
That means each serious slice should deliberately cover:
- truthful state/model
- rule/module logic
- visible consumer
- explicit config/control
- focused proof ring
