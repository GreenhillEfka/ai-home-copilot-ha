"""Contract tests for user_preference_module.py STORAGE_KEY projection."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

SRC = Path("custom_components/pilotsuite/user_preference_module.py")
CONTENT = SRC.read_text()


class ASTStorageKeyCollector(ast.NodeVisitor):
    """Collect all STORAGE_KEY string assignments."""

    def __init__(self) -> None:
        self.keys: list[str] = []

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "STORAGE_KEY":
                if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                    self.keys.append(node.value.value)
        self.generic_visit(node)


def test_UP_module_1_canonical_storage_key() -> None:
    """UP-module-1: STORAGE_KEY uses pilotsuite namespace."""
    tree = ast.parse(CONTENT)
    collector = ASTStorageKeyCollector()
    collector.visit(tree)
    for key in collector.keys:
        assert key == "pilotsuite_user_preferences", (
            f"STORAGE_KEY '{key}' does not use canonical pilotsuite_user_preferences"
        )
    print(f"UP-module-1 passed: STORAGE_KEY = {collector.keys}")


def test_UP_module_2_no_stale_copilot_ha() -> None:
    """UP-module-2: No stale copilot_ha STORAGE_KEY literals remain."""
    tree = ast.parse(CONTENT)
    collector = ASTStorageKeyCollector()
    collector.visit(tree)
    stale = [k for k in collector.keys if "copilot_ha" in k]
    assert not stale, f"Stale copilot_ha STORAGE_KEY found: {stale}"
    print("UP-module-2 passed: no stale copilot_ha STORAGE_KEY")


def test_UP_module_3_syntax() -> None:
    """UP-module-3: File has valid Python syntax."""
    try:
        ast.parse(CONTENT)
    except SyntaxError as exc:
        raise AssertionError(f"Syntax error in user_preference_module.py: {exc}") from exc
    print("UP-module-3 passed: syntax OK")


if __name__ == "__main__":
    test_UP_module_3_syntax()
    test_UP_module_1_canonical_storage_key()
    test_UP_module_2_no_stale_copilot_ha()
    print("3/3 contract tests passed")
    sys.exit(0)