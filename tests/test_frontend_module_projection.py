"""Contract projection tests for frontend_module.py copilot_ha->pilotsuite parity."""
import ast
import sys
from pathlib import Path

import pytest

SRC = Path("custom_components/pilotsuite/core/modules/frontend_module.py")
MODULE = "custom_components.copotsuite.core.modules.frontend_module"


class TestFrontendModuleProjection:
    """HA-474: frontend_module.py docstring copilot_ha->pilotsuite parity."""

    def test_fm1_kanonische_pilotsuite_refresh_dashboard_in_docstrings(self):
        """Kanonische pilotsuite.refresh_dashboard in module docstring."""
        content = SRC.read_text()
        assert "pilotsuite.refresh_dashboard" in content
        assert "copilot_ha.refresh_dashboard" not in content

    def test_fm2_ast_scan_null_stale_copilot_ha_literale(self):
        """AST scan: null stale copilot_ha literals in frontend_module.py."""
        content = SRC.read_text()
        tree = ast.parse(content, filename=str(SRC))
        found = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if "copilot_ha" in node.value and "pilotsuite" not in node.value:
                    found.append(f"{node.value!r} at L{node.lineno}")
        assert not found, f"Stale copilot_ha literals: {found}"

    def test_fm3_syntax_ok(self):
        """Module compiles without syntax errors."""
        try:
            ast.parse(content := SRC.read_text(), filename=str(SRC))
        except SyntaxError as e:
            pytest.fail(f"SyntaxError at line {e.lineno}: {e.msg}")
        # additionally verify with compile
        with open(SRC) as fh:
            code = fh.read()
        compile(code, str(SRC), "exec")