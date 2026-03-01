# RAG Hybrid Search API Documentation

**Phase 6 Feature** | **Version:** 1.0.0 | **Last Updated:** 2026-03-01

Comprehensive API documentation for the RAG (Retrieval-Augmented Generation) Hybrid Search system, combining BM25 lexical search with vector similarity search using Reciprocal Rank Fusion (RRF) for optimal re-ranking.

---

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [POST /api/v1/rag/search](#post-apiv1ragsearch)
  - [POST /api/v1/rag/search/multi](#post-apiv1ragsearchmulti)
  - [POST /api/v1/rag/documents](#post-apiv1ragdocuments)
  - [DELETE /api/v1/rag/documents/:doc_id](#delete-apiv1ragdocumentsdoc_id)
  - [GET /api/v1/rag/stats](#get-apiv1ragstats)
  - [GET /api/v1/rag/health](#get-apiv1raghealth)
- [Error Codes](#error-codes)
- [Python SDK Examples](#python-sdk-examples)

---

## Overview

The RAG Hybrid Search API provides intelligent search capabilities by combining:

- **BM25 (Best Matching 25):** Lexical full-text search with configurable term frequency saturation
- **Vector Search:** Semantic similarity search using embeddings
- **Reciprocal Rank Fusion (RRF):** Advanced re-ranking algorithm for optimal result ordering

### Key Features

- ⚡ **Performance Optimized:** Target response time <100ms
- 🔀 **Hybrid Scoring:** Configurable weights for BM25 (0.5) and vector search (0.5)
- 🎯 **Multi-Query Support:** Parallel search with query variations for improved recall
- 💾 **Intelligent Caching:** TTL-based cache (300s default) for repeated queries
- 📊 **Rich Results:** Detailed scoring breakdown (BM25, vector, RRF scores)

### Configuration Defaults

| Parameter | Default | Description |
|-----------|---------|-------------|
| `rrf_k` | 60 | RRF fusion parameter |
| `bm25_weight` | 0.5 | Weight for BM25 scores |
| `vector_weight` | 0.5 | Weight for vector scores |
| `top_k` | 10 | Default number of results |
| `bm25_k1` | 1.5 | Term frequency saturation |
| `bm25_b` | 0.75 | Length normalization |
| `vector_threshold` | 0.5 | Minimum similarity threshold |
| `cache_ttl_seconds` | 300 | Cache time-to-live |

---

## Authentication

All endpoints require authentication via one of the following methods:

### Header Authentication

```http
X-Auth-Token: your-api-token-here
```

or

```http
Authorization: Bearer your-api-token-here
```

### Authentication Failure Response

```json
{
  "error": "unauthorized",
  "message": "Valid X-Auth-Token or Bearer token required"
}
```

**HTTP Status:** `401 Unauthorized`

---

## Endpoints

### POST /api/v1/rag/search

Perform hybrid search combining BM25 and vector search with RRF fusion.

#### Description

Executes a single query against the hybrid search engine, combining lexical (BM25) and semantic (vector) search results using Reciprocal Rank Fusion for optimal ranking.

#### Request Format

**Endpoint:** `POST /api/v1/rag/search`

**Headers:**
```http
Content-Type: application/json
X-Auth-Token: your-api-token
```

**Body:**
```json
{
  "query": "string (required)",
  "top_k": 10,
  "filters": {
    "domain": "light",
    "entity_type": "switch"
  },
  "use_multi_query": false
}
```

**Request Parameters:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `query` | string | ✅ Yes | - | Search query string |
| `top_k` | integer | ❌ No | 10 | Number of results (max: 100) |
| `filters` | object | ❌ No | null | Optional filters for vector search |
| `use_multi_query` | boolean | ❌ No | false | Enable multi-query mode |

#### Response Format

**Success Response (200 OK):**

```json
{
  "ok": true,
  "results": [
    {
      "id": "doc_001",
      "score": 0.8542,
      "bm25_score": 0.7821,
      "vector_score": 0.9263,
      "rrf_score": 0.0328,
      "content": "Wohnzimmer Lichtsteuerung für Philips Hue Lampen...",
      "metadata": {
        "domain": "light",
        "entity_id": "light.wohnzimmer"
      },
      "rank_bm25": 2,
      "rank_vector": 1,
      "final_rank": 1
    }
  ],
  "count": 1,
  "query": "Wohnzimmer Licht",
  "query_type": "single",
  "execution_time_ms": 45.23
}
```

**Response Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `ok` | boolean | Success status |
| `results` | array | List of search results |
| `results[].id` | string | Document identifier |
| `results[].score` | float | Combined weighted score |
| `results[].bm25_score` | float | BM25 lexical score |
| `results[].vector_score` | float | Vector similarity score |
| `results[].rrf_score` | float | RRF fusion score |
| `results[].content` | string | Document content (truncated to 500 chars) |
| `results[].metadata` | object | Document metadata |
| `results[].rank_bm25` | integer | BM25 ranking position |
| `results[].rank_vector` | integer | Vector search ranking position |
| `results[].final_rank` | integer | Final combined ranking |
| `count` | integer | Number of results returned |
| `query` | string | Original query |
| `query_type` | string | "single" or "multi" |
| `execution_time_ms` | float | Query execution time in milliseconds |

#### Error Codes

| Status Code | Description |
|-------------|-------------|
| `400` | Bad Request - Missing required field `query` |
| `401` | Unauthorized - Invalid or missing authentication token |
| `403` | Forbidden - Insufficient permissions |
| `500` | Internal Server Error - Search engine failure |

#### Python Code Example

```python
import requests
from typing import List, Dict, Any

class RAGSearchClient:
    """Client for RAG Hybrid Search API."""
    
    def __init__(self, base_url: str, api_token: str):
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.session = requests.Session()
        self.session.headers.update({
            'X-Auth-Token': api_token,
            'Content-Type': 'application/json'
        })
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Dict[str, Any] = None,
        use_multi_query: bool = False
    ) -> Dict[str, Any]:
        """
        Perform hybrid search.
        
        Args:
            query: Search query string
            top_k: Number of results to return
            filters: Optional filters for vector search
            use_multi_query: Enable multi-query mode
            
        Returns:
            Search results with scores and metadata
        """
        payload = {
            'query': query,
            'top_k': min(top_k, 100),
            'filters': filters or {},
            'use_multi_query': use_multi_query
        }
        
        response = self.session.post(
            f'{self.base_url}/api/v1/rag/search',
            json=payload
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 400:
            raise ValueError(f"Bad request: {response.json().get('error')}")
        elif response.status_code == 401:
            raise PermissionError("Invalid API token")
        else:
            response.raise_for_status()
    
    def search_with_details(self, query: str, top_k: int = 5) -> None:
        """
        Perform search and print detailed results.
        
        Args:
            query: Search query
            top_k: Number of results to display
        """
        try:
            result = self.search(query, top_k=top_k)
            
            print(f"\n🔍 Search Results for: '{query}'")
            print(f"⏱️  Execution time: {result['execution_time_ms']:.2f}ms")
            print(f"📊 Query type: {result['query_type']}")
            print(f"📈 Results found: {result['count']}\n")
            
            for i, doc in enumerate(result['results'], 1):
                print(f"{i}. [{doc['final_rank']}] {doc['id']}")
                print(f"   Score: {doc['score']:.4f} (BM25: {doc['bm25_score']:.4f}, Vector: {doc['vector_score']:.4f})")
                print(f"   Content: {doc['content'][:150]}...")
                print()
                
        except Exception as e:
            print(f"❌ Search failed: {e}")


# Usage Example
if __name__ == '__main__':
    # Initialize client
    client = RAGSearchClient(
        base_url='http://localhost:8123',
        api_token='your-api-token-here'
    )
    
    # Simple search
    results = client.search(
        query="Wohnzimmer Lichtsteuerung",
        top_k=5,
        filters={"domain": "light"}
    )
    
    print(f"Found {results['count']} results in {results['execution_time_ms']:.2f}ms")
    
    # Display top result
    if results['results']:
        top = results['results'][0]
        print(f"\nTop result: {top['id']}")
        print(f"Combined score: {top['score']:.4f}")
        print(f"Content preview: {top['content'][:200]}")
```

---

### POST /api/v1/rag/search/multi

Perform multi-query hybrid search with parallel query execution.

#### Description

Executes multiple query variations in parallel and fuses results using RRF. This improves recall by searching with semantically similar queries simultaneously.

#### Request Format

**Endpoint:** `POST /api/v1/rag/search/multi`

**Headers:**
```http
Content-Type: application/json
X-Auth-Token: your-api-token
```

**Body:**
```json
{
  "queries": [
    "Wohnzimmer Licht",
    "Lichtsteuerung Wohnzimmer",
    "Beleuchtung Wohnbereich"
  ],
  "top_k": 10
}
```

**Request Parameters:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `queries` | array[string] | ✅ Yes | - | List of query variations (max: 5) |
| `top_k` | integer | ❌ No | 10 | Number of results (max: 100) |

#### Response Format

**Success Response (200 OK):**

```json
{
  "ok": true,
  "results": [
    {
      "id": "doc_001",
      "score": 0.9124,
      "bm25_score": 0.8532,
      "vector_score": 0.9716,
      "rrf_score": 0.0492,
      "content": "Wohnzimmer Lichtsteuerung...",
      "metadata": {},
      "final_rank": 1
    }
  ],
  "count": 10,
  "queries": [
    "Wohnzimmer Licht",
    "Lichtsteuerung Wohnzimmer",
    "Beleuchtung Wohnbereich"
  ],
  "execution_time_ms": 78.45
}
```

#### Error Codes

| Status Code | Description |
|-------------|-------------|
| `400` | Bad Request - Missing required field `queries` |
| `401` | Unauthorized - Invalid or missing authentication token |
| `403` | Forbidden - Insufficient permissions |
| `500` | Internal Server Error - Search engine failure |

#### Python Code Example

```python
def multi_query_search_example(client: RAGSearchClient):
    """Example: Multi-query search for improved recall."""
    
    query_variations = [
        "Automatisches Licht beim Betreten",
        "Licht automatisch einschalten Anwesenheit",
        "Anwesenheitserkennung Lichtsteuerung"
    ]
    
    try:
        result = client.session.post(
            f'{client.base_url}/api/v1/rag/search/multi',
            headers=client.session.headers,
            json={
                'queries': query_variations,
                'top_k': 10
            }
        ).json()
        
        print(f"🔄 Multi-Query Search Results")
        print(f"   Queries: {len(result['queries'])}")
        print(f"   Results: {result['count']}")
        print(f"   Time: {result['execution_time_ms']:.2f}ms\n")
        
        for i, doc in enumerate(result['results'][:5], 1):
            print(f"{i}. {doc['id']} (Score: {doc['score']:.4f})")
            
    except Exception as e:
        print(f"❌ Multi-query search failed: {e}")
```

---

### POST /api/v1/rag/documents

Add a document to the RAG search index.

#### Description

Indexes a new document with automatic embedding generation for vector search. The document is added to both the BM25 index and the vector store.

#### Request Format

**Endpoint:** `POST /api/v1/rag/documents`

**Headers:**
```http
Content-Type: application/json
X-Auth-Token: your-api-token
```

**Body:**
```json
{
  "doc_id": "doc_wohnzimmer_001",
  "content": "Das Wohnzimmer-Licht wird automatisch eingeschaltet, wenn eine Anwesenheit erkannt wird. Die Helligkeit passt sich der Tageszeit an.",
  "metadata": {
    "domain": "light",
    "entity_id": "light.wohnzimmer",
    "category": "automation_rule"
  }
}
```

**Request Parameters:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `doc_id` | string | ✅ Yes | - | Unique document identifier |
| `content` | string | ✅ Yes | - | Document text content |
| `metadata` | object | ❌ No | {} | Optional metadata dictionary |

#### Response Format

**Success Response (201 Created):**

```json
{
  "ok": true,
  "doc_id": "doc_wohnzimmer_001",
  "content_length": 142
}
```

#### Error Codes

| Status Code | Description |
|-------------|-------------|
| `400` | Bad Request - Missing required fields `doc_id` or `content` |
| `401` | Unauthorized - Invalid or missing authentication token |
| `403` | Forbidden - Insufficient permissions |
| `409` | Conflict - Document ID already exists |
| `500` | Internal Server Error - Failed to generate embedding or index document |

#### Python Code Example

```python
def add_document_example(client: RAGSearchClient):
    """Example: Add a document to the RAG index."""
    
    document = {
        'doc_id': 'automation_licht_001',
        'content': '''
        Automatisches Licht im Wohnzimmer:
        
        Wenn eine Person den Raum betritt (Bewegungserkennung),
        wird das Licht automatisch eingeschaltet. Die Helligkeit
        wird basierend auf der Tageszeit angepasst:
        
        - Morgens (6-12 Uhr): 80% Helligkeit
        - Nachmittags (12-18 Uhr): 60% Helligkeit
        - Abends (18-22 Uhr): 40% Helligkeit
        - Nachts (22-6 Uhr): 20% Helligkeit
        
        Bei Abwesenheit wird das Licht nach 5 Minuten ausgeschaltet.
        ''',
        'metadata': {
            'domain': 'light',
            'room': 'wohnzimmer',
            'type': 'automation',
            'created_by': 'user_andreas'
        }
    }
    
    try:
        response = client.session.post(
            f'{client.base_url}/api/v1/rag/documents',
            headers=client.session.headers,
            json=document
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Document added successfully!")
            print(f"   ID: {result['doc_id']}")
            print(f"   Content length: {result['content_length']} chars")
        else:
            print(f"❌ Failed: {response.status_code} - {response.json()}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
```

---

### DELETE /api/v1/rag/documents/:doc_id

Remove a document from the RAG search index.

#### Description

Permanently removes a document from both the BM25 index and the vector store.

#### Request Format

**Endpoint:** `DELETE /api/v1/rag/documents/:doc_id`

**Headers:**
```http
X-Auth-Token: your-api-token
```

**URL Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `doc_id` | string | Document identifier to remove (URL-encoded if contains special chars) |

#### Response Format

**Success Response (200 OK):**

```json
{
  "ok": true,
  "deleted": "doc_wohnzimmer_001"
}
```

**Not Found Response (404):**

```json
{
  "ok": false,
  "error": "Document not found: doc_wohnzimmer_001"
}
```

#### Error Codes

| Status Code | Description |
|-------------|-------------|
| `401` | Unauthorized - Invalid or missing authentication token |
| `403` | Forbidden - Insufficient permissions |
| `404` | Not Found - Document does not exist |
| `500` | Internal Server Error - Failed to remove document |

#### Python Code Example

```python
def delete_document_example(client: RAGSearchClient, doc_id: str):
    """Example: Remove a document from the index."""
    
    try:
        response = client.session.delete(
            f'{client.base_url}/api/v1/rag/documents/{doc_id}',
            headers=client.session.headers
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Document deleted: {result['deleted']}")
        elif response.status_code == 404:
            print(f"⚠️  Document not found: {doc_id}")
        else:
            print(f"❌ Failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
```

---

### GET /api/v1/rag/stats

Get RAG search engine statistics.

#### Description

Returns comprehensive statistics about the search engine including document count, cache status, and configuration.

#### Request Format

**Endpoint:** `GET /api/v1/rag/stats`

**Headers:**
```http
X-Auth-Token: your-api-token
```

#### Response Format

**Success Response (200 OK):**

```json
{
  "ok": true,
  "stats": {
    "num_documents": 1247,
    "avg_doc_length": 156.3,
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

#### Error Codes

| Status Code | Description |
|-------------|-------------|
| `401` | Unauthorized - Invalid or missing authentication token |
| `403` | Forbidden - Insufficient permissions |
| `500` | Internal Server Error - Failed to retrieve statistics |

#### Python Code Example

```python
def get_stats_example(client: RAGSearchClient):
    """Example: Get search engine statistics."""
    
    try:
        response = client.session.get(
            f'{client.base_url}/api/v1/rag/stats',
            headers=client.session.headers
        )
        
        if response.status_code == 200:
            stats = response.json()['stats']
            print("📊 RAG Search Engine Statistics")
            print(f"   Documents indexed: {stats['num_documents']}")
            print(f"   Avg document length: {stats['avg_doc_length']:.1f} chars")
            print(f"   Cache entries: {stats['cache_size']}")
            print(f"   RRF parameter (k): {stats['config']['rrf_k']}")
            print(f"   BM25 weight: {stats['config']['bm25_weight']}")
            print(f"   Vector weight: {stats['config']['vector_weight']}")
        else:
            print(f"❌ Failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
```

---

### GET /api/v1/rag/health

Health check for RAG service.

#### Description

Returns the health status of the RAG service and its components.

#### Request Format

**Endpoint:** `GET /api/v1/rag/health`

**Headers:**
```http
X-Auth-Token: your-api-token
```

#### Response Format

**Success Response (200 OK):**

```json
{
  "ok": true,
  "status": "healthy",
  "components": {
    "bm25_index": "healthy",
    "vector_store": "healthy",
    "cache": "active"
  },
  "num_documents": 1247
}
```

**Degraded Response (200 OK):**

```json
{
  "ok": true,
  "status": "degraded",
  "components": {
    "bm25_index": "healthy",
    "vector_store": "not_configured",
    "cache": "empty"
  },
  "num_documents": 0
}
```

#### Error Codes

| Status Code | Description |
|-------------|-------------|
| `401` | Unauthorized - Invalid or missing authentication token |
| `500` | Internal Server Error - Service unhealthy |

#### Python Code Example

```python
def health_check_example(client: RAGSearchClient):
    """Example: Check RAG service health."""
    
    try:
        response = client.session.get(
            f'{client.base_url}/api/v1/rag/health',
            headers=client.session.headers
        )
        
        if response.status_code == 200:
            health = response.json()
            status_icon = "✅" if health['status'] == 'healthy' else "⚠️"
            print(f"{status_icon} RAG Service Status: {health['status']}")
            print(f"   Documents: {health['num_documents']}")
            for component, status in health['components'].items():
                icon = "✅" if status == 'healthy' else "⚠️"
                print(f"   {icon} {component}: {status}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
```

---

## Error Codes

### Standard HTTP Status Codes

| Code | Status | Description |
|------|--------|-------------|
| `200` | OK | Request successful |
| `201` | Created | Document successfully added |
| `400` | Bad Request | Invalid request format or missing required fields |
| `401` | Unauthorized | Missing or invalid authentication token |
| `403` | Forbidden | Valid token but insufficient permissions |
| `404` | Not Found | Resource (document, zone, etc.) does not exist |
| `409` | Conflict | Resource already exists (e.g., duplicate document ID) |
| `500` | Internal Server Error | Server-side error during processing |
| `503` | Service Unavailable | Search engine not initialized |

### Error Response Format

```json
{
  "ok": false,
  "error": "Error message description",
  "details": "Optional additional details"
}
```

---

## Python SDK Examples

### Complete Usage Example

```python
#!/usr/bin/env python3
"""
RAG Hybrid Search API - Complete Usage Examples

This script demonstrates all major operations with the RAG Hybrid Search API.
"""

import requests
from typing import List, Dict, Any, Optional


class RAGHybridSearchClient:
    """
    Complete client for RAG Hybrid Search API.
    
    Features:
    - Hybrid search (BM25 + Vector)
    - Multi-query search
    - Document management
    - Statistics and health monitoring
    """
    
    def __init__(self, base_url: str, api_token: str, timeout: int = 30):
        """
        Initialize the RAG client.
        
        Args:
            base_url: API base URL (e.g., 'http://localhost:8123')
            api_token: Authentication token
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.api_token = api_token
        self.timeout = timeout
        
        self.session = requests.Session()
        self.session.headers.update({
            'X-Auth-Token': api_token,
            'Content-Type': 'application/json'
        })
    
    # ==================== Search Operations ====================
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        use_multi_query: bool = False
    ) -> Dict[str, Any]:
        """
        Perform hybrid search.
        
        Args:
            query: Search query string
            top_k: Number of results (max 100)
            filters: Optional filters for vector search
            use_multi_query: Enable multi-query mode
            
        Returns:
            Search results with scores and metadata
        """
        payload = {
            'query': query,
            'top_k': min(top_k, 100),
            'filters': filters or {},
            'use_multi_query': use_multi_query
        }
        
        response = self.session.post(
            f'{self.base_url}/api/v1/rag/search',
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def multi_query_search(
        self,
        queries: List[str],
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        Perform multi-query hybrid search.
        
        Args:
            queries: List of query variations
            top_k: Number of results
            
        Returns:
            Fused search results
        """
        payload = {
            'queries': queries[:5],  # Limit to 5 queries
            'top_k': min(top_k, 100)
        }
        
        response = self.session.post(
            f'{self.base_url}/api/v1/rag/search/multi',
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    # ==================== Document Management ====================
    
    def add_document(
        self,
        doc_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a document to the search index.
        
        Args:
            doc_id: Unique document identifier
            content: Document text content
            metadata: Optional metadata
            
        Returns:
            Confirmation with document ID
        """
        payload = {
            'doc_id': doc_id,
            'content': content,
            'metadata': metadata or {}
        }
        
        response = self.session.post(
            f'{self.base_url}/api/v1/rag/documents',
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def delete_document(self, doc_id: str) -> Dict[str, Any]:
        """
        Remove a document from the index.
        
        Args:
            doc_id: Document identifier
            
        Returns:
            Confirmation of deletion
        """
        response = self.session.delete(
            f'{self.base_url}/api/v1/rag/documents/{doc_id}',
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    # ==================== Monitoring ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get search engine statistics."""
        response = self.session.get(
            f'{self.base_url}/api/v1/rag/stats',
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> Dict[str, Any]:
        """Check service health status."""
        response = self.session.get(
            f'{self.base_url}/api/v1/rag/health',
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()


# ==================== Example Usage ====================

if __name__ == '__main__':
    # Configuration
    BASE_URL = 'http://localhost:8123'
    API_TOKEN = 'your-api-token-here'
    
    # Initialize client
    client = RAGHybridSearchClient(BASE_URL, API_TOKEN)
    
    print("=" * 60)
    print("RAG Hybrid Search API - Usage Examples")
    print("=" * 60)
    
    # 1. Health Check
    print("\n1. 🔍 Health Check")
    print("-" * 40)
    health = client.health_check()
    print(f"Status: {health['status']}")
    print(f"Documents: {health['num_documents']}")
    
    # 2. Add Sample Documents
    print("\n2. 📝 Adding Sample Documents")
    print("-" * 40)
    
    documents = [
        {
            'doc_id': 'automation_licht_001',
            'content': 'Automatisches Licht im Wohnzimmer bei Anwesenheit',
            'metadata': {'room': 'wohnzimmer', 'type': 'light'}
        },
        {
            'doc_id': 'automation_heizung_001',
            'content': 'Heizungssteuerung basierend auf Temperatur und Zeit',
            'metadata': {'room': 'wohnzimmer', 'type': 'climate'}
        },
    ]
    
    for doc in documents:
        try:
            result = client.add_document(**doc)
            print(f"✅ Added: {result['doc_id']}")
        except Exception as e:
            print(f"❌ Failed: {e}")
    
    # 3. Single Query Search
    print("\n3. 🔎 Single Query Search")
    print("-" * 40)
    
    results = client.search(
        query="Licht automatisch",
        top_k=5,
        filters={'type': 'light'}
    )
    
    print(f"Query: 'Licht automatisch'")
    print(f"Results: {results['count']} in {results['execution_time_ms']:.2f}ms")
    
    for i, doc in enumerate(results['results'], 1):
        print(f"  {i}. {doc['id']} (Score: {doc['score']:.4f})")
    
    # 4. Multi-Query Search
    print("\n4. 🔄 Multi-Query Search")
    print("-" * 40)
    
    queries = [
        "Automatisches Licht",
        "Lichtsteuerung Anwesenheit",
        "Beleuchtung automatisch"
    ]
    
    results = client.multi_query_search(queries, top_k=5)
    print(f"Queries: {len(queries)}")
    print(f"Results: {results['count']} in {results['execution_time_ms']:.2f}ms")
    
    # 5. Statistics
    print("\n5. 📊 Statistics")
    print("-" * 40)
    
    stats = client.get_stats()
    print(f"Total documents: {stats['stats']['num_documents']}")
    print(f"Cache size: {stats['stats']['cache_size']}")
    
    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
```

---

## Appendix: Response Time Benchmarks

| Operation | Target | Typical | Max |
|-----------|--------|---------|-----|
| Single query search | <100ms | 45ms | 150ms |
| Multi-query search | <200ms | 95ms | 300ms |
| Add document | <500ms | 250ms | 1000ms |
| Delete document | <50ms | 15ms | 100ms |
| Get stats | <20ms | 5ms | 50ms |

---

**Documentation Version:** 1.0.0  
**Last Updated:** 2026-03-01  
**Maintained By:** PilotSuite Core Team
