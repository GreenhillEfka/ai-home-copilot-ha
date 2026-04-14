"""Contract tests for core/__init__.py docstring projection."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

SRC = Path("custom_components/pilotsuite/core/__init__.py")
CONTENT = SRC.read_text()


def test_CI1_canonical_pilotsuite_docstring() -> None:
    """CI1: core/__init__.py docstring uses canonical pilotsuite reference."""
    lines = CONTENT.splitlines()
    assert lines, "File is empty"
    first_line = lines[0]
    assert "pilotsuite" in first_line, (
        f"First line docstring does not use canonical pilotsuite reference: {first_line!r}"
    )
    assert "copilot_ha" not in first_line, (
        f"First line docstring contains stale copilot_ha: {first_line!r}"
    )
    print(f"CI1 passed: docstring uses pilotsuite — {first_line!r}")


def test_CI2_no_stale_copilot_ha() -> None:
    """CI2: No stale copilot_ha string literals in docstring."""
    docstring_lines = [l for l in CONTENT.splitlines() if l.strip().startswith("#") or (not l.strip() and len(CONTENT.splitlines()) < 20)]
    # Just scan the whole content
    stale = [l for l in CONTENT.splitlines() if "copilot_ha" in l and not l.strip().startswith("#")]
    assert not stale, f"Stale copilot_ha found outside comment: {stale}"
    print("CI2 passed: no stale copilot_ha literals")


def test_CI3_syntax() -> None:
    """CI3: File has valid Python syntax."""
    try:
        ast.parse(CONTENT)
    except SyntaxError as exc:
        raise AssertionError(f"Syntax error in core/__init__.py: {exc}") from exc
    print("CI3 passed: syntax OK")


if __name__ == "__main__":
    test_CI3_syntax()
    test_CI1_canonical_pilotsuite_docstring()
    test_CI2_no_stale_copilot_ha()
    print("3/3 contract tests passed")
    sys.exit(0)
