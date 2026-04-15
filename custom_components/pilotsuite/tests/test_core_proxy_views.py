from __future__ import annotations

from custom_components.copilot_ha.card_assets import _CARD_FILENAMES, get_card_asset_url
from custom_components.copilot_ha.core_proxy import _normalize_proxy_path


def test_normalize_proxy_path_accepts_api_paths():
    assert _normalize_proxy_path("api/v1/styx/dashboard") == "/api/v1/styx/dashboard"
    assert _normalize_proxy_path("/api/v1/cards/pilotsuite-cards.js") == "/api/v1/cards/pilotsuite-cards.js"


def test_normalize_proxy_path_rejects_non_api_paths():
    assert _normalize_proxy_path("") is None
    assert _normalize_proxy_path("health") is None
    assert _normalize_proxy_path("../api/v1/styx/dashboard") is None


def test_card_asset_urls_are_same_origin_api_routes():
    for filename in _CARD_FILENAMES:
        assert get_card_asset_url(filename) == f"/api/pilotsuite/cards/{filename}"
