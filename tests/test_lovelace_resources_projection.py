"""Contract tests for lovelace_resources.py projection parity (HA-455).

Belegt:
  LR1 - LOCAL_CARD_FILES comment refs /custom_components/pilotsuite/www/ not copilot_ha/www/
  LR2 - AST-Scan: null stale copilot_ha/www path literal in lovelace_resources.py
  LR3 - CARD_JS_PATH and LOCAL_CARD_FILES use pilotsuite DOMAIN in URLs
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

SRC = Path("/config/clawd/team/worktrees/pilotsuite-styx-ha-current/custom_components/pilotsuite/lovelace_resources.py")
STALE_SUBSTRING = "custom_components/copilot_ha/www"


def _read() -> str:
    return SRC.read_text()


def _parse() -> ast.Module:
    return ast.parse(_read(), filename=str(SRC))


def test_lr1_comment_ref_pilotsuite():
    """LR1: LOCAL_CARD_FILES comment refs pilotsuite not copilot_ha."""
    content = _read()
    # The comment should reference the pilotsuite path
    for line in content.splitlines():
        if "custom_components" in line and "www" in line:
            assert "pilotsuite" in line, f"Expected pilotsuite path in: {line.strip()}"
            assert "copilot_ha" not in line, f"Stale copilot_ha path in comment: {line.strip()}"


def test_lr2_ast_scan_no_stale_copilot_ha_path():
    """LR2: AST-Scan null stale copilot_ha/www path literal in lovelace_resources.py."""
    content = _read()
    # The stale substring must not appear anywhere (it would indicate a missed consolidation)
    assert STALE_SUBSTRING not in content, (
        f"Found stale copilot_ha path literal in lovelace_resources.py: '{STALE_SUBSTRING}'"
    )


def test_lr3_domains_in_urls():
    """LR3: CARD_JS_PATH and LOCAL_CARD_FILES use pilotsuite DOMAIN in URLs."""
    content = _read()
    tree = _parse()

    # Find LOCAL_CARD_FILES assignment
    found_local_card_files = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "LOCAL_CARD_FILES":
                    found_local_card_files = True
                    # All url strings in the list should use pilotsuite domain paths
                    if isinstance(node.value, ast.List):
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Constant) and "www" in elt.value:
                                assert "pilotsuite" in elt.value or "community" in elt.value, (
                                    f"Unexpected domain path in LOCAL_CARD_FILES item: {elt.value}"
                                )
    assert found_local_card_files, "LOCAL_CARD_FILES assignment not found"


if __name__ == "__main__":
    test_lr1_comment_ref_pilotsuite()
    test_lr2_ast_scan_no_stale_copilot_ha_path()
    test_lr3_domains_in_urls()
    print("LR1/LR2/LR3: 3/3 green")
    sys.exit(0)
