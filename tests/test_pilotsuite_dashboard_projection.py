"""Contract test: pilotsuite_dashboard.py notification_id parity."""
import re


def test_pilotsuite_dashboard_notification_id():
    """PD1: pilotsuite_dashboard.py uses pilotsuite_pilotsuite_dashboard notification_id."""
    path = "custom_components/pilotsuite/pilotsuite_dashboard.py"
    with open(path) as f:
        src = f.read()
    assert 'notification_id="pilotsuite_pilotsuite_dashboard"' in src
    assert 'notification_id="copilot_ha_pilotsuite_dashboard"' not in src


def test_pilotsuite_dashboard_download_notification_id():
    """PD2: pilotsuite_dashboard.py uses pilotsuite_pilotsuite_dashboard_download notification_id."""
    path = "custom_components/pilotsuite/pilotsuite_dashboard.py"
    with open(path) as f:
        src = f.read()
    assert 'notification_id="pilotsuite_pilotsuite_dashboard_download"' in src
    assert 'notification_id="copilot_ha_pilotsuite_dashboard_download"' not in src


def test_pilotsuite_dashboard_no_stale_copilot_ha_notification_id():
    """PD3: AST scan – no copilot_ha notification_id hardcodes in pilotsuite_dashboard.py."""
    path = "custom_components/pilotsuite/pilotsuite_dashboard.py"
    with open(path) as f:
        src = f.read()
    found = re.findall(r'notification_id=["\']copilot_ha[_a-z]*["\']', src)
    assert not found, f"Unexpected copilot_ha notification_id literals: {found}"
