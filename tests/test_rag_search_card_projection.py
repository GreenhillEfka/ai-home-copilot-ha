"""Projection contract for rag_search_card dashboard example parity.

Verifiziert den gezogenen YAML-Slice:
- Pfadkopf zeigt auf den kanonischen pilotsuite-Pfad
- eingebettete Mood-Card nutzt `sensor.pilotsuite_mood`
- gezogene Legacy-Referenzen kommen im Artefakt nicht mehr vor
"""

from pathlib import Path


RAG_SEARCH_CARD_PATH = (
    Path(__file__).resolve().parents[1]
    / "custom_components"
    / "pilotsuite"
    / "dashboard_cards"
    / "rag_search_card.yaml"
)


class TestRagSearchCardProjection:
    """RSC1-RSC3: rag_search_card projection contract."""

    def test_RSC1_uses_canonical_pilotsuite_path_header(self):
        source = RAG_SEARCH_CARD_PATH.read_text(encoding="utf-8")

        assert "# Path: custom_components/pilotsuite/dashboard_cards/rag_search_card.yaml" in source

    def test_RSC2_uses_pilotsuite_mood_entity_in_embedded_dashboard_example(self):
        source = RAG_SEARCH_CARD_PATH.read_text(encoding="utf-8")

        assert "title: 😊 Stimmung" in source
        assert "entity: sensor.pilotsuite_mood" in source

    def test_RSC3_removes_drawn_legacy_path_and_mood_entity_refs(self):
        source = RAG_SEARCH_CARD_PATH.read_text(encoding="utf-8")

        assert "custom_components/copilot_ha/dashboard_cards/rag_search_card.yaml" not in source
        assert "entity: sensor.copilot_ha_mood" not in source
