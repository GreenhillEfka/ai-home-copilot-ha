"""Source guard for styx-zone-card.js projection contract."""
import ast
import re

ARTIFACT = "custom_components/pilotsuite/www/styx-zone-card.js"


def test_zone_card_no_copilot_ha_comment():
    """ZC1: stale copilot_ha REST comment must not appear in zone card."""
    with open(ARTIFACT, encoding="utf-8") as f:
        content = f.read()
    # The stale comment references copilot_ha as a REST command but the actual
    # service call uses the generic rest_command/zone_presence_hold
    assert "copilot_ha REST command" not in content, (
        "stale comment references copilot_ha REST command; "
        "actual service is generic rest_command/zone_presence_hold"
    )


def test_zone_card_service_is_generic_rest_command():
    """ZC2: zone presence hold must use generic rest_command, not copilot_ha-prefixed."""
    with open(ARTIFACT, encoding="utf-8") as f:
        content = f.read()
    # The service call must use generic 'rest_command' domain
    assert "callService('rest_command'" in content, (
        "zone presence hold must use generic rest_command domain"
    )
    # Must NOT have a copilot_ha-specific service name in zone presence hold
    match = re.search(r"callService\(['\"]([^'\"]+)['\"]", content)
    if match:
        service_domain = match.group(1)
        assert service_domain not in ("copilot_ha", "pilotsuite"), (
            f"zone presence hold uses domain '{service_domain}'; "
            "must be generic rest_command"
        )


def test_zone_card_no_copilot_ha_hass_states():
    """ZC3: no copilot_ha state lookups in zone card."""
    with open(ARTIFACT, encoding="utf-8") as f:
        content = f.read()
    assert "['sensor.copilot_ha_" not in content, (
        "zone card must not look up copilot_ha sensor states"
    )
