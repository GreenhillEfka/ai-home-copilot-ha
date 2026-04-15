"""Contract tests for home_alerts_module.py hass.data key and STORAGE_KEY projection."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

SRC = Path("custom_components/pilotsuite/core/modules/home_alerts_module.py")
CONTENT = SRC.read_text()


class ASTKeyCollector(ast.NodeVisitor):
    """Collect STORAGE_KEY assignments and hass.data get/setdefault calls."""

    def __init__(self) -> None:
        self.storage_keys: list[str] = []
        self.hass_data_refs: list[str] = []

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "STORAGE_KEY":
                if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                    self.storage_keys.append(node.value.value)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        # match hass.data.setdefault("namespace", ...) or hass.data["namespace"]
        if isinstance(func, ast.Attribute):
            if func.attr in ("setdefault", "get"):
                if isinstance(func.value, ast.Attribute) and func.value.attr == "data":
                    for arg in node.args:
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                            self.hass_data_refs.append(arg.value)
                    for kw in node.keywords:
                        if kw.arg in ("default", "entry_id"):
                            pass
        # match hass.data["namespace"] direct subscript
        if isinstance(func, ast.Subscript):
            if isinstance(func.value, ast.Attribute) and func.value.attr == "data":
                if isinstance(func.slice, ast.Constant) and isinstance(func.slice.value, str):
                    self.hass_data_refs.append(func.slice.value)
        self.generic_visit(node)


def test_HA_module_1_canonical_storage_key() -> None:
    """HA-module-1: STORAGE_KEY uses pilotsuite namespace."""
    tree = ast.parse(CONTENT)
    collector = ASTKeyCollector()
    collector.visit(tree)
    for key in collector.storage_keys:
        assert key == "pilotsuite.home_alerts", (
            f"STORAGE_KEY '{key}' does not use canonical pilotsuite.home_alerts"
        )
    print(f"HA-module-1 passed: STORAGE_KEY = {collector.storage_keys}")


def test_HA_module_2_no_stale_copilot_ha_storage_key() -> None:
    """HA-module-2: No stale copilot_ha STORAGE_KEY literals remain."""
    tree = ast.parse(CONTENT)
    collector = ASTKeyCollector()
    collector.visit(tree)
    stale = [k for k in collector.storage_keys if "copilot_ha" in k]
    assert not stale, f"Stale copilot_ha STORAGE_KEY found: {stale}"
    print("HA-module-2 passed: no stale copilot_ha STORAGE_KEY")


def test_HA_module_3_canonical_hass_data_refs() -> None:
    """HA-module-3: hass.data refs use pilotsuite namespace."""
    tree = ast.parse(CONTENT)
    collector = ASTKeyCollector()
    collector.visit(tree)
    copilot_ha_refs = [r for r in collector.hass_data_refs if "copilot_ha" in r]
    assert not copilot_ha_refs, (
        f"Stale copilot_ha hass.data refs found: {copilot_ha_refs}"
    )
    pilotsuite_refs = [r for r in collector.hass_data_refs if "pilotsuite" in r]
    assert pilotsuite_refs, (
        f"Expected pilotsuite hass.data refs but found none; collected: {collector.hass_data_refs}"
    )
    print(f"HA-module-3 passed: hass.data refs = {collector.hass_data_refs}")


def test_HA_module_4_syntax() -> None:
    """HA-module-4: File has valid Python syntax."""
    try:
        ast.parse(CONTENT)
    except SyntaxError as exc:
        raise AssertionError(f"Syntax error in home_alerts_module.py: {exc}") from exc
    print("HA-module-4 passed: syntax OK")


def test_HA_module_5_docstring_entity_ids() -> None:
    """HA-module-5: Docstring entity ID examples use pilotsuite namespace."""
    # The module docstring references sensor entity IDs for the alerts and health sensors
    assert "sensor.pilotsuite_alerts" in CONTENT, (
        "Docstring should reference canonical sensor.pilotsuite_alerts"
    )
    assert "sensor.pilotsuite_health" in CONTENT, (
        "Docstring should reference canonical sensor.pilotsuite_health"
    )
    # Ensure no stale copilot_ha entity IDs remain in docstring
    stale_patterns = ["sensor.copilot_ha_alerts", "sensor.copilot_ha_health"]
    for pat in stale_patterns:
        assert pat not in CONTENT, f"Stale docstring entity ID found: {pat}"
    print("HA-module-5 passed: docstring entity IDs use pilotsuite namespace")


if __name__ == "__main__":
    test_HA_module_4_syntax()
    test_HA_module_1_canonical_storage_key()
    test_HA_module_2_no_stale_copilot_ha_storage_key()
    test_HA_module_3_canonical_hass_data_refs()
    print("4/4 contract tests passed")
    sys.exit(0)