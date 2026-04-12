"""
Contract test: interactive_dashboard.py Projection Parity (HA-392)
===================================================================
Source guard for custom_components/pilotsuite/dashboard_cards/interactive/interactive_dashboard.py
Verifies that service references use the canonical pilotsuite domain, not the legacy copilot_ha domain.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

# Path to the artifact under contract
ARTIFACT = Path(
    "custom_components/pilotsuite/dashboard_cards/interactive/interactive_dashboard.py"
)


class ID1_HINT_PATH_KONSISTENZ:
    """ID1: Path header in docstring must reference canonical pilotsuite path."""

    @staticmethod
    def guard() -> None:
        src = ARTIFACT.read_text(encoding="utf-8")
        assert "custom_components/pilotsuite/dashboard_cards/" in src, (
            "Docstring path header must reference 'custom_components/pilotsuite/dashboard_cards/', "
            "not 'custom_components/copilot_ha/dashboard_cards/'"
        )
        assert "custom_components/copilot_ha/dashboard_cards/" not in src, (
            "Stale copilot_ha path reference found in docstring"
        )


class ID2_HINT_KONSISTENZ:
    """ID2: Service references in card configs must use canonical pilotsuite domain."""

    @staticmethod
    def guard() -> None:
        src = ARTIFACT.read_text(encoding="utf-8")
        # Ensure stale copilot_ha. service references are gone
        for line in src.splitlines():
            if "service:" in line or '"service"' in line:
                assert "copilot_ha." not in line, (
                    f"Stale copilot_ha. service reference found: {line.strip()}"
                )
        # Ensure canonical pilotsuite references are present for known services
        for svc in ["pilotsuite.toggle_neuron", "pilotsuite.refresh_neuron", "pilotsuite.disable_neuron"]:
            assert svc in src, f"Canonical service reference '{svc}' must be present in artifact"


class ID3_HINT_KONSISTENZ:
    """ID3: No stale copilot_ha domain strings in the interactive dashboard Python source."""

    @staticmethod
    def guard() -> None:
        src = ARTIFACT.read_text(encoding="utf-8")
        # Walk the AST to find all string constants
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                assert "copilot_ha" not in node.value or "www/copilot_ha" in node.value, (
                    f"Stale copilot_ha reference at line {node.lineno}: {node.value!r}"
                )


# ---------------------------------------------------------------------------
# Pytest glue
# ---------------------------------------------------------------------------

def test_id1_path_header_canonical() -> None:
    ID1_HINT_PATH_KONSISTENZ.guard()


def test_id2_service_refs_canonical() -> None:
    ID2_HINT_KONSISTENZ.guard()


def test_id3_no_stale_copilot_ha_strings() -> None:
    ID3_HINT_KONSISTENZ.guard()