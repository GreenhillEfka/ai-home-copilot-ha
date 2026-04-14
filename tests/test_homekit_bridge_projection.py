"""Contract tests: homekit_bridge.py copilot_ha → pilotsuite projection parity."""
from __future__ import annotations

import ast
import sys


def _scan_copilot_ha_literals(path: str) -> list[str]:
    """Return sorted list of copilot_ha literal strings found outside comments."""
    with open(path) as fh:
        src = fh.read()
    tree = ast.parse(src)
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            val = node.value
            if "copilot_ha" in val:
                hits.append(f"L{node.lineno}: {val!r}")
    return hits


def test_hk1_kanonische_homekit_store_key(tmp_path):
    """HK1: HOMEKIT_STORE_KEY uses pilotsuite domain."""
    from custom_components.pilotsuite.core.modules.homekit_bridge import (
        HOMEKIT_STORE_KEY,
    )
    assert HOMEKIT_STORE_KEY == "pilotsuite.homekit_zones", (
        f"HK1 FAILED: expected pilotsuite.homekit_zones, got {HOMEKIT_STORE_KEY!r}"
    )


def test_hk2_kanonische_signal_name(tmp_path):
    """HK2: SIGNAL_HOMEKIT_ZONE_TOGGLED uses pilotsuite domain."""
    from custom_components.pilotsuite.core.modules.homekit_bridge import (
        SIGNAL_HOMEKIT_ZONE_TOGGLED,
    )
    assert SIGNAL_HOMEKIT_ZONE_TOGGLED == "pilotsuite_homekit_zone_toggled", (
        f"HK2 FAILED: expected pilotsuite_homekit_zone_toggled, "
        f"got {SIGNAL_HOMEKIT_ZONE_TOGGLED!r}"
    )


def test_hk3_null_stale_copilot_ha_literals(tmp_path):
    """HK3: AST scan finds no stale copilot_ha string literals in the module."""
    path = "custom_components/pilotsuite/core/modules/homekit_bridge.py"
    hits = _scan_copilot_ha_literals(path)
    stale = [h for h in hits if "copilot_ha" in h]
    assert not stale, (
        f"HK3 FAILED: stale copilot_ha literals remaining:\n" +
        "\n".join(f"  {s}" for s in stale)
    )


def test_hk4_syntax_ok(tmp_path):
    """HK4: homekit_bridge.py compiles without SyntaxError."""
    path = "custom_components/pilotsuite/core/modules/homekit_bridge.py"
    with open(path) as fh:
        src = fh.read()
    try:
        ast.parse(src)
    except SyntaxError as e:
        raise AssertionError(f"HK4 FAILED: SyntaxError at line {e.lineno}: {e.msg}")
