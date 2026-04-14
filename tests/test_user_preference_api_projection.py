"""Contract tests for user_preference.py api: name projection."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

SRC = Path("custom_components/pilotsuite/api/user_preference.py")
CONTENT = SRC.read_text()


class ASTNameCollector(ast.NodeVisitor):
    """Collect all 'name = ' string assignments from HomeAssistantView subclasses."""

    def __init__(self) -> None:
        self.names: list[str] = []
        self._in_view = False

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        # Only visit view subclasses (contain HomeAssistantView)
        for base in node.bases:
            if isinstance(base, ast.Name) and "View" in base.id:
                self._in_view = True
                self.generic_visit(node)
                self._in_view = False
        # Do not recurse into non-view classes

    def visit_Assign(self, node: ast.Assign) -> None:
        if not self._in_view:
            return
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "name":
                if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                    self.names.append(node.value.value)


def test_UP1_canonical_pilotsuite_names() -> None:
    """UP1: All view name attributes use the pilotsuite API namespace."""
    tree = ast.parse(CONTENT)
    collector = ASTNameCollector()
    collector.visit(tree)
    for name in collector.names:
        assert name.startswith("api:pilotsuite:"), (
            f"View name '{name}' does not use api:pilotsuite: namespace"
        )
    print(f"UP1 passed: {len(collector.names)} view name(s) all api:pilotsuite:")


def test_UP2_no_stale_copilot_ha() -> None:
    """UP2: No stale 'copilot_ha' view-name literals remain."""
    tree = ast.parse(CONTENT)
    collector = ASTNameCollector()
    collector.visit(tree)
    stale = [n for n in collector.names if "copilot_ha" in n]
    assert not stale, f"Stale copilot_ha view names found: {stale}"
    print("UP2 passed: no stale copilot_ha view names")


def test_UP3_syntax() -> None:
    """UP3: File has valid Python syntax."""
    try:
        ast.parse(CONTENT)
    except SyntaxError as exc:
        raise AssertionError(f"Syntax error in user_preference.py: {exc}") from exc
    print("UP3 passed: syntax OK")


if __name__ == "__main__":
    test_UP3_syntax()
    test_UP1_canonical_pilotsuite_names()
    test_UP2_no_stale_copilot_ha()
    print("3/3 contract tests passed")
    sys.exit(0)
