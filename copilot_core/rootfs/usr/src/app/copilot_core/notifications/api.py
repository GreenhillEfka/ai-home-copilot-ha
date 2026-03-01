"""Notification API endpoints - Flask blueprint for notification management.

Phase 5: Notifications API
Provides REST endpoints for notification creation, retrieval, digest, and statistics.

Endpoints:
- GET /api/v1/notifications - Get notification history
- POST /api/v1/notifications - Create a new notification
- GET /api/v1/notifications/digest - Get notification digest summary
- GET /api/v1/notifications/pending - Get pending notifications for delivery
- GET /api/v1/notifications/stats - Get engine statistics

All endpoints require API key authentication via @require_api_key decorator.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from flask import Blueprint, jsonify, request

from ..api.security import require_api_key
from .engine import NotificationEngine, Priority

notifications_bp = Blueprint("notifications", __name__)

_engine: Optional[NotificationEngine] = None


def init_notifications_api(engine: NotificationEngine) -> None:
    """Initialize the notifications API with an engine instance.
    
    Args:
        engine: NotificationEngine instance for managing notifications.
    """
    global _engine
    _engine = engine


@notifications_bp.route("/api/v1/notifications", methods=["GET"])
@require_api_key
def get_notifications() -> Tuple[Dict[str, Any], int]:
    """Get notification history.

    Query params:
        limit: Max items (default 50)
        source: Filter by source module
    
    Returns:
        Tuple[Dict[str, Any], int]: JSON response with count and notifications list.
    """
    if not _engine:
        return jsonify({"error": "Notification engine not initialized"}), 503

    limit = request.args.get("limit", 50, type=int)
    source = request.args.get("source")

    items = _engine.get_history(limit=limit, source=source)
    return jsonify({"ok": True, "count": len(items), "notifications": items})


@notifications_bp.route("/api/v1/notifications", methods=["POST"])
@require_api_key
def create_notification() -> Tuple[Dict[str, Any], int]:
    """Submit a notification.

    Request body:
        {
            "source": str (optional, default "api"),
            "title": str (required),
            "message": str (required),
            "priority": int (optional, 1-4, default 3),
            "channel": str (optional, default "default"),
            "data": dict (optional)
        }
    
    Returns:
        Tuple[Dict[str, Any], int]: Creation result with notification ID or status.
    """
    if not _engine:
        return jsonify({"error": "Notification engine not initialized"}), 503

    body = request.get_json(silent=True) or {}
    source = body.get("source", "api")
    title = body.get("title")
    message = body.get("message")

    if not title or not message:
        return jsonify({"ok": False, "error": "title and message required"}), 400

    priority = body.get("priority", 3)
    channel = body.get("channel", "default")
    data = body.get("data", {})

    notif = _engine.notify(
        source=source,
        title=title,
        message=message,
        priority=priority,
        channel=channel,
        data=data,
    )

    if notif is None:
        return jsonify({"ok": True, "status": "deduplicated_or_rate_limited"})

    return jsonify({
        "ok": True,
        "id": notif.id,
        "priority": notif.priority.name,
        "channel": notif.channel,
    }), 201


@notifications_bp.route("/api/v1/notifications/digest", methods=["GET"])
@require_api_key
def get_digest() -> Tuple[Dict[str, Any], int]:
    """Get notification digest.

    Query params:
        hours: Look-back period (default 24)
    
    Returns:
        Tuple[Dict[str, Any], int]: Digest summary with period, counts, and items.
    """
    if not _engine:
        return jsonify({"error": "Notification engine not initialized"}), 503

    hours = request.args.get("hours", 24.0, type=float)
    digest = _engine.get_digest(hours=hours)

    return jsonify({
        "ok": True,
        "period_start": digest.period_start,
        "period_end": digest.period_end,
        "count": digest.count,
        "by_source": digest.by_source,
        "by_priority": digest.by_priority,
        "items": digest.items,
    })


@notifications_bp.route("/api/v1/notifications/pending", methods=["GET"])
@require_api_key
def get_pending() -> Tuple[Dict[str, Any], int]:
    """Flush and return pending notifications for delivery.
    
    Returns:
        Tuple[Dict[str, Any], int]: List of pending notifications with full details.
    """
    if not _engine:
        return jsonify({"error": "Notification engine not initialized"}), 503

    pending = _engine.flush_pending()
    return jsonify({
        "ok": True,
        "count": len(pending),
        "notifications": [
            {
                "id": n.id,
                "source": n.source,
                "title": n.title,
                "message": n.message,
                "priority": n.priority.name if isinstance(n.priority, Priority) else str(n.priority),
                "channel": n.channel,
                "data": n.data,
            }
            for n in pending
        ],
    })


@notifications_bp.route("/api/v1/notifications/stats", methods=["GET"])
@require_api_key
def get_stats() -> Tuple[Dict[str, Any], int]:
    """Get notification engine statistics.
    
    Returns:
        Tuple[Dict[str, Any], int]: Statistics dictionary with counts and metrics.
    """
    if not _engine:
        return jsonify({"error": "Notification engine not initialized"}), 503

    return jsonify({"ok": True, **_engine.get_stats()})
