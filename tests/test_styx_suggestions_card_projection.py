"""
Contract test: styx-suggestions-card.js Projection Parity (HA-378)
Source-Guard for canonical pilotsuite entity references in the suggestions card frontend.
"""
import re

def _extract_block(content, func_name, tail_marker):
    """Extract a function body block from JS source."""
    start = content.find(f"{func_name}() {{")
    if start == -1:
        start = content.find(f"{func_name}(config) {{")
    end = content.find(tail_marker, start + 1)
    return content[start:end]


def test_styx_suggestions_card_loadfromsensor_pilotsuite_first():
    """SSC1: _loadFromSensor candidates order puts pilotsuite_suggestions before copilot_ha_suggestions."""
    path = "custom_components/pilotsuite/www/styx-suggestions-card.js"
    content = open(path, encoding="utf-8").read()

    block = _extract_block(content, "_loadFromSensor", "if (!s) return false;")
    # Normalise whitespace for safe substring search
    compacted = re.sub(r'\s+', ' ', block)

    ps_idx = compacted.find("sensor.pilotsuite_suggestions")
    cha_idx = compacted.find("sensor.copilot_ha_suggestions")
    cop_idx = compacted.find("sensor.copilot_suggestions")

    assert ps_idx >= 0, "sensor.pilotsuite_suggestions must appear in _loadFromSensor"
    assert cha_idx >= 0, "sensor.copilot_ha_suggestions must appear as fallback in _loadFromSensor"
    assert ps_idx < cha_idx, \
        "_loadFromSensor must list pilotsuite_suggestions before copilot_ha_suggestions"


def test_styx_suggestions_card_loadfromsensor_copilot_ha_fallback():
    """SSC2: _loadFromSensor includes copilot_ha_suggestions as secondary fallback (after pilotsuite)."""
    path = "custom_components/pilotsuite/www/styx-suggestions-card.js"
    content = open(path, encoding="utf-8").read()

    block = _extract_block(content, "_loadFromSensor", "if (!s) return false;")
    compacted = re.sub(r'\s+', ' ', block)

    cha_idx = compacted.find("sensor.copilot_ha_suggestions")
    cop_idx = compacted.find("sensor.copilot_suggestions")

    assert cha_idx >= 0, "sensor.copilot_ha_suggestions must appear as fallback"
    # copilot_suggestions may be absent — that's ok


def test_styx_suggestions_card_loadfromsensor_no_stale_ai_prefix():
    """SSC3: _loadFromSensor contains no stale sensor.ai_copilot_suggestions."""
    path = "custom_components/pilotsuite/www/styx-suggestions-card.js"
    content = open(path, encoding="utf-8").read()

    block = _extract_block(content, "_loadFromSensor", "if (!s) return false;")
    assert "sensor.ai_copilot_suggestions" not in block, \
        "Source must not contain stale sensor.ai_copilot_suggestions"


def test_styx_suggestions_card_getcoreurl_pilotsuite_first():
    """SSC4: _getCoreUrl resolves pilotsuite_core_api_v1 before copilot_ha_core_api_v1."""
    path = "custom_components/pilotsuite/www/styx-suggestions-card.js"
    content = open(path, encoding="utf-8").read()

    block = _extract_block(content, "_getCoreUrl", "return 'http://homeassistant.local:8909';")
    compacted = re.sub(r'\s+', ' ', block)

    ps_idx = compacted.find("sensor.pilotsuite_core_api_v1")
    cha_idx = compacted.find("sensor.copilot_ha_core_api_v1")

    assert ps_idx >= 0, "_getCoreUrl must reference sensor.pilotsuite_core_api_v1"
    assert cha_idx >= 0, "_getCoreUrl must reference sensor.copilot_ha_core_api_v1 as fallback"
    assert ps_idx < cha_idx, \
        "_getCoreUrl must list pilotsuite_core_api_v1 before copilot_ha_core_api_v1"
