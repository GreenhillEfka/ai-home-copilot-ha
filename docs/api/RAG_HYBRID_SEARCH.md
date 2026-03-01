# RAG Hybrid Search API Documentation

**Version:** 1.0  
**Base URL:** `/api/v1/rag`  
**Authentication:** Required (X-Auth-Token or Bearer token)

---

## Overview

The RAG (Retrieval-Augmented Generation) Hybrid Search API provides advanced search capabilities combining:

- **BM25** (Lexical/Keyword Search)
- **Vector Similarity Search** (Semantic Search)
- **Reciprocal Rank Fusion (RRF)** for optimal re-ranking

This hybrid approach delivers superior search results by leveraging both exact term matching and semantic understanding.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Request                          │
│                   (Query + Parameters)                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  Hybrid Search Engine                       │
│  ┌─────────────────┐           ┌─────────────────┐          │
│  │   BM25 Index    │           │  Vector Store   │          │
│  │  (Lexical)      │           │  (Semantic)     │          │
│  │  k1=1.5, b=0.75 │           │  threshold=0.5  │          │
│  └─────────────────┘           └─────────────────┘          │
│         │                              │                     │
│         └──────────┬───────────────────┘                     │
│                    │                                         │
│                    ▼                                         │
│         ┌─────────────────────┐                              │
│         │  RRF Re-Ranking     │                              │
│         │  (k=60, weights 0.5)│                              │
│         └─────────────────────┘                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Ranked Results                            │
│         (score, bm25_score, vector_score, rrf_score)        │
└─────────────────────────────────────────────────────────────┘
```

---

## Endpoints

### POST `/api/v1/rag/search`

Perform hybrid search with BM25 + Vector fusion.

**Request:**
```json
{
  "query": "string (required)",
  "top_k": "integer (optional, default: 10, max: 100)",
  "filters": "object (optional)",
  "use_multi_query": "boolean (optional, default: false)"
}
```

**Response:**
```json
{
  "ok": true,
  "results": [
    {
      "id": "string",
      "score": 0.95,
      "bm25_score": 0.8,
      "vector_score": 0.9,
      "rrf_score": 0.0167,
      "content": "string (truncated to 500 chars)",
      "metadata": {},
      "rank_bm25": 1,
      "rank_vector": 2,
      "final_rank": 1
    }
  ],
  "count": 10,
  "query": "original query string",
  "query_type": "single|multi",
  "execution_time_ms": 45.23
}
```

**Example:**
```bash
curl -X POST http://localhost:8909/api/v1/rag/search \
  -H "X-Auth-Token: your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "living room lighting automation",
    "top_k": 5,
    "use_multi_query": false
  }'
```

---

### POST `/api/v1/rag/search/multi`

Perform multi-query hybrid search with parallel query variations.

**Request:**
```json
{
  "queries": ["string array (required)"],
  "top_k": "integer (optional, default: 10, max: 100)"
}
```

**Response:**
```json
{
  "ok": true,
  "results": [...],
  "count": 10,
  "queries_processed": 3,
  "execution_time_ms": 78.45
}
```

**Example:**
```bash
curl -X POST http://localhost:8909/api/v1/rag/search/multi \
  -H "X-Auth-Token: your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "queries": [
      "living room lights",
      "wohnzimmer beleuchtung",
      "lighting automation living room"
    ],
    "top_k": 10
  }'
```

---

### POST `/api/v1/rag/documents`

Add a document to the search index.

**Request:**
```json
{
  "doc_id": "string (required, unique)",
  "content": "string (required)",
  "metadata": "object (optional)"
}
```

**Response:**
```json
{
  "ok": true,
  "doc_id": "string",
  "indexed": true,
  "tokens": 150
}
```

**Example:**
```bash
curl -X POST http://localhost:8909/api/v1/rag/documents \
  -H "X-Auth-Token: your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "automation_living_room_001",
    "content": "When motion is detected in the living room after sunset, turn on the ceiling lights to 50% brightness.",
    "metadata": {
      "room": "living_room",
      "type": "automation",
      "trigger": "motion"
    }
  }'
```

---

### DELETE `/api/v1/rag/documents/<doc_id>`

Remove a document from the search index.

**Response:**
```json
{
  "ok": true,
  "doc_id": "string",
  "deleted": true
}
```

**Example:**
```bash
curl -X DELETE http://localhost:8909/api/v1/rag/documents/automation_living_room_001 \
  -H "X-Auth-Token: your-token"
```

---

### GET `/api/v1/rag/stats`

Get search engine statistics and index information.

**Response:**
```json
{
  "ok": true,
  "stats": {
    "num_documents": 1250,
    "num_terms": 8432,
    "avg_doc_length": 145.3,
    "cache_enabled": true,
    "cache_size": 42,
    "config": {
      "rrf_k": 60,
      "bm25_weight": 0.5,
      "vector_weight": 0.5,
      "top_k": 10,
      "multi_query_enabled": true
    }
  }
}
```

**Example:**
```bash
curl -X GET http://localhost:8909/api/v1/rag/stats \
  -H "X-Auth-Token: your-token"
```

---

## Configuration

### HybridSearchConfig Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `rrf_k` | int | 60 | RRF parameter for rank fusion |
| `bm25_weight` | float | 0.5 | Weight for BM25 scores (0.0-1.0) |
| `vector_weight` | float | 0.5 | Weight for vector scores (0.0-1.0) |
| `top_k` | int | 10 | Number of results to return |
| `bm25_k1` | float | 1.5 | BM25 term frequency saturation |
| `bm25_b` | float | 0.75 | BM25 length normalization |
| `vector_threshold` | float | 0.5 | Minimum vector similarity threshold |
| `multi_query_enabled` | bool | true | Enable multi-query mode |
| `multi_query_count` | int | 3 | Number of parallel queries |
| `use_cache` | bool | true | Enable result caching |
| `cache_ttl_seconds` | int | 300 | Cache time-to-live |

---

## Response Fields

### SearchResult Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique document identifier |
| `score` | float | Final combined score (0.0-1.0) |
| `bm25_score` | float | BM25 lexical search score |
| `vector_score` | float | Vector semantic search score |
| `rrf_score` | float | Reciprocal Rank Fusion score |
| `content` | string | Document content (truncated) |
| `metadata` | object | Document metadata |
| `rank_bm25` | int | Rank in BM25 results |
| `rank_vector` | int | Rank in vector results |
| `final_rank` | int | Final rank after RRF |

---

## Error Handling

### Common Error Codes

| Code | Error | Description |
|------|-------|-------------|
| 400 | Bad Request | Missing required field or invalid parameter |
| 401 | Unauthorized | Missing or invalid authentication token |
| 404 | Not Found | Document ID not found (DELETE) |
| 500 | Internal Error | Search engine error |

### Error Response Format

```json
{
  "ok": false,
  "error": "error message"
}
```

---

## Performance

### Benchmarks

| Operation | P50 (ms) | P95 (ms) | P99 (ms) |
|-----------|----------|----------|----------|
| Single Query Search | 45 | 78 | 120 |
| Multi-Query Search | 85 | 145 | 210 |
| Document Indexing | 12 | 25 | 45 |
| Document Deletion | 5 | 10 | 18 |

### Optimization Tips

1. **Use caching:** Enable `use_cache` for repeated queries
2. **Limit top_k:** Request only the results you need
3. **Multi-query sparingly:** Use only when query variations add value
4. **Filter early:** Use filters to reduce vector search space

---

## Best Practices

### Query Formulation

✅ **Good:**
- Specific, descriptive queries: `"living room motion automation"`
- Include context: `"evening lighting scene bedroom"`
- Use natural language: `"turn off lights when leaving"`

❌ **Avoid:**
- Single generic terms: `"light"`
- Overly long queries: 50+ words
- Special characters without escaping

### Indexing Strategy

1. **Chunk documents** into logical units (100-300 words)
2. **Add rich metadata** for filtering (room, type, tags)
3. **Use unique doc_ids** with meaningful prefixes
4. **Remove stale documents** regularly

### Multi-Query Usage

Use multi-query when:
- Searching across languages
- Query has multiple interpretations
- Need broader recall

Example:
```json
{
  "queries": [
    "lights off",
    "turn off lighting",
    "beleuchtung ausschalten"
  ]
}
```

---

## Integration Examples

### Python Client

```python
import requests

class RAGSearchClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.token = token
        self.headers = {
            "X-Auth-Token": token,
            "Content-Type": "application/json"
        }
    
    def search(self, query: str, top_k: int = 10) -> dict:
        response = requests.post(
            f"{self.base_url}/rag/search",
            headers=self.headers,
            json={"query": query, "top_k": top_k}
        )
        return response.json()
    
    def add_document(self, doc_id: str, content: str, metadata: dict = None) -> dict:
        response = requests.post(
            f"{self.base_url}/rag/documents",
            headers=self.headers,
            json={
                "doc_id": doc_id,
                "content": content,
                "metadata": metadata or {}
            }
        )
        return response.json()
```

### JavaScript Client

```javascript
class RAGSearchClient {
  constructor(baseUrl, token) {
    this.baseUrl = baseUrl;
    this.token = token;
    this.headers = {
      'X-Auth-Token': token,
      'Content-Type': 'application/json'
    };
  }
  
  async search(query, topK = 10) {
    const response = await fetch(`${this.baseUrl}/rag/search`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({ query, top_k: topK })
    });
    return await response.json();
  }
  
  async addDocument(docId, content, metadata = {}) {
    const response = await fetch(`${this.baseUrl}/rag/documents`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({ doc_id: docId, content, metadata })
    });
    return await response.json();
  }
}
```

---

## Related Documentation

- [Vector Store API](./VECTOR_STORE.md)
- [Notifications API](./NOTIFICATIONS_API.md)
- [Blueprint Registration](./BLUEPRINT_API.md)

---

**Last Updated:** 2026-03-01  
**Maintained by:** @cowdya
