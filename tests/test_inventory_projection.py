"""Contract test: inventory.py notification_id parity."""
import ast

def test_inventory_overview_notification_id():
    """INV1: inventory.py uses pilotsuite_overview notification_id."""
    path = "custom_components/pilotsuite/inventory.py"
    with open(path) as f:
        src = f.read()
    assert 'notification_id="pilotsuite_overview"' in src
    assert 'notification_id="copilot_ha_overview"' not in src

def test_inventory_no_stale_copilot_ha_hardcodes():
    """INV2: AST scan – no copilot_ha notification_id hardcodes in inventory.py."""
    path = "custom_components/pilotsuite/inventory.py"
    with open(path) as f:
        src = f.read()
    # notification_id is the projection surface; paths/docs are runtime/config references
    import re
    found = re.findall(r'notification_id=["\']copilot_ha[_a-z]*["\']', src)
    assert not found, f"Unexpected copilot_ha notification_id literals: {found}"
