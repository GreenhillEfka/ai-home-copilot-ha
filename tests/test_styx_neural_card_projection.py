"""
Contract test: styx-neural-card.js Projection Parity (HA-381)
Source-Guard for canonical pilotsuite core API lookup in the neural card frontend.
"""
import re


def _extract_block(content, func_name, tail_marker):
    """Extract a function body block from JS source."""
    start = content.find(f"{func_name}() {{")
    end = content.find(tail_marker, start + 1)
    return content[start:end]


def test_styx_neural_card_getcoreurl_pilotsuite_first():
    """SNC1: _getCoreUrl resolves pilotsuite_core_api_v1 before copilot_ha_core_api_v1."""
    path = "custom_components/pilotsuite/www/styx-neural-card.js"
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


def test_styx_neural_card_getcoreurl_keeps_copilot_ha_fallback():
    """SNC2: _getCoreUrl keeps copilot_ha_core_api_v1 as the secondary fallback."""
    path = "custom_components/pilotsuite/www/styx-neural-card.js"
    content = open(path, encoding="utf-8").read()

    block = _extract_block(content, "_getCoreUrl", "return 'http://homeassistant.local:8909';")
    assert "sensor.copilot_ha_core_api_v1" in block, (
        "_getCoreUrl must keep sensor.copilot_ha_core_api_v1 as fallback"
    )
