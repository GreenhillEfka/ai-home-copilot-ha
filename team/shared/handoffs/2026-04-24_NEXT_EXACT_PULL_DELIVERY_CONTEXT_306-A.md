# 2026-04-24 — Next exact pull: DELIVERY-CONTEXT-306-A

**Stand:** 2026-04-24 Europe/Berlin
**Status:** ready now
**Owner:** PilotClaw
**Why now:** `DELIVERY-INTERACTIVE-303-A/B`, `DELIVERY-DURABILITY-304`, and `E2E-OBSERVABILITY-305` are file-backed closed. The strongest remaining follow-up from the concept review is object/context framing, so delivery truth is not only token/state technical output but also names the real household-visible object. This stays on the same delivery seam without opening a new action family.

## Goal
Add one bounded canonical **delivery context envelope** on the existing Core read paths so delivery status/proof names the user-visible object, not only `delivery_token` + state.

## Canonical user-visible object
`zone-driven household prompt on a named surface`

## Exact seam
Normalize existing delivery metadata into a read-only `context` object on the current delivery status/proof outputs.

## Exact files
- `/config/clawd/team/worktrees/pilotsuite-styx-core-current/addons/pilotsuite/app/copilot_core/api/v1/delivery_interactive.py`
- `/config/clawd/team/worktrees/pilotsuite-styx-core-current/addons/pilotsuite/app/copilot_core/api/v1/observability.py`
- `/config/clawd/team/worktrees/pilotsuite-styx-core-current/addons/pilotsuite/app/copilot_core/api/v1/delivery_intent_store.py`
- `/config/clawd/team/worktrees/pilotsuite-styx-core-current/tests/test_delivery_context_306_contract.py`

## Required behavior
1. Existing API family stays bounded:
   - `POST /api/v1/delivery/acknowledge`
   - `GET /api/v1/delivery/<delivery_token>/status`
   - `GET /api/v1/delivery/<delivery_token>/proof`
   - `GET /api/v1/observability/delivery-proof`
2. Add a canonical read-only `context` object to the delivery read paths.
3. `context` must stay small and explicit:
   - `zone`
   - `surface`
   - `prompt_label`
4. `context` is derived from the existing stored metadata path only, not from a new endpoint family.
5. Missing context remains explicit and non-crashing, not silently widened.

## Focused proof ring
```bash
cd /config/clawd/team/worktrees/pilotsuite-styx-core-current
python3 -m py_compile \
  addons/pilotsuite/app/copilot_core/api/v1/delivery_interactive.py \
  addons/pilotsuite/app/copilot_core/api/v1/observability.py \
  addons/pilotsuite/app/copilot_core/api/v1/delivery_intent_store.py

/config/clawd/.venv_smoke_gate/bin/python -m pytest -q \
  tests/test_delivery_context_306_contract.py \
  tests/test_delivery_interactive_api_contract.py \
  tests/test_e2e_observability_305_contract.py
```

## Done means
- delivery read paths expose one canonical `context` object
- proof/status stay machine-checkable and backward-safe
- no new endpoint family exists
- proof ring green
- commit landed with a short closeout packet
- next exact pull advances to `DELIVERY-CONTEXT-306-B`

## Non-goals
- no new action button family
- no delivery broker rewrite
- no dashboard family
- no broad observability platform work
- no HA-side UI work in this packet

## Next exact pull after landing
- `DELIVERY-CONTEXT-306-B` — HA projection of the same canonical delivery context envelope
