"""Neuron API endpoints for PilotSuite.

Exposes the neural network to Home Assistant integration.
"""
from flask import Blueprint, jsonify, request

from ..neurons import get_neuron_manager

bp = Blueprint("neurons", __name__, url_prefix="/neurons")


@bp.get("")
def list_neurons():
    """List all neurons and their states."""
    manager = get_neuron_manager()
    return jsonify({
        "ok": True,
        "neurons": manager.get_all_neurons(),
        "stats": manager.get_stats()
    })


@bp.get("/<neuron_id>")
def get_neuron(neuron_id: str):
    """Get state of a specific neuron."""
    manager = get_neuron_manager()
    state = manager.get_neuron_state(neuron_id)
    
    if state is None:
        return jsonify({"ok": False, "error": "neuron_not_found"}), 404
    
    return jsonify({
        "ok": True,
        "neuron_id": neuron_id,
        "state": state
    })


@bp.post("/evaluate")
def evaluate_neurons():
    """Evaluate the entire neural pipeline with given context.
    
    Request body:
    {
        "states": {"entity_id": {"state": "...", "attributes": {...}}},
        "time": {"hour": ..., "weekday": ...},
        "weather": {...},
        "presence": {...},
        "sleep": {...},
        "calendar": {...},
        "security": {...}
    }
    """
    manager = get_neuron_manager()
    context = request.get_json(silent=True) or {}
    
    result = manager.evaluate(context)
    
    return jsonify({
        "ok": True,
        **result
    })


@bp.get("/mood")
def get_mood():
    """Get current mood state."""
    manager = get_neuron_manager()
    return jsonify({
        "ok": True,
        **manager.get_mood()
    })


@bp.post("/mood/evaluate")
def evaluate_mood():
    """Force mood evaluation with context."""
    manager = get_neuron_manager()
    context = request.get_json(silent=True) or {}
    
    result = manager.evaluate(context)
    
    return jsonify({
        "ok": True,
        "mood": result.get("dominant_mood"),
        "confidence": result.get("mood", {}).get(result.get("dominant_mood", ""), 0),
        "all_moods": result.get("mood", {}),
        "suggestions": result.get("suggestions", [])
    })


@bp.get("/suggestions")
def get_suggestions():
    """Get active suggestions."""
    manager = get_neuron_manager()
    stats = manager.get_stats()
    
    return jsonify({
        "ok": True,
        "suggestions": [],  # TODO: Get from synapse manager
        "stats": stats.get("synapse_stats", {})
    })


@bp.post("/feedback")
def submit_feedback():
    """Submit user feedback for a suggestion.
    
    Request body:
    {
        "suggestion_id": "...",
        "accepted": true/false
    }
    """
    manager = get_neuron_manager()
    data = request.get_json(silent=True) or {}
    
    suggestion_id = data.get("suggestion_id")
    accepted = data.get("accepted", False)
    
    if not suggestion_id:
        return jsonify({"ok": False, "error": "suggestion_id_required"}), 400
    
    manager.apply_feedback(suggestion_id, accepted)
    
    return jsonify({
        "ok": True,
        "message": f"Feedback applied: {'accepted' if accepted else 'rejected'}"
    })


@bp.get("/stats")
def get_stats():
    """Get neural network statistics."""
    manager = get_neuron_manager()
    return jsonify({
        "ok": True,
        **manager.get_stats()
    })