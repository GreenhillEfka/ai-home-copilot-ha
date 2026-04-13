"""Projection test for search_integration docstring service references."""
import ast
from pathlib import Path

ROOT = Path("/config/clawd/team/worktrees/pilotsuite-styx-ha-current/custom_components/pilotsuite")
SRC = ROOT / "search_integration.py"


class TestSearchIntegrationCanonical:
    """Contract tests for service name references in search_integration.py docstring."""

    def test_docstring_service_references_use_pilotsuite(self):
        """Docstring service names must reference pilotsuite, not copilot_ha."""
        src_text = SRC.read_text()
        assert "- pilotsuite.search - Perform search" in src_text, (
            f"Docstring must reference pilotsuite.search, found copilot_ha references:\n"
            f"{[l for l in src_text.splitlines() if 'copilot_ha' in l]}"
        )
        assert "- pilotsuite.index_search - Update search index" in src_text, (
            f"Docstring must reference pilotsuite.index_search, found copilot_ha references:\n"
            f"{[l for l in src_text.splitlines() if 'copilot_ha' in l]}"
        )

    def test_no_copilot_ha_service_name_hardcodes(self):
        """AST scan: no hardcoded copilot_ha service names in search_integration.py."""
        src_text = SRC.read_text()
        tree = ast.parse(src_text)

        # We check string literals in the module (docstring, constants)
        violations = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if "copilot_ha.search" in node.value or "copilot_ha.index_search" in node.value:
                    violations.append(f"Line {node.lineno}: {node.value!r}")

        assert not violations, f"Found copilot_ha service name hardcodes:\n{violations}"