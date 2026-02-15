"""
AI Home CoPilot Core TypeScript SDK

Client SDK for interacting with the AI Home CoPilot Core API.
"""

import os
import requests
from typing import Optional, Dict, Any, List

__version__ = "0.5.0"
__api_version__ = "v1"


class CoPilotClient:
    """Client for AI Home CoPilot Core API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        auth_token: Optional[str] = None,
        timeout: int = 30,
    ):
        """Initialize the client.
        
        Args:
            base_url: Base URL of the API (default: from env or Home Assistant)
            auth_token: Authentication token (optional)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or os.environ.get(
            "COPILOT_API_URL", "http://homeassistant.local:8123/api/copilot"
        )
        self.auth_token = auth_token or os.environ.get("COPILOT_AUTH_TOKEN")
        self.timeout = timeout
        self.session = requests.Session()
        if self.auth_token:
            self.session.headers.update({"X-Auth-Token": self.auth_token})

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make API request."""
        url = f"{self.base_url}/{endpoint}"
        response = self.session.request(method, url, timeout=self.timeout, **kwargs)
        response.raise_for_status()
        return response.json()

    def get_system_health(self) -> Dict[str, Any]:
        """Get system health status."""
        return self._request("GET", f"{__api_version__}/system/health")

    def get_mood_context(self) -> Dict[str, Any]:
        """Get current mood context."""
        return self._request("GET", f"{__api_version__}/mood/context")

    def get_brain_graph(self) -> Dict[str, Any]:
        """Get brain graph visualization data."""
        return self._request("GET", f"{__api_version__}/graph/visualization")

    def submit_event(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Submit an event to the API.
        
        Args:
            event_type: Type of event (e.g., "user_action", "sensor_update")
            payload: Event data
            
        Returns:
            API response with event_id
        """
        return self._request(
            "POST",
            f"{__api_version__}/events",
            json={"type": event_type, "payload": payload},
        )

    def get_habitus_rules(self) -> List[Dict[str, Any]]:
        """Get discovered Habitus rules (A→B patterns)."""
        return self._request("GET", f"{__api_version__}/habitus/rules")

    def get_tag_registry(self) -> Dict[str, Any]:
        """Get tag registry with entity classifications."""
        return self._request("GET", f"{__api_version__}/tags/registry")

    def close(self):
        """Close the session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def get_client(
    base_url: Optional[str] = None,
    auth_token: Optional[str] = None,
) -> CoPilotClient:
    """Get a configured client instance.
    
    Convenience function for quick client creation.
    """
    return CoPilotClient(base_url=base_url, auth_token=auth_token)
