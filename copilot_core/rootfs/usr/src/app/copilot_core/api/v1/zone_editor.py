"""Zone Editor API - CRUD operations for PilotSuite Dashboard zones.

Endpunkte:
  POST   /api/v1/zone/editor/create           - Neue Zone erstellen
  GET    /api/v1/zone/editor/list             - Alle Zonen auflisten
  GET    /api/v1/zone/editor/<zone_id>        - Zone Details
  PUT    /api/v1/zone/editor/<zone_id>        - Zone aktualisieren
  DELETE /api/v1/zone/editor/<zone_id>        - Zone löschen
  POST   /api/v1/zone/editor/<zone_id>/rooms  - Room zu Zone hinzufügen
  DELETE /api/v1/zone/editor/<zone_id>/rooms/<room_id> - Room aus Zone entfernen

Author: Clawdya
Version: 1.0.0
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from flask import Blueprint, jsonify, request

from copilot_core.api.security import require_token

_LOGGER = logging.getLogger(__name__)

zone_editor_bp = Blueprint("zone_editor", __name__, url_prefix="/api/v1/zone/editor")

# In-memory zone storage (would be replaced by persistent storage in production)
_zones_store: Dict[str, Dict[str, Any]] = {}


def init_zone_editor_api() -> None:
    """Initialize the Zone Editor API."""
    _LOGGER.info("Zone Editor API initialized")


def get_zone_engine():
    """Get the zone engine instance (lazy import to avoid circular deps)."""
    class ZoneEngine:
        def get_all_zones(self) -> List[Dict[str, Any]]:
            return list(_zones_store.values())
        
        def get_zone(self, zone_id: str) -> Optional[Dict[str, Any]]:
            return _zones_store.get(zone_id)
        
        def create_zone(self, zone_data: Dict[str, Any]) -> Dict[str, Any]:
            zone_id = zone_data["zone_id"]
            _zones_store[zone_id] = zone_data
            return zone_data
        
        def update_zone(self, zone_id: str, updates: Dict[str, Any]) -> bool:
            if zone_id not in _zones_store:
                return False
            _zones_store[zone_id].update(updates)
            return True
        
        def delete_zone(self, zone_id: str) -> bool:
            if zone_id in _zones_store:
                del _zones_store[zone_id]
                return True
            return False
        
        def add_room_to_zone(self, zone_id: str, room_id: str) -> bool:
            if zone_id not in _zones_store:
                return False
            if "rooms" not in _zones_store[zone_id]:
                _zones_store[zone_id]["rooms"] = []
            if room_id not in _zones_store[zone_id]["rooms"]:
                _zones_store[zone_id]["rooms"].append(room_id)
            return True
        
        def remove_room_from_zone(self, zone_id: str, room_id: str) -> bool:
            if zone_id not in _zones_store:
                return False
            if "rooms" in _zones_store[zone_id]:
                try:
                    _zones_store[zone_id]["rooms"].remove(room_id)
                    return True
                except ValueError:
                    return False
            return False
    
    return ZoneEngine()


@zone_editor_bp.route("/create", methods=["POST"])
@require_token
def create_zone():
    """Create a new zone.
    
    Required fields:
    - zone_id: Unique identifier for the zone
    - name: Human-readable name
    
    Optional fields:
    - icon: Material Design Icon (default: mdi:room)
    - rooms: List of room IDs
    - mode: Zone mode (active, idle, disabled)
    - enabled: Boolean (default: True)
    - priority: Integer priority (default: 0)
    """
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400
    
    if not data:
        return jsonify({"error": "Missing request body"}), 400
    
    # Validate required fields
    if "zone_id" not in data:
        return jsonify({"error": "Missing required field: zone_id"}), 400
    
    if "name" not in data:
        return jsonify({"error": "Missing required field: name"}), 400
    
    zone_id = data["zone_id"]
    engine = get_zone_engine()
    
    # Check for duplicate
    existing = engine.get_zone(zone_id)
    if existing:
        return jsonify({"error": f"Zone {zone_id} already exists"}), 409
    
    # Build zone object with defaults
    zone_data = {
        "zone_id": zone_id,
        "name": data["name"],
        "icon": data.get("icon", "mdi:room"),
        "rooms": data.get("rooms", []),
        "mode": data.get("mode", "active"),
        "enabled": data.get("enabled", True),
        "priority": data.get("priority", 0),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    
    created = engine.create_zone(zone_data)
    _LOGGER.info(f"Created zone: {zone_id}")
    
    return jsonify({
        "ok": True,
        "zone": created,
    })


@zone_editor_bp.route("/list", methods=["GET"])
@require_token
def list_zones():
    """List all zones."""
    engine = get_zone_engine()
    zones = engine.get_all_zones()
    
    return jsonify({
        "zones": zones,
        "count": len(zones),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    })


@zone_editor_bp.route("/<zone_id>", methods=["GET"])
@require_token
def get_zone(zone_id: str):
    """Get details for a specific zone."""
    engine = get_zone_engine()
    zone = engine.get_zone(zone_id)
    
    if not zone:
        return jsonify({"error": f"Zone {zone_id} not found"}), 404
    
    return jsonify({
        "ok": True,
        "zone": zone,
    })


@zone_editor_bp.route("/<zone_id>", methods=["PUT"])
@require_token
def update_zone(zone_id: str):
    """Update an existing zone."""
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400
    
    if not data:
        return jsonify({"error": "Missing request body"}), 400
    
    engine = get_zone_engine()
    
    # Check if zone exists
    existing = engine.get_zone(zone_id)
    if not existing:
        return jsonify({"error": f"Zone {zone_id} not found"}), 404
    
    # Build updates (exclude zone_id as it's the key)
    updates = {k: v for k, v in data.items() if k != "zone_id"}
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    success = engine.update_zone(zone_id, updates)
    
    if not success:
        return jsonify({"error": "Failed to update zone"}), 500
    
    _LOGGER.info(f"Updated zone: {zone_id}")
    
    return jsonify({
        "ok": True,
        "zone": engine.get_zone(zone_id),
    })


@zone_editor_bp.route("/<zone_id>", methods=["DELETE"])
@require_token
def delete_zone(zone_id: str):
    """Delete a zone."""
    engine = get_zone_engine()
    
    # Check if zone exists
    existing = engine.get_zone(zone_id)
    if not existing:
        return jsonify({"error": f"Zone {zone_id} not found"}), 404
    
    success = engine.delete_zone(zone_id)
    
    if not success:
        return jsonify({"error": "Failed to delete zone"}), 500
    
    _LOGGER.info(f"Deleted zone: {zone_id}")
    
    return jsonify({
        "ok": True,
    })


@zone_editor_bp.route("/<zone_id>/rooms", methods=["POST"])
@require_token
def add_room(zone_id: str):
    """Add a room to a zone."""
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400
    
    if not data or "room_id" not in data:
        return jsonify({"error": "Missing required field: room_id"}), 400
    
    room_id = data["room_id"]
    engine = get_zone_engine()
    
    # Check if zone exists
    existing = engine.get_zone(zone_id)
    if not existing:
        return jsonify({"error": f"Zone {zone_id} not found"}), 404
    
    success = engine.add_room_to_zone(zone_id, room_id)
    
    if not success:
        return jsonify({"error": "Failed to add room to zone"}), 500
    
    _LOGGER.info(f"Added room {room_id} to zone {zone_id}")
    
    return jsonify({
        "ok": True,
        "zone": engine.get_zone(zone_id),
    })


@zone_editor_bp.route("/<zone_id>/rooms/<room_id>", methods=["DELETE"])
@require_token
def remove_room(zone_id: str, room_id: str):
    """Remove a room from a zone."""
    engine = get_zone_engine()
    
    # Check if zone exists
    existing = engine.get_zone(zone_id)
    if not existing:
        return jsonify({"error": f"Zone {zone_id} not found"}), 404
    
    success = engine.remove_room_from_zone(zone_id, room_id)
    
    if not success:
        return jsonify({"error": f"Room {room_id} not found in zone {zone_id}"}), 404
    
    _LOGGER.info(f"Removed room {room_id} from zone {zone_id}")
    
    return jsonify({
        "ok": True,
        "zone": engine.get_zone(zone_id),
    })
