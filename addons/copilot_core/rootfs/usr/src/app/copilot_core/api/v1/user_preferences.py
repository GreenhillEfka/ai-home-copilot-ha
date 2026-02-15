"""User Preference API endpoints for AI Home CoPilot Core.

Provides endpoints for Multi-User Preference Learning (MUP-L).
Privacy-first: user IDs remain local and are never forwarded to external services.

Design Doc: docs/MUPL_DESIGN.md
"""
from __future__ import annotations

import logging
from typing import Any

from flask import Blueprint, current_app, jsonify, request

bp = Blueprint("user_preferences", __name__, url_prefix="/user")

_LOGGER = logging.getLogger(__name__)

# In-memory preference store (for now; will be persisted later)
# Structure: {user_id: {preferences: {...}, patterns: {...}, priority: 0.5}}
_user_store: dict[str, dict[str, Any]] = {}

# Device affinity store
# Structure: {entity_id: {primary_user: str, usage_distribution: {user_id: float}}}
_device_affinities: dict[str, dict[str, Any]] = {}

# Active users cache (populated from Home Assistant person entities)
_active_users: list[str] = []


def _get_ha_client():
    """Get Home Assistant client from app config."""
    cfg = current_app.config.get("COPILOT_CFG")
    if hasattr(cfg, "ha_client"):
        return cfg.ha_client
    return None


@bp.get("/<user_id>/preferences")
def get_user_preferences(user_id: str):
    """Get all preferences for a user.
    
    Args:
        user_id: User ID (person entity_id)
        
    Returns:
        JSON with user_id and preferences dict
    """
    prefs = _user_store.get(user_id, {}).get("preferences", {
        "light_brightness": {"default": 0.8, "by_zone": {}},
        "media_volume": {"default": 0.5, "by_zone": {}},
        "temperature": {"default": 21.0, "by_zone": {}},
        "mood_weights": {"comfort": 0.5, "frugality": 0.5, "joy": 0.5},
    })
    
    return jsonify({
        "user_id": user_id,
        "preferences": prefs,
    })


@bp.get("/<user_id>/zone/<zone_id>/preference")
def get_user_zone_preference(user_id: str, zone_id: str):
    """Get preference for a user in a specific zone.
    
    Args:
        user_id: User ID (person entity_id)
        zone_id: Zone ID (e.g., "living", "bedroom")
        
    Returns:
        JSON with user_id, zone_id, and preference
    """
    user_data = _user_store.get(user_id, {})
    prefs = user_data.get("preferences", {})
    
    # Check zone-specific preference
    for pref_type in ["light_brightness", "media_volume", "temperature"]:
        zone_prefs = prefs.get(pref_type, {}).get("by_zone", {})
        if zone_id in zone_prefs:
            pref = zone_prefs[zone_id]
        else:
            pref = prefs.get(pref_type, {}).get("default", 0.5)
    
    # Get zone-specific mood weights
    mood = prefs.get("mood_weights", {"comfort": 0.5, "frugality": 0.5, "joy": 0.5})
    
    return jsonify({
        "user_id": user_id,
        "zone_id": zone_id,
        "preference": {
            "mood_weights": mood,
        },
    })


@bp.post("/<user_id>/preference")
def update_user_preference(user_id: str):
    """Update a user's preference for a zone.
    
    Args:
        user_id: User ID (person entity_id)
        
    Body:
        zone_id: Zone ID (required)
        comfort_bias: Comfort bias (0.0-1.0, optional)
        frugality_bias: Frugality bias (0.0-1.0, optional)
        joy_bias: Joy bias (0.0-1.0, optional)
        
    Returns:
        Updated preference dict
    """
    data = request.get_json(silent=True) or {}
    
    zone_id = data.get("zone_id")
    if not zone_id:
        return jsonify({"error": "zone_id_required"}), 400
    
    # Initialize user if needed
    if user_id not in _user_store:
        _user_store[user_id] = {
            "preferences": {
                "light_brightness": {"default": 0.8, "by_zone": {}},
                "media_volume": {"default": 0.5, "by_zone": {}},
                "temperature": {"default": 21.0, "by_zone": {}},
                "mood_weights": {"comfort": 0.5, "frugality": 0.5, "joy": 0.5},
            },
            "patterns": {},
            "priority": 0.5,
        }
    
    prefs = _user_store[user_id]["preferences"]
    
    # Update mood weights
    mood = prefs.get("mood_weights", {"comfort": 0.5, "frugality": 0.5, "joy": 0.5})
    
    if "comfort_bias" in data:
        mood["comfort"] = max(0.0, min(1.0, float(data["comfort_bias"])))
    if "frugality_bias" in data:
        mood["frugality"] = max(0.0, min(1.0, float(data["frugality_bias"])))
    if "joy_bias" in data:
        mood["joy"] = max(0.0, min(1.0, float(data["joy_bias"])))
    
    prefs["mood_weights"] = mood
    
    _LOGGER.info("Updated preference for user %s in zone %s: %s", user_id, zone_id, mood)
    
    return jsonify({
        "user_id": user_id,
        "zone_id": zone_id,
        "preference": {"mood_weights": mood},
    })


@bp.get("/active")
def get_active_users():
    """Get list of currently active (home) users.
    
    Queries Home Assistant person entities to find users currently home.
    
    Returns:
        List of active user dicts with user_id and name
    """
    global _active_users
    
    ha_client = _get_ha_client()
    active = []
    
    if ha_client:
        try:
            # Get all person entities
            states = ha_client.get_states()
            for state in states:
                if state.get("entity_id", "").startswith("person."):
                    if state.get("state") == "home":
                        active.append({
                            "user_id": state["entity_id"],
                            "name": state.get("attributes", {}).get("friendly_name", state["entity_id"]),
                        })
        except Exception as e:
            _LOGGER.warning("Failed to get active users from HA: %s", e)
    
    _active_users = [u["user_id"] for u in active]
    
    return jsonify({
        "status": "ok",
        "users": active,
        "count": len(active),
    })


@bp.get("/all")
def get_all_users():
    """Get all known users with their preferences.
    
    Returns:
        Dict of user_id to user data
    """
    return jsonify({
        "status": "ok",
        "users": _user_store,
        "count": len(_user_store),
    })


@bp.post("/<user_id>/priority")
def set_user_priority(user_id: str):
    """Set user priority for conflict resolution.
    
    Args:
        user_id: User ID
        
    Body:
        priority: Priority value (0.0-1.0, higher = more important)
        
    Returns:
        Updated user data
    """
    data = request.get_json(silent=True) or {}
    
    priority = data.get("priority")
    if priority is None:
        return jsonify({"error": "priority_required"}), 400
    
    priority = max(0.0, min(1.0, float(priority)))
    
    if user_id not in _user_store:
        _user_store[user_id] = {"preferences": {}, "patterns": {}, "priority": priority}
    else:
        _user_store[user_id]["priority"] = priority
    
    _LOGGER.info("Set priority %.2f for user %s", priority, user_id)
    
    return jsonify({
        "user_id": user_id,
        "priority": priority,
    })


@bp.delete("/<user_id>")
def delete_user_data(user_id: str):
    """Delete all data for a user (privacy/GDPR).
    
    Args:
        user_id: User to delete
        
    Returns:
        Status dict
    """
    if user_id not in _user_store:
        return jsonify({"error": "user_not_found"}), 404
    
    del _user_store[user_id]
    
    # Remove from device affinities
    for entity_id, aff in _device_affinities.items():
        if aff.get("primary_user") == user_id:
            aff["primary_user"] = None
        if user_id in aff.get("usage_distribution", {}):
            del aff["usage_distribution"][user_id]
    
    # Remove from active users
    if user_id in _active_users:
        _active_users.remove(user_id)
    
    _LOGGER.info("Deleted all data for user: %s", user_id)
    
    return jsonify({"status": "deleted", "user_id": user_id})


@bp.get("/<user_id>/export")
def export_user_data(user_id: str):
    """Export all data for a user (privacy/GDPR).
    
    Args:
        user_id: User to export
        
    Returns:
        User data dict
    """
    if user_id not in _user_store:
        return jsonify({"error": "user_not_found"}), 404
    
    user_data = _user_store[user_id]
    
    # Include relevant device affinities
    affinities = {}
    for entity_id, aff in _device_affinities.items():
        if user_id in aff.get("usage_distribution", {}):
            affinities[entity_id] = aff["usage_distribution"]
    
    return jsonify({
        "user_id": user_id,
        "data": user_data,
        "device_affinities": affinities,
    })


# ==================== Aggregated Mood ====================


@bp.get("/mood/aggregated")
def get_aggregated_mood():
    """Get aggregated mood for multiple users.
    
    Query params:
        users: Comma-separated list of user IDs (optional, defaults to active users)
        
    Returns:
        Aggregated mood dict with comfort, frugality, joy
    """
    users_param = request.args.get("users")
    
    if users_param:
        user_ids = [u.strip() for u in users_param.split(",") if u.strip()]
    else:
        user_ids = _active_users
    
    if not user_ids:
        return jsonify({
            "status": "ok",
            "mood": {"comfort": 0.5, "frugality": 0.5, "joy": 0.5},
            "user_count": 0,
        })
    
    if len(user_ids) == 1:
        user_id = user_ids[0]
        if user_id in _user_store:
            mood = _user_store[user_id].get("preferences", {}).get("mood_weights", {})
        else:
            mood = {"comfort": 0.5, "frugality": 0.5, "joy": 0.5}
        return jsonify({
            "status": "ok",
            "mood": mood,
            "user_count": 1,
        })
    
    # Weighted aggregation by priority
    total_weight = 0.0
    mood = {"comfort": 0.0, "frugality": 0.0, "joy": 0.0}
    
    for user_id in user_ids:
        if user_id not in _user_store:
            continue
        
        user = _user_store[user_id]
        weight = user.get("priority", 0.5)
        user_mood = user.get("preferences", {}).get("mood_weights", {})
        
        mood["comfort"] += user_mood.get("comfort", 0.5) * weight
        mood["frugality"] += user_mood.get("frugality", 0.5) * weight
        mood["joy"] += user_mood.get("joy", 0.5) * weight
        total_weight += weight
    
    if total_weight > 0:
        mood = {k: round(v / total_weight, 3) for k, v in mood.items()}
    
    return jsonify({
        "status": "ok",
        "mood": mood,
        "user_count": len(user_ids),
    })