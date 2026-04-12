"""Projection contract for pilotsuite_dashboard_v13 mood identity (HA-372).

Verifiziert den rekonsolidierten Dashboard-Projection-Slice:
- `sensor.ai_copilot_mood` wurde in `pilotsuite_dashboard_v13.yaml` vollständig auf
  `sensor.pilotsuite_mood` umgezogen
- beide Mood-Slots im YAML zeigen auf die kanonische PilotSuite-Entity
- der Legacy-String kommt im v13-Dashboard nicht mehr vor
"""

from pathlib import Path


DASHBOARD_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "pilotsuite"
    / "dashboard"
    / "pilotsuite_dashboard_v13.yaml"
)


class TestPilotSuiteDashboardV13Projection:
    """PDV13-1..3: v13 dashboard mood projection contract."""

    def test_PDV131_uses_pilotsuite_mood_entity_in_distribution_card(self):
        source = DASHBOARD_PATH.read_text(encoding="utf-8")

        assert 'title: "🎭 Stimmungsverteilung"' in source
        assert "- entity: sensor.pilotsuite_mood" in source

    def test_PDV132_uses_pilotsuite_mood_entity_in_styx_status_card(self):
        source = DASHBOARD_PATH.read_text(encoding="utf-8")

        assert 'name: "Aktueller Mood"' in source
        assert source.count("entity: sensor.pilotsuite_mood") == 2

    def test_PDV133_contains_no_legacy_ai_copilot_mood_entity(self):
        source = DASHBOARD_PATH.read_text(encoding="utf-8")

        assert "entity: sensor.ai_copilot_mood" not in source
