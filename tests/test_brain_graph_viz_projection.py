"""
Source guard for brain_graph_viz.py (HA-397).
Ensures copilot_ha www paths and notification IDs are canonicalized
to pilotsuite.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = REPO_ROOT / "custom_components" / "pilotsuite" / "brain_graph_viz.py"


class TestBrainGraphVizProjection:
    """Projection contract for brain_graph_viz.py."""

    def test_bgv1_canonical_www_path_in_artifact(self) -> None:
        """brain_graph_viz must use /config/www/pilotsuite/ (not /config/www/copilot_ha/)."""
        source = ARTIFACT.read_text()
        assert "/config/www/pilotsuite/" in source, (
            "brain_graph_viz.py muss /config/www/pilotsuite/ (nicht /config/www/copilot_ha/) verwenden"
        )

    def test_bgv2_no_stale_copilot_ha_www_path(self) -> None:
        """brain_graph_viz must not reference /config/www/copilot_ha/."""
        source = ARTIFACT.read_text()
        assert "/config/www/copilot_ha/" not in source, (
            "brain_graph_viz.py darf /config/www/copilot_ha/ nicht mehr referenzieren"
        )

    def test_bgv3_canonical_notification_id(self) -> None:
        """brain_graph_viz must use notification_id='pilotsuite_brain_graph_viz'."""
        source = ARTIFACT.read_text()
        assert 'notification_id="pilotsuite_brain_graph_viz"' in source, (
            "brain_graph_viz.py muss notification_id='pilotsuite_brain_graph_viz' (nicht copilot_ha_*) verwenden"
        )

    def test_bgv4_no_stale_copilot_ha_notification_id(self) -> None:
        """brain_graph_viz must not use notification_id='copilot_ha_brain_graph_viz'."""
        source = ARTIFACT.read_text()
        assert 'notification_id="copilot_ha_brain_graph_viz"' not in source, (
            "brain_graph_viz.py darf notification_id='copilot_ha_brain_graph_viz' nicht mehr referenzieren"
        )

    def test_bgv5_canonical_local_url(self) -> None:
        """brain_graph_viz must use /local/pilotsuite/ URL for brain_graph_latest.html."""
        source = ARTIFACT.read_text()
        assert "/local/pilotsuite/brain_graph_latest.html" in source, (
            "brain_graph_viz.py muss /local/pilotsuite/brain_graph_latest.html (nicht /local/copilot_ha/) verwenden"
        )

    def test_bgv6_no_stale_copilot_ha_local_url(self) -> None:
        """brain_graph_viz must not use /local/copilot_ha/brain_graph_latest.html."""
        source = ARTIFACT.read_text()
        assert "/local/copilot_ha/brain_graph_latest.html" not in source, (
            "brain_graph_viz.py darf /local/copilot_ha/brain_graph_latest.html nicht mehr referenzieren"
        )