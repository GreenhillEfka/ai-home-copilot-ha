# 2026-04-24 — Next exact pull: DELIVERY-CONTEXT-306-B

**Stand:** 2026-04-24 Europe/Berlin
**Status:** queued behind `DELIVERY-CONTEXT-306-A`
**Owner:** HomeClaw
**Why next:** once Core read paths expose one canonical delivery `context` object, HA must project the same bounded context on the existing delivery interaction confirmation path so the household-visible object is preserved end-to-end without inventing a new UI family.

## Goal
Project the canonical delivery `context` envelope from the existing Core delivery read path into the existing HA confirmation path.

## Canonical user-visible object
`zone-driven household prompt on a named surface`

## Exact seam
Extend the existing HA `delivery_interactive` projection so HA-visible confirmation and emitted event data carry the same bounded `context` object from canonical Core state.

## Exact files
- `/config/clawd/team/worktrees/pilotsuite-styx-ha-current/custom_components/pilotsuite/services_setup.py`
- `/config/clawd/team/worktrees/pilotsuite-styx-ha-current/tests/test_delivery_context_306_ha_projection.py`

## Required behavior
1. Stay on the existing HA seam only:
   - `pilotsuite.delivery_interactive`
   - existing persistent notification confirmation
   - existing `pilotsuite_delivery_interactive` event projection
2. Read canonical `context` from the current Core delivery status/proof payload only.
3. `context` remains small and explicit:
   - `zone`
   - `surface`
   - `prompt_label`
4. Missing `context` stays explicit and non-crashing.
5. No new HA action family, dashboard family, or detached card path is introduced.

## Focused proof ring
```bash
cd /config/clawd/team/worktrees/pilotsuite-styx-ha-current
python3 -m py_compile \
  custom_components/pilotsuite/services_setup.py \
  tests/test_delivery_context_306_ha_projection.py

.venv/bin/python -m pytest -q \
  tests/test_delivery_context_306_ha_projection.py \
  tests/test_e2e_observability_305_ha_projection.py \
  tests/test_delivery_interactive_service_projection.py
```

## Done means
- HA confirmation path projects one canonical `context` object on the existing seam
- event payload stays machine-checkable and bounded
- proof ring green
- commit landed with a short closeout packet
- next exact pull advances to `RAG-RESILIENCE-307`

## Non-goals
- no new dashboard/card family
- no config-flow widening
- no second delivery action family
- no Core seam changes in this packet

## Next exact pull after landing
- `RAG-RESILIENCE-307` — make degraded retrieval truth explicit on the existing Core RAG seam
