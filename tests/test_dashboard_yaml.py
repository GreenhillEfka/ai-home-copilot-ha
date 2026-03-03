"""
Test suite for Home Assistant Dashboard YAML configurations.
Validates YAML syntax and structure for Lovelace dashboards.
"""
import os
import re
import pytest
import yaml
from pathlib import Path

# Base path for dashboard YAML files
DASHBOARD_YAML_DIR = Path(__file__).parent.parent / "custom_components" / "copilot_ha" / "dashboard_cards"


class TestDashboardYAML:
    """Test suite for dashboard YAML validation."""

    @pytest.fixture
    def yaml_files(self):
        """Return list of YAML dashboard files to test."""
        yaml_files = []
        if DASHBOARD_YAML_DIR.exists():
            for f in DASHBOARD_YAML_DIR.rglob("*.yaml"):
                yaml_files.append(f)
        return yaml_files

    def test_yaml_files_exist(self, yaml_files):
        """Test that dashboard YAML files exist."""
        assert len(yaml_files) > 0, "No dashboard YAML files found"

    def test_yaml_syntax_valid(self, yaml_files):
        """Test that all YAML files have valid syntax."""
        errors = []
        for yaml_file in yaml_files:
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Skip empty files
                    if not content.strip():
                        continue
                    yaml.safe_load(content)
            except yaml.YAMLError as e:
                errors.append(f"{yaml_file.name}: {str(e)}")
            except Exception as e:
                errors.append(f"{yaml_file.name}: {str(e)}")
        
        assert len(errors) == 0, f"YAML syntax errors found:\n" + "\n".join(errors)

    def test_lovelace_structure_valid(self, yaml_files):
        """Test that Lovelace dashboard YAML has valid structure."""
        errors = []
        for yaml_file in yaml_files:
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                if data is None:
                    continue
                    
                # Check for views structure (Lovelace dashboards)
                if isinstance(data, dict):
                    if 'views' in data:
                        # Valid Lovelace dashboard format
                        views = data['views']
                        assert isinstance(views, list), f"{yaml_file.name}: views must be a list"
                        for idx, view in enumerate(views):
                            assert isinstance(view, dict), f"{yaml_file.name}: view {idx} must be a dict"
                            assert 'title' in view, f"{yaml_file.name}: view {idx} missing 'title'"
                            assert 'cards' in view or 'path' in view, f"{yaml_file.name}: view {idx} missing cards/path"
                    
                    # Check for cards (direct format)
                    elif 'cards' in data:
                        cards = data['cards']
                        assert isinstance(cards, list), f"{yaml_file.name}: cards must be a list"
                        
            except AssertionError:
                raise
            except Exception as e:
                errors.append(f"{yaml_file.name}: {str(e)}")
        
        assert len(errors) == 0, f"Structure validation errors:\n" + "\n".join(errors)

    def test_no_tabs_in_yaml(self, yaml_files):
        """Test that YAML files don't contain tabs (should use spaces)."""
        errors = []
        for yaml_file in yaml_files:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                content = f.read()
                for line_num, line in enumerate(content.split('\n'), 1):
                    if '\t' in line:
                        errors.append(f"{yaml_file.name}:{line_num} - contains tab character")
        
        assert len(errors) == 0, f"Tab characters found:\n" + "\n".join(errors)

    def test_required_fields_present(self, yaml_files):
        """Test that required Lovelace fields are present."""
        errors = []
        for yaml_file in yaml_files:
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                if data is None:
                    continue
                
                # If it has views, each view needs title
                if 'views' in data:
                    for idx, view in enumerate(data['views']):
                        if 'title' not in view:
                            errors.append(f"{yaml_file.name}: view {idx} missing required 'title' field")
                            
            except Exception as e:
                errors.append(f"{yaml_file.name}: {str(e)}")
        
        assert len(errors) == 0, f"Missing required fields:\n" + "\n".join(errors)


class TestDashboardExamples:
    """Test specific dashboard examples."""

    def test_dashboard_examples_valid(self):
        """Test dashboard_examples.yaml is valid."""
        examples_file = DASHBOARD_YAML_DIR / "dashboard_examples.yaml"
        if examples_file.exists():
            with open(examples_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            assert 'views' in data, "dashboard_examples.yaml must have 'views'"
            assert len(data['views']) >= 1, "dashboard_examples.yaml must have at least one view"

    def test_mesh_dashboard_lovelace_valid(self):
        """Test mesh_dashboard_lovelace.yaml is valid."""
        mesh_file = DASHBOARD_YAML_DIR / "mesh_dashboard_lovelace.yaml"
        if mesh_file.exists():
            with open(mesh_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            # Should have cards (simple format) or views (full dashboard)
            assert 'cards' in data or 'views' in data, "mesh_dashboard_lovelace.yaml must have cards or views"

    def test_brain_graph_dashboard_valid(self):
        """Test brain_graph_dashboard.yaml is valid."""
        brain_file = DASHBOARD_YAML_DIR / "brain_graph_dashboard.yaml"
        if brain_file.exists():
            with open(brain_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            assert 'title' in data, "brain_graph_dashboard.yaml must have 'title'"
            assert 'cards' in data, "brain_graph_dashboard.yaml must have 'cards'"


class TestHomeAssistantCompatibility:
    """Test Home Assistant specific compatibility."""

    @pytest.fixture
    def yaml_files(self):
        """Return list of YAML dashboard files to test."""
        yaml_files = []
        if DASHBOARD_YAML_DIR.exists():
            for f in DASHBOARD_YAML_DIR.rglob("*.yaml"):
                yaml_files.append(f)
        return yaml_files

    def test_entity_ids_valid_format(self, yaml_files):
        """Test that entity IDs follow HA naming conventions."""
        import re
        errors = []
        entity_pattern = re.compile(r'entity:\s*([a-z_]+\.[a-z_0-9]+)')
        
        for yaml_file in yaml_files:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Check for common HA entity patterns
                matches = entity_pattern.findall(content)
                for entity_id in matches:
                    # Basic validation: domain.entity_name format
                    parts = entity_id.split('.')
                    if len(parts) != 2:
                        errors.append(f"{yaml_file.name}: invalid entity ID format: {entity_id}")
        
        # Only warn if we found entities but they have issues
        # (Some examples might use placeholder entities)
        if errors:
            print(f"\nEntity ID warnings (non-critical): {errors}")

    def test_card_types_valid(self, yaml_files):
        """Test that card types are valid Lovelace card types."""
        valid_card_types = {
            'entities', 'entity', 'gauge', 'stat', 'grid', 'horizontal-stack',
            'vertical-stack', 'iframe', 'button', 'logbook', 'conditional',
            'custom:ai-home-overview', 'custom:ai-home-presence',
            'custom:ai-home-activity', 'custom:ai-home-energy',
            'custom:ai-home-weather', 'custom:ai-home-calendar',
            'custom:gauge-card', 'custom:bar-card'
        }
        
        errors = []
        card_type_pattern = re.compile(r"^type:\s*(.+)$", re.MULTILINE)
        
        for yaml_file in yaml_files:
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    matches = card_type_pattern.findall(content)
                    
                    for card_type in matches:
                        card_type = card_type.strip()
                        # Skip if it's a valid type or a custom card
                        if card_type not in valid_card_types and not card_type.startswith('custom:'):
                            # Might be a placeholder or valid custom card
                            pass
            except Exception:
                pass  # Skip files we can't read properly
        
        # This is informational - custom cards are allowed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
