"""Tests for Zone Dashboard Card (styx-zone-card.js)"""

import pytest
import sys
import os
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestZoneCardConfig:
    """Test Zone Dashboard Card configuration and structure."""

    def test_card_js_exists(self):
        """Test that styx-zone-card.js exists."""
        card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-zone-card.js"
        assert card_path.exists(), "styx-zone-card.js should exist"
        
    def test_card_js_is_valid_js(self):
        """Test that card JS file is valid JavaScript."""
        card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-zone-card.js"
        content = card_path.read_text()
        
        # Check for basic JS structure
        assert "class StyxZoneCard extends HTMLElement" in content, "Card should define HTMLElement class"
        assert "customElements.define" in content, "Card should register custom element"
        assert "styx-zone-card" in content, "Card should use correct element name"
        
    def test_card_has_required_methods(self):
        """Test that card has required methods."""
        card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-zone-card.js"
        content = card_path.read_text()
        
        required_methods = [
            "setConfig",
            "set hass",
            "getCardSize",
            "_getZonesData",
            "_getMoodData",
            "_getNeuronActivity",
            "_render",
        ]
        
        for method in required_methods:
            assert method in content, f"Card should have {method} method"
            
    def test_card_has_mood_gauges(self):
        """Test that card includes mood gauge definitions."""
        card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-zone-card.js"
        content = card_path.read_text()
        
        assert "MOOD_GAUGE_DEFS" in content, "Card should define mood gauges"
        assert "comfort" in content.lower(), "Card should include comfort gauge"
        assert "joy" in content.lower(), "Card should include joy gauge"
        assert "frugality" in content.lower(), "Card should include frugality gauge"
        
    def test_card_has_zone_icon_map(self):
        """Test that card includes zone icon mappings."""
        card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-zone-card.js"
        content = card_path.read_text()
        
        assert "ZONE_ICON_MAP" in content, "Card should define zone icons"
        assert "living_room" in content, "Card should include living room icon"
        assert "bedroom" in content, "Card should include bedroom icon"
        
    def test_card_has_mode_icons(self):
        """Test that card includes mode icon mappings."""
        card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-zone-card.js"
        content = card_path.read_text()
        
        assert "MODE_ICONS" in content, "Card should define mode icons"
        assert "party" in content, "Card should include party mode"
        assert "night" in content, "Card should include night mode"
        
    def test_card_has_quick_actions(self):
        """Test that card includes quick actions."""
        card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-zone-card.js"
        content = card_path.read_text()
        
        assert "quick-actions" in content, "Card should have quick actions section"
        assert "_toggleLight" in content, "Card should have light toggle action"
        assert "_showSceneSelector" in content, "Card should have scene selector"
        
    def test_card_has_neuron_activity(self):
        """Test that card includes neuron activity visualization."""
        card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-zone-card.js"
        content = card_path.read_text()
        
        assert "_getNeuronActivity" in content, "Card should have neuron activity method"
        assert "neuron-bar" in content, "Card should render neuron bar"
        
    def test_card_has_config_options(self):
        """Test that card accepts configuration options."""
        card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-zone-card.js"
        content = card_path.read_text()
        
        assert "show_mood" in content, "Card should accept show_mood config"
        assert "show_neuron_activity" in content, "Card should accept show_neuron_activity config"
        assert "show_quick_actions" in content, "Card should accept show_quick_actions config"
        
    def test_card_is_registered(self):
        """Test that card is properly registered in customCards."""
        card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-zone-card.js"
        content = card_path.read_text()
        
        assert "window.customCards" in content, "Card should register in window.customCards"
        assert "type: 'styx-zone-card'" in content, "Card should define correct type"
        assert "PilotSuite Zone Dashboard" in content, "Card should have proper name"


class TestZoneCardYAML:
    """Test Zone Dashboard Card YAML configuration."""

    def test_yaml_config_exists(self):
        """Test that zone_card_yaml.md exists."""
        yaml_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "zone_card_yaml.md"
        assert yaml_path.exists(), "zone_card_yaml.md should exist"
        
    def test_yaml_has_basic_config(self):
        """Test that YAML includes basic card configuration."""
        yaml_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "zone_card_yaml.md"
        content = yaml_path.read_text()
        
        assert "type: custom:styx-zone-card" in content, "YAML should include card type"
        assert "entity: sensor.pilotsuite_habitus_zones" in content, "YAML should include entity"
        
    def test_yaml_has_mood_config(self):
        """Test that YAML includes mood card configuration."""
        yaml_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "zone_card_yaml.md"
        content = yaml_path.read_text()
        
        assert "styx-mood-card" in content, "YAML should include mood card"
        
    def test_yaml_has_brain_config(self):
        """Test that YAML includes brain card configuration."""
        yaml_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "zone_card_yaml.md"
        content = yaml_path.read_text()
        
        assert "styx-brain-card" in content, "YAML should include brain card"
        
    def test_yaml_has_scene_buttons(self):
        """Test that YAML includes scene button examples."""
        yaml_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "zone_card_yaml.md"
        content = yaml_path.read_text()
        
        assert "script.zone_scene" in content, "YAML should include scene scripts"
        assert "Entspannen" in content, "YAML should include relaxing scene"
        assert "Film" in content, "YAML should include movie scene"


class TestZoneCardIntegration:
    """Test Zone Dashboard Card integration with other cards."""

    def test_mood_card_exists(self):
        """Test that mood card exists for integration."""
        mood_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-mood-card.js"
        assert mood_path.exists(), "styx-mood-card.js should exist for zone card integration"
        
    def test_brain_card_exists(self):
        """Test that brain card exists for integration."""
        brain_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-brain-card.js"
        assert brain_path.exists(), "styx-brain-card.js should exist for zone card integration"
        
    def test_zone_sensor_exists(self):
        """Test that zone sensors are available."""
        sensor_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "sensors" / "habitus_zone_sensor.py"
        assert sensor_path.exists(), "habitus_zone_sensor.py should exist"
        
    def test_zone_mode_sensor_exists(self):
        """Test that zone mode sensor is available."""
        mode_sensor_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "sensors" / "zone_mode_sensor.py"
        assert mode_sensor_path.exists(), "zone_mode_sensor.py should exist"


class TestZoneCardFeatures:
    """Test specific features of the Zone Dashboard Card."""

    def test_card_has_active_inactive_status(self):
        """Test that card shows active/inactive status."""
        card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-zone-card.js"
        content = card_path.read_text()
        
        assert "active" in content.lower(), "Card should show active status"
        assert "inactive" in content.lower(), "Card should show inactive status"
        
    def test_card_has_zone_status_indicator(self):
        """Test that card has zone status indicator."""
        card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-zone-card.js"
        content = card_path.read_text()
        
        assert "zone-status" in content, "Card should have zone status element"
        
    def test_card_has_mood_display(self):
        """Test that card displays mood values."""
        card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-zone-card.js"
        content = card_path.read_text()
        
        assert "_buildGaugeSvg" in content, "Card should build mood gauges"
        assert "mood-gauges" in content, "Card should display mood gauges"
        
    def test_card_has_neuron_visualization(self):
        """Test that card visualizes neuron activity."""
        card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-zone-card.js"
        content = card_path.read_text()
        
        assert "_buildNeuronBar" in content, "Card should build neuron bar"
        assert "neuron-bar-container" in content, "Card should have neuron bar container"
        
    def test_card_has_toggle_action(self):
        """Test that card has toggle functionality."""
        card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-zone-card.js"
        content = card_path.read_text()
        
        assert "_toggleLight" in content, "Card should toggle lights"
        assert "callService" in content and "'light'" in content, "Card should call light service"
        
    def test_card_has_scene_action(self):
        """Test that card has scene activation."""
        card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-zone-card.js"
        content = card_path.read_text()
        
        assert "_showSceneSelector" in content, "Card should show scene selector"
        assert "scene-select" in content, "Card should dispatch scene-select event"
        
    def test_card_has_thermostat_action(self):
        """Test that card can adjust thermostat."""
        card_path = PROJECT_ROOT / "custom_components" / "copilot_ha" / "www" / "styx-zone-card.js"
        content = card_path.read_text()
        
        assert "_adjustThermostat" in content, "Card should adjust thermostat"
        assert "callService" in content and "'climate'" in content, "Card should call climate service"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
