"""Contract tests for habitus_miner.py pilotsuite parity."""
import ast
import pytest
from pathlib import Path

ROOT = Path("custom_components/pilotsuite/core/modules/habitus_miner.py")
SRC = ROOT.read_text()


def _get_lineno_for_pattern(src: str, pattern: str) -> list[int]:
    return [i + 1 for i, line in enumerate(src.splitlines()) if pattern in line]


class TestHabitusMinerStorageKey:
    """HM-1: STORAGE_KEY must use pilotsuite namespace."""

    def test_storage_key_uses_pilotsuite(self):
        linenos = _get_lineno_for_pattern(SRC, 'STORAGE_KEY = "pilotsuite.habitus_miner"')
        assert linenos, "STORAGE_KEY = pilotsuite.habitus_miner not found in habitus_miner.py"
        # exactly one
        assert len(linenos) == 1, f"Multiple pilotsuite.habitus_miner STORAGE_KEY found at {linenos}"


class TestHabitusMinerBusEvents:
    """HM-2: async_fire calls must not use copilot_ha bus event names."""

    def test_no_copilot_ha_bus_event_type(self):
        """copilot_ha_notification and copilot_ha_habitus_patterns_discovered must not appear as event types."""
        for line_idx, line in enumerate(SRC.splitlines(), 1):
            if 'async_fire("copilot_ha_notification"' in line or \
               'async_fire("copilot_ha_habitus_patterns_discovered"' in line:
                pytest.fail(
                    f"Line {line_idx}: stale copilot_ha bus event type found:\n  {line.strip()}"
                )

    def test_pilotsuite_bus_events_present(self):
        """Pilotsuite event types must be used in async_fire calls."""
        pilotsuite_notification_lines = _get_lineno_for_pattern(
            SRC, '"pilotsuite_notification"'
        )
        pilotsuite_pattern_lines = _get_lineno_for_pattern(
            SRC, '"pilotsuite_habitus_patterns_discovered"'
        )
        assert pilotsuite_notification_lines, (
            "No pilotsuite_notification event type found; expected in async_fire calls"
        )
        assert pilotsuite_pattern_lines, (
            "No pilotsuite_habitus_patterns_discovered event type found; expected in async_fire call"
        )


class TestHabitusMinerSyntax:
    """HM-3: habitus_miner.py must be syntactically valid."""

    def test_syntax_ok(self):
        try:
            ast.parse(SRC)
        except SyntaxError as e:
            pytest.fail(f"Syntax error in habitus_miner.py: {e}")
