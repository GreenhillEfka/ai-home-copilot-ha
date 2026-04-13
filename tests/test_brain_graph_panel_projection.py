"""Brain Graph Panel Projection Guard — HA-395.

Verifies the brain_graph_panel.py uses canonical PilotSuite www paths
and notification IDs, not legacy copilot_ha paths.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = REPO_ROOT / "custom_components" / "pilotsuite" / "brain_graph_panel.py"


class TestBrainGraphPanelProjection:
    """Projection contract for brain_graph_panel.py."""

    def test_bgp1_canonical_notification_id(self) -> None:
        """BGP1: notification_id uses pilotsuite_brain_graph_panel not copilot_ha."""
        content = ARTIFACT.read_text()
        assert 'notification_id="pilotsuite_brain_graph_panel"' in content
        assert content.count('notification_id="copilot_ha_brain_graph_panel"') == 0

    def test_bgp2_canonical_www_path(self) -> None:
        """BGP2: panel is written to /config/www/pilotsuite/ not /config/www/copilot_ha/."""
        content = ARTIFACT.read_text()
        assert '/config/www/pilotsuite/brain_graph_panel.html' in content
        assert '/config/www/copilot_ha/brain_graph_panel.html' not in content

    def test_bgp3_canonical_local_url(self) -> None:
        """BGP3: Lovelace URL uses /local/pilotsuite/ not /local/copilot_ha/."""
        content = ARTIFACT.read_text()
        assert '/local/pilotsuite/brain_graph_panel.html' in content
        assert '/local/copilot_ha/brain_graph_panel.html' not in content

    def test_bgp4_no_stale_copilot_ha_strings(self) -> None:
        """BGP4: zero stale copilot_ha path/id strings remain in brain_graph_panel.py."""
        content = ARTIFACT.read_text()
        # Only allow LEGACY_DOMAIN references in comments or as plain strings
        # not in paths/URLs/notification_ids
        stale_patterns = [
            'copilot_ha_brain_graph_panel',
            '/www/copilot_ha/',
            '/local/copilot_ha/',
        ]
        for pattern in stale_patterns:
            assert pattern not in content, f"stale legacy pattern still present: {pattern}"

    def test_bgp5_www_path_in_code_context(self) -> None:
        """BGP5: /config/www/pilotsuite path appears in actual Path construction."""
        content = ARTIFACT.read_text()
        # Verify the path is in a Path() call, not just a comment
        assert re.search(r'Path\s*\(\s*["\']/config/www/pilotsuite/', content)
