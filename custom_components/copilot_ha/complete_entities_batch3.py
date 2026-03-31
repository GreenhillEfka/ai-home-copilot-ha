"""Complete Entities Batch 3: Intelligence APIs (RAG, Anomaly, Energy, Weather, Calendar)."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN, SIGNAL_MODULE_UPDATE
from .entity import CopilotBaseEntity
from .api_wrapper import PilotSuiteAPI

_LOGGER = logging.getLogger(__name__)


# =============================================================================
# BATCH 3: Intelligence Entities (RAG, Anomaly, Energy, Weather, Calendar)
# =============================================================================

class EnergyForecastSensor(CopilotBaseEntity, SensorEntity):
    """Energy forecast sensor."""
    
    _attr_icon = "mdi:lightning-bolt"
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = "kWh"
    _attr_state_class = SensorStateClass.MEASUREMENT
    
    def __init__(self, api: PilotSuiteAPI):
        super().__init__(api.api)
        self._attr_unique_id = "pilotsuite_energy_forecast"
        self._attr_name = "PilotSuite Energy Forecast"
        self._attr_native_value = 0.0
        self._attr_extra_state_attributes = {
            "forecast_24h": 0.0,
            "forecast_7d": 0.0,
            "pv_forecast": 0.0,
            "optimization_potential": 0.0,
        }
    
    @callback
    def _handle_update(self, data: dict) -> None:
        """Handle update."""
        self._attr_native_value = data.get("current_consumption", 0.0)
        self._attr_extra_state_attributes.update({
            "forecast_24h": data.get("forecast_24h", 0.0),
            "forecast_7d": data.get("forecast_7d", 0.0),
            "pv_forecast": data.get("pv_forecast", 0.0),
            "optimization_potential": data.get("optimization_potential", 0.0),
        })
        self.async_write_ha_state()
    
    async def async_added_to_hass(self) -> None:
        """Register update dispatcher."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_MODULE_UPDATE, self._handle_update)
        )
        await self._async_update()
    
    async def _async_update(self) -> None:
        """Fetch latest data."""
        try:
            data = await self._api.energy.get_consumption_forecast(hours=24)
            self._handle_update(data)
        except Exception as e:
            _LOGGER.debug("Failed to fetch energy forecast: %s", e)


class WeatherSensor(CopilotBaseEntity, SensorEntity):
    """Weather sensor."""
    
    _attr_icon = "mdi:weather-partly-cloudy"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = "°C"
    _attr_state_class = SensorStateClass.MEASUREMENT
    
    def __init__(self, api: PilotSuiteAPI):
        super().__init__(api.api)
        self._attr_unique_id = "pilotsuite_weather"
        self._attr_name = "PilotSuite Weather"
        self._attr_native_value = 20.0
        self._attr_extra_state_attributes = {
            "condition": "clear",
            "humidity": 50,
            "pressure": 1013,
            "wind_speed": 0,
            "forecast": [],
        }
    
    @callback
    def _handle_update(self, data: dict) -> None:
        """Handle update."""
        self._attr_native_value = data.get("temperature", 20.0)
        self._attr_extra_state_attributes.update({
            "condition": data.get("condition", "clear"),
            "humidity": data.get("humidity", 50),
            "pressure": data.get("pressure", 1013),
            "wind_speed": data.get("wind_speed", 0),
            "forecast": data.get("forecast", [])[:3],
        })
        self.async_write_ha_state()
    
    async def async_added_to_hass(self) -> None:
        """Register update dispatcher."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_MODULE_UPDATE, self._handle_update)
        )
        await self._async_update()
    
    async def _async_update(self) -> None:
        """Fetch latest data."""
        try:
            data = await self._api.weather.get_current_weather()
            self._handle_update(data)
        except Exception as e:
            _LOGGER.debug("Failed to fetch weather: %s", e)


class CalendarSensor(CopilotBaseEntity, SensorEntity):
    """Calendar sensor."""
    
    _attr_icon = "mdi:calendar"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["idle", "event_today", "multiple_events"]
    
    def __init__(self, api: PilotSuiteAPI):
        super().__init__(api.api)
        self._attr_unique_id = "pilotsuite_calendar"
        self._attr_name = "PilotSuite Calendar"
        self._attr_native_value = "idle"
        self._attr_extra_state_attributes = {
            "events_today": 0,
            "next_event": None,
            "next_event_time": None,
        }
    
    @callback
    def _handle_update(self, data: dict) -> None:
        """Handle update."""
        events = data.get("events", [])
        
        if len(events) == 0:
            self._attr_native_value = "idle"
        elif len(events) == 1:
            self._attr_native_value = "event_today"
        else:
            self._attr_native_value = "multiple_events"
        
        self._attr_extra_state_attributes.update({
            "events_today": len(events),
            "next_event": events[0].get("summary") if events else None,
            "next_event_time": events[0].get("start") if events else None,
        })
        self.async_write_ha_state()
    
    async def async_added_to_hass(self) -> None:
        """Register update dispatcher."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_MODULE_UPDATE, self._handle_update)
        )
        await self._async_update()
    
    async def _async_update(self) -> None:
        """Fetch latest data."""
        try:
            data = await self._api.calendar.get_todays_events()
            self._handle_update(data)
        except Exception as e:
            _LOGGER.debug("Failed to fetch calendar: %s", e)


class AnomalyAlertSensor(CopilotBaseEntity, SensorEntity):
    """Anomaly alert sensor."""
    
    _attr_icon = "mdi:alert"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["ok", "warning", "critical"]
    
    def __init__(self, api: PilotSuiteAPI):
        super().__init__(api.api)
        self._attr_unique_id = "pilotsuite_anomaly_alert"
        self._attr_name = "PilotSuite Anomaly Alert"
        self._attr_native_value = "ok"
        self._attr_extra_state_attributes = {
            "active_alerts": 0,
            "last_anomaly": None,
            "sensor_health": {},
        }
    
    @callback
    def _handle_update(self, data: dict) -> None:
        """Handle update."""
        alerts = data.get("alerts", [])
        
        if len(alerts) == 0:
            self._attr_native_value = "ok"
        elif any(a.get("severity") == "critical" for a in alerts):
            self._attr_native_value = "critical"
        else:
            self._attr_native_value = "warning"
        
        self._attr_extra_state_attributes.update({
            "active_alerts": len(alerts),
            "last_anomaly": alerts[0].get("description") if alerts else None,
            "sensor_health": data.get("sensor_health", {}),
        })
        self.async_write_ha_state()
    
    async def async_added_to_hass(self) -> None:
        """Register update dispatcher."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_MODULE_UPDATE, self._handle_update)
        )
        await self._async_update()
    
    async def _async_update(self) -> None:
        """Fetch latest data."""
        try:
            data = await self._api.anomaly.get_alerts()
            self._handle_update(data)
        except Exception as e:
            _LOGGER.debug("Failed to fetch anomaly alerts: %s", e)


class RAGContextSensor(CopilotBaseEntity, SensorEntity):
    """RAG context sensor."""
    
    _attr_icon = "mdi:database-search"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["ready", "indexing", "error"]
    
    def __init__(self, api: PilotSuiteAPI):
        super().__init__(api.api)
        self._attr_unique_id = "pilotsuite_rag_context"
        self._attr_name = "PilotSuite RAG Context"
        self._attr_native_value = "ready"
        self._attr_extra_state_attributes = {
            "vector_count": 0,
            "last_index": None,
            "context_size": 0,
        }
    
    @callback
    def _handle_update(self, data: dict) -> None:
        """Handle update."""
        self._attr_native_value = data.get("status", "ready")
        self._attr_extra_state_attributes.update({
            "vector_count": data.get("vector_count", 0),
            "last_index": data.get("last_index"),
            "context_size": data.get("context_size", 0),
        })
        self.async_write_ha_state()
    
    async def async_added_to_hass(self) -> None:
        """Register update dispatcher."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_dispatcher_connect(self.hass, SIGNAL_MODULE_UPDATE, self._handle_update)
        )
        await self._async_update()
    
    async def _async_update(self) -> None:
        """Fetch latest data."""
        try:
            data = await self._api.rag.get_rag_context()
            self._handle_update(data)
        except Exception as e:
            _LOGGER.debug("Failed to fetch RAG context: %s", e)


async def async_create_batch3_entities(
    hass: HomeAssistant,
    api: PilotSuiteAPI,
    config_entry: ConfigEntry,
) -> list[SensorEntity]:
    """Create Batch 3 entities."""
    entities = []
    
    entities.append(EnergyForecastSensor(api))
    entities.append(WeatherSensor(api))
    entities.append(CalendarSensor(api))
    entities.append(AnomalyAlertSensor(api))
    entities.append(RAGContextSensor(api))
    
    return entities
