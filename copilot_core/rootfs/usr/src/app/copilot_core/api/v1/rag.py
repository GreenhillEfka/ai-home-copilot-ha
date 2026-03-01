"""RAG Hybrid Search API (Flask Blueprint).

Endpoints for hybrid search (BM25 + Semantic), document indexing,
reranking, and statistics. Mounted at /api/rag (absolute prefix).

Endpoints:
  POST /api/rag/search          – Hybrid Search (BM25 + Semantic + RRF)
  POST /api/rag/search/bm25     – BM25-only lexical search
  POST /api/rag/search/semantic  – Semantic-only search
  POST /api/rag/rerank          – RRF reranking of pre-existing hit lists
  GET  /api/rag/stats           – Index statistics
  POST /api/rag/index           – Upsert documents into index
"""

from __future__ import annotations

import importlib
import logging
import os
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from flask import Blueprint, jsonify, request

from copilot_core.api.security import validate_token
from copilot_core.rag.bm25 import BM25Config, BM25Document, BM25Hit, BM25SqliteIndex
from copilot_core.rag.hybrid_search import FusedHit, RankedHit, reciprocal_rank_fusion
from copilot_core.rag.searxng_client import SearXNGClient, SearXNGResult, get_searxng_client
from copilot_core.rag.query_router import classify_query, QueryType

logger = logging.getLogger(__name__)

bp = Blueprint("rag", __name__, url_prefix="/api/v1/rag")

_DEFAULT_DB_PATH = os.getenv("COPILOT_CORE_RAG_DB_PATH", "/data/copilot_core_rag.sqlite3")
_SEMANTIC_BACKEND_MODULE = os.getenv("COPILOT_CORE_RAG_SEMANTIC_BACKEND", "").strip()
_SEARXNG_BASE_URL = os.getenv("COPILOT_CORE_RAG_SEARXNG_URL", "http://localhost:8080")

# ── Limits ──────────────────────────────────────────────────────────────
_MAX_DOCUMENTS_PER_REQUEST = 2000
_MAX_TOP_K = 500
_MAX_RERANK_HITS = 1000


# ── Auth guard ──────────────────────────────────────────────────────────

@bp.before_request
def _require_auth() -> Any:
    if not validate_token(request):
        return jsonify({"ok": False, "error": "unauthorized"}), 401


# ── Semantic backend abstraction ────────────────────────────────────────

@dataclass
class _SemanticBackend:
    index_fn: Callable[..., Any]
    search_fn: Callable[..., Any]
    module_path: str


class _Metrics:
    """Thread-safe request metrics."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.search_requests: int = 0
        self.index_requests: int = 0
        self.rerank_requests: int = 0
        self.errors: int = 0
        self._avg_search_ms: float = 0.0
        self._avg_search_n: int = 0
        self.last_search_ms: Optional[float] = None
        self.last_error: Optional[str] = None

    def record_search(self, took_ms: float, *, ok: bool) -> None:
        with self._lock:
            self.search_requests += 1
            if ok:
                self._avg_search_n += 1
                self._avg_search_ms += (took_ms - self._avg_search_ms) / float(self._avg_search_n)
                self.last_search_ms = took_ms
            else:
                self.errors += 1

    def record_index(self, *, ok: bool) -> None:
        with self._lock:
            self.index_requests += 1
            if not ok:
                self.errors += 1

    def record_rerank(self, *, ok: bool) -> None:
        with self._lock:
            self.rerank_requests += 1
            if not ok:
                self.errors += 1

    def record_error(self, message: str) -> None:
        with self._lock:
            self.errors += 1
            self.last_error = message

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "search_requests": self.search_requests,
                "index_requests": self.index_requests,
                "rerank_requests": self.rerank_requests,
                "errors": self.errors,
                "avg_search_ms": round(self._avg_search_ms, 3) if self._avg_search_n else 0.0,
                "last_search_ms": round(self.last_search_ms, 3) if self.last_search_ms is not None else None,
                "last_error": self.last_error,
            }


_metrics = _Metrics()

# ── Singletons (double-checked locking) ────────────────────────────────

_bm25_lock = threading.Lock()
_bm25_index: Optional[BM25SqliteIndex] = None

_semantic_lock = threading.Lock()
_semantic_backend: Optional[_SemanticBackend] = None


def init_rag_api() -> None:
    """Reset RAG API state for test isolation.
    
    Call this before each test to ensure clean state.
    Resets metrics, BM25 index, and semantic backend singletons.
    """
    global _metrics, _bm25_index, _semantic_backend
    _metrics = _Metrics()
    _bm25_index = None
    _semantic_backend = None
    logger.debug("RAG API state reset for test isolation")


def _get_bm25() -> BM25SqliteIndex:
    global _bm25_index
    if _bm25_index is not None:
        return _bm25_index
    with _bm25_lock:
        if _bm25_index is None:
            _bm25_index = BM25SqliteIndex(BM25Config(db_path=_DEFAULT_DB_PATH))
            logger.info("RAG BM25 index initialized (db_path=%s)", _DEFAULT_DB_PATH)
    return _bm25_index


def _load_semantic_backend() -> Optional[_SemanticBackend]:
    global _semantic_backend
    if _semantic_backend is not None:
        return _semantic_backend

    with _semantic_lock:
        if _semantic_backend is not None:
            return _semantic_backend

        if not _SEMANTIC_BACKEND_MODULE:
            return None

        try:
            mod = importlib.import_module(_SEMANTIC_BACKEND_MODULE)
        except Exception:
            logger.exception("Failed to import semantic backend: %s", _SEMANTIC_BACKEND_MODULE)
            return None

        index_fn = getattr(mod, "rag_semantic_index", None) or getattr(mod, "semantic_index", None)
        search_fn = getattr(mod, "rag_semantic_search", None) or getattr(mod, "semantic_search", None)

        if callable(index_fn) and callable(search_fn):
            _semantic_backend = _SemanticBackend(
                index_fn=index_fn,
                search_fn=search_fn,
                module_path=_SEMANTIC_BACKEND_MODULE,
            )
            logger.info("Semantic backend loaded: %s", _SEMANTIC_BACKEND_MODULE)
            return _semantic_backend

    return None


# ── SearXNG Client (Web Search) ─────────────────────────────────────────

_searxng_lock = threading.Lock()
_searxng_client: Optional[SearXNGClient] = None


def _get_searxng_client() -> SearXNGClient:
    """Get or create global SearXNG client instance."""
    global _searxng_client
    if _searxng_client is None:
        with _searxng_lock:
            if _searxng_client is None:
                _searxng_client = SearXNGClient(base_url=_SEARXNG_BASE_URL, timeout=10)
                logger.info("SearXNG client initialized (base_url=%s)", _SEARXNG_BASE_URL)
    return _searxng_client


async def _searxng_search(
    query: str,
    categories: Optional[List[str]] = None,
    top_k: int = 10,
    warnings: Optional[List[str]] = None,
) -> List[SearXNGResult]:
    """Search SearXNG for web results.
    
    Args:
        query: Search query
        categories: SearXNG categories (e.g., ['general', 'news', 'weather'])
        top_k: Maximum results to return
        warnings: List to append warnings to
    
    Returns:
        List of SearXNGResult objects
    """
    if warnings is None:
        warnings = []
    
    client = _get_searxng_client()
    
    try:
        # Note: This is async, but Flask is sync. We'll use asyncio.run() or
        # the client should handle this internally. For now, assume sync wrapper.
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        results = await client.search(query=query, categories=categories, top_k=top_k)
        return results
    
    except Exception as exc:
        logger.warning("SearXNG search failed for query '%s': %s", query, exc)
        warnings.append(f"Web search (SearXNG) failed: {exc}")
        return []


# ── Internal helpers ────────────────────────────────────────────────────

def _semantic_index(
    *,
    namespace: str,
    documents: Sequence[Dict[str, Any]],
    warnings: List[str],
) -> int:
    backend = _load_semantic_backend()
    if backend is None:
        warnings.append("semantic backend not configured; BM25-only indexing performed")
        return 0

    try:
        result = backend.index_fn(namespace=namespace, documents=documents)
    except TypeError:
        result = backend.index_fn(documents=documents, namespace=namespace)
    except Exception as exc:
        logger.exception("Semantic index failed (namespace=%s)", namespace)
        warnings.append("semantic index failed; BM25-only index is still updated")
        _metrics.record_error(f"semantic index failed: {exc}")
        return 0

    if isinstance(result, int):
        return result
    if isinstance(result, list):
        return len(result)
    return 0


def _semantic_search(
    *,
    namespace: str,
    query: str,
    top_k: int,
    warnings: List[str],
) -> List[RankedHit]:
    backend = _load_semantic_backend()
    if backend is None:
        warnings.append("semantic backend not configured; returning BM25-only results")
        return []

    try:
        raw = backend.search_fn(namespace=namespace, query=query, top_k=top_k)
    except TypeError:
        raw = backend.search_fn(query=query, top_k=top_k, namespace=namespace)
    except Exception as exc:
        logger.exception("Semantic search failed (namespace=%s)", namespace)
        warnings.append("semantic search failed; returning BM25-only results")
        _metrics.record_error(f"semantic search failed: {exc}")
        return []

    hits: List[RankedHit] = []
    if not raw:
        return hits

    for i, item in enumerate(raw, start=1):
        doc_id: Optional[str] = None
        score: float = 0.0

        if isinstance(item, dict):
            doc_id = item.get("id") or item.get("doc_id") or item.get("document_id")
            try:
                score = float(item.get("score", 0.0))
            except Exception:
                score = 0.0
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            doc_id = str(item[0]) if item[0] is not None else None
            try:
                score = float(item[1])
            except Exception:
                score = 0.0
        else:
            doc_id = getattr(item, "id", None) or getattr(item, "doc_id", None)
            try:
                score = float(getattr(item, "score", 0.0))
            except Exception:
                score = 0.0

        if not doc_id:
            continue
        hits.append(RankedHit(doc_id=str(doc_id), score=float(score), rank=int(i)))

    return hits


def _clamp_top_k(raw: Any, default: int = 10) -> int:
    try:
        v = int(raw)
    except (TypeError, ValueError):
        return default
    return max(1, min(v, _MAX_TOP_K))


def _enrich_results(
    bm25: BM25SqliteIndex,
    namespace: str,
    doc_ids: List[str],
    include_text: bool,
    include_metadata: bool,
) -> Dict[str, Dict[str, Any]]:
    if not doc_ids or (not include_text and not include_metadata):
        return {}
    return bm25.get_documents(namespace=namespace, doc_ids=doc_ids)


def _build_result_entry(
    doc_id: str,
    score: float,
    docs: Dict[str, Dict[str, Any]],
    include_text: bool,
    include_metadata: bool,
    **extra: Any,
) -> Dict[str, Any]:
    doc = docs.get(doc_id, {})
    entry: Dict[str, Any] = {"id": doc_id, "score": round(score, 6)}
    entry.update(extra)
    if include_text:
        entry["text"] = doc.get("text")
    if include_metadata:
        entry["metadata"] = doc.get("metadata")
    return entry


# ══════════════════════════════════════════════════════════════════════════
# ENDPOINT 1: POST /api/rag/search  –  Hybrid Search (BM25 + Semantic + RRF)
# ══════════════════════════════════════════════════════════════════════════

@bp.route("/search", methods=["POST"])
def rag_search() -> Tuple[Any, int] | Any:
    """Hybrid search combining BM25 lexical and semantic results via RRF."""
    started = time.monotonic()
    warnings: List[str] = []
    ok = False

    try:
        data: Dict[str, Any] = request.get_json(silent=True) or {}
        namespace = str(data.get("namespace", "default") or "default")
        query = str(data.get("query", "")).strip()

        if not query:
            return jsonify({"error": "query required"}), 400

        top_k = _clamp_top_k(data.get("top_k", 10))
        use_lexical = bool(data.get("use_lexical", True))
        use_semantic = bool(data.get("use_semantic", True))
        rrf_k = max(1, int(data.get("rrf_k", 60)))
        lexical_weight = max(0.0, float(data.get("lexical_weight", 1.0)))
        semantic_weight = max(0.0, float(data.get("semantic_weight", 1.0)))
        include_text = bool(data.get("include_text", True))
        include_metadata = bool(data.get("include_metadata", True))

        if not use_lexical and not use_semantic:
            return jsonify({"error": "at least one of use_lexical/use_semantic must be true"}), 400

        bm25 = _get_bm25()

        lexical_hits: List[BM25Hit] = []
        semantic_hits: List[RankedHit] = []

        if use_lexical:
            lexical_hits = bm25.search(
                namespace=namespace, query=query, top_k=top_k,
                include_text=False, include_metadata=False,
            )

        if use_semantic:
            semantic_hits = _semantic_search(
                namespace=namespace, query=query, top_k=top_k, warnings=warnings,
            )

        mode: str
        results: List[Dict[str, Any]] = []

        if use_lexical and use_semantic:
            fused = reciprocal_rank_fusion(
                lexical_hits=[
                    RankedHit(doc_id=h.doc_id, score=h.score, rank=h.rank) for h in lexical_hits
                ],
                semantic_hits=semantic_hits,
                top_k=top_k, k=rrf_k,
                lexical_weight=lexical_weight, semantic_weight=semantic_weight,
            )
            mode = "hybrid_rrf"
            doc_ids = [f.doc_id for f in fused]
            docs = _enrich_results(bm25, namespace, doc_ids, include_text, include_metadata)

            for f in fused:
                results.append(_build_result_entry(
                    f.doc_id, f.fused_score, docs, include_text, include_metadata,
                    fused_score=round(f.fused_score, 6),
                    lexical_rank=f.lexical_rank, semantic_rank=f.semantic_rank,
                    lexical_score=f.lexical_score, semantic_score=f.semantic_score,
                ))

        elif use_lexical:
            mode = "bm25"
            trimmed = lexical_hits[:top_k]
            doc_ids = [h.doc_id for h in trimmed]
            docs = _enrich_results(bm25, namespace, doc_ids, include_text, include_metadata)
            for h in trimmed:
                results.append(_build_result_entry(
                    h.doc_id, h.score, docs, include_text, include_metadata,
                    lexical_score=round(h.score, 6), lexical_rank=h.rank,
                ))
        else:
            mode = "semantic"
            trimmed = semantic_hits[:top_k]
            doc_ids = [h.doc_id for h in trimmed]
            docs = _enrich_results(bm25, namespace, doc_ids, include_text, include_metadata)
            for h in trimmed:
                results.append(_build_result_entry(
                    h.doc_id, h.score, docs, include_text, include_metadata,
                    semantic_score=round(h.score, 6), semantic_rank=h.rank,
                ))

        ok = True
        took_ms = (time.monotonic() - started) * 1000.0
        return jsonify({
            "namespace": namespace,
            "query": query,
            "mode": mode,
            "results": results,
            "result_count": len(results),
            "warnings": warnings,
            "took_ms": round(took_ms, 3),
        })

    except ValueError as exc:
        _metrics.record_error(str(exc))
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        _metrics.record_error(str(exc))
        logger.exception("RAG hybrid search failed")
        return jsonify({"error": "RAG search failed"}), 500
    finally:
        took_ms = (time.monotonic() - started) * 1000.0
        _metrics.record_search(took_ms, ok=ok)


# ══════════════════════════════════════════════════════════════════════════
# ENDPOINT 2: POST /api/rag/search/bm25  –  BM25-only lexical search
# ══════════════════════════════════════════════════════════════════════════

@bp.route("/search/bm25", methods=["POST"])
def rag_search_bm25() -> Tuple[Any, int] | Any:
    """BM25 lexical search only."""
    started = time.monotonic()
    ok = False

    try:
        data: Dict[str, Any] = request.get_json(silent=True) or {}
        namespace = str(data.get("namespace", "default") or "default")
        query = str(data.get("query", "")).strip()

        if not query:
            return jsonify({"error": "query required"}), 400

        top_k = _clamp_top_k(data.get("top_k", 10))
        include_text = bool(data.get("include_text", True))
        include_metadata = bool(data.get("include_metadata", True))

        bm25 = _get_bm25()
        hits = bm25.search(
            namespace=namespace, query=query, top_k=top_k,
            include_text=include_text, include_metadata=include_metadata,
        )

        results: List[Dict[str, Any]] = []
        for h in hits:
            entry: Dict[str, Any] = {
                "id": h.doc_id,
                "score": round(h.score, 6),
                "rank": h.rank,
            }
            if include_text:
                entry["text"] = h.text
            if include_metadata:
                entry["metadata"] = h.metadata
            results.append(entry)

        ok = True
        took_ms = (time.monotonic() - started) * 1000.0
        return jsonify({
            "namespace": namespace,
            "query": query,
            "mode": "bm25",
            "results": results,
            "result_count": len(results),
            "took_ms": round(took_ms, 3),
        })

    except ValueError as exc:
        _metrics.record_error(str(exc))
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        _metrics.record_error(str(exc))
        logger.exception("RAG BM25 search failed")
        return jsonify({"error": "RAG BM25 search failed"}), 500
    finally:
        took_ms = (time.monotonic() - started) * 1000.0
        _metrics.record_search(took_ms, ok=ok)


# ══════════════════════════════════════════════════════════════════════════
# ENDPOINT 3: POST /api/rag/search/semantic  –  Semantic-only search
# ══════════════════════════════════════════════════════════════════════════

@bp.route("/search/semantic", methods=["POST"])
def rag_search_semantic() -> Tuple[Any, int] | Any:
    """Semantic (embedding-based) search only."""
    started = time.monotonic()
    warnings: List[str] = []
    ok = False

    try:
        data: Dict[str, Any] = request.get_json(silent=True) or {}
        namespace = str(data.get("namespace", "default") or "default")
        query = str(data.get("query", "")).strip()

        if not query:
            return jsonify({"error": "query required"}), 400

        top_k = _clamp_top_k(data.get("top_k", 10))
        include_text = bool(data.get("include_text", True))
        include_metadata = bool(data.get("include_metadata", True))

        hits = _semantic_search(
            namespace=namespace, query=query, top_k=top_k, warnings=warnings,
        )

        bm25 = _get_bm25()
        doc_ids = [h.doc_id for h in hits[:top_k]]
        docs = _enrich_results(bm25, namespace, doc_ids, include_text, include_metadata)

        results: List[Dict[str, Any]] = []
        for h in hits[:top_k]:
            results.append(_build_result_entry(
                h.doc_id, h.score, docs, include_text, include_metadata,
                semantic_score=round(h.score, 6), semantic_rank=h.rank,
            ))

        ok = True
        took_ms = (time.monotonic() - started) * 1000.0
        return jsonify({
            "namespace": namespace,
            "query": query,
            "mode": "semantic",
            "results": results,
            "result_count": len(results),
            "warnings": warnings,
            "took_ms": round(took_ms, 3),
        })

    except ValueError as exc:
        _metrics.record_error(str(exc))
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        _metrics.record_error(str(exc))
        logger.exception("RAG semantic search failed")
        return jsonify({"error": "RAG semantic search failed"}), 500
    finally:
        took_ms = (time.monotonic() - started) * 1000.0
        _metrics.record_search(took_ms, ok=ok)


# ══════════════════════════════════════════════════════════════════════════
# ENDPOINT 4: POST /api/rag/rerank  –  RRF Reranking
# ══════════════════════════════════════════════════════════════════════════

@bp.route("/rerank", methods=["POST"])
def rag_rerank() -> Tuple[Any, int] | Any:
    """Rerank pre-existing hit lists using Reciprocal Rank Fusion."""
    started = time.monotonic()
    ok = False

    try:
        data: Dict[str, Any] = request.get_json(silent=True) or {}

        lexical_raw = data.get("lexical_hits", [])
        semantic_raw = data.get("semantic_hits", [])

        if not lexical_raw and not semantic_raw:
            return jsonify({"error": "at least one of lexical_hits/semantic_hits required"}), 400

        if len(lexical_raw) > _MAX_RERANK_HITS or len(semantic_raw) > _MAX_RERANK_HITS:
            return jsonify({"error": f"max {_MAX_RERANK_HITS} hits per list"}), 400

        top_k = _clamp_top_k(data.get("top_k", 10))
        rrf_k = max(1, int(data.get("rrf_k", 60)))
        lexical_weight = max(0.0, float(data.get("lexical_weight", 1.0)))
        semantic_weight = max(0.0, float(data.get("semantic_weight", 1.0)))

        def _parse_hits(raw: List[Dict[str, Any]]) -> List[RankedHit]:
            hits: List[RankedHit] = []
            for i, item in enumerate(raw, start=1):
                doc_id = str(item.get("id") or item.get("doc_id", "")).strip()
                if not doc_id:
                    continue
                score = float(item.get("score", 0.0))
                rank = int(item.get("rank", i))
                hits.append(RankedHit(doc_id=doc_id, score=score, rank=rank))
            return hits

        lexical_hits = _parse_hits(lexical_raw)
        semantic_hits = _parse_hits(semantic_raw)

        fused = reciprocal_rank_fusion(
            lexical_hits=lexical_hits,
            semantic_hits=semantic_hits,
            top_k=top_k, k=rrf_k,
            lexical_weight=lexical_weight, semantic_weight=semantic_weight,
        )

        results: List[Dict[str, Any]] = []
        for f in fused:
            results.append({
                "id": f.doc_id,
                "fused_score": round(f.fused_score, 6),
                "lexical_rank": f.lexical_rank,
                "semantic_rank": f.semantic_rank,
                "lexical_score": f.lexical_score,
                "semantic_score": f.semantic_score,
            })

        ok = True
        took_ms = (time.monotonic() - started) * 1000.0
        return jsonify({
            "results": results,
            "result_count": len(results),
            "rrf_k": rrf_k,
            "took_ms": round(took_ms, 3),
        })

    except ValueError as exc:
        _metrics.record_error(str(exc))
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        _metrics.record_error(str(exc))
        logger.exception("RAG rerank failed")
        return jsonify({"error": "RAG rerank failed"}), 500
    finally:
        _metrics.record_rerank(ok=ok)


# ══════════════════════════════════════════════════════════════════════════
# ENDPOINT 5: GET /api/rag/stats  –  Index Statistics
# ══════════════════════════════════════════════════════════════════════════

@bp.route("/stats", methods=["GET"])
def rag_stats() -> Tuple[Any, int] | Any:
    """Return BM25 index statistics and request metrics."""
    namespace = request.args.get("namespace", "default")

    try:
        bm25 = _get_bm25()
        s = bm25.stats(namespace=namespace)
        return jsonify({
            "namespace": s.namespace,
            "doc_count": s.doc_count,
            "term_count": s.term_count,
            "posting_count": s.posting_count,
            "avg_doc_len": round(s.avg_doc_len, 3),
            "total_doc_len": s.total_doc_len,
            "updated_at": s.updated_at,
            "db_path": s.db_path,
            "db_size_bytes": s.db_size_bytes,
            "schema_version": s.schema_version,
            "semantic_backend": _SEMANTIC_BACKEND_MODULE or None,
            "metrics": _metrics.snapshot(),
        })
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        logger.exception("RAG stats failed")
        return jsonify({"error": "RAG stats failed"}), 500


# ══════════════════════════════════════════════════════════════════════════
# ENDPOINT 6: POST /api/rag/index  –  Document Indexing
# ══════════════════════════════════════════════════════════════════════════

@bp.route("/index", methods=["POST"])
def rag_index() -> Tuple[Any, int] | Any:
    """Upsert documents into the BM25 (and optionally semantic) index."""
    started = time.monotonic()
    warnings: List[str] = []
    ok = False

    try:
        data: Dict[str, Any] = request.get_json(silent=True) or {}
        namespace = str(data.get("namespace", "default") or "default")
        documents_data = data.get("documents", [])
        index_semantic = bool(data.get("index_semantic", True))

        if not documents_data:
            return jsonify({"error": "documents required"}), 400
        if len(documents_data) > _MAX_DOCUMENTS_PER_REQUEST:
            return jsonify({"error": f"max {_MAX_DOCUMENTS_PER_REQUEST} documents per request"}), 400

        docs: List[BM25Document] = []
        for d in documents_data:
            doc_id = str(d.get("id", "")).strip()
            text = str(d.get("text", "")).strip()
            metadata = d.get("metadata")

            if not doc_id:
                return jsonify({"error": "document id required"}), 400
            if not text:
                return jsonify({"error": "document text required"}), 400

            docs.append(BM25Document(doc_id=doc_id, text=text, metadata=metadata))

        bm25 = _get_bm25()
        bm25_indexed, bm25_errors = bm25.upsert_documents(namespace=namespace, documents=docs)

        semantic_indexed = 0
        if index_semantic:
            semantic_indexed = _semantic_index(
                namespace=namespace, documents=documents_data, warnings=warnings,
            )

        ok = True
        took_ms = (time.monotonic() - started) * 1000.0
        return jsonify({
            "namespace": namespace,
            "bm25_indexed": bm25_indexed,
            "semantic_indexed": semantic_indexed,
            "errors": bm25_errors,
            "warnings": warnings,
            "took_ms": round(took_ms, 3),
        })

    except ValueError as exc:
        _metrics.record_error(str(exc))
        return jsonify({"error": str(exc)}), 400
    except Exception:
        _metrics.record_error(str(exc))
        logger.exception("RAG index failed")
        return jsonify({"error": "RAG index failed"}), 500
    finally:
        _metrics.record_index(ok=ok)


# ══════════════════════════════════════════════════════════════════════════
# ENDPOINT 7: POST /api/rag/search/enhanced  –  Hybrid Search with SearXNG
# ══════════════════════════════════════════════════════════════════════════

@bp.route("/search/enhanced", methods=["POST"])
def rag_search_enhanced() -> Tuple[Any, int] | Any:
    """Enhanced hybrid search with SearXNG web integration.
    
    This endpoint implements the full RAG pipeline with query routing:
    1. Classify query as local, web, or hybrid
    2. Search local sources (BM25 + Semantic)
    3. Search web (SearXNG) if needed
    4. Fuse results with weighted RRF
    
    Request body:
        - query: Search query string (required)
        - namespace: Index namespace (default: "default")
        - use_web: Force web search (default: auto-detect via query router)
        - top_k: Max results (default: 10)
        - searxng_categories: SearXNG categories (default: ["general", "news"])
        - weights: Fusion weights (default: {"local": 1.0, "semantic": 0.8, "web": 0.5})
    
    Returns:
        Enhanced search results with query classification and multi-source fusion
    """
    started = time.monotonic()
    warnings: List[str] = []
    ok = False
    
    try:
        data: Dict[str, Any] = request.get_json(silent=True) or {}
        namespace = str(data.get("namespace", "default") or "default")
        query = str(data.get("query", "")).strip()
        
        if not query:
            return jsonify({"error": "query required"}), 400
        
        top_k = _clamp_top_k(data.get("top_k", 10))
        use_web = data.get("use_web")  # None = auto-detect
        searxng_categories = data.get("searxng_categories", ["general", "news"])
        
        # Fusion weights
        weights_config = data.get("weights", {})
        local_weight = float(weights_config.get("local", 1.0))
        semantic_weight = float(weights_config.get("semantic", 0.8))
        web_weight = float(weights_config.get("web", 0.5))
        
        include_text = bool(data.get("include_text", True))
        include_metadata = bool(data.get("include_metadata", True))
        
        # Step 1: Query Classification
        classification = classify_query(query)
        query_type = classification.query_type
        
        # Determine if web search is needed
        perform_web_search = False
        if use_web is True:
            perform_web_search = True
        elif use_web is False:
            perform_web_search = False
        else:
            # Auto-detect based on query classification
            perform_web_search = classification.use_web_search
        
        logger.info(
            "Enhanced RAG search: query='%s', type=%s, web=%s",
            query,
            query_type.value,
            perform_web_search,
        )
        
        bm25 = _get_bm25()
        
        # Step 2: Local Search (BM25 + Semantic)
        lexical_hits: List[BM25Hit] = []
        semantic_hits: List[RankedHit] = []
        
        # Always do BM25 for local context
        lexical_hits = bm25.search(
            namespace=namespace,
            query=query,
            top_k=top_k,
            include_text=False,
            include_metadata=False,
        )
        
        # Semantic search (if backend configured)
        semantic_hits = _semantic_search(
            namespace=namespace,
            query=query,
            top_k=top_k,
            warnings=warnings,
        )
        
        # Step 3: Web Search (SearXNG) if needed
        web_results: List[SearXNGResult] = []
        
        if perform_web_search:
            web_results = _searxng_search_sync(
                query=query,
                categories=searxng_categories,
                top_k=top_k,
                warnings=warnings,
            )
        
        # Step 4: Result Fusion
        mode: str
        results: List[Dict[str, Any]] = []
        
        if query_type == QueryType.LOCAL and not perform_web_search:
            # Local-only mode
            mode = "local"
            
            # Fuse BM25 + Semantic
            if lexical_hits and semantic_hits:
                fused = reciprocal_rank_fusion(
                    lexical_hits=[
                        RankedHit(doc_id=h.doc_id, score=h.score, rank=h.rank)
                        for h in lexical_hits
                    ],
                    semantic_hits=semantic_hits,
                    top_k=top_k,
                    k=60,
                    lexical_weight=local_weight,
                    semantic_weight=semantic_weight,
                )
                doc_ids = [f.doc_id for f in fused]
                docs = _enrich_results(bm25, namespace, doc_ids, include_text, include_metadata)
                
                for f in fused:
                    results.append(_build_result_entry(
                        f.doc_id,
                        f.fused_score,
                        docs,
                        include_text,
                        include_metadata,
                        fused_score=round(f.fused_score, 6),
                        lexical_rank=f.lexical_rank,
                        semantic_rank=f.semantic_rank,
                    ))
            elif lexical_hits:
                # BM25 only
                trimmed = lexical_hits[:top_k]
                doc_ids = [h.doc_id for h in trimmed]
                docs = _enrich_results(bm25, namespace, doc_ids, include_text, include_metadata)
                for h in trimmed:
                    results.append(_build_result_entry(
                        h.doc_id,
                        h.score,
                        docs,
                        include_text,
                        include_metadata,
                        lexical_score=round(h.score, 6),
                        lexical_rank=h.rank,
                    ))
            else:
                # Semantic only
                trimmed = semantic_hits[:top_k]
                doc_ids = [h.doc_id for h in trimmed]
                docs = _enrich_results(bm25, namespace, doc_ids, include_text, include_metadata)
                for h in trimmed:
                    results.append(_build_result_entry(
                        h.doc_id,
                        h.score,
                        docs,
                        include_text,
                        include_metadata,
                        semantic_score=round(h.score, 6),
                        semantic_rank=h.rank,
                    ))
        
        elif query_type == QueryType.WEB and perform_web_search:
            # Web-only mode
            mode = "web"
            
            for i, web_result in enumerate(web_results[:top_k]):
                results.append({
                    "id": web_result.url,
                    "title": web_result.title,
                    "url": web_result.url,
                    "content": web_result.content,
                    "score": round(web_result.score, 6),
                    "rank": i + 1,
                    "source": "searxng",
                    "category": web_result.category,
                    "engine": web_result.engine,
                })
        
        else:
            # Hybrid mode (local + web)
            mode = "hybrid"
            
            # First, fuse local results
            local_results: List[Dict[str, Any]] = []
            
            if lexical_hits and semantic_hits:
                fused = reciprocal_rank_fusion(
                    lexical_hits=[
                        RankedHit(doc_id=h.doc_id, score=h.score, rank=h.rank)
                        for h in lexical_hits
                    ],
                    semantic_hits=semantic_hits,
                    top_k=top_k,
                    k=60,
                    lexical_weight=local_weight,
                    semantic_weight=semantic_weight,
                )
                doc_ids = [f.doc_id for f in fused]
                docs = _enrich_results(bm25, namespace, doc_ids, include_text, include_metadata)
                
                for f in fused:
                    local_results.append(_build_result_entry(
                        f.doc_id,
                        f.fused_score,
                        docs,
                        include_text,
                        include_metadata,
                        fused_score=round(f.fused_score, 6),
                        source="local",
                    ))
            elif lexical_hits:
                for h in lexical_hits[:top_k]:
                    local_results.append({
                        "id": h.doc_id,
                        "score": round(h.score, 6),
                        "rank": h.rank,
                        "source": "local_bm25",
                    })
            
            # Add web results
            web_result_dicts = [
                {
                    "id": web_result.url,
                    "title": web_result.title,
                    "url": web_result.url,
                    "content": web_result.content,
                    "score": round(web_result.score * web_weight, 6),
                    "source": "searxng",
                    "category": web_result.category,
                    "engine": web_result.engine,
                }
                for web_result in web_results[:top_k]
            ]
            
            # Combine and re-rank (simple approach: local first, then web)
            # For more sophisticated fusion, implement cross-source RRF
            results = local_results + web_result_dicts
            results = results[:top_k]
        
        ok = True
        took_ms = (time.monotonic() - started) * 1000.0
        
        return jsonify({
            "namespace": namespace,
            "query": query,
            "mode": mode,
            "query_classification": {
                "type": query_type.value,
                "confidence": classification.confidence,
                "web_keywords": classification.web_keywords_found,
                "local_keywords": classification.local_keywords_found,
                "reasoning": classification.reasoning,
            },
            "results": results,
            "result_count": len(results),
            "sources_used": {
                "local_bm25": len(lexical_hits) > 0,
                "semantic": len(semantic_hits) > 0,
                "web_searxng": len(web_results) > 0,
            },
            "warnings": warnings,
            "took_ms": round(took_ms, 3),
        })
    
    except ValueError as exc:
        _metrics.record_error(str(exc))
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        _metrics.record_error(str(exc))
        logger.exception("Enhanced RAG search failed")
        return jsonify({"error": "Enhanced RAG search failed"}), 500
    finally:
        took_ms = (time.monotonic() - started) * 1000.0
        _metrics.record_search(took_ms, ok=ok)


def _searxng_search_sync(
    query: str,
    categories: Optional[List[str]] = None,
    top_k: int = 10,
    warnings: Optional[List[str]] = None,
) -> List[SearXNGResult]:
    """Synchronous wrapper for SearXNG search.
    
    Flask is synchronous, but our SearXNG client is async.
    This wrapper handles the async call properly.
    """
    import asyncio
    
    client = _get_searxng_client()
    
    try:
        # Try to get existing event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context (unlikely in Flask, but handle it)
                # Return empty results to avoid blocking
                logger.warning("Event loop running, skipping SearXNG search")
                return []
        except RuntimeError:
            # No event loop exists, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        results = loop.run_until_complete(
            client.search(query=query, categories=categories, top_k=top_k)
        )
        return results
    
    except Exception as exc:
        logger.warning("SearXNG sync search failed for query '%s': %s", query, exc)
        if warnings is not None:
            warnings.append(f"Web search failed: {exc}")
        return []
