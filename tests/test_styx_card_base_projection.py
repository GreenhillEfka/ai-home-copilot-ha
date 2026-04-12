"""
Contract test: styx-card-base.js Projection Parity (HA-383)
Source-Guard for canonical pilotsuite entity priority in shared card base helpers.
"""
import re


def _extract_block(content, func_name, tail_marker):
    """Extract a function body block from JS source."""
    start = content.find(f"{func_name}(entityId, fallback) {{")
    end = content.find(tail_marker, start + 1)
    return content[start:end]


def test_styx_card_base_sensorval_prioritizes_pilotsuite_prefixes():
    """SCB1: shared _sensorVal resolves pilotsuite entities before legacy copilot fallbacks."""
    path = "custom_components/pilotsuite/www/styx-card-base.js"
    content = open(path, encoding="utf-8").read()

    block = _extract_block(content, "_sensorVal", "for (const eid of candidates) {")
    compacted = re.sub(r"\s+", " ", block)

    expected_prefixes = "['sensor.pilotsuite_', 'sensor.copilot_ha_', 'sensor.copilot_']"
    assert expected_prefixes in compacted, (
        "_sensorVal must prioritize sensor.pilotsuite_ before legacy copilot fallbacks"
    )


def test_styx_card_base_sensorval_keeps_legacy_fallbacks():
    """SCB2: shared _sensorVal keeps both legacy fallback prefixes for compatibility."""
    path = "custom_components/pilotsuite/www/styx-card-base.js"
    content = open(path, encoding="utf-8").read()

    block = _extract_block(content, "_sensorVal", "for (const eid of candidates) {")
    assert "sensor.copilot_ha_" in block, (
        "_sensorVal must keep sensor.copilot_ha_ as fallback prefix"
    )
    assert "sensor.copilot_" in block, (
        "_sensorVal must keep sensor.copilot_ as fallback prefix"
    )
