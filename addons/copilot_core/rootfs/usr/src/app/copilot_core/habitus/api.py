"""
Habitus API endpoints - Pattern mining REST interface.

Provides HTTP API for habitus pattern discovery and candidate management:
- POST /api/v1/habitus/mine - Trigger pattern mining
- GET /api/v1/habitus/stats - Mining statistics  
- GET /api/v1/habitus/patterns - Recent patterns
"""
import time
import logging
from flask import Blueprint, request, jsonify, Response

from .service import HabitusService
from ..api.security import require_api_key

logger = logging.getLogger(__name__)

# Create blueprint
habitus_bp = Blueprint('habitus', __name__, url_prefix='/api/v1/habitus')

# Global service instance (will be initialized in main.py)
_habitus_service: HabitusService = None

def init_habitus_api(service: HabitusService):
    """Initialize the habitus API with service instance."""
    global _habitus_service
    _habitus_service = service

@habitus_bp.route('/mine', methods=['POST'])
@require_api_key
def trigger_mining() -> Response:
    """
    Trigger habitus pattern mining and candidate creation.
    
    Optional JSON body:
    {
        "lookback_hours": 72,  // How far back to analyze (default 72)
        "force": false        // Force run even if recent (default false)
    }
    """
    if not _habitus_service:
        return jsonify({"error": "Habitus service not initialized"}), 503
        
    try:
        # Parse request parameters
        data = request.get_json() or {}
        lookback_hours = data.get("lookback_hours", 72)
        force = data.get("force", False)
        
        # Validate parameters
        if not isinstance(lookback_hours, int) or lookback_hours < 1 or lookback_hours > 168:
            return jsonify({"error": "lookback_hours must be between 1 and 168"}), 400
            
        if not isinstance(force, bool):
            return jsonify({"error": "force must be boolean"}), 400
            
        logger.info(f"Mining request: lookback_hours={lookback_hours}, force={force}")
        
        # Run mining
        results = _habitus_service.mine_and_create_candidates(lookback_hours, force)
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Mining endpoint error: {e}")
        return jsonify({"error": f"Internal error: {str(e)}"}), 500

@habitus_bp.route('/stats', methods=['GET'])
@require_api_key
def get_stats() -> Response:
    """Get habitus mining statistics and configuration."""
    if not _habitus_service:
        return jsonify({"error": "Habitus service not initialized"}), 503
        
    try:
        stats = _habitus_service.get_pattern_stats()
        
        # Add current timestamp
        stats["current_timestamp"] = int(time.time() * 1000)
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Stats endpoint error: {e}")
        return jsonify({"error": f"Internal error: {str(e)}"}), 500

@habitus_bp.route('/patterns', methods=['GET'])
@require_api_key  
def get_patterns() -> Response:
    """
    Get recently discovered patterns from candidates.
    
    Query parameters:
    - limit: Number of patterns to return (default 10, max 100)
    """
    if not _habitus_service:
        return jsonify({"error": "Habitus service not initialized"}), 503
        
    try:
        # Parse limit parameter
        limit = request.args.get('limit', '10')
        try:
            limit = int(limit)
            if limit < 1 or limit > 100:
                return jsonify({"error": "limit must be between 1 and 100"}), 400
        except ValueError:
            return jsonify({"error": "limit must be an integer"}), 400
            
        patterns = _habitus_service.list_recent_patterns(limit)
        
        return jsonify({
            "version": 1,
            "timestamp": int(time.time() * 1000),
            "count": len(patterns),
            "patterns": patterns
        })
        
    except Exception as e:
        logger.error(f"Patterns endpoint error: {e}")
        return jsonify({"error": f"Internal error: {str(e)}"}), 500

@habitus_bp.route('/health', methods=['GET'])
@require_api_key
def health_check() -> Response:
    """Health check for habitus service."""
    if not _habitus_service:
        return jsonify({"status": "error", "message": "Service not initialized"}), 503
        
    try:
        # Basic health check - verify service is responsive
        stats = _habitus_service.get_pattern_stats()
        
        return jsonify({
            "status": "ok",
            "timestamp": int(time.time() * 1000),
            "mining_enabled": True,
            "last_run_ago_seconds": int(time.time() - _habitus_service.last_mining_run) if _habitus_service.last_mining_run > 0 else None
        })
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            "status": "error", 
            "message": f"Service error: {str(e)}"
        }), 500