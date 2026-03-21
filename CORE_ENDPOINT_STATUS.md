# Core Endpoint Status — Live Measurement

**Measured:** Sat 2026-03-21 22:20 GMT+1  
**Core:** localhost:8909  
**Source:** curl against live Core without auth token

## Zone Automation API (`/api/v1/zone-automation/`)

| Endpoint | Method | Status | Notes |
|---|---|---|---|
| `/dashboard` | GET | 200 | Works without auth |
| `/module-schemas` | GET | 200 | Returns 7 modules with 39 fields |
| `/zones/{zone_id}` | GET | 200 | Single zone, no plural `/zones` |
| `/zones/{zone_id}/config` | POST | 401 | Needs auth (expected) |
| `/zones/{zone_id}/mode` | GET/POST | 401 | Needs auth (expected) |
| `/zones/{zone_id}/presence` | POST | 401 | Needs auth (expected) |
| `/zones/{zone_id}/modules/{id}` | GET/POST | 401 | Needs auth (expected) |
| `/ensure-zones` | POST | 401 | Needs auth — route exists |
| `/sync-definitions` | POST | 401 | Needs auth — route exists |
| `/zones` | GET | 404 | No plural route — only `/zones/{id}` |
| `/mood-profiles` | GET | ? | Not tested |
| `/entities/search` | GET | ? | Not tested |

## Other Core APIs

| Endpoint | Status |
|---|---|
| `/health` | 200 — version: 14.7.3 |
| `/api/v1/zones` | 200 — 0 zones (no auth, no write) |
| `/api/v1/openapi.json` | 200 — 71 endpoints (no zone-automation listed) |
| `/api/v1/autonomy/dashboard` | 401 — needs auth |
| `/api/v1/modules/dashboard` | 401 — needs auth |

## Conclusions

- **Routing: COMPLETE** — no routing drift
- **Auth required** — POST endpoints need HA addon token
- **No `/zones` plural** — only `/zones/{zone_id}`
- **Core version: 14.7.3** — but code appears to be v15 (all routes present)

## Action After Addon Restart

1. HA addon → Restart
2. HA calls `POST /ensure-zones` with token → creates 12 zones in Core
3. HA calls `POST /sync-definitions` → syncs entity metadata
4. Dashboard shows zones + module states
