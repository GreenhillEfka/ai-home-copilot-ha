"""Contract test: habitus_dashboard.py notification_id parity."""
import ast
import re


def test_habitus_dashboard_notification_id():
    """HD1: habitus_dashboard.py uses pilotsuite_habitus_dashboard notification_id."""
    path = "custom_components/pilotsuite/habitus_dashboard.py"
    with open(path) as f:
        src = f.read()
    assert 'notification_id="pilotsuite_habitus_dashboard"' in src
    assert 'notification_id="copilot_ha_habitus_dashboard"' not in src


def test_habitus_dashboard_download_notification_id():
    """HD2: habitus_dashboard.py uses pilotsuite_habitus_dashboard_download notification_id."""
    path = "custom_components/pilotsuite/habitus_dashboard.py"
    with open(path) as f:
        src = f.read()
    assert 'notification_id="pilotsuite_habitus_dashboard_download"' in src
    assert 'notification_id="copilot_ha_habitus_dashboard_download"' not in src


def test_habitus_dashboard_no_stale_copilot_ha_notification_id():
    """HD3: AST scan – no copilot_ha notification_id hardcodes in habitus_dashboard.py."""
    path = "custom_components/pilotsuite/habitus_dashboard.py"
    with open(path) as f:
        src = f.read()
    found = re.findall(r'notification_id=["\']copilot_ha[_a-z]*["\']', src)
    assert not found, f"Unexpected copilot_ha notification_id literals: {found}"
