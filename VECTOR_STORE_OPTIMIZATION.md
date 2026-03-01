# VectorStore Optimization - v12.3.0 Iteration 5

## Overview

Optimized vector search for larger datasets by implementing HNSW (Hierarchical Navigable Small World) indexing, replacing O(n) linear search with O(log n) approximate nearest neighbor search.

## Changes Made

### 1. New File: `vector_store/config.py`

Configuration module for vector store with HNSW parameters:

```python
@dataclass
class VectorStoreConfig:
    # HNSW Index Configuration
    index_type: Literal["hnsw", "flat"] = "hnsw"
    hnsw_m: int = 16                      # Max connections per node
    hnsw_ef_construction: int = 200       # Construction search width
    hnsw_ef_search: int = 50              # Search width
    hnsw_max_elements: int = 100000       # Max index size
    
    # Memory Optimization
    use_float16: bool = True              # Float16 vs Float32
    batch_size: int = 100
```

**Environment Variables:**
- `COPILOT_VECTOR_INDEX_TYPE`: "hnsw" or "flat"
- `COPILOT_VECTOR_HNSW_M`: 16-64 (default: 16)
- `COPILOT_VECTOR_HNSW_EF_CONSTRUCTION`: 100-400 (default: 200)
- `COPILOT_VECTOR_HNSW_EF_SEARCH`: 20-100 (default: 50)
- `COPILOT_VECTOR_HNSW_MAX_ELEMENTS`: Max index size (default: 100000)
- `COPILOT_VECTOR_FLOAT16`: "true"/"false" (default: true)

### 2. Updated: `vector_store/store.py`

**Key Features:**

#### HNSWIndex Class
- Wrapper around hnswlib for efficient indexing
- Automatic fallback to flat index if hnswlib unavailable
- Incremental updates (no rebuild on changes)
- Persistent index storage

#### VectorStore Improvements
- **HNSW-accelerated search**: O(log n) vs O(n)
- **Batch query support**: `batch_search()` for multiple vectors
- **Float16 optimization**: 50% memory reduction
- **Per-type indices**: Separate HNSW index per entry type
- **Lazy initialization**: Index created on first use

**New Methods:**
```python
async def batch_search(
    query_vectors: list[list[float]],
    entry_type: str | None = None,
    limit: int = 10,
    threshold: float | None = None,
) -> list[list[SearchResult]]
```

### 3. Updated: `api/v1/rag.py`

**New Endpoint: `/api/v1/rag/search/batch`**

Batch search for multiple queries in single request:

```json
POST /api/v1/rag/search/batch
{
    "namespace": "default",
    "queries": ["query1", "query2", "query3"],
    "top_k": 10,
    "use_lexical": true,
    "use_semantic": true,
    "rrf_k": 60,
    "lexical_weight": 1.0,
    "semantic_weight": 1.0
}
```

**Response:**
```json
{
    "namespace": "default",
    "results": [
        {
            "query": "query1",
            "mode": "hybrid_rrf",
            "hits": [...],
            "took_ms": 12.5
        }
    ],
    "total_took_ms": 45.2,
    "batch_size": 3
}
```

### 4. Updated: `Dockerfile`

Added hnswlib dependency:

```dockerfile
pip3 install ... numpy hnswlib
```

### 5. New File: `vector_store/benchmark.py`

Performance benchmark script comparing HNSW vs flat search.

**Usage:**
```bash
python benchmark_vector_store.py --num-vectors 10000 --dim 384 --queries 100
```

## Performance Comparison

### Expected Performance Gains

| Dataset Size | Flat Search (ms) | HNSW Search (ms) | Speedup |
|--------------|------------------|------------------|---------|
| 1,000 vectors | ~5ms | ~2ms | 2.5x |
| 10,000 vectors | ~50ms | ~5ms | 10x |
| 100,000 vectors | ~500ms | ~8ms | 62x |
| 1,000,000 vectors | ~5000ms | ~12ms | 416x |

**Note:** Actual performance depends on vector dimension and HNSW parameters.

### Complexity Comparison

- **Flat (Linear) Search**: O(n) - searches all vectors
- **HNSW Search**: O(log n) - navigates graph structure

### Memory Efficiency

- **Float32**: 4 bytes per dimension
- **Float16**: 2 bytes per dimension (50% reduction)

For 384-dimensional vectors:
- 100,000 vectors × 384 dims × 2 bytes = **73 MB** (Float16)
- 100,000 vectors × 384 dims × 4 bytes = **147 MB** (Float32)

## Configuration Recommendations

### Small Dataset (< 1,000 vectors)
```python
index_type = "flat"  # HNSW overhead not worth it
```

### Medium Dataset (1,000 - 50,000 vectors)
```python
index_type = "hnsw"
hnsw_m = 16
hnsw_ef_construction = 200
hnsw_ef_search = 50
```

### Large Dataset (50,000 - 500,000 vectors)
```python
index_type = "hnsw"
hnsw_m = 32
hnsw_ef_construction = 300
hnsw_ef_search = 100
hnsw_max_elements = 1000000
```

### Very Large Dataset (> 500,000 vectors)
```python
index_type = "hnsw"
hnsw_m = 48
hnsw_ef_construction = 400
hnsw_ef_search = 150
hnsw_max_elements = 5000000
```

## Migration Guide

### Backward Compatibility

The changes are **fully backward compatible**:

1. Existing code continues to work without modification
2. Falls back to flat search if hnswlib unavailable
3. Config defaults to HNSW but can be disabled

### Enabling HNSW

**Option 1: Environment Variables**
```bash
export COPILOT_VECTOR_INDEX_TYPE=hnsw
export COPILOT_VECTOR_HNSW_M=16
export COPILOT_VECTOR_HNSW_EF_SEARCH=50
```

**Option 2: Config Object**
```python
from copilot_core.vector_store.config import VectorStoreConfig

config = VectorStoreConfig(
    index_type="hnsw",
    hnsw_m=16,
    hnsw_ef_search=50,
)
store = VectorStore(config)
```

### Running Benchmarks

```bash
cd /config/.openclaw/workspace/pilotsuite-styx-core/copilot_core/rootfs/usr/src/app

# Quick benchmark (10k vectors)
python -m copilot_core.vector_store.benchmark --num-vectors 10000

# Large benchmark (100k vectors)
python -m copilot_core.vector_store.benchmark --num-vectors 100000 --queries 200

# Save results to JSON
python -m copilot_core.vector_store.benchmark --output /tmp/benchmark_results.json
```

## Testing

### Unit Tests

```python
import asyncio
from copilot_core.vector_store.config import VectorStoreConfig
from copilot_core.vector_store.store import VectorStore

async def test_hnsw():
    config = VectorStoreConfig(index_type="hnsw")
    store = VectorStore(config)
    
    # Add vectors
    await store.upsert("test1", [0.1] * 384, "entity")
    await store.upsert("test2", [0.2] * 384, "entity")
    
    # Search
    results = await store.search_similar([0.15] * 384, limit=10)
    assert len(results) > 0
    
    # Batch search
    batch = await store.batch_search([[0.1] * 384, [0.2] * 384])
    assert len(batch) == 2
    
    store.close()

asyncio.run(test_hnsw())
```

## Files Changed

1. ✅ `copilot_core/vector_store/config.py` - NEW
2. ✅ `copilot_core/vector_store/store.py` - UPDATED
3. ✅ `copilot_core/api/v1/rag.py` - UPDATED (batch endpoint)
4. ✅ `copilot_core/vector_store/benchmark.py` - NEW
5. ✅ `copilot_core/Dockerfile` - UPDATED (hnswlib dependency)

## Dependencies

- **hnswlib**: Python bindings for HNSW indexing
- **numpy**: Required for vector operations (already present)

## Next Steps

1. **Build & Deploy**: Rebuild Docker image with hnswlib
2. **Benchmark**: Run performance tests on production data
3. **Monitor**: Track search latency metrics
4. **Tune**: Adjust HNSW parameters based on actual usage

## Summary

✅ **HNSW Index**: O(log n) search instead of O(n)  
✅ **Batch Queries**: Efficient multi-vector search  
✅ **Incremental Updates**: No rebuild on changes  
✅ **Memory Efficient**: Float16 support (50% reduction)  
✅ **Configurable**: Environment-based configuration  
✅ **Backward Compatible**: Graceful fallback to flat search  

**Expected Performance**: 10-100x faster search for datasets >10,000 vectors
