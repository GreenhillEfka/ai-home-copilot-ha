# AI Home CoPilot – Model v0.1 (Habitus → Candidates → Mood)

This doc is **implementation-oriented** (what we’ll very likely need soon) and keeps **privacy-first** + **governance-first** constraints.

## 0) Goals (near-term)
- Turn raw HA events into **Habitus patterns** (A→B correlations).
- Convert patterns into **Candidates** (actionable automation suggestions) with clear explainability.
- Rank candidates using a small **Mood** vector (comfort / frugality / joy + guardrails).
- Surface candidates in HA via **Repairs + Blueprint**, never creating automations silently.

## 1) Core concepts
### 1.1 Event
Minimal event schema for ingestion (from HA Integration → Core):

```json
{
  "event_id": "uuid",
  "ts": "2026-02-07T10:00:00+01:00",
  "source": "home_assistant",
  "kind": "state_changed",
  "entity_id": "light.kitchen",
  "old_state": "off",
  "new_state": "on",
  "attributes": {
    "domain": "light"
  },
  "context": {
    "user_id": null,
    "automation_id": null
  }
}
```

Privacy notes:
- Don’t ship any personal entity_ids in repo defaults.
- In the Core storage, we can **optionally** hash `entity_id` at rest, but we still need cleartext for building a candidate/blueprint input mapping. Practical approach: store cleartext but keep retention short + avoid exporting.

### 1.2 Habitus Pattern (A→B)
A pattern represents: “When A happens, B tends to follow within Δt”.

Data we want to compute:
- `a` (trigger signature): entity + transition (e.g. `switch.coffee_machine: off→on`)
- `b` (action signature): entity + transition or service-like effect (e.g. `switch.grinder: off→on`)
- `window_s`: max time window for matching (e.g. 180s)
- `support`: number of observed A occurrences
- `matches`: number of A occurrences followed by B within window
- `confidence = matches / support`
- `baseline_b_rate`: probability of B within same window without A (for lift)
- `lift = confidence / baseline_b_rate` (or other association metric)
- `median_dt`, `p90_dt`: response-time distribution
- `stability`: how consistent across days/weeks

### 1.3 Candidate
A candidate is an actionable, governed suggestion.

Core candidate schema (storage / API):
```json
{
  "candidate_id": "hab_a_to_b__kitchen__001",
  "kind": "blueprint",
  "blueprint": {
    "blueprint_id": "ai_home_copilot/a_to_b_safe",
    "inputs": {
      "a_entity": "switch.coffee_machine",
      "a_to_state": "on",
      "a_for": {"seconds": 0},
      "b_target": {"entity_id": ["switch.grinder"]},
      "b_action": "turn_on"
    }
  },
  "explanation": {
    "summary": "Wenn Kaffeemaschine an → folgt meist Mühle an (≈45s später).",
    "evidence": {
      "support": 37,
      "confidence": 0.78,
      "median_dt_seconds": 42,
      "lift": 6.2
    },
    "guardrails": [
      "local_only",
      "no_external_calls",
      "target_domains: light|switch|fan"
    ]
  },
  "ranking": {
    "score": 0.81,
    "mood": {"comfort": 0.7, "frugality": 0.4, "joy": 0.6},
    "risk": 0.1
  },
  "lifecycle": {
    "state": "new",
    "first_seen_ts": "...",
    "last_seen_ts": "...",
    "last_offered_ts": null
  }
}
```

Lifecycle states (Core-side):
- `new` → discovered, not yet offered
- `offered` → shown in HA (Repairs issue exists)
- `accepted` → user confirmed + created automation
- `dismissed` → user rejected; don’t offer again
- `deferred` → user postponed; offer again later
- `stale` → pattern no longer holds (optional)

HA-side storage we already have (`storage.py`) maps cleanly to `accepted/dismissed/offered`.

## 2) Mood v0.1 (small, useful)
We don’t need a complex affect model yet; we need a **consistent scoring vector**.

Recommended minimal mood vector (values 0..1):
- `comfort`: reduces friction (fewer manual steps, fewer “oops I forgot” moments)
- `frugality`: saves energy/consumables, avoids waste
- `joy`: adds delight (scenes, ambiance, playful convenience)

(We can extend later to the 7-dim concept, but these 3 are the ones we’ll actually use early.)

Mood signals (heuristics, no LLM required initially):
- Comfort: number of steps saved, frequency of pattern, time-of-day convenience
- Frugality: devices involved (HVAC, lights), typical runtime impact, avoids idle-on
- Joy: scenes/lights/music patterns, user-initiated routines

## 3) Ranking formula (v0.1)
We need something deterministic, debuggable.

### 3.1 Quality score
- `q1 = clamp(confidence, 0..1)`
- `q2 = clamp(log1p(lift)/log1p(10), 0..1)` (cap lift)
- `q3 = clamp(min(1, support/30), 0..1)`
- `q = 0.45*q1 + 0.35*q2 + 0.20*q3`

### 3.2 Risk score (guardrails)
Start conservative:
- Penalize cross-domain actions with side effects (locks, covers, alarms) → disallow in safe blueprint
- Penalize actions that could be annoying (turn_off music, change thermostat) unless explicit allowlist

`risk ∈ [0..1]`, default low for allowed domains only.

### 3.3 Final score
`score = 0.65*q + 0.25*mood_mix - 0.10*risk`

Where `mood_mix` is a weighted sum based on user priorities (defaults can be equal; later configurable in Integration options).

## 4) Governance UX mapping (HA)
We already implement:
- Create Repairs issue with `is_fixable=true`.
- Fix flow asks user to confirm after blueprint/automation creation.

Next incremental improvements (likely needed):
- Provide a **direct link** to Blueprints UI filtered by `ai_home_copilot`.
- Add choices: `accepted`, `dismissed`, `defer 7 days`.
- Store `deferred_until_ts` in HA storage to avoid re-offering too soon.

## 5) API v1 endpoints (minimum set)
Core:
- `POST /api/v1/ingest/events` (batch)
- `GET /api/v1/habitus/candidates` (list new/offered)
- `POST /api/v1/habitus/candidates/{id}/accept|dismiss|defer`

Push option:
- Core → HA webhook: send `{"data": {"online": true, "version": "..."}}` (already supported)
- Later: send candidate notifications similarly (we’ll extend webhook payload envelope)

Auth:
- Always `X-Auth-Token` header.
- Token must never be written to logs.

## 6) Data retention & privacy
Pragmatic defaults:
- Store events in a rolling window (e.g. 7–14 days) sufficient for mining.
- Keep only aggregate stats for older periods.
- Never export raw events outside LAN.
- No personal identifiers in repo defaults; all user-specific configuration is entered via UI.

## 7) “We will definitely need this soon” checklist
- [ ] Candidate lifecycle incl. `defer` and `deferred_until`.
- [ ] Evidence fields (support/confidence/lift + dt stats) for explainability.
- [ ] Stable blueprint id + input mapping.
- [ ] Deterministic ranking formula + guardrails.
- [ ] Retention policy for events.
