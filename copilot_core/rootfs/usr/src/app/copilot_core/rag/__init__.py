"""RAG Hybrid Search Module.

Provides BM25 lexical search with semantic fusion via Reciprocal Rank Fusion.
"""

from .bm25 import BM25Document, BM25Hit, BM25SqliteIndex
from .hybrid_search import FusedHit, RankedHit, reciprocal_rank_fusion

__all__ = [
    "BM25Document",
    "BM25Hit",
    "BM25SqliteIndex",
    "FusedHit",
    "RankedHit",
    "reciprocal_rank_fusion",
]
