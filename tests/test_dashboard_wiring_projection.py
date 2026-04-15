"""Contract tests for dashboard_wiring.py projection surface.

Guard: dashboard_wiring.py notification_id and block marker must reference
'pilotsuite', never 'copilot_ha', per PS-151 canonical naming policy.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_WIRING_PATH = REPO_ROOT / "custom_components" / "pilotsuite" / "dashboard_wiring.py"


class TestDashboardWiringProjection:
    """Projection surface guard for dashboard_wiring.py."""

    def test_notification_id_uses_pilotsuite(self) -> None:
        """DW1: _NOTIFICATION_ID must use pilotsuite prefix, not copilot_ha."""
        content = DASHBOARD_WIRING_PATH.read_text()
        for line in content.splitlines():
            if "_NOTIFICATION_ID" in line and "=" in line:
                assert "pilotsuite" in line, f"Expected pilotsuite in _NOTIFICATION_ID, got: {line!r}"
                assert "copilot_ha" not in line, f"Unexpected copilot_ha in _NOTIFICATION_ID: {line!r}"
                break

    def test_automated_block_marker_uses_pilotsuite(self) -> None:
        """DW2: _AUTOMATED_BLOCK_MARKER must reference pilotsuite, not copilot_ha."""
        content = DASHBOARD_WIRING_PATH.read_text()
        for line in content.splitlines():
            if "_AUTOMATED_BLOCK_MARKER" in line and "=" in line:
                assert "pilotsuite" in line, f"Expected pilotsuite in _AUTOMATED_BLOCK_MARKER, got: {line!r}"
                assert "copilot_ha" not in line, f"Unexpected copilot_ha in _AUTOMATED_BLOCK_MARKER: {line!r}"
                break

    def test_no_stale_copilot_ha_hardcodes(self) -> None:
        """DW3: AST scan — no unexplained copilot_ha string literals in dashboard_wiring.py.

        Legitimate exceptions (legacy fallback lookups for entity resolution):
        - button.copilot_ha_*  / button.pilotsuite_*  (entity ID prefixes, runtime choice)
        All other copilot_ha literals are stale drift.
        """
        content = DASHBOARD_WIRING_PATH.read_text()
        tree = ast.parse(content)

        violations: list[str] = []
        LEGIT_LINES = {341, 342}

        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if "copilot_ha" in node.value:
                    lineno = getattr(node, "lineno", None)
                    if lineno and lineno not in LEGIT_LINES:
                        violations.append(f"line {lineno}: {node.value!r}")

        assert not violations, (
            "Stale copilot_ha literals found outside known-good legacy fallback zones:\n"
            + "\n".join(violations)
        )

    def test_sensor_fallbacks_use_pilotsuite_only(self) -> None:
        """DW4: sensor entity fallbacks in dashboard_wiring.py use pilotsuite names only."""
        content = DASHBOARD_WIRING_PATH.read_text()
        lines = content.splitlines()

        for lineno, line in enumerate(lines, start=1):
            if "sensor.pilotsuite_mood" in line or "sensor.pilotsuite_brain_graph" in line or "sensor.pilotsuite_habitus" in line:
                if "sensor.copilot_ha_" in line:
                    assert False, (
                        f"Stale copilot_ha sensor fallback at line {lineno}: {line.strip()!r}; "
                        "all sensor fallbacks must use only pilotsuite-prefixed names"
                    )
        for lineno, line in enumerate(lines, start=1):
            if "sensor.copilot_ha_" in line:
                assert False, f"Stale sensor.copilot_ha_ reference at line {lineno}: {line.strip()!r}"