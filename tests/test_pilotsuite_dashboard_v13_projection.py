"""Projection contract for pilotsuite_dashboard_v13 entity parity.

Verifiziert den rekonsolidierten Dashboard-Projection-Slice:
- Mood-Slots zeigen auf `sensor.pilotsuite_mood`
- neuron-/habitus-/presence-Referenzen nutzen die kanonischen PilotSuite-Entities
- die gezogenen Legacy-Strings kommen im v13-Dashboard nicht mehr vor
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
    """PDV13-1..6: v13 dashboard projection contract."""

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

    def test_PDV134_uses_pilotsuite_neuron_and_habitus_entities(self):
        source = DASHBOARD_PATH.read_text(encoding="utf-8")

        assert "entity: sensor.pilotsuite_neuron_activity" in source
        assert "entity: sensor.pilotsuite_habitus_zones" in source

    def test_PDV135_uses_pilotsuite_presence_intelligence_in_both_presence_slots(self):
        source = DASHBOARD_PATH.read_text(encoding="utf-8")

        assert source.count("entity: sensor.pilotsuite_presence_intelligence") == 2

    def test_PDV136_uses_pilotsuite_neuron_dashboard_and_removes_drawn_legacy_refs(self):
        source = DASHBOARD_PATH.read_text(encoding="utf-8")

        assert "entity: sensor.pilotsuite_neuron_dashboard" in source
        assert "entity: sensor.copilot_ha_neuron_activity" not in source
        assert "entity: sensor.copilot_ha_habitus_zones" not in source
        assert "entity: sensor.ai_copilot_presence" not in source
        assert "entity: sensor.ai_copilot_neuron_dashboard" not in source
