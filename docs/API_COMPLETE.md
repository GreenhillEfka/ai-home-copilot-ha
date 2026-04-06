"""API Reference — Complete PilotSuite Core API Documentation."""

# PilotSuite Core API Reference

**Version:** 1.0.0-rc2  
**Base URL:** `http://localhost:8080`  
**Authentication:** JWT Bearer Token

---

## Table of Contents

1. [Authentication](#authentication)
2. [System Endpoints](#system-endpoints)
3. [Events API](#events-api)
4. [Vector API](#vector-api)
5. [Knowledge Graph API](#knowledge-graph-api)
6. [Mood/Neural API](#moodneural-api)
7. [Habitus API](#habitus-api)
8. [Search API](#search-api)
9. [Tags API](#tags-api)
10. [Dashboard API](#dashboard-api)

---

## Authentication

### Get Token

```http
POST /api/v1/auth/token
Content-Type: application/json

{
  "api_key": "your_api_key",
  "scope": "read"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 86400,
  "scope": "read"
}
```

**Scopes:**
- `read` — Read-only access
- `write` — Read + write access
- `admin` — Full access

### Revoke Token

```http
POST /api/v1/auth/revoke
Authorization: Bearer <token>

token=<token_to_revoke>
```

---

## System Endpoints

### Health Check

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0-rc2",
  "uptime_seconds": 3600.5,
  "timestamp": 1712444400.0
}
```

### Version Info

```http
GET /version
```

**Response:**
```json
{
  "version": "1.0.0-rc2",
  "build": "takeover/main",
  "python": "3.10+",
  "fastapi": true
}
```

### System Status

```http
GET /api/v1/status
Authorization: Bearer <token>
```

**Response:**
```json
{
  "status": "operational",
  "version": "1.0.0-rc2",
  "modules": {
    "rag": true,
    "ml": true,
    "presence": true,
    "energy": true,
    "brain": true,
    "voice": true
  },
  "capabilities": [
    "vector_search",
    "embedding",
    "presence_detection",
    "energy_optimization",
    "knowledge_graph",
    "voice_pipeline"
  ],
  "timestamp": 1712444400.0
}
```

### Capabilities

```http
GET /api/v1/capabilities
Authorization: Bearer <token>
```

---

## Events API

### Get Events

```http
GET /api/v1/events?limit=100
Authorization: Bearer <token>
```

### Create Event

```http
POST /api/v1/events
Authorization: Bearer <token>
Content-Type: application/json

{
  "type": "motion",
  "entity_id": "pir.living_room",
  "data": {"confidence": 0.95}
}
```

### Batch Event Ingestion

```http
POST /api/v1/events/batch
Authorization: Bearer <token>
Content-Type: application/json

{
  "events": [
    {"type": "motion", "entity_id": "pir.1"},
    {"type": "motion", "entity_id": "pir.2"}
  ]
}
```

---

## Vector API

### Vector Stats

```http
GET /api/v1/vector/stats
Authorization: Bearer <token>
```

**Response:**
```json
{
  "vector_count": 1000,
  "dimension": 384,
  "memory_usage_mb": 50.5
}
```

### List Vectors

```http
GET /api/v1/vector/vectors?limit=100
Authorization: Bearer <token>
```

### Create Embeddings

```http
POST /api/v1/vector/embeddings
Authorization: Bearer <token>
Content-Type: application/json

{
  "texts": ["Text 1", "Text 2"]
}
```

### Similarity Search

```http
GET /api/v1/vector/similar/{entity_id}?k=10
Authorization: Bearer <token>
```

### Custom Similarity Query

```http
POST /api/v1/vector/similarity
Authorization: Bearer <token>
Content-Type: application/json

{
  "query_vector": [0.1, 0.2, ...],
  "k": 10,
  "filters": {"type": "document"}
}
```

---

## Knowledge Graph API

### Graph Stats

```http
GET /api/v1/graph/stats
Authorization: Bearer <token>
```

### Graph State

```http
GET /api/v1/graph/state?entity_type=device
Authorization: Bearer <token>
```

### Graph Patterns

```http
GET /api/v1/graph/patterns
Authorization: Bearer <token>
```

### Graph Snapshot (SVG)

```http
GET /api/v1/graph/snapshot.svg
Authorization: Bearer <token>
```

---

## Mood/Neural API

### Mood State

```http
GET /api/v1/mood/state
Authorization: Bearer <token>
```

### Mood Score

```http
GET /api/v1/mood/score
Authorization: Bearer <token>
```

### Neural System State

```http
GET /api/v1/neurons
Authorization: Bearer <token>
```

### Evaluate Neurons

```http
POST /api/v1/neurons/evaluate
Authorization: Bearer <token>
Content-Type: application/json

{
  "input_data": {...}
}
```

---

## Habitus API

### User Habitus

```http
GET /api/v1/habitus/mine
Authorization: Bearer <token>
```

### Dashboard Cards

```http
GET /api/v1/habitus/dashboard-cards
Authorization: Bearer <token>
```

---

## Search API

### Semantic Search

```http
GET /api/v1/search?q=query&limit=20
Authorization: Bearer <token>
```

**Response:**
```json
{
  "results": [
    {"id": "doc_1", "score": 0.95, "text": "..."},
    {"id": "doc_2", "score": 0.87, "text": "..."}
  ],
  "query": "query",
  "total": 2
}
```

---

## Tags API

### List Tags

```http
GET /api/v1/tags
Authorization: Bearer <token>
```

---

## Candidates API

### List Candidates

```http
GET /api/v1/candidates
Authorization: Bearer <token>
```

---

## Dashboard API

### Brain Summary

```http
GET /api/v1/dashboard/brain-summary
Authorization: Bearer <token>
```

### Dashboard Health

```http
GET /api/v1/dashboard/health
Authorization: Bearer <token>
```

---

## Error Responses

### 401 Unauthorized

```json
{
  "error": "Unauthorized",
  "message": "Invalid or expired token",
  "code": "HTTP_401",
  "timestamp": 1712444400.0
}
```

### 429 Rate Limit Exceeded

```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests",
  "code": "HTTP_429",
  "timestamp": 1712444400.0
}
```

Headers: `Retry-After: 60`

### 500 Internal Server Error

```json
{
  "error": "Internal Server Error",
  "message": "An unexpected error occurred",
  "code": "INTERNAL_ERROR",
  "timestamp": 1712444400.0
}
```

---

## Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| All endpoints | 100 requests | 60 seconds |

---

## OpenAPI Documentation

Interactive API documentation available at:
- **Swagger UI:** `/docs`
- **ReDoc:** `/redoc`
- **OpenAPI JSON:** `/openapi.json`

---

*Last updated: 2026-04-07*
*Version: 1.0.0-rc2*
