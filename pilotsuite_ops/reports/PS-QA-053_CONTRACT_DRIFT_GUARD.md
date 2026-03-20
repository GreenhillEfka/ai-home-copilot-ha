# PS-QA-053 — Webhook Contract Drift Guard Report

- generated_at_utc: `2026-03-19 07:54:54Z`
- result: **FAIL**

## Zielcodes

- `missing_type`, `missing_data`, `unknown_type`, `invalid_token`, `invalid_payload`

## Geprüfte Quellen

- core_openapi: `/config/clawd/team/repos/pilotsuite-styx-ha/team/repos/pilotsuite-styx-core/docs/openapi.yaml`
- ha_openapi: `/config/clawd/team/repos/pilotsuite-styx-ha/team/repos/pilotsuite-styx-ha/docs/openapi.yaml`
- ha_runtime: `/config/clawd/team/repos/pilotsuite-styx-ha/team/repos/pilotsuite-styx-ha/custom_components/copilot_ha/webhook.py`
- response_schema: `/config/clawd/team/repos/pilotsuite-styx-ha/pilotsuite_ops/schemas/webhook_response.schema.json`

## Ergebnis je Quelle

### core_openapi

- status: FAIL (Datei nicht lesbar)
- detail: `read_error: [Errno 2] No such file or directory: '/config/clawd/team/repos/pilotsuite-styx-ha/team/repos/pilotsuite-styx-core/docs/openapi.yaml'`

### ha_openapi

- status: FAIL (Datei nicht lesbar)
- detail: `read_error: [Errno 2] No such file or directory: '/config/clawd/team/repos/pilotsuite-styx-ha/team/repos/pilotsuite-styx-ha/docs/openapi.yaml'`

### ha_runtime

- status: FAIL (Datei nicht lesbar)
- detail: `read_error: [Errno 2] No such file or directory: '/config/clawd/team/repos/pilotsuite-styx-ha/team/repos/pilotsuite-styx-ha/custom_components/copilot_ha/webhook.py'`

### response_schema

- present (5/5): `missing_type`, `missing_data`, `unknown_type`, `invalid_token`, `invalid_payload`
- missing (0): (none)

