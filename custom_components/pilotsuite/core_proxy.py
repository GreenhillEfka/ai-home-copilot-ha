from __future__ import annotations

from collections.abc import Iterable, Mapping
import logging
from typing import Final

from aiohttp import ClientError, ClientTimeout, hdrs, web
from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .connection_config import build_core_headers, resolve_core_connection
from .core_endpoint import build_base_url
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

_PROXY_TIMEOUT: Final = ClientTimeout(total=20)
_ALLOWED_PREFIXES: Final = ("/api/",)
_HOP_BY_HOP_HEADERS: Final = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
    "content-length",
    "content-encoding",
}
_FORWARD_REQUEST_HEADERS: Final = (
    hdrs.ACCEPT,
    hdrs.CONTENT_TYPE,
    hdrs.IF_NONE_MATCH,
    hdrs.IF_MODIFIED_SINCE,
    hdrs.CACHE_CONTROL,
)
_FORWARD_RESPONSE_HEADERS: Final = (
    hdrs.CONTENT_TYPE,
    hdrs.CACHE_CONTROL,
    hdrs.ETAG,
    hdrs.LAST_MODIFIED,
    hdrs.EXPIRES,
)


def _normalize_proxy_path(tail: str) -> str | None:
    cleaned = (tail or "").strip().lstrip("/")
    if not cleaned:
        return None

    normalized = f"/{cleaned}"
    if not any(normalized.startswith(prefix) for prefix in _ALLOWED_PREFIXES):
        return None
    return normalized


def _filter_forward_headers(source: Mapping[str, str], allowed: Iterable[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    allowed_lower = {item.lower() for item in allowed}
    for key, value in source.items():
        if key.lower() in allowed_lower and value:
            result[key] = value
    return result


def _filter_response_headers(source: Mapping[str, str]) -> dict[str, str]:
    headers = _filter_forward_headers(source, _FORWARD_RESPONSE_HEADERS)
    for key, value in source.items():
        lowered = key.lower()
        if lowered in _HOP_BY_HOP_HEADERS:
            continue
        if lowered.startswith("x-") and value:
            headers[key] = value
    return headers


def _resolve_entry(hass: HomeAssistant, request: web.Request) -> ConfigEntry | None:
    requested_entry_id = str(request.query.get("entry_id") or "").strip()
    entries = hass.config_entries.async_entries(DOMAIN)
    if requested_entry_id:
        return next((entry for entry in entries if entry.entry_id == requested_entry_id), None)
    return entries[0] if entries else None


class CoreProxyView(HomeAssistantView):
    """Authenticated same-origin proxy from Home Assistant to PilotSuite Core."""

    url = "/api/copilot_proxy/{tail:.*}"
    name = "api:pilotsuite:core_proxy"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass

    async def get(self, request: web.Request, tail: str) -> web.Response:
        return await self._handle(request, tail)

    async def post(self, request: web.Request, tail: str) -> web.Response:
        return await self._handle(request, tail)

    async def put(self, request: web.Request, tail: str) -> web.Response:
        return await self._handle(request, tail)

    async def patch(self, request: web.Request, tail: str) -> web.Response:
        return await self._handle(request, tail)

    async def delete(self, request: web.Request, tail: str) -> web.Response:
        return await self._handle(request, tail)

    async def _handle(self, request: web.Request, tail: str) -> web.Response:
        proxy_path = _normalize_proxy_path(tail)
        if not proxy_path:
            return web.json_response({"error": "invalid_proxy_path"}, status=400)

        entry = _resolve_entry(self._hass, request)
        if entry is None:
            return web.json_response({"error": "core_entry_not_found"}, status=503)

        host, port, token = resolve_core_connection(entry)
        base_url = build_base_url(host, port)
        headers = build_core_headers(token)
        headers.update(_filter_forward_headers(request.headers, _FORWARD_REQUEST_HEADERS))

        payload = await request.read() if request.can_read_body else None
        forwarded_query = [(key, value) for key, value in request.query.items() if key != "entry_id"]
        target_url = f"{base_url}{proxy_path}"

        session = async_get_clientsession(self._hass)
        try:
            async with session.request(
                request.method,
                target_url,
                params=forwarded_query,
                data=payload,
                headers=headers,
                timeout=_PROXY_TIMEOUT,
                allow_redirects=False,
            ) as response:
                body = await response.read()
                return web.Response(
                    status=response.status,
                    body=body,
                    headers=_filter_response_headers(response.headers),
                )
        except TimeoutError:
            _LOGGER.warning("Core proxy timeout for %s", target_url)
            return web.json_response({"error": "core_timeout", "path": proxy_path}, status=504)
        except ClientError as err:
            _LOGGER.warning("Core proxy client error for %s: %s", target_url, err)
            return web.json_response(
                {"error": "core_unreachable", "message": str(err), "path": proxy_path},
                status=502,
            )
        except Exception as err:  # noqa: BLE001
            _LOGGER.exception("Unexpected core proxy failure for %s", target_url)
            return web.json_response(
                {"error": "core_proxy_failed", "message": str(err), "path": proxy_path},
                status=500,
            )


async def async_register_core_proxy(hass: HomeAssistant) -> None:
    """Register the Core proxy view once per HA instance."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get("core_proxy_registered"):
        return

    hass.http.register_view(CoreProxyView(hass))
    domain_data["core_proxy_registered"] = True
    _LOGGER.info("PilotSuite Core proxy registered at /api/copilot_proxy")


__all__ = [
    "CoreProxyView",
    "async_register_core_proxy",
    "_normalize_proxy_path",
]
