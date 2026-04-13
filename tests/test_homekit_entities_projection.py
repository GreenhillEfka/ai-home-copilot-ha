"""Projection contract for homekit_entities: pilotsuite unique_id parity."""
from __future__ import annotations

import ast
import pathlib

SRC = pathlib.Path("custom_components/pilotsuite/homekit_entities.py")
CONTENT = SRC.read_text()


class _Visitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.pilotsuite_unique_ids: list[str] = []
        self.copilot_ha_unique_ids: list[str] = []

    def visit_Assign(self, node: ast.Assign) -> None:
        for t in node.targets:
            if isinstance(t, ast.Attribute) and t.attr == "_attr_unique_id":
                val = self._extract_unique_id_value(node.value)
                if val is not None:
                    if "pilotsuite_homekit_" in val:
                        self.pilotsuite_unique_ids.append(val)
                    elif "copilot_ha_homekit_" in val:
                        self.copilot_ha_unique_ids.append(val)
        self.generic_visit(node)

    def _extract_unique_id_value(self, node: ast.expr) -> str | None:
        """Extract string value from a Constant, JoinedStr (f-string), or BinOp."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.JoinedStr):
            # f"pilotsuite_homekit_..." or f"copilot_ha_homekit_..."
            parts = []
            for v in node.values:
                if isinstance(v, ast.Constant) and isinstance(v.value, str):
                    parts.append(v.value)
                elif isinstance(v, ast.FormattedValue):
                    parts.append("<VAR>")
            return "".join(parts)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
            # "pilotsuite_homekit_toggle_%s" % zone_id
            left = self._extract_unique_id_value(node.left)
            return left if left else None
        return None


def _get_unique_ids(src: str) -> tuple[list[str], list[str]]:
    tree = ast.parse(src)
    v = _Visitor()
    v.visit(tree)
    return v.pilotsuite_unique_ids, v.copilot_ha_unique_ids


class TestHomeKitEntitiesUniqueIdParity:
    """Contract: homekit_entities unique_ids must use pilotsuite prefix."""

    def test_hk1_pilotsuite_homekit_toggle_unique_id(self) -> None:
        """HK1: HomeKitZoneToggleButton uses pilotsuite_homekit_toggle_ prefix."""
        pilotsuite, copilot_ha = _get_unique_ids(CONTENT)
        toggle_ids = [u for u in pilotsuite if "pilotsuite_homekit_toggle_" in u]
        assert len(toggle_ids) >= 1, (
            f"Expected pilotsuite_homekit_toggle_ unique_id(s), got pilotsuite={pilotsuite} copilot_ha={copilot_ha}"
        )

    def test_hk2_pilotsuite_homekit_qr_unique_id(self) -> None:
        """HK2: HomeKitZoneQRSensor uses pilotsuite_homekit_qr_ prefix."""
        pilotsuite, copilot_ha = _get_unique_ids(CONTENT)
        qr_ids = [u for u in pilotsuite if "pilotsuite_homekit_qr_" in u]
        assert len(qr_ids) >= 1, (
            f"Expected pilotsuite_homekit_qr_ unique_id(s), got pilotsuite={pilotsuite} copilot_ha={copilot_ha}"
        )

    def test_hk3_no_stale_copilot_ha_unique_ids(self) -> None:
        """HK3: AST scan confirms zero stale copilot_ha_homekit_ literals."""
        pilotsuite, copilot_ha = _get_unique_ids(CONTENT)
        stale = [u for u in copilot_ha if "homekit_" in u]
        assert stale == [], f"Found stale copilot_ha_homekit_ unique_ids: {stale}"
