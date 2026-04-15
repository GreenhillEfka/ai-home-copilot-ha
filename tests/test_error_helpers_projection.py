"""Contract tests for error_helpers.py — HA-485.

Verifies that the stacktrace sanitization filter uses pilotsuite (not copilot_ha)
as the DOMAIN marker, since the integration has been renamed.
"""
import ast
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../custom_components/pilotsuite"))

from custom_components.pilotsuite.core.error_helpers import (
    _sanitize_traceback,
    _extract_traceback_summary,
)


# EH1: _sanitize_traceback uses pilotsuite marker list (not copilot_ha)
def test_eh1_sanitize_traceback_filter_uses_pilotsuite():
    """EH1: _sanitize_traceback keeps pilotsuite frames, not copilot_ha."""
    fake_tb = [
        '  File "/config/custom_components/pilotsuite/core/error_helpers.py", line 42, in _sanitize_traceback',
        '  File "/config/custom_components/pilotsuite/some_module.py", line 10, in init',
        'Traceback (most recent call last):',
    ]
    result = _sanitize_traceback(fake_tb)
    assert any("pilotsuite" in line for line in result)
    assert not any("copilot_ha" in line for line in result)


# EH2: _extract_traceback_summary matches on pilotsuite (not copilot_ha)
def test_eh2_extract_traceback_summary_uses_pilotsuite():
    """EH2: _extract_traceback_summary detects pilotsuite File lines."""
    fake_tb = [
        '  File "/config/custom_components/pilotsuite/core/sensor.py", line 88, in update',
    ]
    summary = _extract_traceback_summary(fake_tb)
    assert "core/sensor.py" in summary or "sensor.py" in summary


# EH3: AST scan — no copilot_ha in error_helpers.py source
def test_eh3_ast_no_copilot_ha_in_source():
    """EH3: AST scan finds no copilot_ha literals in error_helpers.py."""
    path = os.path.join(
        os.path.dirname(__file__),
        "../custom_components/pilotsuite/core/error_helpers.py",
    )
    with open(path) as f:
        source = f.read()
    tree = ast.parse(source)
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if "copilot_ha" in node.value and "sensor.copilot_ha" not in node.value:
                found.append(node.value)
    assert not found, f"Unexpected copilot_ha literals: {found}"


# EH4: Syntax OK
def test_eh4_syntax_ok():
    """EH4: error_helpers.py compiles without syntax errors."""
    path = os.path.join(
        os.path.dirname(__file__),
        "../custom_components/pilotsuite/core/error_helpers.py",
    )
    with open(path) as f:
        source = f.read()
    ast.parse(source)