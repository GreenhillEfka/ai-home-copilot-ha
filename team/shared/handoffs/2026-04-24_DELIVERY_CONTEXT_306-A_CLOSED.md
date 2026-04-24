# DELIVERY-CONTEXT-306-A — closed

**Stand:** 2026-04-24 Europe/Berlin
**Owner:** PilotClaw
**Commit:** `37fe0deb` (`feat(core): DELIVERY-CONTEXT-306-A context envelope (10 tests)`)

## Landed truth
- the existing canonical delivery read paths now expose one bounded read-only `context` envelope
- `context` stays explicit and small:
  - `zone`
  - `surface`
  - `prompt_label`
- context is derived only from the existing stored metadata path
- missing context remains explicit with null fields and does not widen semantics or crash
- no new endpoint family or action family was introduced

## Exact files
- `addons/pilotsuite/app/copilot_core/api/v1/delivery_interactive.py`
- `addons/pilotsuite/app/copilot_core/api/v1/observability.py`
- `addons/pilotsuite/app/copilot_core/api/v1/delivery_intent_store.py`
- `tests/test_delivery_context_306_contract.py`

## Focused proof
```bash
python3 -m py_compile \
  addons/pilotsuite/app/copilot_core/api/v1/delivery_interactive.py \
  addons/pilotsuite/app/copilot_core/api/v1/observability.py \
  addons/pilotsuite/app/copilot_core/api/v1/delivery_intent_store.py

/config/clawd/.venv_smoke_gate/bin/python -m pytest -q \
  tests/test_delivery_context_306_contract.py \
  tests/test_delivery_interactive_api_contract.py \
  tests/test_e2e_observability_305_contract.py
```

## Proof result
- syntax: PASS
- context proof ring: `42 passed`

## User-visible / config effect
- delivery status and proof now name the household-visible object as a bounded context envelope on the existing Core seam
- visualization and config follow-on remains deferred to `DELIVERY-CONTEXT-306-B`

## Queue effect
`DELIVERY-CONTEXT-306-A` is file-backed closed.
Next exact pull: `DELIVERY-CONTEXT-306-B`.
