"""Energy Report Sensor for Home Assistant (v5.13.0).

Exposes weekly energy report highlights as an HA sensor.
State shows the weekly net cost in EUR.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from ..entity import CopilotBaseEntity

_LOGGER = logging.getLogger(__name__)


def _as_mapping(value: Any) -> dict[str, Any]:
    """Return a safe mapping for projection work."""
    return value if isinstance(value, dict) else {}


def _extract_usage_pattern_export(payload: Any) -> dict[str, Any]:
    """Unwrap the bounded usage-pattern export payload."""
    payload = _as_mapping(payload)
    for candidate in (
        payload.get("export"),
        payload.get("data"),
        payload.get("report"),
        payload,
    ):
        mapped = _as_mapping(candidate)
        if any(key in mapped for key in ("patterns", "impact", "drift", "window")):
            return mapped
    return {}


class EnergyReportSensor(CopilotBaseEntity, SensorEntity):
    """Sensor showing latest energy report highlights."""

    _attr_name = "Energy Report"
    _attr_unique_id = "copilot_energy_report"
    _attr_icon = "mdi:file-chart-outline"
    _attr_native_unit_of_measurement = "EUR"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._data: dict[str, Any] = {}

    @property
    def native_value(self) -> float | None:
        impact = _as_mapping(self._data.get("impact"))
        value = impact.get("estimated_cost_impact_eur")
        return value if isinstance(value, (int, float)) else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        window = _as_mapping(self._data.get("window"))
        impact = _as_mapping(self._data.get("impact"))
        drift_summary = _as_mapping(_as_mapping(self._data.get("drift")).get("summary"))
        patterns = self._data.get("patterns") if isinstance(self._data.get("patterns"), list) else []
        recommendations = (
            self._data.get("recommendations") if isinstance(self._data.get("recommendations"), list) else []
        )
        return {
            "report_type": "usage_patterns_export",
            "period_start": window.get("from", ""),
            "period_end": window.get("to", ""),
            "pattern_count": len(patterns),
            "recommendations_count": len(recommendations),
            "estimated_energy_impact_kwh": impact.get("estimated_energy_impact_kwh", 0),
            "estimated_cost_impact_eur": impact.get("estimated_cost_impact_eur", 0),
            "new_patterns": drift_summary.get("new_patterns", 0),
            "fading_patterns": drift_summary.get("fading_patterns", 0),
            "rising_patterns": drift_summary.get("rising_patterns", 0),
            "top_pattern_ids": [
                pattern.get("pattern_id")
                for pattern in patterns[:3]
                if isinstance(pattern, dict) and pattern.get("pattern_id")
            ],
        }

    async def async_update(self) -> None:
        session = async_get_clientsession(self.hass)
        url = f"{self._core_base_url()}/api/v1/energy/reports/usage-patterns/export"
        headers = self._core_headers()
        try:
            async with session.get(url, headers=headers, timeout=15) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    export_payload = _extract_usage_pattern_export(data)
                    if export_payload:
                        self._data = export_payload
                else:
                    _LOGGER.warning("Energy report API returned %s", resp.status)
        except Exception as exc:
            _LOGGER.error("Failed to fetch energy report: %s", exc)
