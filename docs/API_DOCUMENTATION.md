# PilotSuite Core API - OpenAPI Specification

**Current Version:** v0.9.1-alpha.6  
**Last Updated:** 2026-02-17 17:45

This document describes the OpenAPI specification for the PilotSuite Core Add-on API.

## Endpoints

### System Endpoints
- `GET /health` - System health
- `GET /version` - Version info
- `GET /api/v1/status` - Status
- `GET /api/v1/capabilities` - Capabilities

### Event Endpoints
- `POST /api/v1/events` - Ingest events
- `GET /api/v1/events` - Query events
- `GET /api/v1/events/stats` - Event statistics

### Brain Graph Endpoints
- `GET /api/v1/graph/state` - Graph state
- `GET /api/v1/graph/stats` - Graph statistics
- `POST /api/v1/graph/snapshot` - Create snapshot
- `DELETE /api/v1/graph/prune` - Prune old data

### Habitus Endpoints
- `GET /api/v1/habitus/rules` - Get rules
- `POST /api/v1/habitus/mine` - Mine patterns
- `GET /api/v1/habitus/dashboard` - Dashboard cards

### Mood Endpoints (v0.9.1-alpha.6)
- `POST /api/v1/mood/score` - Score events
- `GET /api/v1/mood/state` - Current mood state
- `POST /api/v1/mood/zones/{zone_name}/orchestrate` - Zone orchestration
- `POST /api/v1/mood/zones/{zone_name}/force_mood` - Force mood
- `GET /api/v1/mood/zones/{zone_name}/status` - Zone status
- `GET /api/v1/mood/zones/status` - All zones status

### Neurons Endpoints
- `GET /api/v1/neurons/state` - Neuron state
- `GET /api/v1/neurons/stats` - Neuron statistics

### Candidates Endpoints
- `GET /api/v1/candidates` - Get candidates
- `POST /api/v1/candidates` - Create candidate
- `DELETE /api/v1/candidates/{id}` - Delete candidate

### User Preferences Endpoints
- `GET /api/v1/user/preferences` - Get user preferences
- `POST /api/v1/user/preferences` - Set user preferences

### Performance Endpoints
- `GET /api/v1/performance/stats` - Cache stats
- `GET /api/v1/performance/pool/status` - Connection pool status
- `GET /api/v1/performance/metrics` - Performance metrics
- `DELETE /api/v1/performance/cache/clear` - Clear cache

## Authentication
All endpoints require `X-Auth-Token` header when authentication is enabled.

## Idempotency
Event endpoints support `Idempotency-Key` header for deduplication.

## Error Responses
All endpoints return standard error responses:
```json
{
  "ok": false,
  "error": "Error message"
}
```

## Status Codes
- `200` - Success
- `401` - Authentication required
- `429` - Rate limited
- `500` - Internal error
