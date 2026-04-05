"""conftest.py — stub homeassistant.* before any HA integration imports.

This must load before any custom_components.copilot_ha module,
because sensor/coordinator files import homeassistant.core directly.
"""
from __future__ import annotations

import sys
from unittest.mock import MagicMock

for _mod in [
    "homeassistant",
    "homeassistant.core",
    "homeassistant.config_entries",
    "homeassistant.helpers",
    "homeassistant.helpers.area_registry",
    "homeassistant.helpers.device_registry",
    "homeassistant.helpers.entity_registry",
    "homeassistant.helpers.service",
    "homeassistant.helpers.config_validation",
    "homeassistant.helpers.entity_platform",
    "homeassistant.helpers.update_coordinator",
    "homeassistant.const",
    "homeassistant.components",
    "homeassistant.components.sensor",
    "homeassistant.components.binary_sensor",
    "homeassistant.components.select",
    "homeassistant.components.button",
    "homeassistant.util",
    "homeassistant.util.yaml",
    "homeassistant.util.json",
    "homeassistant.exceptions",
]:
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

# Make key classes available as mock objects
import voluptuous as vol
sys.modules["homeassistant"].core = MagicMock()
sys.modules["homeassistant"].core.HomeAssistant = MagicMock()
sys.modules["homeassistant"].core.callback = getattr(MagicMock(), "callback", lambda f: f)
sys.modules["homeassistant"].config_entries = MagicMock()
sys.modules["homeassistant"].config_entries.ConfigEntry = MagicMock()
sys.modules["homeassistant"].components = MagicMock()
sys.modules["homeassistant"].components.sensor = MagicMock()
sys.modules["homeassistant"].components.sensor.SensorEntity = MagicMock()
sys.modules["homeassistant"].components.binary_sensor = MagicMock()
sys.modules["homeassistant"].components.binary_sensor.BinarySensorEntity = MagicMock()
sys.modules["homeassistant"].components.select = MagicMock()
sys.modules["homeassistant"].components.select.SelectEntity = MagicMock()
sys.modules["homeassistant"].components.button = MagicMock()
sys.modules["homeassistant"].components.button.ButtonEntity = MagicMock()
sys.modules["homeassistant"].helpers = MagicMock()
sys.modules["homeassistant"].helpers.entity_platform = MagicMock()
sys.modules["homeassistant"].helpers.entity_platform.AddEntitiesCallback = MagicMock()
sys.modules["homeassistant"].helpers.update_coordinator = MagicMock()
sys.modules["homeassistant"].helpers.update_coordinator.CoordinatorEntity = MagicMock()
sys.modules["homeassistant"].const = MagicMock()
sys.modules["homeassistant"].util = MagicMock()
sys.modules["homeassistant"].util.yaml = MagicMock()
sys.modules["homeassistant"].util.json = MagicMock()
sys.modules["homeassistant"].exceptions = MagicMock()
