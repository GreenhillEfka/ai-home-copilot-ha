from __future__ import annotations

from flask import Blueprint, jsonify, make_response, request

from copilot_core.brain_graph.provider import get_graph_service

bp = Blueprint("graph", __name__, url_prefix="/graph")


def _svc():
    return get_graph_service()


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

    state = _svc().export_state(
        kind=kinds,
        domain=domains,
        center=center,
        hops=hops,
        limit_nodes=limit_nodes,
        limit_edges=limit_edges,
    )
    return jsonify(state)


@bp.get("/stats")
def graph_stats():
    """Graph statistics for health checks."""
    state = _svc().export_state(limit_nodes=1, limit_edges=1)
    return jsonify({
        "ok": True,
        "nodes": state.get("node_count", 0),
        "edges": state.get("edge_count", 0),
        "updated_at_ms": state.get("generated_at_ms", 0)
    })


@bp.get("/patterns")
def graph_patterns():
    """Pattern summary for health checks."""
    return jsonify({"ok": True, "patterns": [], "message": "Use /graph/state for full data"})


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
