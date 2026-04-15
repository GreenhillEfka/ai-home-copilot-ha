"""Contract tests for seed_store.py copilot_ha → pilotsuite LEGACY_DOMAIN parity."""

import ast
import subprocess
import sys

REPO_ROOT = "/config/clawd/team/worktrees/pilotsuite-styx-ha-current"
SOURCE_FILE = f"{REPO_ROOT}/custom_components/pilotsuite/seed_store.py"


class TestSeedStoreProjection:
    """SS-owners: seed_store.py LEGACY_DOMAIN parity."""

    def test_ss1_kanonische_legacyj_domain_konstante(self):
        """SS1: Kanonische LEGACY_DOMAIN nutzt pilotsuite statt copilot_ha."""
        tree = ast.parse(open(SOURCE_FILE).read())
        legacy_domain_nodes = [
            n for n in ast.walk(tree)
            if isinstance(n, ast.Assign) and any(
                t.id == "LEGACY_DOMAIN" for t in n.targets if isinstance(t, ast.Name)
            )
        ]
        assert len(legacy_domain_nodes) == 1, "LEGACY_DOMAIN must be defined exactly once"
        value_node = legacy_domain_nodes[0].value
        assert isinstance(value_node, ast.Constant), "LEGACY_DOMAIN value must be a string literal"
        assert value_node.value == "pilotsuite", (
            f"LEGACY_DOMAIN must be 'pilotsuite', got '{value_node.value}'"
        )

    def test_ss2_ast_scan_null_stale_copilot_ha_literal(self):
        """SS2: AST-Scan findet null stale copilot_ha-Literale in seed_store.py."""
        tree = ast.parse(open(SOURCE_FILE).read())
        stale_nodes = [
            (n.__class__.__name__, ast.unparse(n))
            for n in ast.walk(tree)
            if isinstance(n, (ast.Constant, ast.FormattedValue)) and
            isinstance(n, ast.Constant) and isinstance(n.value, str) and
            "copilot_ha" in n.value and "legitim" not in n.value.lower()
        ]
        assert not stale_nodes, (
            f"Stale copilot_ha literals found in seed_store.py: {stale_nodes}"
        )

    def test_ss3_syntax_ok(self):
        """SS3: seed_store.py kompiliert fehlerfrei."""
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", SOURCE_FILE],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"syntax error: {result.stderr}"

    def test_ss4_legitimLegacy_store_key_format(self):
        """SS4: LEGACY_STORE_KEY nutzt LEGACY_DOMAIN-Variable korrekt formatiert."""
        tree = ast.parse(open(SOURCE_FILE).read())
        legacy_store_key_nodes = [
            n for n in ast.walk(tree)
            if isinstance(n, ast.Assign) and any(
                t.id == "LEGACY_STORE_KEY" for t in n.targets if isinstance(t, ast.Name)
            )
        ]
        assert len(legacy_store_key_nodes) == 1
        # LEGACY_STORE_KEY muss f"{LEGACY_DOMAIN}.seed_limiter" sein
        value_node = legacy_store_key_nodes[0].value
        assert isinstance(value_node, ast.JoinedStr), "LEGACY_STORE_KEY must be an f-string"
        formatted_values = [v for v in value_node.values if isinstance(v, ast.FormattedValue)]
        assert any(
            isinstance(v.value, ast.Name) and v.value.id == "LEGACY_DOMAIN"
            for v in formatted_values
        ), "LEGACY_STORE_KEY must reference LEGACY_DOMAIN variable"