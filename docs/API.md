# AI Home CoPilot Core API Reference

## Base URL

```
http://homeassistant.local:8909/api/v1
```

## Authentication

All endpoints require `X-Auth-Token` header when authentication is enabled:

```http
X-Auth-Token: your-secret-token
```

## Idempotency

Event endpoints support `Idempotency-Key` header for deduplication:

```http
Idempotency-Key: unique-key-per-request
```

---

## Habitus Module

### Get Habitus Status

```http
GET /api/v1/habitus/status
```

**Response:**
```json
{
  "status": "ok",
  "version": "0.4.5",
  "statistics": {
    "total_rules": 42,
    "total_events": 1250,
    "last_mining_ms": 125
  },
  "config": {
    "min_confidence": 0.5,
    "max_delta_seconds": 3600
  }
}
```

### Get Discovered Rules

```http
GET /api/v1/habitus/rules?limit=100&min_score=0.5
```

**Query Parameters:**
- `limit`: Maximum rules to return (default: 100)
- `min_score`: Minimum score filter
- `a_filter`: Filter by antecedent entity
- `b_filter`: Filter by consequent entity
- `domain_filter`: Filter by domain

**Response:**
```json
{
  "status": "ok",
  "total_rules": 42,
  "rules": [
    {
      "A": "person.anna_arrived_home",
      "B": "light.living_room_on",
      "dt_sec": 120.5,
      "nA": 25,
      "nB": 40,
      "nAB": 18,
      "confidence": 0.72,
      "confidence_lb": 0.65,
      "lift": 1.85,
      "leverage": 0.08,
      "score": 0.78,
      "evidence": {
        "hit_examples": [
          {"A_ts": "2026-02-15T10:30:00Z", "B_ts": "2026-02-15T10:32:00Z"}
        ],
        "miss_examples": []
      }
    }
  ]
}
```

### Trigger Mining

```http
POST /api/v1/habitus/mine
Content-Type: application/json
```

**Request:**
```json
{
  "events": [
    {
      "type": "state_changed",
      "entity_id": "light.kitchen",
      "old_state": {"state": "off"},
      "new_state": {"state": "on"}
    }
  ],
  "config": {
    "min_confidence": 0.5,
    "max_delta_seconds": 3600
  }
}
```

**Response:**
```json
{
  "status": "ok",
  "mining_time_sec": 0.125,
  "total_input_events": 150,
  "discovered_rules": 8,
  "top_rules": [...]
}
```

---

## Graph Module

### Get Brain Graph State

```http
GET /api/v1/graph/state?max_nodes=500&max_edges=2000
```

**Response:**
```json
{
  "status": "ok",
  "nodes": [
    {
      "id": "light.living_room",
      "type": "entity",
      "label": "Living Room Light",
      "domain": "light",
      "score": 0.85
    }
  ],
  "edges": [
    {
      "source": "person.anna",
      "target": "light.living_room",
      "type": "controls",
      "weight": 0.72
    }
  ]
}
```

### Sync Graph with HA Entities

```http
POST /api/v1/graph/sync
Content-Type: application/json
```

**Request:**
```json
{
  "entities": [
    {
      "entity_id": "light.living_room",
      "domain": "light",
      "attributes": {}
    }
  ],
  "full_sync": false
}
```

**Response:**
```json
{
  "status": "ok",
  "nodes_added": 15,
  "nodes_updated": 3,
  "nodes_removed": 0,
  "edges_added": 22
}
```

---

## Mood Module

### Get Current Mood

```http
GET /api/v1/mood?zone_id=living&user_id=person.anna
```

**Response:**
```json
{
  "status": "ok",
  "mood": {
    "score": 0.72,
    "confidence": 0.85,
    "factors": [
      {
        "name": "media_activity",
        "value": 0.9,
        "weight": 0.4
      },
      {
        "name": "time_of_day",
        "value": 0.8,
        "weight": 0.3
      }
    ]
  },
  "zone_id": "living",
  "user_id": "person.anna"
}
```

---

## Tags Module

### Get All Tags

```http
GET /api/v1/tags2/tags
```

**Response:**
```json
{
  "status": "ok",
  "tags": [
    {
      "tag_id": "aicp.place.kueche",
      "namespace": "aicp",
      "facet": "place",
      "key": "kueche",
      "description": "Kitchen area",
      "created_at": "2026-02-15T10:00:00Z"
    }
  ]
}
```

### Create Tag

```http
POST /api/v1/tags2/tags
Content-Type: application/json
```

**Request:**
```json
{
  "tag_id": "aicp.device.speicher",
  "description": "Storage room device"
}
```

**Response:**
```json
{
  "status": "ok",
  "tag": {
    "tag_id": "aicp.device.speicher",
    "namespace": "aicp",
    "facet": "device",
    "key": "speicher",
    "description": "Storage room device",
    "created_at": "2026-02-15T10:00:00Z"
  }
}
```

### Assign Tag to Subject

```http
POST /api/v1/tags2/subjects/light.kitchen/tags
Content-Type: application/json
```

**Request:**
```json
{
  "tag_id": "aicp.place.kueche",
  "confidence": 0.95,
  "source": "inferred"
}
```

---

## Events Module

### Ingest Event

```http
POST /api/v1/events
Content-Type: application/json
Idempotency-Key: unique-key-123
```

**Request:**
```json
{
  "type": "state_changed",
  "text": "Living room light turned on",
  "payload": {
    "entity_id": "light.living_room",
    "old_state": {"state": "off"},
    "new_state": {"state": "on"}
  },
  "timestamp": "2026-02-15T10:00:00Z"
}
```

**Response:**
```json
{
  "ok": true,
  "stored": true,
  "deduped": false,
  "event_id": "evt_abc123"
}
```

---

## Candidates Module

### Get Candidates

```http
GET /api/v1/candidates?min_score=0.5&limit=50
```

**Response:**
```json
{
  "status": "ok",
  "candidates": [
    {
      "candidate_id": "cand_001",
      "trigger": {
        "entity_id": "person.anna_arrived_home",
        "type": "state"
      },
      "action": {
        "service": "light.turn_on",
        "target": {"entity_id": "light.living_room"}
      },
      "score": 0.78,
      "source": "habitus"
    }
  ]
}
```

### Get Candidate Statistics

```http
GET /api/v1/candidates/stats
```

**Response:**
```json
{
  "status": "ok",
  "total": 125,
  "by_source": {
    "habitus": 85,
    "neurons": 30,
    "manual": 10
  },
  "by_domain": {
    "light": 60,
    "switch": 40,
    "scene": 25
  }
}
```

---

## Neurons Module

### List All Neurons

```http
GET /api/v1/neurons
```

**Response:**
```json
{
  "success": true,
  "data": {
    "context": {},
    "state": {},
    "mood": {},
    "total_count": 5
  }
}
```

### Evaluate Neurons

```http
POST /api/v1/neurons/evaluate
Content-Type: application/json
```

**Request:**
```json
{
  "states": {
    "person.anna": "home",
    "light.living_room": "on"
  },
  "context": {
    "time_of_day": "evening",
    "weather": "cloudy"
  },
  "trigger": "person.anna_arrived_home"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "timestamp": "2026-02-15T10:00:00Z",
    "context_values": {},
    "state_values": {},
    "mood_values": {
      "joy": 0.85,
      "comfort": 0.72
    },
    "dominant_mood": "joy",
    "mood_confidence": 0.88,
    "suggestions": [
      "Turn on fireplace",
      "Adjust thermostat to 22°C"
    ],
    "neuron_count": 5
  }
}
```

---

## Vector Module

### Create Embedding

```http
POST /api/v1/vector/embeddings
Content-Type: application/json
```

**Request:**
```json
{
  "type": "entity",
  "id": "light.living_room",
  "domain": "light",
  "area": "living",
  "capabilities": ["on_off", "brightness"],
  "tags": ["aicp.place.living"],
  "state": {"state": "on", "brightness": 128},
  "metadata": {"source": "discovery"}
}
```

**Response:**
```json
{
  "ok": true,
  "entry": {
    "id": "light.living_room",
    "type": "entity",
    "created_at": "2026-02-15T10:00:00Z",
    "metadata": {"source": "discovery"}
  }
}
```

### Find Similar Entities

```http
GET /api/v1/vector/similar/light.living_room?limit=10&threshold=0.7
```

**Response:**
```json
{
  "ok": true,
  "query_id": "light.living_room",
  "query_type": "entity",
  "results": [
    {
      "id": "light.kitchen",
      "similarity": 0.85,
      "type": "entity",
      "metadata": {}
    }
  ],
  "count": 1
}
```

---

## System Module

### Get System Health

```http
GET /api/v1/system-health
```

**Response:**
```json
{
  "status": "ok",
  "checks": {
    "api": "ok",
    "storage": "ok",
    "ha_connection": "ok"
  },
  "version": "0.6.0",
  "uptime_seconds": 86400
}
```

---

## Documentation Endpoints

### Swagger UI

```http
GET /api/v1/docs
```

Returns interactive Swagger UI documentation.

### OpenAPI Spec (YAML)

```http
GET /api/v1/docs/openapi.yaml
```

Returns raw OpenAPI 3.0.3 specification.

### OpenAPI Spec (JSON)

```http
GET /api/v1/docs/openapi.json
```

Returns OpenAPI specification in JSON format.

### Validate OpenAPI

```http
GET /api/v1/docs/validate
```

**Response:**
```json
{
  "ok": true,
  "version": "0.4.34",
  "title": "AI Home CoPilot Core API",
  "path_count": 42,
  "tag_count": 12
}
```

---

## Error Responses

All endpoints may return error responses:

```json
{
  "status": "error",
  "message": "Error description",
  "code": "ERROR_CODE"
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `AUTH_REQUIRED` | Authentication token missing or invalid |
| `INVALID_PAYLOAD` | Request body validation failed |
| `NOT_FOUND` | Resource not found |
| `CONFLICT` | Idempotency key conflict |
| `INTERNAL_ERROR` | Server-side error |
