"""Contract tests for systemhealth_report.py and blueprints.py pilotsuite parity.

HA-426 — Projections: LEGACY_EXPORT_DIR, LEGACY_PUBLISH_DIR, blueprint target path.
"""

import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent / "custom_components" / "pilotsuite"
SYSTEMHEALTH_REPORT = REPO_ROOT / "systemhealth_report.py"
BLUEPRINTS_PY = REPO_ROOT / "blueprints.py"


class _ASTScanner:
    """Minimal AST visitor that collects all string literals."""

    def __init__(self, source: str):
        self.strings: list[str] = []
        self._tree = ast.parse(source)

    def scan(self) -> list[str]:
        for node in ast.walk(self._tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                self.strings.append(node.value)
            elif isinstance(node, ast.JoinedStr):  # f-strings — visit value nodes
                for n in ast.walk(node):
                    if isinstance(n, ast.Constant) and isinstance(n.value, str):
                        self.strings.append(n.value)
        return self.strings


# ── systemhealth_report.py ──────────────────────────────────────────────────

def test_systemhealth_legacy_export_dir_is_pilotsuite():
    """SHR1: LEGACY_EXPORT_DIR uses pilotsuite, not copilot_ha."""
    src = SYSTEMHEALTH_REPORT.read_text()
    scanner = _ASTScanner(src)
    strings = scanner.scan()
    found = [s for s in strings if "copilot_ha" in s and "LEGACY_EXPORT_DIR" in s]
    assert not found, f"LEGACY_EXPORT_DIR still references copilot_ha: {found!r}"


def test_systemhealth_legacy_publish_dir_is_pilotsuite():
    """SHR2: LEGACY_PUBLISH_DIR uses pilotsuite, not copilot_ha."""
    src = SYSTEMHEALTH_REPORT.read_text()
    scanner = _ASTScanner(src)
    strings = scanner.scan()
    found = [s for s in strings if "copilot_ha" in s and "LEGACY_PUBLISH_DIR" in s]
    assert not found, f"LEGACY_PUBLISH_DIR still references copilot_ha: {found!r}"


def test_systemhealth_no_stale_copilot_ha_in_file():
    """SHR3: AST scan confirms zero stale copilot_ha literals in systemhealth_report.py."""
    src = SYSTEMHEALTH_REPORT.read_text()
    scanner = _ASTScanner(src)
    strings = scanner.scan()
    stale = [s for s in strings if "copilot_ha" in s]
    assert not stale, f"Stale copilot_ha literals found: {stale!r}"


# ── blueprints.py ────────────────────────────────────────────────────────────

def test_blueprints_dst_path_uses_pilotsuite():
    """BP1: Blueprint destination path uses pilotsuite, not copilot_ha."""
    src = BLUEPRINTS_PY.read_text()
    assert '"copilot_ha"' not in src, "blueprints.py still contains 'copilot_ha' in dst path"
    assert "'copilot_ha'" not in src, "blueprints.py still contains 'copilot_ha' in dst path"


def test_blueprints_no_stale_copilot_ha_in_file():
    """BP2: AST scan confirms zero stale copilot_ha literals in blueprints.py."""
    src = BLUEPRINTS_PY.read_text()
    scanner = _ASTScanner(src)
    strings = scanner.scan()
    stale = [s for s in strings if "copilot_ha" in s]
    assert not stale, f"Stale copilot_ha literals found: {stale!r}"
