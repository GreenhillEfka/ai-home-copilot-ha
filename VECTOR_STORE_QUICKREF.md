# VectorStore HNSW - Quick Reference

## Configuration

### Environment Variables
```bash
# Index type
export COPILOT_VECTOR_INDEX_TYPE=hnsw  # or "flat"

# HNSW parameters
export COPILOT_VECTOR_HNSW_M=16                    # Connections per node (16-64)
export COPILOT_VECTOR_HNSW_EF_CONSTRUCTION=200     # Build width (100-400)
export COPILOT_VECTOR_HNSW_EF_SEARCH=50            # Search width (20-100)
export COPILOT_VECTOR_HNSW_MAX_ELEMENTS=100000     # Max index size

# Memory optimization
export COPILOT_VECTOR_FLOAT16=true                 # Use float16 (50% memory)
export COPILOT_VECTOR_BATCH_SIZE=100               # Default batch size

# Storage
export COPILOT_VECTOR_DB_PATH=/data/vector_store.db
export COPILOT_VECTOR_PERSIST=true
export COPILOT_VECTOR_CACHE_SIZE=500
export COPILOT_VECTOR_SIMILARITY_THRESHOLD=0.7
```

### Programmatic Config
```python
from copilot_core.vector_store.config import VectorStoreConfig

config = VectorStoreConfig(
    index_type="hnsw",
    hnsw_m=16,
    hnsw_ef_construction=200,
    hnsw_ef_search=50,
    hnsw_max_elements=100000,
    use_float16=True,
    batch_size=100,
)
```

## API Usage

### Python API
```python
from copilot_core.vector_store.store import VectorStore, get_vector_store

# Get singleton instance
store = get_vector_store()

# Or create custom instance
store = VectorStore(config)

# Insert vector
await store.upsert(
    entry_id="entity:light_1",
    vector=[0.1, 0.2, ...],  # 384-dim
    entry_type="entity",
    metadata={"domain": "light", "area": "living_room"}
)

# Search
results = await store.search_similar(
    query_vector=[0.1, 0.2, ...],
    entry_type="entity",
    limit=10,
    threshold=0.7,
)

# Batch search
batch_results = await store.batch_search(
    query_vectors=[vec1, vec2, vec3],
    entry_type="entity",
    limit=10,
)

# Get stats
stats = await store.stats()
```

### REST API

#### Batch Search
```bash
POST /api/v1/rag/search/batch
Content-Type: application/json

{
  "namespace": "default",
  "queries": ["query1", "query2", "query3"],
  "top_k": 10,
  "use_lexical": true,
  "use_semantic": true,
  "rrf_k": 60,
  "lexical_weight": 1.0,
  "semantic_weight": 1.0,
  "include_text": true,
  "include_metadata": true
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
      "hits": [
        {
          "id": "doc_123",
          "score": 0.95,
          "fused_score": 0.032,
          "lexical_rank": 5,
          "semantic_rank": 2,
          "text": "...",
          "metadata": {...}
        }
      ],
      "took_ms": 12.5
    }
  ],
  "total_took_ms": 45.2,
  "batch_size": 3
}
```

## Performance Tuning

### Dataset Size Recommendations

| Size | M | ef_construction | ef_search |
|------|---|-----------------|-----------|
| <10K | 8-16 | 100-150 | 20-30 |
| 10K-100K | 16-32 | 200-300 | 50-100 |
| 100K-1M | 32-48 | 300-400 | 100-150 |
| >1M | 48-64 | 400+ | 150-200 |

### Memory vs Accuracy Trade-off

**Higher M:**
- ✅ Better recall
- ❌ More memory (M × 4 bytes per element per dimension)
- ❌ Slower indexing

**Higher ef_search:**
- ✅ Better recall
- ❌ Slower search
- ✅ No memory impact

**Higher ef_construction:**
- ✅ Better index quality
- ❌ Slower indexing
- ✅ No runtime impact

## Benchmarking

### Run Benchmarks
```bash
cd /path/to/app

# Quick test (10K vectors)
python -m copilot_core.vector_store.benchmark \
  --num-vectors 10000 \
  --dim 384 \
  --queries 100

# Large test (100K vectors)
python -m copilot_core.vector_store.benchmark \
  --num-vectors 100000 \
  --dim 384 \
  --queries 200 \
  --output /tmp/benchmark.json

# Test HNSW implementation
python -m copilot_core.vector_store.test_hnsw
```

### Expected Performance

```
Dataset: 10,000 vectors, 384 dimensions
─────────────────────────────────────
HNSW:  5.2ms avg search (192 q/s)
Flat:  52.1ms avg search (19 q/s)
Speedup: 10.0x faster

Dataset: 100,000 vectors, 384 dimensions
───────────────────────────────────────
HNSW:  8.3ms avg search (120 q/s)
Flat:  523.7ms avg search (2 q/s)
Speedup: 63.1x faster
```

## Troubleshooting

### hnswlib not available
```
WARNING: hnswlib not available, falling back to flat index
```
**Solution:** Install hnswlib or rebuild Docker image

### Index build failed
```
ERROR: Failed to initialize HNSW index
```
**Solution:** Check `hnsw_max_elements` is sufficient for dataset size

### High memory usage
```python
# Enable Float16
config.use_float16 = True

# Reduce cache size
config.cache_size = 250

# Lower M parameter
config.hnsw_m = 8
```

### Slow search
```python
# Increase ef_search for better accuracy/speed tradeoff
config.hnsw_ef_search = 100

# Or reduce if too slow
config.hnsw_ef_search = 30
```

## Monitoring

### Key Metrics
- `avg_search_ms`: Average search latency
- `p95_search_ms`: 95th percentile latency
- `queries_per_sec`: Throughput
- `cache_size`: In-memory cache entries
- `total_entries`: Total indexed vectors

### Stats Endpoint
```python
stats = await store.stats()
print(f"Index type: {stats['index_config']['type']}")
print(f"Total entries: {stats['total_entries']}")
print(f"Cache size: {stats['cache_size']}")
```

## Best Practices

1. **Use HNSW for >1,000 vectors** - Overhead not worth it for smaller datasets
2. **Enable Float16** - 50% memory savings with minimal accuracy loss
3. **Tune ef_search** - Balance speed vs accuracy for your use case
4. **Set max_elements** - Prevent index rebuilds by sizing upfront
5. **Monitor p95 latency** - Average can hide tail latency issues
6. **Use batch queries** - More efficient than individual requests
7. **Cache frequently accessed** - Hot vectors stay in memory

---

**Version:** v12.3.0 Iteration 5  
**Updated:** 2026-03-01
