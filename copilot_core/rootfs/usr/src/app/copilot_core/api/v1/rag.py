"""RAG Hybrid Search API (Flask Blueprint).

Endpoints for hybrid search (BM25 + Semantic), document indexing, and statistics.
Flask-compatible version for PilotSuite Core.
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

from copilot_core.rag.bm25 import BM25Document, BM25Hit, BM25SqliteIndex
from copilot_core.rag.hybrid_search import FusedHit, RankedHit, reciprocal_rank_fusion

logger = logging.getLogger(__name__)

bp = Blueprint("rag", __name__, url_prefix="/api/v1/rag")

_DEFAULT_DB_PATH = os.getenv("COPILOT_CORE_RAG_DB_PATH", "/data/copilot_core_rag.sqlite3")
_SEMANTIC_BACKEND_MODULE = os.getenv("COPILOT_CORE_RAG_SEMANTIC_BACKEND", "").strip()


@dataclass
class _SemanticBackend:
    index_fn: Callable[..., Any]
    search_fn: Callable[..., Any]
    module_path: str


class _Metrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.search_requests = 0
        self.multi_search_requests = 0
        self.index_requests = 0
        self.errors = 0
        self._avg_search_ms = 0.0
        self._avg_search_n = 0
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

    def record_multi_search(self, *, ok: bool) -> None:
        with self._lock:
            self.multi_search_requests += 1
            if not ok:
                self.errors += 1

    def record_index(self, *, ok: bool) -> None:
        with self._lock:
            self.index_requests += 1
            if not ok:
                self.errors += 1

    def record_error(self, message: str) -> None:
        with self._lock:
            self.errors += 1
            self.last_error = message

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "search_requests": int(self.search_requests),
                "multi_search_requests": int(self.multi_search_requests),
                "index_requests": int(self.index_requests),
                "errors": int(self.errors),
                "avg_search_ms": float(self._avg_search_ms) if self._avg_search_n else 0.0,
                "last_search_ms": float(self.last_search_ms) if self.last_search_ms is not None else None,
                "last_error": self.last_error,
            }


_metrics = _Metrics()

_bm25_lock = threading.Lock()
_bm25_index: Optional[BM25SqliteIndex] = None

_semantic_lock = threading.Lock()
_semantic_backend: Optional[_SemanticBackend] = None


def _get_bm25() -> BM25SqliteIndex:
    global _bm25_index
    if _bm25_index is not None:
        return _bm25_index
    with _bm25_lock:
        if _bm25_index is None:
            _bm25_index = BM25SqliteIndex(db_path=_DEFAULT_DB_PATH)
            logger.info("RAG BM25 index initialized (db_path=%s)", _DEFAULT_DB_PATH)
    return _bm25_index


def _load_semantic_backend() -> Optional[_SemanticBackend]:
    global _semantic_backend
    if _semantic_backend is not None:
        return _semantic_backend

    with _semantic_lock:
        if _semantic_backend is not None:
            return _semantic_backend

        module_candidates = []
        if _SEMANTIC_BACKEND_MODULE:
            module_candidates.append(_SEMANTIC_BACKEND_MODULE)

        for module_path in module_candidates:
            try:
                mod = importlib.import_module(module_path)
            except Exception:
                logger.exception("Failed to import semantic backend module: %s", module_path)
                continue

            index_fn = getattr(mod, "rag_semantic_index", None) or getattr(mod, "semantic_index", None)
            search_fn = getattr(mod, "rag_semantic_search", None) or getattr(mod, "semantic_search", None)

            if callable(index_fn) and callable(search_fn):
                _semantic_backend = _SemanticBackend(
                    index_fn=index_fn,
                    search_fn=search_fn,
                    module_path=module_path,
                )
                logger.info("Semantic backend loaded: %s", module_path)
                return _semantic_backend

        _semantic_backend = None
        return None


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
        return int(result)
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


@bp.route("/index", methods=["POST"])
def rag_index() -> Any:
    started = time.monotonic()
    warnings: List[str] = []
    ok = False
    
    try:
        data = request.get_json() or {}
        namespace = str(data.get("namespace", "default") or "default")
        documents_data = data.get("documents", [])
        index_semantic = bool(data.get("index_semantic", True))
        
        if not documents_data:
            return jsonify({"error": "documents required"}), 400
        if len(documents_data) > 2000:
            return jsonify({"error": "max 2000 documents per request"}), 400
        
        docs = []
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
                namespace=namespace,
                documents=documents_data,
                warnings=warnings,
            )
        
        ok = True
        return jsonify({
            "namespace": namespace,
            "bm25_indexed": int(bm25_indexed),
            "semantic_indexed": int(semantic_indexed),
            "errors": bm25_errors,
            "warnings": warnings,
            "took_ms": (time.monotonic() - started) * 1000.0,
        })
    
    except ValueError as exc:
        _metrics.record_error(str(exc))
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        _metrics.record_error(str(exc))
        logger.exception("RAG index failed")
        return jsonify({"error": "RAG index failed"}), 500
    finally:
        _metrics.record_index(ok=ok)


@bp.route("/index/stats", methods=["GET"])
def rag_index_stats() -> Any:
    namespace = request.args.get("namespace", "default")
    
    try:
        bm25 = _get_bm25()
        s = bm25.stats(namespace=namespace)
        return jsonify({
            "namespace": s.namespace,
            "doc_count": s.doc_count,
            "term_count": s.term_count,
            "posting_count": s.posting_count,
            "avg_doc_len": s.avg_doc_len,
            "total_doc_len": s.total_doc_len,
            "updated_at": s.updated_at,
            "db_path": s.db_path,
            "db_size_bytes": s.db_size_bytes,
            "schema_version": s.schema_version,
        })
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        logger.exception("RAG index stats failed")
        return jsonify({"error": "RAG index stats failed"}), 500


@bp.route("/search", methods=["POST"])
def rag_search() -> Any:
    started = time.monotonic()
    warnings: List[str] = []
    ok = False
    
    try:
        data = request.get_json() or {}
        namespace = str(data.get("namespace", "default") or "default")
        query = str(data.get("query", "")).strip()
        
        if not query:
            return jsonify({"error": "query required"}), 400
        
        top_k = int(data.get("top_k", 10))
        lexical_k = data.get("lexical_k")
        semantic_k = data.get("semantic_k")
        use_lexical = bool(data.get("use_lexical", True))
        use_semantic = bool(data.get("use_semantic", True))
        rrf_k = int(data.get("rrf_k", 60))
        lexical_weight = float(data.get("lexical_weight", 1.0))
        semantic_weight = float(data.get("semantic_weight", 1.0))
        include_text = bool(data.get("include_text", True))
        include_metadata = bool(data.get("include_metadata", True))
        
        if not use_lexical and not use_semantic:
            return jsonify({"error": "At least one of use_lexical/use_semantic must be true"}), 400
        
        bm25 = _get_bm25()
        
        lexical_hits: List[BM25Hit] = []
        semantic_hits: List[RankedHit] = []
        
        lexical_k_val = int(lexical_k) if lexical_k is not None else int(top_k)
        semantic_k_val = int(semantic_k) if semantic_k is not None else int(top_k)
        
        if use_lexical:
            lexical_hits = bm25.search(
                namespace=namespace,
                query=query,
                top_k=lexical_k_val,
                include_text=False,
                include_metadata=False,
            )
        
        if use_semantic:
            semantic_hits = _semantic_search(
                namespace=namespace,
                query=query,
                top_k=semantic_k_val,
                warnings=warnings,
            )
        
        mode: str
        results: List[Dict[str, Any]] = []
        
        if use_lexical and use_semantic:
            fused: List[FusedHit] = reciprocal_rank_fusion(
                lexical_hits=[
                    RankedHit(doc_id=h.doc_id, score=h.score, rank=h.rank) for h in lexical_hits
                ],
                semantic_hits=semantic_hits,
                top_k=int(top_k),
                k=int(rrf_k),
                lexical_weight=float(lexical_weight),
                semantic_weight=float(semantic_weight),
            )
            mode = "hybrid_rrf"
            
            doc_ids = [f.doc_id for f in fused]
            docs = bm25.get_documents(namespace=namespace, doc_ids=doc_ids)
            
            for f in fused:
                doc = docs.get(f.doc_id, {})
                results.append({
                    "id": f.doc_id,
                    "score": float(f.fused_score),
                    "fused_score": float(f.fused_score),
                    "lexical_score": f.lexical_score,
                    "semantic_score": f.semantic_score,
                    "lexical_rank": f.lexical_rank,
                    "semantic_rank": f.semantic_rank,
                    "text": doc.get("text") if include_text else None,
                    "metadata": doc.get("metadata") if include_metadata else None,
                })
        
        elif use_lexical:
            mode = "bm25"
            doc_ids = [h.doc_id for h in lexical_hits[: int(top_k)]]
            docs = bm25.get_documents(namespace=namespace, doc_ids=doc_ids)
            for h in lexical_hits[: int(top_k)]:
                doc = docs.get(h.doc_id, {})
                results.append({
                    "id": h.doc_id,
                    "score": float(h.score),
                    "lexical_score": float(h.score),
                    "lexical_rank": int(h.rank),
                    "text": doc.get("text") if include_text else None,
                    "metadata": doc.get("metadata") if include_metadata else None,
                })
        
        else:
            mode = "semantic"
            doc_ids = [h.doc_id for h in semantic_hits[: int(top_k)]]
            docs = bm25.get_documents(namespace=namespace, doc_ids=doc_ids)
            for h in semantic_hits[: int(top_k)]:
                doc = docs.get(h.doc_id, {})
                results.append({
                    "id": h.doc_id,
                    "score": float(h.score),
                    "semantic_score": float(h.score),
                    "semantic_rank": int(h.rank),
                    "text": doc.get("text") if include_text else None,
                    "metadata": doc.get("metadata") if include_metadata else None,
                })
        
        ok = True
        took_ms = (time.monotonic() - started) * 1000.0
        return jsonify({
            "namespace": namespace,
            "query": query,
            "mode": mode,
            "results": results,
            "warnings": warnings,
            "took_ms": took_ms,
        })
    
    except ValueError as exc:
        _metrics.record_error(str(exc))
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        _metrics.record_error(str(exc))
        logger.exception("RAG search failed")
        return jsonify({"error": "RAG search failed"}), 500
    finally:
        took_ms = (time.monotonic() - started) * 1000.0
        _metrics.record_search(took_ms, ok=ok)


@bp.route("/search/multi", methods=["POST"])
def rag_search_multi() -> Any:
    ok = False
    try:
        data = request.get_json() or {}
        requests_data = data.get("requests", [])
        
        if not requests_data:
            return jsonify({"error": "requests required"}), 400
        if len(requests_data) > 50:
            return jsonify({"error": "max 50 requests per multi-search"}), 400
        
        responses: List[Dict[str, Any]] = []
        for req in requests_data:
            # Simulate individual search by temporarily modifying request
            import io
            old_data = request.get_json()
            responses.append(rag_search().get_json())  # type: ignore
        
        ok = True
        return jsonify({"responses": responses})
    
    except Exception as exc:
        _metrics.record_error(str(exc))
        logger.exception("RAG multi-search failed")
        return jsonify({"error": "RAG multi-search failed"}), 500
    finally:
        _metrics.record_multi_search(ok=ok)


@bp.route("/search/stats", methods=["GET"])
def rag_search_stats() -> Any:
    return jsonify(_metrics.snapshot())
