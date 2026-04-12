"""
Contract test: user_hints_card.py Projection Parity (HA-392)
============================================================
Source guard for custom_components/pilotsuite/dashboard_cards/user_hints_card.py
Verifies that service references use the canonical pilotsuite domain, not the legacy copilot_ha domain.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

# Path to the artifact under contract
ARTIFACT = Path(
    "custom_components/pilotsuite/dashboard_cards/user_hints_card.py"
)


class UH1_HINT_KONSISTENZ:
    """UH1: Service references in hint card configs must use canonical pilotsuite domain."""

    @staticmethod
    def guard() -> None:
        src = ARTIFACT.read_text(encoding="utf-8")
        # Ensure stale copilot_ha. service references are gone
        for line in src.splitlines():
            if "service:" in line or '"service"' in line:
                assert "copilot_ha." not in line, (
                    f"Stale copilot_ha. service reference found: {line.strip()}"
                )
        # Ensure canonical pilotsuite references are present for known hint services
        for svc in ["pilotsuite.accept_hint", "pilotsuite.reject_hint"]:
            assert svc in src, f"Canonical service reference '{svc}' must be present in artifact"


class UH2_HINT_KONSISTENZ:
    """UH2: No stale copilot_ha domain strings in the user hints card Python source."""

    @staticmethod
    def guard() -> None:
        src = ARTIFACT.read_text(encoding="utf-8")
        # Walk the AST to find all string constants containing copilot_ha
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                # Only flag bare copilot_ha references (not share/www paths which are legitimate legacy compat)
                if "copilot_ha" in node.value and not any(
                    safe in node.value for safe in ["www/copilot_ha", "/share/copilot_ha", "/config/copilot_ha"]
                ):
                    assert False, (
                        f"Stale copilot_ha reference at line {node.lineno}: {node.value!r}"
                    )


# ---------------------------------------------------------------------------
# Pytest glue
# ---------------------------------------------------------------------------

def test_uh1_service_refs_canonical() -> None:
    UH1_HINT_KONSISTENZ.guard()


def test_uh2_no_stale_copilot_ha_strings() -> None:
    UH2_HINT_KONSISTENZ.guard()