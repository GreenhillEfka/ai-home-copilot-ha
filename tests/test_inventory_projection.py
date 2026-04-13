"""Contract test: inventory.py notification_id and path parity."""
import re


def test_inventory_overview_notification_id():
    """INV1: inventory.py uses pilotsuite_overview notification_id."""
    path = "custom_components/pilotsuite/inventory.py"
    with open(path) as f:
        src = f.read()
    assert 'notification_id="pilotsuite_overview"' in src
    assert 'notification_id="copilot_ha_overview"' not in src


def test_inventory_no_stale_notification_id_hardcodes():
    """INV2: AST scan – no copilot_ha notification_id hardcodes in inventory.py."""
    path = "custom_components/pilotsuite/inventory.py"
    with open(path) as f:
        src = f.read()
    found = re.findall(r'notification_id=["\']copilot_ha[_a-z]*["\']', src)
    assert not found, f"Unexpected copilot_ha notification_id literals: {found}"


def test_inventory_www_path_uses_pilotsuite():
    """INV3: inventory.py www path references use pilotsuite, not copilot_ha."""
    path = "custom_components/pilotsuite/inventory.py"
    with open(path) as f:
        src = f.read()
    # Primary www path should use pilotsuite
    assert 'hass.config.path("pilotsuite")' in src
    assert 'hass.config.path("copilot_ha")' not in src
    # /share path should also use pilotsuite
    assert 'Path("/share") / "pilotsuite"' in src
    assert 'Path("/share") / "copilot_ha"' not in src


def test_inventory_no_stale_copilot_ha_path_literals():
    """INV4: AST scan – no copilot_ha path hardcodes in inventory.py."""
    path = "custom_components/pilotsuite/inventory.py"
    with open(path) as f:
        src = f.read()
    # Check for copilot_ha inside hass.config.path() argument
    found = re.findall(r'hass\.config\.path\(["\']copilot_ha["\']', src)
    assert not found, f"Unexpected copilot_ha path literals: {found}"
    # Check for copilot_ha in /share Path()
    found2 = re.findall(r'Path\(\"/share/copilot_ha\"\)', src)
    assert not found2, f"Unexpected copilot_ha /share path literals: {found2}"
