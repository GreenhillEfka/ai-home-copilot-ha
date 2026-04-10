"""Anomaly Detection v2 Sensor for Home Assistant (v6.2.0)."""

from __future__ import annotations

import logging
from typing import Any

from ..entity import CopilotBaseEntity

logger = logging.getLogger(__name__)

SCAN_INTERVAL_SECONDS = 120  # 2 minutes


def _as_int(value: Any, default: int = 0) -> int:
    """Return an integer only if the value is a finite numeric type; otherwise return default."""
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        import math
        if math.isfinite(value):
            return int(value)
        return default
    return default


def _as_mapping(value: Any) -> dict:
    """Return value as a dict, or an empty dict if not a dict."""
    if isinstance(value, dict):
        return value
    return {}


def _as_list(value: Any) -> list:
    """Return value as a list, or an empty list if not a list."""
    if isinstance(value, list):
        return value
    return []


class AnomalyDetectionSensor(CopilotBaseEntity):
    """Sensor showing anomaly detection status."""

    _attr_icon = "mdi:alert-decagram-outline"
    _attr_name = "PilotSuite Anomaly Detection"
    _attr_unique_id = "pilotsuite_anomaly_detection"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._anomaly_data: dict[str, Any] = {}

    @property
    def state(self) -> str:
        total = _as_int(self._anomaly_data.get("total_anomalies"), 0)
        critical = _as_int(self._anomaly_data.get("critical"), 0)
        if critical > 0:
            return f"{critical} kritisch"
        if total > 0:
            return f"{total} Anomalien"
        return "Normal"

    @property
    def icon(self) -> str:
        critical = _as_int(self._anomaly_data.get("critical"), 0)
        warning = _as_int(self._anomaly_data.get("warning"), 0)
        if critical > 0:
            return "mdi:alert-octagon"
        if warning > 0:
            return "mdi:alert"
        return "mdi:check-decagram"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        types = _as_mapping(self._anomaly_data.get("anomaly_types"))
        top = _as_list(self._anomaly_data.get("top_anomalies"))
        return {
            "total_entities": _as_int(self._anomaly_data.get("total_entities"), 0),
            "total_anomalies": _as_int(self._anomaly_data.get("total_anomalies"), 0),
            "critical": _as_int(self._anomaly_data.get("critical"), 0),
            "warning": _as_int(self._anomaly_data.get("warning"), 0),
            "info": _as_int(self._anomaly_data.get("info"), 0),
            "anomaly_types": types,
            "top_anomalies": top[:5],
        }

    async def async_update(self) -> None:
        data = await self._fetch("/api/v1/hub/anomalies")
        if data:
            self._anomaly_data = data
