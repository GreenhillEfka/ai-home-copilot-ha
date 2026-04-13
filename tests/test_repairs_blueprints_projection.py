"""Projection test for repairs_blueprints slug and path constants."""
import ast
from pathlib import Path

ROOT = Path("/config/clawd/team/worktrees/pilotsuite-styx-ha-current/custom_components/pilotsuite")
SRC = ROOT / "repairs_blueprints.py"


class TestRepairsBlueprintsCanonical:
    """Contract tests for blueprint slug and path references in repairs_blueprints.py."""

    def test_default_slug_uses_pilotsuite(self):
        """BlueprintApplyPlan default slug must reference pilotsuite, not copilot_ha."""
        src_text = SRC.read_text()
        assert 'slug: str = "pilotsuite__a_to_b_safe"' in src_text, (
            f"Default slug must be pilotsuite__a_to_b_safe, found:\n"
            f"{[l for l in src_text.splitlines() if 'slug' in l and 'safe' in l.lower()]}"
        )
        assert 'slug: str = "copilot_ha__a_to_b_safe"' not in src_text

    def test_default_blueprint_path_uses_pilotsuite(self):
        """Default blueprint_path in async_build_plan_from_issue_data must reference pilotsuite."""
        src_text = SRC.read_text()
        assert 'blueprint_path = "pilotsuite/a_to_b_safe.yaml"' in src_text, (
            f"Default blueprint_path must be pilotsuite/a_to_b_safe.yaml, found:\n"
            f"{[l for l in src_text.splitlines() if 'blueprint_path' in l and 'yaml' in l.lower()]}"
        )
        assert 'blueprint_path = "copilot_ha/a_to_b_safe.yaml"' not in src_text

    def test_no_copilot_ha_hardcoded_blueprint_references(self):
        """AST scan: no hardcoded copilot_ha blueprint references in repairs_blueprints.py."""
        src_text = SRC.read_text()
        tree = ast.parse(src_text)

        violations = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if "copilot_ha" in node.value and ("blueprint" in node.value.lower() or "slug" in node.value.lower()):
                    violations.append(f"Line {node.lineno}: {node.value!r}")

        assert not violations, f"Found copilot_ha blueprint/slug references:\n{violations}"