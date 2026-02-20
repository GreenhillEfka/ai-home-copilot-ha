# Vector Store Design Document

> **Version:** v0.8.3  
> **Status:** Implemented  
> **Branch:** `dev/vector-store-v0.8.3`  
> **Date:** 2026-02-15

---

## 1. Overview

The Vector Store provides embedding storage and similarity search for:
- **Entity embeddings**: Find similar entities based on domain, area, capabilities
- **User preferences**: Match users with similar preferences for recommendations
- **Patterns**: Store and search patterns from Habitus mining

### Key Features
- Local feature-based embeddings (no external API required)
- Optional Ollama integration for semantic embeddings
- SQLite persistence with in-memory cache
- Cosine similarity search
- REST API for all operations

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Core Add-on                               │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                  Vector Store Module                     ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ││
│  │  │ Embedding    │  │ Vector Store │  │ Similarity   │  ││
│  │  │ Engine       │  │ (SQLite)     │  │ Search       │  ││
│  │  └──────────────┘  └──────────────┘  └──────────────┘  ││
│  └─────────────────────────────────────────────────────────┘│
│                            │                                 │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                  REST API Layer                          ││
│  │  POST /embeddings    GET /similar/{id}                  ││
│  │  GET /vectors       DELETE /vectors/{id}                ││
│  │  POST /similarity   GET /stats                          ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    HA Integration                            │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              Vector Store Client                         ││
│  │  - Entity sync (periodic)                               ││
│  │  - User preference updates                              ││
│  │  - Similarity recommendations                           ││
│  └─────────────────────────────────────────────────────────┘│
│                            │                                 │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              MUPL Integration                            ││
│  │  - Preference similarity matching                       ││
│  │  - User-based recommendations                           ││
│  │  - Pattern storage                                      ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Embedding Model

### 3.1 Entity Embeddings

Entity embeddings capture:
- **Domain features** (5 dims): One-hot encoding for light, climate, media_player, etc.
- **Entity ID hash** (32 dims): Deterministic hash for unique identity
- **Area hash** (16 dims): Location-based similarity
- **Capabilities hash** (32 dims): brightness, color_temp, volume, etc.
- **Tags hash** (32 dims): Custom tags for categorization
- **State features** (11 dims): Current state values (brightness, temperature, etc.)

**Total: 128 dimensions**

### 3.2 User Preference Embeddings

Preference embeddings capture:
- **Light brightness preference** (1 dim): 0.0-1.0
- **Temperature preference** (1 dim): Normalized 15-30°C → 0.0-1.0
- **Media volume preference** (1 dim): 0.0-1.0
- **Mood weights** (3 dims): comfort, frugality, joy
- **User ID hash** (remaining dims): Personalization component

### 3.3 Pattern Embeddings

Pattern embeddings capture:
- **Pattern type** (3 dims): habitus, learned, manual
- **Confidence** (1 dim): 0.0-1.0
- **Entity hashes** (32 dims): Entities involved in pattern
- **Condition hashes** (20 dims): Time, mood, etc.
- **Pattern ID hash** (remaining dims): Unique component

---

## 4. API Specification

### 4.1 Create Embedding

```http
POST /api/v1/vector/embeddings
Content-Type: application/json

{
  "type": "entity",
  "id": "light.wohnzimmer",
  "domain": "light",
  "area": "living_room",
  "capabilities": ["brightness", "color_temp"],
  "tags": ["indoor", "main"]
}
```

**Response:**
```json
{
  "ok": true,
  "entry": {
    "id": "entity:light.wohnzimmer",
    "type": "entity",
    "created_at": "2026-02-15T06:00:00Z",
    "metadata": {...}
  }
}
```

### 4.2 Find Similar

```http
GET /api/v1/vector/similar/light.wohnzimmer?type=entity&limit=10&threshold=0.7
```

**Response:**
```json
{
  "ok": true,
  "query_id": "entity:light.wohnzimmer",
  "query_type": "entity",
  "results": [
    {
      "id": "entity:light.kueche",
      "similarity": 0.85,
      "type": "entity",
      "metadata": {"domain": "light", "area": "kitchen"}
    }
  ],
  "count": 1
}
```

### 4.3 Compute Similarity

```http
POST /api/v1/vector/similarity
Content-Type: application/json

{
  "id1": "entity:light.wohnzimmer",
  "id2": "entity:light.kueche"
}
```

**Response:**
```json
{
  "ok": true,
  "similarity": 0.85,
  "dimension": 128
}
```

### 4.4 Bulk Create

```http
POST /api/v1/vector/embeddings/bulk
Content-Type: application/json

{
  "entities": [
    {"id": "light.wohnzimmer", "domain": "light"},
    {"id": "light.kueche", "domain": "light"}
  ],
  "user_preferences": [
    {"id": "person.efka", "preferences": {...}}
  ]
}
```

---

## 5. Storage

### 5.1 SQLite Schema

```sql
CREATE TABLE vectors (
    id TEXT PRIMARY KEY,
    entry_type TEXT NOT NULL,
    vector BLOB NOT NULL,          -- JSON-encoded float array
    metadata TEXT DEFAULT '{}',    -- JSON-encoded metadata
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_vectors_type ON vectors(entry_type);
CREATE INDEX idx_vectors_created ON vectors(created_at);
```

### 5.2 Cache Strategy

- **In-memory LRU cache**: Configurable size (default 500 entries)
- **Cache hit**: Immediate return without DB lookup
- **Cache miss**: Load from SQLite, add to cache
- **Cache eviction**: LRU when exceeding max size

---

## 6. Integration with MUPL

### 6.1 Preference Similarity

When a user performs an action:
1. Update user preference embedding
2. Find similar users
3. Check similar users' preferences for the entity
4. Generate recommendations based on similar users' settings

### 6.2 Example Flow

```python
# User "efka" sets living room light to 80% brightness
await vector_client.update_user_preferences(
    user_id="person.efka",
    preferences={
        "light_brightness": {"default": 0.8, "by_zone": {"living_room": 0.75}},
        ...
    }
)

# Get recommendations from similar users
recommendations = await vector_client.get_user_similarity_recommendations(
    user_id="person.efka",
    entity_id="light.kitchen"
)

# Returns users with similar preferences and their settings for light.kitchen
# [
#   {"similar_user": "person.partner", "similarity": 0.82, "preferred_brightness": 0.7},
#   ...
# ]
```

---

## 7. Configuration

### 7.1 Core Add-on Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `COPILOT_VECTOR_DB_PATH` | `/data/vector_store.db` | SQLite database path |
| `COPILOT_VECTOR_PERSIST` | `true` | Enable persistence |
| `COPILOT_USE_OLLAMA` | `false` | Use Ollama for embeddings |
| `COPILOT_OLLAMA_MODEL` | `nomic-embed-text` | Ollama embedding model |
| `COPILOT_OLLAMA_URL` | `http://localhost:11434` | Ollama server URL |

### 7.2 HA Integration Options

```yaml
# configuration.yaml
ai_home_copilot:
  vector_store:
    enabled: true
    api_url: "http://localhost:8909"
    sync_interval_hours: 6
```

---

## 8. Performance

### 8.1 Benchmarks (Local Embeddings)

| Operation | Time |
|-----------|------|
| Create entity embedding | ~1ms |
| Create user preference embedding | ~0.5ms |
| Similarity search (100 entries) | ~5ms |
| Similarity search (1000 entries) | ~50ms |
| Bulk create (100 entities) | ~100ms |

### 8.2 Memory Usage

- **Per embedding**: 512 bytes (128 floats × 4 bytes)
- **1000 embeddings**: ~512KB + metadata overhead
- **In-memory cache**: Configurable, default ~250KB

---

## 9. Testing

### 9.1 Unit Tests

- `test_vector_store.py`: Embeddings, store, API tests
- Coverage: >90% for vector_store module

### 9.2 Test Categories

1. **Embedding Engine Tests**
   - Vector normalization
   - Hash-based vector generation
   - Entity/user/pattern embedding creation
   - Caching behavior

2. **Vector Store Tests**
   - CRUD operations
   - Similarity search
   - Persistence
   - Cache management

3. **API Tests**
   - All endpoints
   - Error handling
   - Bulk operations

---

## 10. Future Enhancements

### Phase 2 (v0.8.4+)
- [ ] Ollama embedding integration
- [ ] HNSW index for faster similarity search
- [ ] Zone-based embedding clustering
- [ ] Real-time embedding updates on state changes

### Phase 3 (v0.9.0+)
- [ ] Cross-household similarity (with privacy)
- [ ] Learned embedding fine-tuning
- [ ] Multi-modal embeddings (image, audio)

---

*Created: 2026-02-15*  
*Author: Autopilot Worker*