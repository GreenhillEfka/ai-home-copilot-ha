"""Projection contract for pilotsuite_dashboard_v13_3tab entity parity.

Verifiziert den rekonsolidierten Dashboard-Projection-Slice:
- Mood-Slots zeigen auf `sensor.pilotsuite_mood`
- neuron-/habitus-/presence-Referenzen nutzen die kanonischen PilotSuite-Entities
- die gezogenen Legacy-Strings kommen im v13_3tab-Dashboard nicht mehr vor
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
    """PDV133T-1..6: v13 3-tab dashboard projection contract."""

    def test_PDV133T1_uses_pilotsuite_mood_entity_in_distribution_card(self):
        source = DASHBOARD_PATH.read_text(encoding="utf-8")

        assert 'title: "📊 Stimmungsverteilung"' in source
        assert "- entity: sensor.pilotsuite_mood" in source

    def test_PDV133T2_uses_pilotsuite_mood_entity_in_styx_status_card(self):
        source = DASHBOARD_PATH.read_text(encoding="utf-8")

        assert 'name: "Mood Neuron"' in source
        assert source.count("entity: sensor.pilotsuite_mood") == 3

    def test_PDV133T3_contains_no_legacy_ai_copilot_mood_entity(self):
        source = DASHBOARD_PATH.read_text(encoding="utf-8")

        assert "entity: sensor.ai_copilot_mood" not in source

    def test_PDV133T4_uses_pilotsuite_neuron_and_habitus_entities(self):
        source = DASHBOARD_PATH.read_text(encoding="utf-8")

        assert "entity: sensor.pilotsuite_neuron_activity" in source
        assert "entity: sensor.pilotsuite_habitus_zones" in source

    def test_PDV133T5_uses_pilotsuite_presence_intelligence_in_all_presence_slots(self):
        source = DASHBOARD_PATH.read_text(encoding="utf-8")

        assert source.count("entity: sensor.pilotsuite_presence_intelligence") == 3

    def test_PDV133T6_uses_pilotsuite_neuron_dashboard_and_removes_drawn_legacy_refs(self):
        source = DASHBOARD_PATH.read_text(encoding="utf-8")

        assert source.count("entity: sensor.pilotsuite_neuron_dashboard") == 2
        assert "entity: sensor.copilot_ha_neuron_activity" not in source
        assert "entity: sensor.copilot_ha_habitus_zones" not in source
        assert "entity: sensor.ai_copilot_presence" not in source
        assert "entity: sensor.ai_copilot_neuron_dashboard" not in source
