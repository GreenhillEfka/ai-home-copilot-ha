"""P5-005: API Gateway — Auth, Rate Limiting, Routing."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class AuthMethod(Enum):
    """Authentication methods."""
    BEARER = "bearer"
    API_KEY = "api_key"
    BASIC = "basic"
    NONE = "none"


@dataclass
class GatewayConfig:
    """Gateway configuration."""
    rate_limit_per_second: int = 100
    rate_limit_burst: int = 200
    auth_required: bool = True
    auth_method: AuthMethod = AuthMethod.BEARER
    cors_enabled: bool = True
    allowed_origins: List[str] = field(default_factory=lambda: ["*"])
    timeout_seconds: float = 30.0


@dataclass
class GatewayRequest:
    """Incoming gateway request."""
    path: str
    method: str
    headers: Dict[str, str]
    body: Optional[Dict]
    client_ip: str
    user_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class GatewayResponse:
    """Gateway response."""
    status_code: int
    headers: Dict[str, str]
    body: Any
    latency_ms: float


class APIGateway:
    """API Gateway with auth, rate limiting, and routing."""

    def __init__(self, config: Optional[GatewayConfig] = None):
        self.config = config or GatewayConfig()
        self._routes: Dict[str, Callable] = {}
        self._auth_tokens: Dict[str, str] = {}  # token -> user_id
        self._api_keys: Dict[str, str] = {}  # key -> user_id
        self._request_log: List[Dict] = []
        self._rate_limit_tracker: Dict[str, List[float]] = {}

    def register_route(self, path: str, method: str, handler: Callable):
        """Register a route handler."""
        key = f"{method}:{path}"
        self._routes[key] = handler
        logger.info(f"Registered route: {key}")

    def register_token(self, token: str, user_id: str):
        """Register an auth token."""
        self._auth_tokens[token] = user_id

    def register_api_key(self, api_key: str, user_id: str):
        """Register an API key."""
        self._api_keys[api_key] = user_id

    async def handle_request(self, request: GatewayRequest) -> GatewayResponse:
        """Handle incoming request."""
        start = time.time()
        
        # Check auth
        if self.config.auth_required:
            auth_result = self._authenticate(request)
            if not auth_result["valid"]:
                return self._error_response(401, "Unauthorized")
            request.user_id = auth_result.get("user_id")
        
        # Check rate limit
        if not self._check_rate_limit(request.client_ip, request.user_id):
            return self._error_response(429, "Rate limit exceeded")
        
        # Route request
        route_key = f"{request.method}:{request.path}"
        if route_key not in self._routes:
            # Try prefix match
            handler = self._find_matching_route(request.path, request.method)
            if not handler:
                return self._error_response(404, "Not found")
        else:
            handler = self._routes[route_key]
        
        # Execute handler
        try:
            result = await handler(request) if hasattr(handler, '__await__') else handler(request)
            latency_ms = (time.time() - start) * 1000
            
            # Log request
            self._request_log.append({
                "path": request.path,
                "method": request.method,
                "user_id": request.user_id,
                "status": 200,
                "latency_ms": latency_ms,
            })
            
            return GatewayResponse(
                status_code=200,
                headers={"Content-Type": "application/json"},
                body=result,
                latency_ms=latency_ms
            )
        except Exception as e:
            logger.error(f"Handler failed: {e}")
            return self._error_response(500, str(e))

    def _authenticate(self, request: GatewayRequest) -> Dict[str, Any]:
        """Authenticate request."""
        if self.config.auth_method == AuthMethod.BEARER:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
                if token in self._auth_tokens:
                    return {"valid": True, "user_id": self._auth_tokens[token]}
                return {"valid": False, "error": "Invalid token"}
        
        elif self.config.auth_method == AuthMethod.API_KEY:
            api_key = request.headers.get("X-API-Key", "")
            if api_key in self._api_keys:
                return {"valid": True, "user_id": self._api_keys[api_key]}
            return {"valid": False, "error": "Invalid API key"}
        
        return {"valid": True, "user_id": "anonymous"}

    def _check_rate_limit(self, client_ip: str, user_id: Optional[str]) -> bool:
        """Check rate limit for client."""
        key = user_id or client_ip
        now = time.time()
        
        if key not in self._rate_limit_tracker:
            self._rate_limit_tracker[key] = []
        
        # Clean old entries
        self._rate_limit_tracker[key] = [
            t for t in self._rate_limit_tracker[key]
            if now - t < 1.0
        ]
        
        # Check limit
        if len(self._rate_limit_tracker[key]) >= self.config.rate_limit_per_second:
            return False
        
        self._rate_limit_tracker[key].append(now)
        return True

    def _find_matching_route(self, path: str, method: str) -> Optional[Callable]:
        """Find matching route with prefix matching."""
        for route_key, handler in self._routes.items():
            route_method, route_path = route_key.split(":", 1)
            if route_method == method:
                if path.startswith(route_path.rstrip("/") + "/") or path == route_path:
                    return handler
        return None

    def _error_response(self, status_code: int, message: str) -> GatewayResponse:
        """Create error response."""
        return GatewayResponse(
            status_code=status_code,
            headers={"Content-Type": "application/json"},
            body={"error": message},
            latency_ms=0.0
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get gateway statistics."""
        return {
            "registered_routes": len(self._routes),
            "active_tokens": len(self._auth_tokens),
            "active_api_keys": len(self._api_keys),
            "total_requests": len(self._request_log),
            "rate_limited_clients": len([k for k, v in self._rate_limit_tracker.items() if len(v) >= self.config.rate_limit_per_second]),
        }


# Global default gateway
default_gateway: Optional[APIGateway] = None


def init_api_gateway(config: Optional[GatewayConfig] = None) -> APIGateway:
    """Initialize global API gateway."""
    global default_gateway
    default_gateway = APIGateway(config)
    return default_gateway
