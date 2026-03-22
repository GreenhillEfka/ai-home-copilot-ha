# Deprecation Notice: `/api/v1/habitus/zones/*` → `/api/v1/zone-automation/*`

**Effective:** v15.1.0 (upcoming) | **Published:** 2026-03-22

## Summary

All endpoints under `/api/v1/habitus/zones/` are **deprecated** and will be removed in v16.0.0.

The Zone Automation API under `/api/v1/zone-automation/` is now the canonical interface for zone operations.

## Migration Table

| Old Endpoint | New Endpoint | Notes |
|---|---|---|
| `POST /api/v1/habitus/zones/sync` | `POST /api/v1/zone-automation/sync-definitions` | Primary HA→Core sync. Full payload. |
| `POST /api/v1/habitus/zones/sync` (IDs only) | `POST /api/v1/zone-automation/ensure-zones` | Auto-creates missing zones by ID. |
| `GET /api/v1/habitus/zones` | `GET /api/v1/zone-automation/zones` | List all zones. |
| `GET /api/v1/habitus/zones/:zone_id` | `GET /api/v1/zone-automation/zones/:zone_id` | Get zone details. |
| `PUT /api/v1/habitus/zones/:zone_id` | `PUT /api/v1/zone-automation/zones/:zone_id/config` | Update zone config. |
| `DELETE /api/v1/habitus/zones/:zone_id` | — | Use `sync-definitions` with `full_sync: true` to remove zones. |
| `GET /api/v1/habitus/zones/summary` | `GET /api/v1/zone-automation/dashboard` | Dashboard + stats. |

## Why This Change

- `/habitus/zones/sync` was a bidirectional merge endpoint that mixed concerns
- `/zone-automation/` separates concerns: `sync-definitions` (HA→Core full payload) vs `ensure-zones` (ID-only auto-creation)
- The new architecture aligns with the Phase 7 Zone E2E Contract

## Action Required

1. **HA Integration**: Update `copilot_ha` to use `/zone-automation/` endpoints
2. **Core**: Remove `/habitus/zones/*` route handlers in v15.1.0
3. **Documentation**: `docs/ZONE_EDITOR.md` references deprecated endpoints and should be archived or rewritten

## See Also

- `docs/API_REFERENCE.md` — Zone Automation section (current, v15.0.x)
- `docs/API_CONTRACT.yaml` — Zone Automation contract
- `ARCHITECTURE.md` — currently references v7.7.15, needs full refresh
