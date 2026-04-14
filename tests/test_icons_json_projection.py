"""Contract tests for icons.json copilot_ha service icon key parity."""
import json
import pathlib
import pytest

ICON_JSON = pathlib.Path(__file__).parent.parent / "custom_components" / "pilotsuite" / "icons.json"


class TestIconsJsonProjection:
    """Projection contract for icons.json service icon keys."""

    def test_icon1_canonical_unifi_run_diagnostics_key(self):
        """IK1: kanonische pilotsuite_unifi_run_diagnostics als Service-Icon-Key."""
        data = json.loads(ICON_JSON.read_text())
        services = data.get("services", {})
        # Die kanonische pilotsuite-Version des Service-Icon-Keys muss existieren
        assert "pilotsuite_unifi_run_diagnostics" in services, (
            f"pilotsuite_unifi_run_diagnostics nicht in services. "
            f"Vorhanden: {list(services.keys())}"
        )

    def test_icon2_canonical_unifi_get_report_key(self):
        """IK2: kanonische pilotsuite_unifi_get_report als Service-Icon-Key."""
        data = json.loads(ICON_JSON.read_text())
        services = data.get("services", {})
        assert "pilotsuite_unifi_get_report" in services, (
            f"pilotsuite_unifi_get_report nicht in services. "
            f"Vorhanden: {list(services.keys())}"
        )

    def test_icon3_no_stale_copilot_ha_unifi_keys(self):
        """IK3: AST-Scan — keine stale copilot_ha_unifi_*-Literale in icons.json."""
        content = ICON_JSON.read_text()
        # Nur die services-Sektion prüfen
        data = json.loads(content)
        services = data.get("services", {})
        stale = [k for k in services if k.startswith("copilot_ha_unifi_")]
        assert not stale, (
            f"Stale copilot_ha_unifi_*-Keys in icons.json services: {stale}"
        )

    def test_icon4_unifi_run_diagnostics_value_preserved(self):
        """IK4: mdi:network Icon-Wert bleibt für pilotsuite_unifi_run_diagnostics erhalten."""
        data = json.loads(ICON_JSON.read_text())
        services = data.get("services", {})
        assert services.get("pilotsuite_unifi_run_diagnostics") == "mdi:network", (
            "mdi:network Icon-Wert für pilotsuite_unifi_run_diagnostics wurde verändert"
        )

    def test_icon5_unifi_get_report_value_preserved(self):
        """IK5: mdi:file-chart Icon-Wert bleibt für pilotsuite_unifi_get_report erhalten."""
        data = json.loads(ICON_JSON.read_text())
        services = data.get("services", {})
        assert services.get("pilotsuite_unifi_get_report") == "mdi:file-chart", (
            "mdi:file-chart Icon-Wert für pilotsuite_unifi_get_report wurde verändert"
        )

    def test_icon6_json_syntax_ok(self):
        """IK6: icons.json ist valides JSON."""
        data = json.loads(ICON_JSON.read_text())
        assert isinstance(data, dict)
        assert "services" in data
