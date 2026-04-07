from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Optional

import aiohttp
from aiohttp import web

from ..const import HEADER_AUTH
from .models import CommonErrorResponse


@dataclass
class CopilotStatus:
    ok: bool | None
    version: str | None


class CopilotApiError(Exception):
    pass


# ==================== Standardized Error Response Helper ====================


def _error_response(
    code: str,
    message: str,
    field: str | None = None,
    context: dict[str, Any] | None = None,
    status: int = 400,
) -> web.Response:
    """Create a standardized error response.
    
    All HA API endpoints should use this helper to ensure consistent
    error response shapes across the integration.
    
    Args:
        code: Error code (e.g., "VALIDATION_ERROR", "NOT_FOUND")
        message: Human-readable error message
        field: Optional field name that caused the error
        context: Optional additional debug information
        status: HTTP status code (default 400)
    
    Returns:
        aiohttp.web.Response with JSON body and appropriate status code
    
    Example:
        return _error_response(
            code="VALIDATION_ERROR",
            message="user_id is required",
            field="user_id",
            status=400,
        )
    """
    error_data = CommonErrorResponse(
        code=code,
        message=message,
        field=field,
        context=context or {},
    )
    return web.json_response(error_data.model_dump(exclude_none=True), status=status)


class CopilotApiClient:
    def __init__(self, session: aiohttp.ClientSession, base_url: str, token: str | None):
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._token = token

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
            headers[HEADER_AUTH] = self._token
        return headers

    async def _get_json(self, path: str) -> dict:
        url = f"{self._base_url}{path}"
        try:
            async with self._session.get(
                url,
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status >= 400:
                    body = await resp.text()
                    raise CopilotApiError(f"HTTP {resp.status} for {url}: {body[:200]}")
                return await resp.json()
        except asyncio.TimeoutError as e:
            raise CopilotApiError(f"Timeout calling {url}") from e
        except aiohttp.ClientError as e:
            raise CopilotApiError(f"Client error calling {url}: {e}") from e

    async def _post_json(self, path: str, payload: dict) -> dict:
        url = f"{self._base_url}{path}"
        try:
            async with self._session.post(
                url,
                headers=self._headers(),
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status >= 400:
                    body = await resp.text()
                    raise CopilotApiError(f"HTTP {resp.status} for {url}: {body[:200]}")
                return await resp.json()
        except asyncio.TimeoutError as e:
            raise CopilotApiError(f"Timeout calling {url}") from e
        except aiohttp.ClientError as e:
            raise CopilotApiError(f"Client error calling {url}: {e}") from e

    # ── Module APIs (Slices 67-82) ─────────────────────────────────────
    
    async def get_modules_list(self) -> dict:
        """Get list of registered modules."""
        return await self._get_json("/api/v1/modules/list")
    
    async def get_module_status(self, module_name: str) -> dict:
        """Get status of a specific module."""
        return await self._get_json(f"/api/v1/modules/{module_name}/status")
    
    async def get_module_config(self, module_name: str) -> dict:
        """Get configuration of a specific module."""
        return await self._get_json(f"/api/v1/modules/{module_name}/config")
    
    async def execute_module_action(self, module_name: str, action: str, params: dict | None = None) -> dict:
        """Execute a module action."""
        payload = {"action": action}
        if params:
            payload.update(params)
        return await self._post_json(f"/api/v1/modules/{module_name}/action", payload)
    
    # Presence Module
    async def get_presence_zones(self) -> dict:
        """Get presence status for all zones."""
        return await self._get_json("/api/v1/modules/presence/zones")
    
    async def get_presence_zone(self, zone_id: str) -> dict:
        """Get presence status for a specific zone."""
        return await self._get_json(f"/api/v1/modules/presence/zone/{zone_id}")
    
    # Light Module
    async def get_light_zones(self) -> dict:
        """Get light status for all zones."""
        return await self._get_json("/api/v1/modules/light/zones")
    
    async def activate_light_scene(self, zone_id: str, scene: str) -> dict:
        """Activate light scene for a zone."""
        return await self._post_json(f"/api/v1/modules/light/zone/{zone_id}/scene", {"scene": scene})
    
    # Climate Module
    async def get_climate_zones(self) -> dict:
        """Get climate status for all zones."""
        return await self._get_json("/api/v1/modules/climate/zones")
    
    async def set_climate_setpoint(self, zone_id: str, temperature: float) -> dict:
        """Set climate setpoint for a zone."""
        return await self._post_json(f"/api/v1/modules/climate/zone/{zone_id}/setpoint", {"temperature": temperature})
    
    # Humidity Module
    async def get_humidity_zones(self) -> dict:
        """Get humidity status for all zones."""
        return await self._get_json("/api/v1/modules/humidity/zones")
    
    # Energy Module
    async def get_energy_forecast(self) -> dict:
        """Get energy forecast."""
        return await self._get_json("/api/v1/modules/energy/forecast")
    
    async def get_energy_optimization(self) -> dict:
        """Get energy optimization recommendations."""
        return await self._get_json("/api/v1/modules/energy/optimization")
    
    # TimeOfDay Module
    async def get_timeofday_current(self) -> dict:
        """Get current time of day state."""
        return await self._get_json("/api/v1/modules/timeofday/current")
    
    async def get_timeofday_zones(self) -> dict:
        """Get time of day state for all zones."""
        return await self._get_json("/api/v1/modules/timeofday/zones")
    
    # Rules Module
    async def get_rules_list(self) -> dict:
        """List all rules."""
        return await self._get_json("/api/v1/modules/rules/list")

    async def activate_rule(self, rule_id: str) -> dict:
        """Activate a rule."""
        return await self._post_json(f"/api/v1/modules/rules/{rule_id}/activate", {})

    async def _put_json(self, path: str, payload: dict) -> dict:
        url = f"{self._base_url}{path}"
        try:
            async with self._session.put(
                url,
                json=payload,
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status >= 400:
                    body = await resp.text()
                    raise CopilotApiError(f"HTTP {resp.status} for {url}: {body[:200]}")
                if resp.status == 204:
                    return {}
                ctype = resp.headers.get("Content-Type", "")
                if "json" in ctype:
                    return await resp.json()
                return {"text": (await resp.text())[:2000]}
        except asyncio.TimeoutError as e:
            raise CopilotApiError(f"Timeout calling {url}") from e
        except aiohttp.ClientError as e:
            raise CopilotApiError(f"Client error calling {url}: {e}") from e

    async def async_get(self, path: str) -> dict:
        return await self._get_json(path)

    async def async_post(self, path: str, payload: dict) -> dict:
        return await self._post_json(path, payload)

    async def async_put(self, path: str, payload: dict) -> dict:
        return await self._put_json(path, payload)

    async def async_set_zone_presence_hold(
        self,
        person_id: str,
        state: str,
        reason: str = "manual",
        duration: int | None = None,
    ) -> dict:
        """Set manual presence hold for a person via Core /api/v1/presence/hold."""
        payload: dict[str, Any] = {"person_id": person_id, "state": state, "reason": reason}
        if duration is not None:
            payload["duration"] = duration
        return await self._post_json("/api/v1/presence/hold", payload)

    async def async_clear_zone_presence_hold(self, person_id: str) -> dict:
        """Clear manual presence hold for a person via Core DELETE /api/v1/presence/hold."""
        url = f"{self._base_url}/api/v1/presence/hold?person_id={person_id}"
        try:
            async with self._session.delete(
                url,
                headers=self._headers(),
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status >= 400:
                    body = await resp.text()
                    raise CopilotApiError(f"HTTP {resp.status} for {url}: {body[:200]}")
                if resp.status == 204:
                    return {}
                return await resp.json()
        except asyncio.TimeoutError as e:
            raise CopilotApiError(f"Timeout calling {url}") from e
        except aiohttp.ClientError as e:
            raise CopilotApiError(f"Client error calling {url}: {e}") from e

    async def async_get_status(self) -> CopilotStatus:
        health: dict | None = None
        version: dict | None = None

        ok: bool | None = None
        ver: str | None = None

        try:
            health = await self._get_json("/health")
            ok_val = health.get("ok")
            ok = bool(ok_val) if ok_val is not None else None
        except CopilotApiError:
            ok = None

        try:
            version = await self._get_json("/version")
            # allow either {"version": "x"} or {"data": {"version": "x"}}
            if isinstance(version.get("version"), str):
                ver = version.get("version")
            elif isinstance(version.get("data"), dict) and isinstance(version["data"].get("version"), str):
                ver = version["data"].get("version")
            else:
                # fallback to stringified payload
                ver = None
        except CopilotApiError:
            ver = None

        return CopilotStatus(ok=ok, version=ver)


import asyncio  # keep at end to avoid circulars in some HA loaders

__all__ = [
    "_error_response",
    "CopilotStatus",
    "CopilotApiError",
    "CopilotApiClient",
]
