"""
Projection contract tests for media_entities unique_ids.
Verifies all unique_id strings use canonical pilotsuite prefix, not copilot_ha.
"""
import ast
import re

import pytest


class TestMediaEntitiesUniqueIds:
    """Source-Guard: media_entities unique_ids must use pilotsuite prefix."""

    def test_me1_music_active_unique_id(self):
        """ME1: MusicActiveBinarySensor unique_id uses pilotsuite prefix."""
        content = open("custom_components/pilotsuite/media_entities.py").read()
        assert 'unique_id="pilotsuite_music_active"' in content
        assert 'unique_id="copilot_ha_music_active"' not in content

    def test_me2_tv_active_unique_id(self):
        """ME2: TvActiveBinarySensor unique_id uses pilotsuite prefix."""
        content = open("custom_components/pilotsuite/media_entities.py").read()
        assert 'unique_id="pilotsuite_tv_active"' in content
        assert 'unique_id="copilot_ha_tv_active"' not in content

    def test_me3_music_now_playing_unique_id(self):
        """ME3: MusicNowPlayingSensor unique_id uses pilotsuite prefix."""
        content = open("custom_components/pilotsuite/media_entities.py").read()
        assert 'unique_id="pilotsuite_music_now_playing"' in content
        assert 'unique_id="copilot_ha_music_now_playing"' not in content

    def test_me4_music_primary_area_unique_id(self):
        """ME4: MusicPrimaryAreaSensor unique_id uses pilotsuite prefix."""
        content = open("custom_components/pilotsuite/media_entities.py").read()
        assert 'unique_id="pilotsuite_music_primary_area"' in content
        assert 'unique_id="copilot_ha_music_primary_area"' not in content

    def test_me5_tv_primary_area_unique_id(self):
        """ME5: TvPrimaryAreaSensor unique_id uses pilotsuite prefix."""
        content = open("custom_components/pilotsuite/media_entities.py").read()
        assert 'unique_id="pilotsuite_tv_primary_area"' in content
        assert 'unique_id="copilot_ha_tv_primary_area"' not in content

    def test_me6_tv_source_unique_id(self):
        """ME6: TvSourceSensor unique_id uses pilotsuite prefix."""
        content = open("custom_components/pilotsuite/media_entities.py").read()
        assert 'unique_id="pilotsuite_tv_source"' in content
        assert 'unique_id="copilot_ha_tv_source"' not in content

    def test_me7_music_active_count_unique_id(self):
        """ME7: MusicActiveCountSensor unique_id uses pilotsuite prefix."""
        content = open("custom_components/pilotsuite/media_entities.py").read()
        assert 'unique_id="pilotsuite_music_active_count"' in content
        assert 'unique_id="copilot_ha_music_active_count"' not in content

    def test_me8_tv_active_count_unique_id(self):
        """ME8: TvActiveCountSensor unique_id uses pilotsuite prefix."""
        content = open("custom_components/pilotsuite/media_entities.py").read()
        assert 'unique_id="pilotsuite_tv_active_count"' in content
        assert 'unique_id="copilot_ha_tv_active_count"' not in content

    def test_me9_no_stale_copilot_ha_literals(self):
        """ME9: AST scan confirms zero stale copilot_ha string literals remain."""
        content = open("custom_components/pilotsuite/media_entities.py").read()
        tree = ast.parse(content)

        class StaleVisitor(ast.NodeVisitor):
            def visit_Str(self, node):
                # Python <3.8
                if "copilot_ha" in node.s:
                    raise AssertionError(f"Stale copilot_ha literal found: {node.s!r}")
                self.generic_visit(node)

            def visit_Constant(self, node):
                if isinstance(node.value, str) and "copilot_ha" in node.value:
                    raise AssertionError(f"Stale copilot_ha literal found: {node.value!r}")
                self.generic_visit(node)

        try:
            StaleVisitor().visit(tree)
        except AssertionError:
            raise
        # Also check raw content for any copilot_ha strings
        assert "copilot_ha" not in content, "media_entities.py still contains copilot_ha strings"

    def test_me10_module_is_deprecated(self):
        """ME10: media_entities is marked DEPRECATED per project policy."""
        content = open("custom_components/pilotsuite/media_entities.py").read()
        assert "DEPRECATED" in content or "deprecation" in content.lower()
