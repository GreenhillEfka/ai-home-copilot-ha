"""Local user preference API endpoints for PilotSuite.

Privacy-first: user IDs remain local and are never forwarded to Core.
"""
from __future__ import annotations

import logging
from typing import Any

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from ..const import DOMAIN
from . import _error_response

_LOGGER = logging.getLogger(__name__)


class _UserPreferenceBaseView(HomeAssistantView):
    """Base view with shared helpers."""

    requires_auth = True

    def __init__(self, module) -> None:
        self._module = module


class UserPreferencesView(_UserPreferenceBaseView):
    """GET all preferences for a user."""

    url = "/api/v1/user/{user_id}/preferences"
    name = "api:copilot_ha:user_preferences"

    async def get(self, request: web.Request) -> web.Response:
        user_id = request.match_info.get("user_id", "")
        if not user_id:
            return _error_response(
                code="VALIDATION_ERROR",
                message="user_id is required",
                field="user_id",
                context={"received": user_id or None},
                status=400,
            )

        prefs = self._module.get_user_preference(user_id)
        if prefs is None:
            return web.json_response({"user_id": user_id, "preferences": {}}, status=200)

        return web.json_response({"user_id": user_id, "preferences": prefs}, status=200)


class UserZonePreferenceView(_UserPreferenceBaseView):
    """GET preference for a user in a specific zone."""

    url = "/api/v1/user/{user_id}/zone/{zone_id}/preference"
    name = "api:copilot_ha:user_zone_preference"

    async def get(self, request: web.Request) -> web.Response:
        user_id = request.match_info.get("user_id", "")
        zone_id = request.match_info.get("zone_id", "")

        if not user_id or not zone_id:
            missing = []
            if not user_id:
                missing.append("user_id")
            if not zone_id:
                missing.append("zone_id")
            return _error_response(
                code="VALIDATION_ERROR",
                message="user_id and zone_id are required",
                field=", ".join(missing),
                context={"user_id": user_id or None, "zone_id": zone_id or None},
                status=400,
            )

        pref = self._module.get_user_preference(user_id, zone_id)
        if pref is None:
            return web.json_response(
                {"user_id": user_id, "zone_id": zone_id, "preference": None},
                status=200,
            )

        return web.json_response(
            {"user_id": user_id, "zone_id": zone_id, "preference": pref},
            status=200,
        )


class UserPreferenceUpdateView(_UserPreferenceBaseView):
    """POST to update a user's preference for a zone."""

    url = "/api/v1/user/{user_id}/preference"
    name = "api:copilot_ha:user_preference_update"

    async def post(self, request: web.Request) -> web.Response:
        user_id = request.match_info.get("user_id", "")
        if not user_id:
            return _error_response(
                code="VALIDATION_ERROR",
                message="user_id is required",
                field="user_id",
                context={"received": user_id or None},
                status=400,
            )

        try:
            payload = await request.json()
        except Exception:  # noqa: BLE001
            return _error_response(
                code="INVALID_JSON",
                message="Request body must be valid JSON",
                field=None,
                context={},
                status=400,
            )

        if not isinstance(payload, dict):
            return _error_response(
                code="INVALID_PAYLOAD",
                message="Request body must be a JSON object",
                field=None,
                context={"received_type": type(payload).__name__},
                status=400,
            )

        zone_id = payload.get("zone_id")
        if not isinstance(zone_id, str) or not zone_id:
            return _error_response(
                code="VALIDATION_ERROR",
                message="zone_id is required and must be a non-empty string",
                field="zone_id",
                context={
                    "received": zone_id,
                    "received_type": type(zone_id).__name__ if zone_id is not None else None,
                },
                status=400,
            )

        def _as_float(val: Any, field: str) -> float | None:
            if val is None:
                return None
            try:
                return float(val)
            except (TypeError, ValueError) as exc:
                raise ValueError(field) from exc

        try:
            comfort_bias = _as_float(payload.get("comfort_bias"), "comfort_bias")
            frugality_bias = _as_float(payload.get("frugality_bias"), "frugality_bias")
            joy_bias = _as_float(payload.get("joy_bias"), "joy_bias")
        except ValueError as err:
            field_name = str(err)
            received = payload.get(field_name)
            return _error_response(
                code="VALIDATION_ERROR",
                message=f"{field_name} must be a number between 0.0 and 1.0",
                field=field_name,
                context={
                    "received": received,
                    "received_type": type(received).__name__ if received is not None else None,
                },
                status=400,
            )

        updated = await self._module.update_user_preference(
            user_id=user_id,
            zone_id=zone_id,
            comfort_bias=comfort_bias,
            frugality_bias=frugality_bias,
            joy_bias=joy_bias,
        )

        return web.json_response(
            {"user_id": user_id, "zone_id": zone_id, "preference": updated},
            status=200,
        )


async def async_register_user_preference_api(
    hass: HomeAssistant,
    entry_id: str,
    module,
) -> None:
    """Register user preference API views.

    Only registers once per HA instance.
    """
    dom = hass.data.setdefault(DOMAIN, {})
    if dom.get("user_preference_api_registered"):
        return

    hass.http.register_view(UserPreferencesView(module))
    hass.http.register_view(UserZonePreferenceView(module))
    hass.http.register_view(UserPreferenceUpdateView(module))

    dom["user_preference_api_registered"] = True
    _LOGGER.info("User preference API registered for entry %s", entry_id)
