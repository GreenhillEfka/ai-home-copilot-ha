"""
Projection contract tests for services.yaml (HA-448).

Validates:
  SV1 - No copilot_ha_unifi_run_diagnostics / copilot_ha_unifi_get_report legacy
        service IDs remain in services.yaml
  SV2 - Canonical pilotsuite_unifi_run_diagnostics / pilotsuite_unifi_get_report
        service IDs are present in services.yaml
  SV3 - No copilot_ha string literals at all in services.yaml
"""
from __future__ import annotations

import pathlib
import pytest

WORKTREE = pathlib.Path(__file__).parents[1].resolve()
SERVICES_YAML = WORKTREE / "custom_components" / "pilotsuite" / "services.yaml"


class TestServicesYamlProjection:
    """Projection contract for services.yaml service-ID parity."""

    def _load_yaml(self):
        import yaml
        with SERVICES_YAML.open() as fh:
            return yaml.safe_load(fh.read())

    def test_sv1_no_legacy_unifi_service_ids(self) -> None:
        """SV1: No copilot_ha_unifi_* legacy service IDs in services.yaml."""
        import yaml
        with SERVICES_YAML.open() as fh:
            raw = fh.read()
        assert "copilot_ha_unifi_run_diagnostics" not in raw, (
            "Legacy service copilot_ha_unifi_run_diagnostics still in services.yaml"
        )
        assert "copilot_ha_unifi_get_report" not in raw, (
            "Legacy service copilot_ha_unifi_get_report still in services.yaml"
        )

    def test_sv2_canonical_unifi_service_ids_present(self) -> None:
        """SV2: Canonical pilotsuite unifi service IDs present in services.yaml."""
        import yaml
        with SERVICES_YAML.open() as fh:
            data = yaml.safe_load(fh.read())
        services = data if isinstance(data, dict) else {}
        assert "unifi_run_diagnostics" in services, (
            "Canonical unifi_run_diagnostics not in services.yaml"
        )
        assert "unifi_get_report" in services, (
            "Canonical unifi_get_report not in services.yaml"
        )

    def test_sv3_no_copilot_ha_literals(self) -> None:
        """SV3: No copilot_ha string literals at all in services.yaml."""
        with SERVICES_YAML.open() as fh:
            raw = fh.read()
        assert "copilot_ha" not in raw, (
            "Unexpected copilot_ha literals still present in services.yaml"
        )
