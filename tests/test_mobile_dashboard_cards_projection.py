"""Projection contract for mobile dashboard cards mood identity (HA-371).

Verifiziert den mobilen Projection-Builder-Pfad in `mobile_dashboard_cards.py`:
- Mood-Lookup nutzt die kanonische `pilotsuite`-Entity
- Mood-Projektion behält Confidence/Contributors bei
- Produktionsmodul enthält keinen stale `ai_copilot`-Lookup mehr
"""

from pathlib import Path


class TestMobileDashboardCardsProjection:
    @staticmethod
    def _source() -> str:
        return (
            Path(__file__).resolve().parents[1]
            / "custom_components"
            / "pilotsuite"
            / "mobile_dashboard_cards.py"
        ).read_text(encoding="utf-8")

    def test_MDC1_uses_pilotsuite_mood_entity_lookup(self):
        source = self._source()

        assert 'self._hass.states.get("sensor.pilotsuite_mood")' in source

    def test_MDC2_preserves_mood_projection_attributes(self):
        source = self._source()

        assert '"confidence": mood_entity.attributes.get("confidence", 0.0)' in source
        assert '"contributors": mood_entity.attributes.get("contributors", [])' in source

    def test_MDC3_contains_no_legacy_ai_copilot_mood_lookup(self):
        source = self._source()

        assert 'self._hass.states.get("sensor.ai_copilot_mood")' not in source
