"""
Contract test: styx-error-card.js Projection Parity (HA-380)
Source-Guard for canonical pilotsuite entity references in the error card frontend.
"""
import re


def _extract_block(content, func_name, tail_marker):
    """Extract a function body block from JS source."""
    start = content.find(f"{func_name}() {{")
    end = content.find(tail_marker, start + 1)
    return content[start:end]


def test_styx_error_card_docstring_uses_pilotsuite_home_alerts():
    """SEC1: The source header documents pilotsuite home_alerts as canonical source."""
    path = "custom_components/pilotsuite/www/styx-error-card.js"
    content = open(path, encoding="utf-8").read()

    header = content.split("*/", 1)[0]
    assert "sensor.pilotsuite_home_alerts_*" in header, (
        "Header must document sensor.pilotsuite_home_alerts_* as canonical source"
    )
    assert "sensor.copilot_home_alerts_*" not in header, (
        "Header must not keep stale sensor.copilot_home_alerts_* as primary source"
    )


def test_styx_error_card_getcoreurl_pilotsuite_first():
    """SEC2: _getCoreUrl resolves pilotsuite_core_api_v1 before copilot_ha_core_api_v1."""
    path = "custom_components/pilotsuite/www/styx-error-card.js"
    content = open(path, encoding="utf-8").read()

    block = _extract_block(content, "_getCoreUrl", "return 'http://homeassistant.local:8909';")
    compacted = re.sub(r"\s+", " ", block)

    ps_idx = compacted.find("sensor.pilotsuite_core_api_v1")
    cha_idx = compacted.find("sensor.copilot_ha_core_api_v1")

    assert ps_idx >= 0, "_getCoreUrl must reference sensor.pilotsuite_core_api_v1"
    assert cha_idx >= 0, "_getCoreUrl must reference sensor.copilot_ha_core_api_v1 as fallback"
    assert ps_idx < cha_idx, (
        "_getCoreUrl must list pilotsuite_core_api_v1 before copilot_ha_core_api_v1"
    )


def test_styx_error_card_loadfromsensors_pilotsuite_home_alerts_first():
    """SEC3: _loadFromSensors reads pilotsuite_home_alerts_count before legacy fallbacks."""
    path = "custom_components/pilotsuite/www/styx-error-card.js"
    content = open(path, encoding="utf-8").read()

    block = _extract_block(content, "_loadFromSensors", "if (!alertSensor) return false;")
    compacted = re.sub(r"\s+", " ", block)

    ps_idx = compacted.find("sensor.pilotsuite_home_alerts_count")
    cha_idx = compacted.find("sensor.copilot_ha_home_alerts_count")
    ch_idx = compacted.find("sensor.copilot_home_alerts_count")

    assert ps_idx >= 0, "_loadFromSensors must reference sensor.pilotsuite_home_alerts_count"
    assert cha_idx >= 0, "_loadFromSensors must keep sensor.copilot_ha_home_alerts_count as fallback"
    assert ch_idx >= 0, "_loadFromSensors must keep sensor.copilot_home_alerts_count as fallback"
    assert ps_idx < cha_idx < ch_idx, (
        "_loadFromSensors must prioritize pilotsuite_home_alerts_count before legacy fallbacks"
    )


def test_styx_error_card_loadfromsensors_keeps_legacy_home_alerts_fallbacks():
    """SEC4: _loadFromSensors keeps both legacy home_alerts fallbacks for compatibility."""
    path = "custom_components/pilotsuite/www/styx-error-card.js"
    content = open(path, encoding="utf-8").read()

    block = _extract_block(content, "_loadFromSensors", "if (!alertSensor) return false;")
    assert "sensor.copilot_ha_home_alerts_count" in block, (
        "_loadFromSensors must keep sensor.copilot_ha_home_alerts_count as fallback"
    )
    assert "sensor.copilot_home_alerts_count" in block, (
        "_loadFromSensors must keep sensor.copilot_home_alerts_count as fallback"
    )
