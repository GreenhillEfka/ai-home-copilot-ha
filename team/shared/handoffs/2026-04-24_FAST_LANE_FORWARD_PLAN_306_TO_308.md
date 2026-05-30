# 2026-04-24 — Fast lane forward plan (306-A → 308)

**Stand:** 2026-04-24 Europe/Berlin
**Purpose:** remove the queue gap completely. From here on, the next exact pull is always file-backed before the current wave tails out.
**Driving truth:**
- `/config/clawd/team/PILOTSUITE_PROGRESS_LEDGER.md`
- `/config/clawd/team/shared/handoffs/2026-04-24_NEXT_EXACT_PULL_DELIVERY_CONTEXT_306-A.md`
- `/config/clawd/team/shared/handoffs/2026-04-24_NEXT_EXACT_PULL_DELIVERY_CONTEXT_306-B.md`
- `/config/clawd/team/shared/handoffs/2026-04-22_PILOTSUITE_STATE_OF_THE_ART_AND_CONCEPT_REVIEW.md`
- `/config/clawd/docs/RAG_HYBRID_SEARCH.md`
- current Core RAG seam in `addons/pilotsuite/app/copilot_core/api/v1/rag.py`

## Hard execution rule
1. only one active writer packet at a time
2. the full downstream chain stays file-backed
3. no queue tail may stay unset while the current wave is still active
4. `topic:1` reports only landed truth, real blocker, or next exact pull

## Exact forward chain
1. `DELIVERY-CONTEXT-306-A` — PilotClaw — active now
2. `DELIVERY-CONTEXT-306-B` — HomeClaw — queued next
3. `RAG-RESILIENCE-307` — PilotClaw — queued behind `306-B`
4. `FAST-LANE-CONTINUITY-308` — Orakel/Hermes — queued behind `307`

## Packet 1 — DELIVERY-CONTEXT-306-A
**Goal:** expose one bounded canonical delivery `context` object on the Core delivery read/proof seam.

### Task breakdown
- `306A-1` normalize `context` from stored metadata only
- `306A-2` project `context` on delivery status output
- `306A-3` project the same `context` on delivery proof + observability output
- `306A-4` preserve explicit null fields for missing context
- `306A-5` run focused proof ring and land closeout packet

### Exit gate
- Core read paths expose `context.zone`, `context.surface`, `context.prompt_label`
- no new endpoint family
- focused proof ring green

## Packet 2 — DELIVERY-CONTEXT-306-B
**Goal:** project the same bounded `context` object onto the existing HA confirmation seam.

### Task breakdown
- `306B-1` read canonical `context` from current Core delivery payload
- `306B-2` extend HA service projection without widening the action family
- `306B-3` include `context` on event / confirmation payloads
- `306B-4` preserve explicit null behavior when Core has no context
- `306B-5` run focused HA proof ring and land closeout packet

### Exit gate
- HA-visible confirmation carries the same bounded `context`
- no new dashboard/card/action family
- focused proof ring green

## Packet 3 — RAG-RESILIENCE-307
**Goal:** make retrieval degradation explicit and deterministic so memory/research support does not silently depend on semantic availability alone.

### Exact seam
- `POST /api/v1/rag/search`
- `POST /api/v1/rag/search/enhanced`
- current semantic helper path in `addons/pilotsuite/app/copilot_core/api/v1/rag.py`

### Task breakdown
- `307-1` capture semantic degradation reason at the helper seam
- `307-2` expose structured retrieval truth on hybrid responses:
  - `effective_mode`
  - `degraded`
  - `degraded_reason`
- `307-3` keep hybrid/local search deterministic: if semantic degrades and lexical is allowed, return BM25-backed results with explicit degraded truth
- `307-4` preserve bounded behavior for semantic-only requests, no silent widening into a different contract
- `307-5` add focused contract coverage for configured, missing, and failing semantic backend cases
- `307-6` run proof ring and land closeout packet

### Exit gate
- degraded retrieval state is machine-checkable, not only hidden in prose warnings
- hybrid/local search stays useful when semantic is unavailable
- no new search family is opened
- focused proof ring green

## Packet 4 — FAST-LANE-CONTINUITY-308
**Goal:** ensure the chain never ends with an unset tail again.

### Task breakdown
- `308-1` reconcile fresh landed truth from `306-A`, `306-B`, and `307`
- `308-2` write the next exact pull packet(s) from fresh file truth before status chatter
- `308-3` update ledger + checkpoint card so routing truth is current
- `308-4` dispatch exact owners and capture accepted state where possible
- `308-5` leave a file-backed next chain, not an implicit promise

### Exit gate
- next wave exists as concrete packet files
- ledger queue has no unset tail
- owner handoffs are explicit

## Allowed blocker categories
Only these may stop the chain:
- real failing proof ring on the active bounded seam
- missing repository truth that prevents the exact packet from being cut honestly
- external dependency failure that prevents verification and cannot be isolated

## Not allowed as blockers
- vague uncertainty about what comes next
- missing orchestration prep
- timed-out chat handoff when file truth is already sufficient to continue
- meta discussion without packet updates

## End of this wave
This wave is complete only when:
- `306-A` landed
- `306-B` landed
- `307` landed
- `308` has already cut the next bounded wave
