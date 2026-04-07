"""Media sensors for PilotSuite Neurons with Anomaly Framework integration.

Sensors:
- MediaActivitySensor: Media activity detection
- MediaIntensitySensor: Media intensity/volume
- MediaAnomalySensor: Sigma-deviation based media anomaly detection
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Optional

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from ..const import DOMAIN
from ..coordinator import CopilotDataUpdateCoordinator
from ..anomaly_framework import get_framework, AnomalyLevel

_LOGGER = logging.getLogger(__name__)

_MEDIA_CACHE_DURATION: float = 5.0
_VOLUME_LOW: float = 30.0
_VOLUME_MEDIUM: float = 60.0
_DEFAULT_VOLUME: float = 0.5
_TV_KEYWORDS: tuple[str, ...] = ("tv", "fernseher", "living room tv",
                                  "wohnzimmer tv", "fernseher im wohnzimmer")
_MAX_PLAYING_FOR_SCORE: int = 3


@dataclass
class MediaCache:
    states: list[State]
    timestamp: float


class MediaStateCache:
    def __init__(self) -> None:
        self._cache: MediaCache | None = None

    def get_states(self, hass: HomeAssistant, max_age: float = _MEDIA_CACHE_DURATION) -> list[State]:
        now: float = time.time()
        if self._cache is not None and (now - self._cache.timestamp) < max_age:
            return self._cache.states
        states: list[State] = hass.states.async_all("media_player")
        self._cache = MediaCache(states=states, timestamp=now)
        return states

    def invalidate(self) -> None:
        self._cache = None


_media_cache = MediaStateCache()


class MediaActivitySensor(CoordinatorEntity, SensorEntity):
    _attr_name: str = "PilotSuite Media Activity"
    _attr_unique_id: str = "ai_copilot_media_activity"
    _attr_icon: str = "mdi:play-circle"
    _attr_should_poll: bool = False

    def __init__(
        self,
        coordinator: CopilotDataUpdateCoordinator,
        hass: HomeAssistant,
    ) -> None:
        super().__init__(coordinator)
        self._hass: HomeAssistant = hass

    @property
    def native_value(self) -> str:
        return self.coordinator.data.get("media_activity", "idle") if self.coordinator.data else "idle"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs: dict[str, Any] = {}
        if self.coordinator.data:
            attrs = self.coordinator.data.get("media_activity_attrs", {})
        return attrs

    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()


class MediaIntensitySensor(CoordinatorEntity, SensorEntity):
    _attr_name: str = "PilotSuite Media Intensity"
    _attr_unique_id: str = "ai_copilot_media_intensity"
    _attr_icon: str = "mdi:volume-high"
    _attr_should_poll: bool = False

    def __init__(
        self,
        coordinator: CopilotDataUpdateCoordinator,
        hass: HomeAssistant,
    ) -> None:
        super().__init__(coordinator)
        self._hass: HomeAssistant = hass

    @property
    def native_value(self) -> float:
        if not self.coordinator.data:
            return 0.0
        return float(self.coordinator.data.get("media_intensity", 0))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs: dict[str, Any] = {"level": "off"}
        if self.coordinator.data:
            intensity = self.coordinator.data.get("media_intensity", 0)
            if intensity >= _VOLUME_MEDIUM:
                attrs["level"] = "high"
            elif intensity >= _VOLUME_LOW:
                attrs["level"] = "medium"
            elif intensity > 0:
                attrs["level"] = "low"
            else:
                attrs["level"] = "off"
            attrs["playing_count"] = self.coordinator.data.get("playing_count", 0)
        return attrs

    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()


class MediaAnomalySensor(CoordinatorEntity, SensorEntity):
    """Media anomaly detection using sigma-deviation from learned baseline."""

    _attr_name: str = "PilotSuite Media Anomaly"
    _attr_unique_id: str = "ai_copilot_media_anomaly"
    _attr_icon: str = "mdi:play-circle-outline"
    _attr_should_poll: bool = False

    def __init__(
        self,
        coordinator: CopilotDataUpdateCoordinator,
        hass: HomeAssistant,
    ) -> None:
        super().__init__(coordinator)
        self._hass: HomeAssistant = hass
        self._level = "normal"
        self._framework = None

    @property
    def native_value(self) -> str:
        return self._level

    @property
    def icon(self) -> str:
        return {
            "critical": "mdi:alert-octagon",
            "high": "mdi:alert",
            "medium": "mdi:alert-circle-outline",
            "low": "mdi:information",
            "normal": "mdi:check-decagram",
        }.get(self._level, "mdi:help-circle")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs: dict[str, Any] = {
            "anomaly_framework": "sigma_deviation",
            "baseline_window_days": 7,
        }
        if self._framework:
            media_alerts = [a for a in self._framework._alerts
                           if a.sensor_type == "media"]
            if media_alerts:
                latest = media_alerts[-1]
                attrs.update({
                    "confidence": latest.confidence,
                    "deviation_sigma": round(latest.deviation_sigma, 2),
                    "failure_prediction_48h": latest.predicted_48h,
                    "baseline_mean": latest.baseline_mean,
                    "current_value": latest.current_value,
                    "message": latest.message,
                })
        return attrs

    def _handle_coordinator_update(self) -> None:
        self._framework = get_framework(self._hass)
        # Feed media intensity into anomaly framework
        if self.coordinator.data:
            intensity = self.coordinator.data.get("media_intensity", 0)
            if intensity:
                alert = self._framework.record(
                    sensor_type="media",
                    sensor_id="media_intensity",
                    metric="intensity_score",
                    value=float(intensity),
                )
                if alert:
                    self._level = alert.level.value
                    _LOGGER.info(
                        "Media anomaly: %.1fσ, confidence %.0f%%, level=%s",
                        alert.deviation_sigma, alert.confidence, alert.level.value
                    )
                else:
                    self._level = "normal"
        self.async_write_ha_state()
