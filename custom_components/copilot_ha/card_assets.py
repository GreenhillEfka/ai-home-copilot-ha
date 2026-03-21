from __future__ import annotations

from pathlib import Path
import logging

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

_CARD_FILENAMES = {
    # Active Lovelace cards (registered and referenced in dashboards)
    "styx-chat-card.js": "www/styx-chat-card.js",
    "styx-suggestions-card.js": "www/styx-suggestions-card.js",
    "styx-error-card.js": "www/styx-error-card.js",
    "styx-household-card.js": "www/styx-household-card.js",
    "styx-mood-card.js": "www/styx-mood-card.js",
    "styx-brain-card.js": "www/styx-brain-card.js",
    "styx-habitus-card.js": "www/styx-habitus-card.js",
    "styx-zone-card.js": "www/styx-zone-card.js",
    # Legacy/unused cards removed in v14.9.x cleanup:
    #   pilotstack-zone-cards.mjs — PS-198/199/200 zone creator (0 refs, never imported)
    #   frontend/styx-dashboard-card.js — orphan (0 refs)
    #   frontend/module-control-card.js — orphan (0 refs)
    #   frontend/neuron-layer-card.js — orphan (0 refs)
    #   frontend/habitus-zone-card.js — orphan (0 refs)
}

_CARD_ROOT = Path(__file__).resolve().parent


def get_card_asset_url(filename: str) -> str:
    return f"/api/{DOMAIN}/cards/{filename}"


class CardAssetView(HomeAssistantView):
    """Serve bundled PilotSuite Lovelace card scripts from the integration itself."""

    url = f"/api/{DOMAIN}/cards/{{filename}}"
    name = "api:copilot_ha:card_assets"
    requires_auth = False

    async def get(self, request: web.Request, filename: str) -> web.Response:
        relative_path = _CARD_FILENAMES.get(filename)
        if not relative_path:
            raise web.HTTPNotFound()

        file_path = _CARD_ROOT / relative_path
        if not file_path.is_file():
            _LOGGER.warning("PilotSuite card asset missing: %s", file_path)
            raise web.HTTPNotFound()

        return web.Response(
            text=file_path.read_text(encoding="utf-8"),
            content_type="application/javascript",
            headers={"Cache-Control": "public, max-age=3600"},
        )


async def async_register_card_asset_views(hass: HomeAssistant) -> None:
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get("card_asset_views_registered"):
        return

    hass.http.register_view(CardAssetView())
    domain_data["card_asset_views_registered"] = True
    _LOGGER.info("PilotSuite card asset views registered")


__all__ = [
    "_CARD_FILENAMES",
    "CardAssetView",
    "async_register_card_asset_views",
    "get_card_asset_url",
]
