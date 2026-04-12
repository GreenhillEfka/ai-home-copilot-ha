"""Projection contract for pilotsuite_dashboard_v13_3tab mood identity (HA-373).

Verifiziert den rekonsolidierten Dashboard-Projection-Slice:
- `sensor.ai_copilot_mood` wurde in `pilotsuite_dashboard_v13_3tab.yaml` vollständig auf
  `sensor.pilotsuite_mood` umgezogen
- beide Mood-Slots im YAML zeigen auf die kanonische PilotSuite-Entity
- der Legacy-String kommt im v13_3tab-Dashboard nicht mehr vor
"""

from pathlib import Path


DASHBOARD_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "pilotsuite"
    / "dashboard"
    / "pilotsuite_dashboard_v13_3tab.yaml"
)


class TestPilotSuiteDashboardV133TabProjection:
    """PDV133T-1..3: v13 3-tab dashboard mood projection contract."""

    def test_PDV133T1_uses_pilotsuite_mood_entity_in_distribution_card(self):
        source = DASHBOARD_PATH.read_text(encoding="utf-8")

        assert 'title: "📊 Stimmungsverteilung"' in source
        assert "- entity: sensor.pilotsuite_mood" in source

    def test_PDV133T2_uses_pilotsuite_mood_entity_in_styx_status_card(self):
        source = DASHBOARD_PATH.read_text(encoding="utf-8")

        assert 'name: "Mood Neuron"' in source
        assert source.count("entity: sensor.pilotsuite_mood") == 2

    def test_PDV133T3_contains_no_legacy_ai_copilot_mood_entity(self):
        source = DASHBOARD_PATH.read_text(encoding="utf-8")

        assert "entity: sensor.ai_copilot_mood" not in source
