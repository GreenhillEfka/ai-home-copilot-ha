"""RAG Hybrid Search Module.

Provides BM25 lexical search with semantic fusion via Reciprocal Rank Fusion.
Now includes SearXNG web search integration and query routing.
"""

from .bm25 import BM25Document, BM25Hit, BM25SqliteIndex
from .hybrid_search import FusedHit, RankedHit, reciprocal_rank_fusion
from .searxng_client import SearXNGClient, SearXNGResult, get_searxng_client
from .query_router import QueryType, QueryClassification, classify_query

__all__ = [
    "BM25Document",
    "BM25Hit",
    "BM25SqliteIndex",
    "FusedHit",
    "RankedHit",
    "reciprocal_rank_fusion",
    "SearXNGClient",
    "SearXNGResult",
    "get_searxng_client",
    "QueryType",
    "QueryClassification",
    "classify_query",
]
