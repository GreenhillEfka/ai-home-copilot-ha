"""
Contract test: styx-household-card.js Projection Parity (HA-382)
Source-Guard for canonical pilotsuite entity references in the household card frontend.
"""
import re


def _extract_block(content, func_name, tail_marker):
    """Extract a function body block from JS source."""
    start = content.find(f"{func_name}(entityId, fallback) {{")
    end = content.find(tail_marker, start + 1)
    return content[start:end]


def test_styx_household_card_header_uses_pilotsuite_entities():
    """SHC1: the source header documents pilotsuite household entities as canonical sources."""
    path = "custom_components/pilotsuite/www/styx-household-card.js"
    content = open(path, encoding="utf-8").read()

    header = content.split("*/", 1)[0]
    for entity in (
        "sensor.pilotsuite_home_health_score",
        "sensor.pilotsuite_weather_warnings",
        "sensor.pilotsuite_electricity_tariff",
        "sensor.pilotsuite_fuel_price_comparison",
        "sensor.pilotsuite_proactive_alerts",
        "sensor.pilotsuite_persons_home",
        "sensor.pilotsuite_habitus_zones",
    ):
        assert entity in header, f"Header must document {entity} as canonical source"

    for stale_entity in (
        "sensor.copilot_home_health_score",
        "sensor.copilot_weather_warnings",
        "sensor.copilot_electricity_tariff",
        "sensor.copilot_fuel_price_comparison",
        "sensor.copilot_proactive_alerts",
        "sensor.copilot_persons_home",
        "sensor.copilot_habitus_zones",
    ):
        assert stale_entity not in header, f"Header must not keep stale {stale_entity} as primary source"


def test_styx_household_card_sensorval_prioritizes_pilotsuite_prefixes():
    """SHC2: _sensorVal resolves pilotsuite entities before legacy copilot fallbacks."""
    path = "custom_components/pilotsuite/www/styx-household-card.js"
    content = open(path, encoding="utf-8").read()

    block = _extract_block(content, "_sensorVal", "for (const eid of suffixes) {")
    compacted = re.sub(r"\s+", " ", block)

    expected_prefixes = "['sensor.pilotsuite_', 'sensor.copilot_ha_', 'sensor.copilot_']"
    assert expected_prefixes in compacted, (
        "_sensorVal must prioritize sensor.pilotsuite_ before legacy copilot fallbacks"
    )


def test_styx_household_card_sensorval_keeps_legacy_fallbacks():
    """SHC3: _sensorVal keeps both legacy prefix fallbacks for compatibility."""
    path = "custom_components/pilotsuite/www/styx-household-card.js"
    content = open(path, encoding="utf-8").read()

    block = _extract_block(content, "_sensorVal", "for (const eid of suffixes) {")
    assert "sensor.copilot_ha_" in block, (
        "_sensorVal must keep sensor.copilot_ha_ as fallback prefix"
    )
    assert "sensor.copilot_" in block, (
        "_sensorVal must keep sensor.copilot_ as fallback prefix"
    )
