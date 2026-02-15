from __future__ import annotations

import time
import hashlib
import json
from flask import Blueprint, jsonify, make_response, request

from copilot_core.brain_graph.provider import get_graph_service
from copilot_core.performance import brain_graph_cache

bp = Blueprint("graph", __name__, url_prefix="/graph")


def _svc():
    return get_graph_service()


def _compute_cache_key(prefix: str, **params) -> str:
    """Compute a deterministic cache key from parameters."""
    sorted_params = json.dumps(params, sort_keys=True, default=str)
    content = f"{prefix}:{sorted_params}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


@bp.get("/state")
def graph_state():
    # Multi-value query params: kind=...&kind=...
    kinds = request.args.getlist("kind")
    domains = request.args.getlist("domain")
    center = request.args.get("center")

    try:
        hops = int(request.args.get("hops", "1"))
    except Exception:
        hops = 1

    try:
        limit_nodes = int(request.args.get("limitNodes", request.args.get("limit_nodes", "200")))
    except Exception:
        limit_nodes = 200

    try:
        limit_edges = int(request.args.get("limitEdges", request.args.get("limit_edges", "400")))
    except Exception:
        limit_edges = 400

    # Server-side caps: tighter than storage maxima by default.
    limit_nodes = max(1, min(limit_nodes, 500))
    limit_edges = max(1, min(limit_edges, 1500))
    hops = max(0, min(hops, 2))

    # Check cache bypass
    nocache = request.args.get('nocache', '0') == '1'
    
    # Compute cache key
    cache_key = _compute_cache_key(
        "graph_state",
        kinds=kinds,
        domains=domains,
        center=center,
        hops=hops,
        limit_nodes=limit_nodes,
        limit_edges=limit_edges
    )
    
    # Try cache first (unless nocache)
    if not nocache:
        cached_result = brain_graph_cache.get(cache_key)
        if cached_result is not None:
            cached_result["_cached"] = True
            return jsonify(cached_result)

    # Convert query params to match BrainGraphService.get_graph_state signature
    kinds = [k for k in kinds if isinstance(k, str)]
    domains = [d for d in domains if isinstance(d, str)]
    
    state = _svc().get_graph_state(
        kinds=kinds if kinds else None,
        domains=domains if domains else None,
        center_node=center if center else None,
        hops=hops,
        limit_nodes=limit_nodes,
        limit_edges=limit_edges,
    )
    
    # Cache the result
    brain_graph_cache.set(cache_key, state, ttl=30.0)
    state["_cached"] = False
    
    return jsonify(state)


@bp.get("/stats")
def graph_stats():
    """Graph statistics for health checks."""
    # Get cache stats
    cache_stats = brain_graph_cache.get_stats()
    
    state = _svc().get_graph_state(limit_nodes=1, limit_edges=1)
    return jsonify({
        "version": 1,
        "ok": True,
        "nodes": len(state.get("nodes", [])),
        "edges": len(state.get("edges", [])),
        "updated_at_ms": state.get("generated_at_ms", 0),
        "limits": state.get("limits", {}),
        "cache": {
            "enabled": brain_graph_cache.enabled,
            "size": cache_stats["size"],
            "max_size": cache_stats["max_size"],
            "hits": cache_stats["hits"],
            "misses": cache_stats["misses"],
            "hit_rate": round(cache_stats["hit_rate"], 3),
        }
    })


@bp.get("/patterns")
def graph_patterns():
    """Pattern summary for health checks."""
    patterns = _svc().infer_patterns()
    return jsonify({
        "version": 1,
        "ok": True,
        "generated_at_ms": int(time.time() * 1000),
        "patterns": patterns
    })


@bp.get("/snapshot.svg")
def graph_snapshot_svg():
    # v0.1: keep lightweight. Returning a placeholder (or 501) is acceptable.
    svg = (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"640\" height=\"120\">\n"
        "  <rect x=\"0\" y=\"0\" width=\"100%\" height=\"100%\" fill=\"#111\"/>\n"
        "  <text x=\"20\" y=\"55\" fill=\"#eee\" font-family=\"monospace\" font-size=\"16\">"
        "Brain Graph snapshot.svg not implemented (v0.1 placeholder)"
        "</text>\n"
        "  <text x=\"20\" y=\"85\" fill=\"#aaa\" font-family=\"monospace\" font-size=\"12\">"
        "Use /api/v1/graph/state for JSON."
        "</text>\n"
        "</svg>\n"
    )
    resp = make_response(svg, 200)
    resp.headers["Content-Type"] = "image/svg+xml; charset=utf-8"
    return resp


@bp.post("/cache/clear")
def clear_cache():
    """Clear graph cache."""
    brain_graph_cache.clear()
    return jsonify({
        "ok": True,
        "message": "Cache cleared",
        "timestamp_ms": int(time.time() * 1000)
    })
