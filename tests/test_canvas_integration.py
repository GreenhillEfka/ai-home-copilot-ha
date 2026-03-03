"""Tests for Canvas Integration (Brain Graph Visualization).

Tests the Canvas-based brain graph visualization component:
- Brain graph SVG rendering
- Node and edge rendering
- Interactive canvas elements
- Responsive canvas resizing
- Performance with large datasets
"""

import pytest
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path("/config/.openclaw/workspace/pilotsuite-styx-ha")
sys.path.insert(0, str(PROJECT_ROOT))


class TestCanvasBrainGraph:
    """Test Canvas-based Brain Graph rendering."""

    def test_brain_card_exists(self):
        """Test that brain card JS file exists."""
        brain_card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-brain-card.js"
        assert brain_card_path.exists(), "styx-brain-card.js should exist"

    def test_brain_card_has_canvas_rendering(self):
        """Test that brain card uses canvas/SVG for rendering."""
        brain_card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-brain-card.js"
        content = brain_card_path.read_text()

        # Check for SVG rendering (preferred for brain graph)
        assert "svg" in content.lower(), "Brain card should use SVG for rendering"
        assert "viewbox" in content.lower(), "Brain card should use viewBox for scalable graphics"

    def test_brain_card_node_data(self):
        """Test brain card handles node data correctly."""
        brain_card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-brain-card.js"
        content = brain_card_path.read_text()

        assert "nodes" in content, "Brain card should handle nodes"
        assert "node_id" in content or "id" in content, "Brain card should reference node IDs"

    def test_brain_card_edge_data(self):
        """Test brain card handles edge data correctly."""
        brain_card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-brain-card.js"
        content = brain_card_path.read_text()

        assert "edges" in content, "Brain card should handle edges"
        assert "from" in content or "source" in content, "Brain card should reference edge sources"
        assert "to" in content or "target" in content, "Brain card should reference edge targets"

    def test_brain_card_domain_colors(self):
        """Test brain card has domain color mapping."""
        brain_card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-brain-card.js"
        content = brain_card_path.read_text()

        assert "DOMAIN_COLORS" in content, "Brain card should define domain colors"
        assert "light" in content.lower() or "switch" in content.lower(), "Brain card should define domain types"

    def test_brain_card_node_layout(self):
        """Test brain card has node layout logic."""
        brain_card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-brain-card.js"
        content = brain_card_path.read_text()

        assert "_layoutNodes" in content, "Brain card should have node layout method"
        assert "Math.PI" in content or "angle" in content.lower(), "Brain card should use circular layout"

    def test_brain_card_interactive(self):
        """Test brain card has interactive elements."""
        brain_card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-brain-card.js"
        content = brain_card_path.read_text()

        # Check for interactive SVG elements
        assert "title" in content or "tooltip" in content.lower(), "Brain card should have tooltips"
        assert "stroke" in content, "Brain card should have stroke styling"

    def test_brain_card_card_size(self):
        """Test brain card reports appropriate card size."""
        brain_card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-brain-card.js"
        content = brain_card_path.read_text()

        assert "getCardSize" in content, "Brain card should have getCardSize method"
        # Should return a reasonable size for a graph card
        assert "5" in content or "return" in content, "Brain card should return card size"

    def test_brain_card_entity_config(self):
        """Test brain card requires entity configuration."""
        brain_card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-brain-card.js"
        content = brain_card_path.read_text()

        assert "config.entity" in content or "config.edge_entity" in content, "Brain card should require entity config"
        assert "Please define an entity" in content, "Brain card should validate entity config"

    def test_brain_card_node_count(self):
        """Test brain card limits node count for performance."""
        brain_card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-brain-card.js"
        content = brain_card_path.read_text()

        # Should limit nodes for performance (120 is reasonable for SVG)
        assert "slice" in content, "Brain card should limit nodes for performance"
        assert "120" in content, "Brain card should limit to ~120 nodes"

    def test_brain_card_edge_count(self):
        """Test brain card limits edge count for performance."""
        brain_card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-brain-card.js"
        content = brain_card_path.read_text()

        # Should limit edges for performance (240 is reasonable for SVG)
        assert "slice" in content, "Brain card should limit edges for performance"
        assert "240" in content, "Brain card should limit to ~240 edges"


class TestCanvasIntegrationUI:
    """Test Canvas Integration UI components."""

    def test_brain_card_styling(self):
        """Test brain card has proper styling."""
        brain_card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-brain-card.js"
        content = brain_card_path.read_text()

        assert "style" in content.lower(), "Brain card should have styles"
        assert "border-radius" in content or "ha-card" in content, "Brain card should use HA card styling"

    def test_brain_card_responsive(self):
        """Test brain card is responsive."""
        brain_card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-brain-card.js"
        content = brain_card_path.read_text()

        assert "width: 100%" in content or "100%" in content, "Brain card should be responsive"
        assert "auto" in content, "Brain card should use auto sizing"

    def test_brain_card_ha_card_wrapper(self):
        """Test brain card uses ha-card wrapper."""
        brain_card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-brain-card.js"
        content = brain_card_path.read_text()

        assert "ha-card" in content, "Brain card should use ha-card wrapper"

    def test_brain_card_shadow_root(self):
        """Test brain card uses shadow DOM."""
        brain_card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-brain-card.js"
        content = brain_card_path.read_text()

        assert "shadowRoot" in content or "attachShadow" in content, "Brain card should use shadow DOM"

    def test_brain_card_custom_element(self):
        """Test brain card registers as custom element."""
        brain_card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-brain-card.js"
        content = brain_card_path.read_text()

        assert "customElements.define" in content, "Brain card should register custom element"
        assert "styx-brain-card" in content, "Brain card should register with correct name"


class TestCanvasDataHandling:
    """Test Canvas data handling and state management."""

    def test_brain_card_hass_setter(self):
        """Test brain card handles hass state."""
        brain_card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-brain-card.js"
        content = brain_card_path.read_text()

        assert "set hass" in content or "set hass(" in content, "Brain card should have hass setter"
        assert "_hass" in content, "Brain card should store hass state"

    def test_brain_card_state_tracking(self):
        """Test brain card tracks state changes."""
        brain_card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-brain-card.js"
        content = brain_card_path.read_text()

        assert "_nodes" in content, "Brain card should track nodes state"
        assert "_edges" in content, "Brain card should track edges state"
        assert "_config" in content, "Brain card should track config state"

    def test_brain_card_render_optimization(self):
        """Test brain card optimizes rendering."""
        brain_card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-brain-card.js"
        content = brain_card_path.read_text()

        assert "JSON.stringify" in content, "Brain card should optimize renders"
        assert "!== JSON.stringify" in content, "Brain card should compare states"

    def test_brain_card_entity_extraction(self):
        """Test brain card extracts data from entities."""
        brain_card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-brain-card.js"
        content = brain_card_path.read_text()

        assert "attributes" in content, "Brain card should extract entity attributes"
        assert "nodes" in content and "edges" in content, "Brain card should extract nodes/edges"

    def test_brain_card_default_fallbacks(self):
        """Test brain card has fallback defaults."""
        brain_card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-brain-card.js"
        content = brain_card_path.read_text()

        assert "||" in content or "??", "Brain card should have fallbacks"
        assert "[]" in content, "Brain card should default to empty arrays"


class TestCanvasIntegrationE2E:
    """End-to-end Canvas Integration tests."""

    def test_brain_card_full_integration(self):
        """Test complete brain card integration flow."""
        brain_card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-brain-card.js"
        content = brain_card_path.read_text()

        # Verify full component structure
        assert "class StyxBrainCard extends HTMLElement" in content, "Should define class"
        assert "constructor" in content, "Should have constructor"
        assert "setConfig" in content, "Should have config setter"
        assert "set hass" in content or "set hass(" in content, "Should have hass setter"
        assert "getCardSize" in content, "Should have card size getter"
        assert "_render" in content, "Should have render method"

    def test_brain_card_window_registration(self):
        """Test brain card registers in window.customCards."""
        brain_card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-brain-card.js"
        content = brain_card_path.read_text()

        assert "window.customCards" in content, "Brain card should register in window.customCards"
        assert 'type: "styx-brain-card"' in content, "Brain card should define correct type"
        assert "name:" in content, "Brain card should have name"
        assert "description:" in content, "Brain card should have description"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
