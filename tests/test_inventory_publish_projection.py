"""Contract tests for inventory_publish.py projection surface.

Guard: inventory_publish.py www paths, URL prefixes, and notification_id
must reference 'pilotsuite', never 'copilot_ha', per PS-151 canonical naming policy.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PUBLISH_PATH = REPO_ROOT / "custom_components" / "pilotsuite" / "inventory_publish.py"


class TestInventoryPublishProjection:
    """Projection surface guard for inventory_publish.py."""

    def test_www_dir_uses_pilotsuite(self) -> None:
        """IP1: www directory must use pilotsuite prefix, not copilot_ha."""
        content = INVENTORY_PUBLISH_PATH.read_text()
        # www_dir assignment must use pilotsuite
        for line in content.splitlines():
            if "www_dir" in line and "Path" in line and "www" in line:
                assert "pilotsuite" in line, f"Expected pilotsuite in www_dir assignment, got: {line!r}"
                assert "copilot_ha" not in line, f"Unexpected copilot_ha in www_dir assignment: {line!r}"
                break

    def test_url_prefix_uses_pilotsuite(self) -> None:
        """IP2: URL prefix must use pilotsuite, not copilot_ha."""
        content = INVENTORY_PUBLISH_PATH.read_text()
        for line in content.splitlines():
            if "/local/" in line and "f\"" in line:
                # Must use pilotsuite URL prefix
                assert "pilotsuite" in line, f"Expected pilotsuite in /local URL prefix, got: {line!r}"
                assert "copilot_ha" not in line, f"Unexpected copilot_ha in URL prefix: {line!r}"
                break

    def test_notification_id_uses_pilotsuite(self) -> None:
        """IP3: notification_id must use pilotsuite prefix, not copilot_ha."""
        content = INVENTORY_PUBLISH_PATH.read_text()
        for line in content.splitlines():
            if "notification_id" in line and "=" in line:
                assert "pilotsuite" in line, f"Expected pilotsuite in notification_id, got: {line!r}"
                assert "copilot_ha" not in line, f"Unexpected copilot_ha in notification_id: {line!r}"
                break

    def test_no_stale_copilot_ha_hardcodes(self) -> None:
        """IP4: AST scan — no unexplained copilot_ha string literals in inventory_publish.py."""
        content = INVENTORY_PUBLISH_PATH.read_text()
        tree = ast.parse(content)

        violations: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if "copilot_ha" in node.value:
                    lineno = getattr(node, "lineno", None)
                    violations.append(f"line {lineno}: {node.value!r}")

        assert not violations, (
            "Stale copilot_ha literals found in inventory_publish.py:\n"
            + "\n".join(violations)
        )