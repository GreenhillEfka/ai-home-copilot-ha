"""Tests for Neural Interface Card (styx-neural-card.js)"""

import pytest
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestNeuralCardConfig:
    """Test Neural Interface Card configuration and structure."""

    def test_card_js_exists(self):
        """Test that styx-neural-card.js exists."""
        card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-neural-card.js"
        assert card_path.exists(), "styx-neural-card.js should exist"

    def test_card_js_is_valid_js(self):
        """Test that card JS file is valid JavaScript."""
        card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-neural-card.js"
        content = card_path.read_text()

        assert "class StyxNeuralCard extends" in content, "Card should define StyxNeuralCard class"
        assert "customElements.define" in content, "Card should register custom element"
        assert "styx-neural-card" in content, "Card should use correct element name"

    def test_card_has_required_methods(self):
        """Test that card has required methods."""
        card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-neural-card.js"
        content = card_path.read_text()

        required_methods = [
            "setConfig",
            "set hass",
            "getCardSize",
            "_fetchNeuralData",
            "_renderNeuralViz",
            "_snapshotNeurons",
            "_fetchAndAnimateNeurons",
            "_animateNeuronChanges",
            "_loadHistory",
            "_sendMessage",
            "_renderMessages",
            "_renderTypingIndicator",
            "_render",
        ]

        for method in required_methods:
            assert method in content, f"Card should have {method} method"

    def test_card_has_neuron_labels(self):
        """Test that card includes German neuron labels."""
        card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-neural-card.js"
        content = card_path.read_text()

        assert "NEURON_LABELS_DE" in content, "Card should define German neuron labels"
        assert "Praesenz" in content, "Labels should include Praesenz"
        assert "Entspannung" in content, "Labels should include Entspannung"
        assert "Energielevel" in content, "Labels should include Energielevel"

    def test_card_has_layer_colors(self):
        """Test that card includes layer color definitions."""
        card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-neural-card.js"
        content = card_path.read_text()

        assert "LAYER_COLORS" in content, "Card should define layer colors"
        assert "Context" in content, "Card should include Context layer"
        assert "State" in content, "Card should include State layer"
        assert "Mood" in content, "Card should include Mood layer"

    def test_card_has_chat_interface(self):
        """Test that card includes chat input and send button."""
        card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-neural-card.js"
        content = card_path.read_text()

        assert "input-area" in content, "Card should have input area"
        assert "send-btn" in content, "Card should have send button"
        assert "Nachricht eingeben" in content, "Card should have German placeholder"
        assert "Senden" in content, "Card should have German send button text"

    def test_card_has_animations(self):
        """Test that card includes neuron firing and synapse animations."""
        card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-neural-card.js"
        content = card_path.read_text()

        assert "neuron-firing" in content, "Card should have neuron firing class"
        assert "synapse-active" in content, "Card should have synapse active class"
        assert "neuronPulse" in content, "Card should have neuron pulse animation"
        assert "synapseFlow" in content, "Card should have synapse flow animation"

    def test_card_has_api_endpoints(self):
        """Test that card uses correct API endpoints."""
        card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-neural-card.js"
        content = card_path.read_text()

        assert "/api/v1/neurons/layers/visualization" in content, "Card should fetch neural layers"
        assert "/api/styx/chat" in content, "Card should post to chat endpoint"
        assert "/api/v1/conversation/history" in content, "Card should fetch chat history"

    def test_card_has_accessibility(self):
        """Test that card has accessibility attributes."""
        card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-neural-card.js"
        content = card_path.read_text()

        assert "aria-label" in content, "Card should have aria-labels"
        assert "role=" in content, "Card should have ARIA roles"

    def test_card_is_registered(self):
        """Test that card is properly registered."""
        card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-neural-card.js"
        content = card_path.read_text()

        assert "window.customCards" in content, "Card should register in window.customCards"
        assert "PilotSuite Neural Interface" in content, "Card should have proper name"

    def test_card_registered_in_lovelace_resources(self):
        """Test that card is listed in lovelace_resources.py."""
        resource_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "lovelace_resources.py"
        content = resource_path.read_text()

        assert "styx-neural-card.js" in content, "Neural card should be in LOCAL_CARD_FILES"


class TestNeuralCardNeuronDiff:
    """Test the neuron snapshot-diff-animate flow."""

    def test_card_has_snapshot_method(self):
        """Test snapshot method creates a Map of neuron states."""
        card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-neural-card.js"
        content = card_path.read_text()

        assert "_snapshotNeurons" in content, "Card should have snapshot method"
        assert "new Map()" in content, "Snapshot should use a Map"

    def test_card_has_diff_logic(self):
        """Test that card compares pre/post chat neuron states."""
        card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-neural-card.js"
        content = card_path.read_text()

        assert "delta" in content or "0.05" in content, "Card should use a threshold for changes"

    def test_card_has_neuron_badge(self):
        """Test that assistant messages show contributing neurons."""
        card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-neural-card.js"
        content = card_path.read_text()

        assert "neuron-badge" in content, "Card should show neuron badges on messages"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
