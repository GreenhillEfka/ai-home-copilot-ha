"""Projection contract for dashboard_examples.yaml parity.

Verifiziert den gezogenen YAML-Slice:
- Pfadkopf zeigt auf den kanonischen pilotsuite-Dateipfad
- alle verbliebenen Mood-Referenzen nutzen `sensor.pilotsuite_mood`
- gezogene Legacy-Pfad-/Mood-Strings kommen im Artefakt nicht mehr vor
"""

from pathlib import Path


DASHBOARD_EXAMPLES_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "pilotsuite"
    / "dashboard_cards"
    / "dashboard_examples.yaml"
)


class TestDashboardExamplesProjection:
    """DEP1-DEP3: dashboard_examples projection contract."""

    def test_DEP1_uses_canonical_pilotsuite_path_header(self):
        source = DASHBOARD_EXAMPLES_PATH.read_text(encoding="utf-8")

        assert (
            "# Path: custom_components/pilotsuite/dashboard_cards/dashboard_examples.yaml"
            in source
        )

    def test_DEP2_uses_pilotsuite_mood_entity_in_all_example_slots(self):
        source = DASHBOARD_EXAMPLES_PATH.read_text(encoding="utf-8")

        assert source.count("sensor.pilotsuite_mood") == 3
        assert "entity: sensor.pilotsuite_mood" in source
        assert "- sensor.pilotsuite_mood" in source

    def test_DEP3_removes_drawn_legacy_path_and_mood_entity_refs(self):
        source = DASHBOARD_EXAMPLES_PATH.read_text(encoding="utf-8")

        assert "custom_components/copilot_ha/dashboard_cards/" not in source
        assert "sensor.copilot_ha_mood" not in source
