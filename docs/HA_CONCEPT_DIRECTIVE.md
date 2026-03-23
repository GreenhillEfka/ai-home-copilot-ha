# HA Concept Directive — PilotSuite Home Assistant / HACS Boundary

**Date:** 2026-03-22  
**Scope:** `pilotsuite-styx-ha`  
**Authority:** HomeClaw has holistic autonomous ownership of this HA repo and owns the HA/HACS concept boundary. Core/Add-on direction remains PilotClaw's lane.
**Ownership routing (reaffirmed by Andreas, 2026-03-22):** Route HA/HACS direction and implementation questions to HomeClaw. Route Core/Add-on direction and implementation questions to PilotClaw.
**Binding overall concept reference (approved 2026-03-23):** `/config/clawd/team/PILOTSUITE_APPROVED_CONCEPTS_2026-03-23.md`

## Binding baseline after approval
- **HA delivers raw runtime reality / UX / execution.**
- **Core holds semantic truth.**
- **Core `homeassistant` is a connection module.**
- **Habitus zones are the configuration/policy layer of domain modules.**
- **RAG / Proposals / Action Intents consume the same Core truth.**

This directive must now be read through that approved baseline.

## 1. Purpose

This directive defines the durable boundary between:
- **HA/HACS** = the Home Assistant-native adapter, configuration surface, and UX package
- **Core/Add-on** = the semantic, decision, automation, and model-execution engine

This boundary is **not optional**. It exists to stop the HA repo from drifting into a second Core.

---

## 2. Evidence base used for this directive

The current repo already shows both the intended split and the places where it drifted.

### Documents
- `TASKBOARD.md` — asks for recovery of the HA/HACS vs Core boundary
- `memory/2026-03-21.md` — explicitly states: **HA/HACS delivers entities, events, and HA context into Core; Core is the semantic/neuronal truth layer; HA visualizes Core truth back into HA**
- `FRONTEND_ZONE_CHAIN.md` and `docs/FRONTEND_ZONE_CHAIN.md` — distinguish HA-local zone display from Core dashboard/runtime
- `CORE_ENDPOINT_STATUS.md` — confirms actual Core contract surface used by HA (`/ensure-zones`, `/sync-definitions`, `/module-schemas`, zone routes)
- `docs/agent/HA_AGENT_COMMUNICATION.md` — confirms HA-side operational access and restart checks
- `custom_components/copilot_ha/CHANGELOG.md` — shows repeated HA/HACS packaging and runtime compatibility work

### HA integration code proving HA-side ownership
- `custom_components/copilot_ha/config_flow.py` + `config_options_flow.py` + `config_zones_flow.py` — HA owns setup, options, zone editing flows, dashboard publish actions
- `custom_components/copilot_ha/habitus_zones_store_v2.py` — HA stores curated zone definitions in HA storage
- `custom_components/copilot_ha/zone_auto_setup.py` — HA derives initial zones from HA areas/entities
- `custom_components/copilot_ha/forwarder_n3.py` — HA listens to HA events and forwards normalized envelopes to Core
- `custom_components/copilot_ha/webhook.py` — HA receives Core push events and maps them into HA
- `custom_components/copilot_ha/dashboard_wiring.py`, `pilotsuite_dashboard.py`, `www/*.js`, `lovelace_resources.py` — HA owns Lovelace/dashboard surfaces
- `custom_components/copilot_ha/conversation.py`, `stt.py`, `tts.py` — HA exposes voice/chat surfaces while proxying execution to Core
- `custom_components/copilot_ha/core_proxy.py` — HA provides same-origin proxying to Core APIs

### Code proving current drift / boundary violations
- `custom_components/copilot_ha/__init__.py` loads a large `_MODULES` list from `custom_components/copilot_ha/core/modules/*` inside the HA package
- `custom_components/copilot_ha/habitus_zones_store_v2.py` advertises "Brain Graph integration" in the HA zone store
- `custom_components/copilot_ha/habitus_zones_entities_v2.py` and `zone_auto_setup.py` carry non-trivial zone matching logic locally
- `custom_components/copilot_ha/habitus_zones_api.py` tries optional Python imports from `copilot_core.homeassistant.*`
- `custom_components/copilot_ha/lovelace_resources.py` registers both a **Core-served** card bundle and **local** HACS card files, which creates ownership ambiguity

---

## 3. Canonical ownership model

## 3.1 HA/HACS owns

HA/HACS is the **Home Assistant adapter and product surface**.

It owns:

1. **Installation/package shape for Home Assistant**
   - `hacs.json`
   - `custom_components/copilot_ha/manifest.json`
   - translations, services, icons, `www/` assets, repair surfaces, dashboards

2. **Connection/bootstrap into Core**
   - host/port/token discovery and persistence
   - config entry setup/reconfigure flows
   - same-origin proxying where needed for HA frontend access

3. **Home Assistant-native ingestion**
   - reading HA registries, areas, states, service calls, local storage
   - constructing mechanical transport payloads for Core
   - forwarding HA events as minimal, privacy-bounded envelopes

4. **HA-side curated zone definitions**
   - zone creation/editing/deletion from HA config flows
   - mapping HA areas/entities/roles into user-facing zone definitions
   - storing HA-local zone definitions/snapshots in HA storage

5. **Translation layer between HA objects and Core contracts**
   - strip/add `zone:` prefixes as needed
   - convert HA area/entity structures into stable contract payloads
   - expose HA entities/sensors/buttons/selects that reflect Core state

6. **User-facing HA surfaces**
   - Lovelace cards/resources/dashboard wiring
   - persistent notifications
   - config flows/options flows
   - HA entities/buttons/switches/selects/numbers/sensors
   - HA conversation/STT/TTS entity integration points

7. **HA-local backups/snapshots**
   - snapshots of HA integration config and HA-curated zones only
   - not Core brain/state backups

## 3.2 Core/Add-on owns

Core is the **semantic and runtime truth layer**.

It owns:

1. **Semantic interpretation and durable system logic**
   - normalization, categorization, habitus recognition
   - zone-state logic and automation policy
   - suggestions, rankings, brain/neuron/mood truth
   - cross-zone/cross-domain reasoning

2. **Executable automation/runtime behavior**
   - module schemas
   - zone automation runtime state
   - decisioning and execution logic
   - chat completion orchestration
   - STT/TTS model execution

3. **Canonical runtime contracts**
   - REST APIs consumed by HA
   - webhook event types/payloads sent into HA
   - versioned runtime behavior behind those contracts

4. **Core-owned derived truth**
   - what a zone currently means/feels/should do
   - module health/automation state
   - anomaly/suggestion/neuron/brain outputs

## 3.3 Shared but not duplicated

These are shared concepts, but they must have **one owner each**:

| Concept | HA/HACS role | Core role | Canonical owner |
|---|---|---|---|
| Core connection settings | Collect/store in HA | Consume | HA/HACS |
| HA event capture | Observe and forward | Ingest and interpret | HA/HACS for capture; Core for meaning |
| Zone definitions tied to HA entities | Create/edit/store | Ingest/use | HA/HACS |
| Zone runtime state / automation mode effects | Mirror in entities | Compute/execute | Core |
| Module schemas | Render config UI | Define schema | Core |
| Mood / neuron / suggestion outputs | Display/act on | Compute | Core |
| Dashboards/cards/resources | Ship/render in HA | Provide data only | HA/HACS |
| Webhook auth + receive path in HA | Verify/receive | Send | split by side |

---

## 4. Boundary rules

## Rule A — HA is allowed to adapt, not to become Core

HA may:
- adapt HA registries/states into transport payloads
- keep HA-local user curation
- render/collect settings
- mirror Core outputs into HA entities

HA may **not** become the canonical place for:
- semantic inference
- cross-zone reasoning
- brain/neuron truth
- long-lived automation policy logic
- module definitions
- Core business rules

## Rule B — Zone ownership is split cleanly

### HA/HACS owns:
- which HA areas/entities/roles belong to a user-facing zone
- the config UI for creating/editing those mappings
- local storage of those mappings in Home Assistant

### Core owns:
- automation/runtime interpretation of those zones
- current zone state, automation mode behavior, derived mood/context, and module behavior

So: **HA defines the zone inputs; Core defines the zone runtime truth.**

## Rule C — Event ingestion starts in HA, meaning starts in Core

`forwarder_n3.py` is the correct HA-side pattern: listen to HA events, redact, enrich with local metadata only as needed, then forward.

HA should send:
- entity identifiers
- state transitions
- call-service intent envelopes
- local area/zone references
- minimal privacy-bounded context

Core should decide:
- relevance
- categorization
- inference
- suggestions
- automation consequences

## Rule D — Cards and dashboards are HA assets, not Core assets

The HACS package must be self-contained for its frontend assets.

Therefore:
- custom cards under `custom_components/copilot_ha/www/` are the preferred ownership model
- dashboards/wiring remain HA-owned
- Core may expose **data APIs**, but it should **not be the canonical shipper of HA card JS**

`lovelace_resources.py` currently registers both Core-served and local assets; this is drift and must be resolved in favor of **HA-owned card assets**.

## Rule E — No Python import dependency from HA package into Core package

`habitus_zones_api.py` currently attempts optional imports from `copilot_core.homeassistant.*`.

Durable rule:
- HA/HACS must interoperate with Core via **HTTP/webhook contracts**, not by importing Core Python modules into the HA package
- optional helper imports are acceptable only for transitional tooling, never for required production behavior

## Rule F — Repo content outside `custom_components/` is not HACS runtime truth

This repo still contains `addons/`, `agents/`, `docs/`, `pilotsuite_ops/`, and memory artifacts.
Those may be useful as evidence/reference, but they are **not** the HACS runtime surface.

Autonomous work must not treat those directories as proof that the HA integration should absorb add-on or ops responsibilities.

---

## 5. Durable interface contract

## 5.1 HA → Core

HA/HACS may call/send only these classes of things:

1. **Connection/bootstrap**
   - host/port/token setup

2. **Curated zone definition sync**
   - ensure zones exist in Core
   - sync HA-authored zone definitions/roles/entity membership

3. **Event envelopes**
   - state changes
   - service-call intent envelopes
   - optional bounded local metadata

4. **Operator/user commands**
   - set zone mode
   - set per-zone config
   - set module config
   - suggestion feedback / operator actions

5. **Capability/health checks**
   - module schemas
   - runtime dashboards
   - health/version endpoints

## 5.2 Core → HA

Core may send/serve only these classes of things into HA:

1. **Runtime state for display/control**
   - mood
   - suggestions
   - neurons / ranked candidates / anomalies
   - zone/module status

2. **Schemas that HA renders**
   - module schemas
   - explicit runtime capability descriptors

3. **Webhook events**
   - the canonical event types defined in `webhook.py`

4. **Voice/chat execution results**
   - conversation replies
   - STT transcriptions
   - TTS audio bytes

5. **Data for HA frontend surfaces**
   - JSON/state data only; not frontend asset ownership

---

## 6. What must stay in HA/HACS

These items are specifically in-bounds for HA/HACS and should remain there:

- `config_flow.py`, `config_options_flow.py`, `config_zones_flow.py`
- HA entity platforms and services
- HA repairs/issues surfaces
- `dashboard_wiring.py`, `pilotsuite_dashboard.py`, `habitus_dashboard.py`
- `www/*.js` and HACS Lovelace resource registration
- webhook receiver/auth verification on the HA side
- same-origin Core proxy for HA frontend convenience
- zone snapshots/import/export that are explicitly HA-local

---

## 7. What must move out of HA/HACS over time

These areas are conceptually drifted and must not expand further in this repo:

1. `custom_components/copilot_ha/core/modules/*`
   - Too much Core-like module/runtime logic currently lives inside the HA package.
   - Freeze expansion.
   - Long-term direction: migrate true business/runtime logic to Core and leave HA adapters only.

2. HA-local semantic matchers and brain language
   - `habitus_zones_store_v2.py` should not grow as a "Brain Graph" truth layer
   - `zone_auto_setup.py` / `habitus_zones_entities_v2.py` heuristics may remain for bootstrap/suggestion, but not as canonical semantic truth

3. Core-served frontend bundles as primary card source
   - remove ownership ambiguity
   - keep the HACS package self-contained

---

## 8. Release and packaging responsibilities

## HA/HACS release reviewer must verify
- `hacs.json` is valid for tagged HACS installs
- `manifest.json`, version files, and package layout agree
- startup/import path is clean in HA
- config flow/options flow load
- webhook receiver loads
- dashboards/resources/cards are present and locally shippable
- no new required dependency on Core Python imports
- no new Core business logic was added under the HA package

## Core release reviewer must verify
- endpoints used by HA still exist and match expected payloads
- webhook event types remain compatible
- module schemas remain renderable by HA
- conversation/STT/TTS endpoints remain compatible
- runtime truth surfaces consumed by HA still work

## Cross-lane rule
A change is not complete unless the owner states which lane it belongs to:
- **HA/HACS version**
- **Core/Add-on version**
- **git/repo state**
- **live/runtime state**

Do not collapse them.

---

## 9. Documentation that must exist so autonomous work stops drifting

Before autonomous work proceeds freely, the HA repo must keep these docs current:

1. **This directive** — conceptual ownership boundary
2. **HA concept review** — go/no-go criteria for boundary compliance
3. **HA↔Core contract inventory**
   - every Core endpoint HA calls
   - every webhook event Core sends
   - which side owns each payload shape
4. **Frontend ownership note**
   - where card JS lives
   - how dashboards get wired
   - whether any Core-served assets remain transitional only
5. **Release checklist by lane**
   - HA/HACS checklist
   - Core checklist
   - live verification checklist

---

## 10. Immediate decisions from this review

1. **HA remains the Home Assistant adapter and UX surface, not a second Core.**
2. **Curated zone definitions tied to HA belong to HA; runtime meaning of those zones belongs to Core.**
3. **Event capture belongs to HA; event interpretation belongs to Core.**
4. **Cards/dashboards/resources belong to HA/HACS; Core should provide data, not own the shipped HA frontend.**
5. **No new required Core Python imports inside the HA package.**
6. **No new Core-like module growth under `custom_components/copilot_ha/core/modules/`.**

These six decisions are the durable concept boundary for the HA/HACS side.
