# AI Home CoPilot – Next version concept (draft)

User goal (2026-02-07):
- Build first *Stimmungsmodule* (mood modules).
- Build *Habitusmodul* to detect behavior patterns (example: whenever coffee machine turns on, grinder also turns on).
- From patterns, propose automations and/or generate configurable “coffee module”.
- Generate early “synapses” linking two signals and weight them by mood.

Work in progress: spawned sub-agents for HA best practices + pattern detection + architecture spec.

## Working assumptions
- Copilot Core is an HA add-on exposing API (`/health`, `/version`), auth via `X-Auth-Token`.
- HA custom integration exists (`ai_home_copilot`) with webhook push + watchdog fallback.
- All actions that change state require user confirmation (user preference).

## Design sketch (to be refined)
- Core ingests HA event stream (either pulled via HA websocket API w/ LLAT, or pushed by HA integration via webhook/event bridge).
- Habitus engine: incremental association rules over discrete events (entity_id + state change), using time windows and confidence/lift.
- Mood engine: stores current mood state (manual + inferred) + weights recommendations.
- Synapse: directed relation A -> B, with stats (support, confidence, lift), context (time-of-day, day-of-week), mood-weighted score.
- Advisor: turns top synapses into recommended automations (Blueprints), surfaced in HA via Repairs/Issues + blueprint link; optional create button.

## MVP algorithm idea
- Watch for event pairs within T seconds (e.g., 120s).
- Update counts:
  - count(A)
  - count(B)
  - count(A then B within window)
- Compute confidence P(B|A)=count(A->B)/count(A)
- Compute lift = P(B|A)/P(B)
- Recommend when confidence >= threshold and lift >= threshold and count(A->B) >= min_support.

## Next steps
- Decide data flow: HA integration pushes state-change events to Core OR Core subscribes to HA websocket.
- Define Core endpoints for:
  - ingest events
  - list synapses
  - list recommendations
  - accept recommendation -> generate blueprint/automation
  - mood state get/set

