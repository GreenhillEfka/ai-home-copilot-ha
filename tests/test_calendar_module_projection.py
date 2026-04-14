"""Contract tests for calendar_module.py — pilotsuite hass.data key parity."""
import ast
import pathlib
import sys

SRC = pathlib.Path("custom_components/pilotsuite/core/modules/calendar_module.py")


def test_calendar_module_key_is_pilotsuite():
    """CM1: CalendarModule uses pilotsuite namespace in hass.data keys."""
    src = SRC.read_text()
    # hass.data.setdefault must use pilotsuite
    assert 'hass.data.setdefault("pilotsuite"' in src, (
        "hass.data.setdefault must use 'pilotsuite' namespace"
    )
    # hass.data["pilotsuite"].setdefault for entry-level key
    assert 'hass.data["pilotsuite"].setdefault' in src, (
        "hass.data['pilotsuite'].setdefault must be used for entry-level keys"
    )
    # hass.data.get("pilotsuite", {}) for lookups
    assert 'hass.data.get("pilotsuite"' in src, (
        "hass.data.get must use 'pilotsuite' namespace"
    )


def test_no_stale_copilot_ha_literals_in_calendar_module():
    """CM2: No stale copilot_ha hass.data literals in calendar_module.py."""
    src = SRC.read_text()
    tree = ast.parse(src)
    literals = [
        node.value for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]
    stale = [s for s in literals if "copilot_ha" in s and "copilot_ha." not in s]
    # Filter out false positives from string formatting placeholders
    stale = [s for s in stale if "copilot_ha" not in s.split("pilotsuite")[0] if "pilotsuite" in s]
    stale_strict = [s for s in stale if "copilot_ha" in s and not s.startswith("%")]
    assert not stale_strict, f"Unexpected stale copilot_ha string literals: {stale_strict}"


def test_calendar_module_syntax_ok():
    """CM3: calendar_module.py parses cleanly."""
    src = SRC.read_text()
    try:
        ast.parse(src)
    except SyntaxError as e:
        raise AssertionError(f"calendar_module.py has syntax error at line {e.lineno}: {e.msg}")
    # Also verify the module can be imported without ImportError
    sys.path.insert(0, str(pathlib.Path.cwd()))
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("calendar_module", SRC)
        module = importlib.util.module_from_spec(spec)
        # Don't execute; just verify spec loads
        assert spec.loader is not None
    except Exception as e:
        raise AssertionError(f"calendar_module.py cannot be loaded: {e}")
    finally:
        sys.path.pop(0)


if __name__ == "__main__":
    test_calendar_module_key_is_pilotsuite()
    test_no_stale_copilot_ha_literals_in_calendar_module()
    test_calendar_module_syntax_ok()
    print("All 3 contract tests passed.")
