"""Contract tests for brain_graph_dashboard.yaml and brain_graph_card.yaml projection parity.

HA-451 — brain_graph_dashboard.yaml and brain_graph_card.yaml copilot_ha → pilotsuite parity.
These are example/guidance YAML files that users add to their Lovelace config.
They contain stale copilot_ha references that must be canonically aligned.
"""
from __future__ import annotations

import pytest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


# ---------------------------------------------------------------------------
# BGD1: brain_graph_dashboard.yaml uses /local/pilotsuite/ not /local/copilot_ha/
# ---------------------------------------------------------------------------
def test_bgd1_lovelace_url_uses_pilotsuite_path() -> None:
    """BGD1: iframe url uses /local/pilotsuite/brain_graph_panel.html (not copilot_ha)."""
    path = Path("custom_components/pilotsuite/dashboard_cards/brain_graph_dashboard.yaml")
    content = path.read_text()
    assert "/local/pilotsuite/brain_graph_panel.html" in content
    assert "/local/copilot_ha/" not in content


# ---------------------------------------------------------------------------
# BGD2: brain_graph_card.yaml uses custom:styx-brain-card not custom:copilot_ha
# ---------------------------------------------------------------------------
def test_bgd2_card_type_uses_styx_brain_card() -> None:
    """BGD2: brain_graph_card uses custom:styx-brain-card (the pilotsuite card)."""
    path = Path("custom_components/pilotsuite/dashboard_cards/brain_graph_card.yaml")
    content = path.read_text()
    assert "custom:styx-brain-card" in content
    assert "custom:copilot_ha" not in content


# ---------------------------------------------------------------------------
# BGD3: no stale copilot_ha literals remain in either file
# ---------------------------------------------------------------------------
def test_bgd3_no_stale_copilot_ha_strings() -> None:
    """BGD3: zero stale copilot_ha literals remain in brain_graph dashboard/card YAMLs."""
    paths = [
        Path("custom_components/pilotsuite/dashboard_cards/brain_graph_dashboard.yaml"),
        Path("custom_components/pilotsuite/dashboard_cards/brain_graph_card.yaml"),
    ]
    for path in paths:
        content = path.read_text()
        assert "copilot_ha" not in content, f"{path}: stale copilot_ha literal found"
