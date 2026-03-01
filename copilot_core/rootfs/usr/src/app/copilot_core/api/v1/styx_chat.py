"""
PilotSuite-Styx Chat API Endpoint.

Bietet REST-Endpoint für Chat-Queries mit RAG-API Integration.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from flask import Blueprint, jsonify, request

from copilot_core.api.security import validate_token
from copilot_core.styx.chat_handler import ChatHandler

logger = logging.getLogger(__name__)

bp = Blueprint("styx_chat", __name__, url_prefix="/api/styx")


# ── Auth guard ──────────────────────────────────────────────────────────

@bp.before_request
def _require_auth() -> Optional[Any]:
    if not validate_token(request):
        return jsonify({"ok": False, "error": "unauthorized"}), 401


# ── Request/Response Schemas ────────────────────────────────────────────

@dataclass
class ChatRequest:
    """Request-Schema für Chat-Endpoint."""
    query: str
    user_id: str
    use_web: bool = False
    model: str = "qwen3.5:397b-cloud"
    
    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "ChatRequest":
        return cls(
            query=str(data.get("query", "")).strip(),
            user_id=str(data.get("user_id", "anonymous")),
            use_web=bool(data.get("use_web", False)),
            model=str(data.get("model", "qwen3.5:397b-cloud")),
        )


# ── Configuration ───────────────────────────────────────────────────────

# Default URLs (können via ENV überschrieben werden)
RAG_API_URL = "http://localhost:8765"
OLLAMA_URL = "http://localhost:11434"

# Singleton ChatHandler
_chat_handler: Optional[ChatHandler] = None


def _get_chat_handler() -> ChatHandler:
    """Liefert singleton ChatHandler."""
    global _chat_handler
    if _chat_handler is None:
        _chat_handler = ChatHandler(
            rag_api_url=RAG_API_URL,
            ollama_url=OLLAMA_URL,
        )
    return _chat_handler


# ══════════════════════════════════════════════════════════════════════════
# ENDPOINT: POST /api/styx/chat
# ══════════════════════════════════════════════════════════════════════════

@bp.route("/chat", methods=["POST"])
def styx_chat() -> Any:
    """
    PilotSuite-Styx Chat-Endpoint.
    
    Verarbeitet Chat-Queries mit RAG-API Integration:
    1. RAG-Suche (lokal + optional Web via SearXNG)
    2. LLM-Prompt mit RAG-Kontext
    3. Ollama-Inferenz
    4. Logging für History
    
    Args:
        query: User-Frage (required)
        user_id: User-Identifier (required, für History)
        use_web: Web-Suche aktivieren (default: false)
        model: Ollama-Modell (default: qwen3.5:397b-cloud)
    
    Returns:
        JSON mit:
        - response: LLM-Antwort
        - sources: Liste der RAG-Sources (für UI-Anzeige)
        - query_type: local|web|hybrid
        - context_used: Verwendete Kontext-Informationen
    
    Example Request:
        POST /api/styx/chat
        {
            "query": "Wie war der Energieverbrauch gestern?",
            "user_id": "user_123",
            "use_web": false
        }
    
    Example Response:
        {
            "response": "Der Energieverbrauch gestern betrug...",
            "sources": [
                {"id": "ha_state_123", "score": 0.95, "source": "ha_states"}
            ],
            "query_type": "local",
            "context_used": [...]
        }
    """
    try:
        data = request.get_json(silent=True) or {}
        
        # Request validieren
        if not data.get("query"):
            return jsonify({
                "ok": False,
                "error": "query is required",
            }), 400
        
        if not data.get("user_id"):
            return jsonify({
                "ok": False,
                "error": "user_id is required",
            }), 400
        
        # Request parsen
        chat_request = ChatRequest.from_json(data)
        
        logger.info(
            "Styx chat request (user_id=%s, query=%s, use_web=%s, model=%s)",
            chat_request.user_id,
            chat_request.query[:100] if len(chat_request.query) > 100 else chat_request.query,
            chat_request.use_web,
            chat_request.model
        )
        
        # ChatHandler aufrufen
        handler = _get_chat_handler()
        result = handler.handle_query(
            query=chat_request.query,
            user_id=chat_request.user_id,
            use_web=chat_request.use_web,
            model=chat_request.model,
        )
        
        logger.info(
            "Styx chat response (query_type=%s, sources_count=%s, response_length=%s)",
            result.get("query_type", "local"),
            len(result.get("sources", [])),
            len(result.get("response", ""))
        )
        
        return jsonify({
            "ok": True,
            "response": result.get("response", ""),
            "sources": result.get("sources", []),
            "query_type": result.get("query_type", "local"),
            "context_used": result.get("context_used", []),
        })
        
    except Exception as exc:
        logger.exception("Styx chat endpoint failed: %s", exc)
        return jsonify({
            "ok": False,
            "error": str(exc),
        }), 500


# ══════════════════════════════════════════════════════════════════════════
# ENDPOINT: GET /api/styx/health
# ══════════════════════════════════════════════════════════════════════════

@bp.route("/health", methods=["GET"])
def styx_health() -> Any:
    """
    Health-Check für Styx Chat-Service.
    
    Returns:
        Status von RAG-API und Ollama
    """
    import requests
    
    rag_status = "unknown"
    ollama_status = "unknown"
    
    # RAG-API checken
    try:
        resp = requests.get(
            f"{RAG_API_URL}/api/rag/stats",
            timeout=5,
        )
        rag_status = "ok" if resp.status_code == 200 else "error"
    except Exception:
        rag_status = "unreachable"
    
    # Ollama checken
    try:
        resp = requests.get(
            f"{OLLAMA_URL}/api/tags",
            timeout=5,
        )
        ollama_status = "ok" if resp.status_code == 200 else "error"
    except Exception:
        ollama_status = "unreachable"
    
    status = {
        "rag_api": rag_status,
        "ollama": ollama_status,
        "rag_api_url": RAG_API_URL,
        "ollama_url": OLLAMA_URL,
    }
    
    all_ok = status["rag_api"] == "ok" and status["ollama"] == "ok"
    
    return jsonify({
        "ok": all_ok,
        "services": status,
    }), 200 if all_ok else 503
