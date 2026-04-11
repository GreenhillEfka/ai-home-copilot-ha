"""Projection contract for mobile responsive dashboard defaults (HA-351).

Verifiziert den Projection-Builder-Pfad in `create_complete_mobile_dashboard`:
- default mood entity nutzt pilotsuite statt legacy copilot_ha
- explizite Overrides bleiben erhalten
- Produktionsmodul enthält keine stale legacy default/path strings mehr
"""

import inspect

from custom_components.pilotsuite.dashboard_cards.mobile.mobile_responsive_dashboard import (
    create_complete_mobile_dashboard,
)
import custom_components.pilotsuite.dashboard_cards.mobile.mobile_responsive_dashboard as mobile_dashboard_module


class TestMobileResponsiveDashboardProjection:
    """MRD1–MRD3: mobile responsive dashboard projection builder contract."""

    def test_MRD1_default_mood_entity_uses_pilotsuite_identity(self):
        dashboard = create_complete_mobile_dashboard({})

        mood_card = dashboard["cards"][0]["cards"][1]

        assert mood_card["entity"] == "sensor.pilotsuite_mood"

    def test_MRD2_explicit_mood_entity_override_is_preserved(self):
        dashboard = create_complete_mobile_dashboard(
            {"mood_entity": "sensor.custom_mood"}
        )

        mood_card = dashboard["cards"][0]["cards"][1]

        assert mood_card["entity"] == "sensor.custom_mood"

    def test_MRD3_source_contains_no_legacy_mobile_dashboard_defaults(self):
        source = inspect.getsource(mobile_dashboard_module)

        assert "custom_components/copilot_ha/dashboard_cards/" not in source
        assert 'data.get("mood_entity", "sensor.copilot_ha_mood")' not in source
        assert "custom_components/pilotsuite/dashboard_cards/" in source
        assert 'data.get("mood_entity", "sensor.pilotsuite_mood")' in source
