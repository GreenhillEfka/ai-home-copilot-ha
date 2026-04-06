"""conftest.py — comprehensive homeassistant stub for CI runner.

Every stub class inherits from object so super().__init__() works.
Uses types.ModuleType with __path__ for proper package treatment.
"""
from __future__ import annotations

import sys
import types
import os
from datetime import datetime, timezone
from typing import Generic, TypeVar
from unittest.mock import MagicMock
import voluptuous as vol
import pytest

_T = TypeVar("_T")


def stub(name: str) -> types.ModuleType:
    mod = types.ModuleType(name)
    mod.__path__ = []
    sys.modules[name] = mod
    return mod


def leaf(name: str) -> types.ModuleType:
    mod = types.ModuleType(name)
    sys.modules[name] = mod
    return mod


# ─── package tree ────────────────────────────────────────────────────────────────
stub("homeassistant")
stub("homeassistant.core")
stub("homeassistant.config_entries")
stub("homeassistant.helpers")
stub("homeassistant.helpers.area_registry")
stub("homeassistant.helpers.device_registry")
stub("homeassistant.helpers.entity_registry")
stub("homeassistant.helpers.service")
stub("homeassistant.helpers.entity")
stub("homeassistant.helpers.entity_platform")
stub("homeassistant.helpers.update_coordinator")
stub("homeassistant.helpers.aiohttp_client")
stub("homeassistant.helpers.storage")
stub("homeassistant.helpers.dispatcher")
stub("homeassistant.const")
stub("homeassistant.components")
stub("homeassistant.components.sensor")
stub("homeassistant.components.binary_sensor")
stub("homeassistant.components.select")
stub("homeassistant.components.button")
stub("homeassistant.components.camera")
stub("homeassistant.util")
leaf("homeassistant.util.dt")
stub("homeassistant.util.yaml")
stub("homeassistant.util.json")
leaf("homeassistant.exceptions")

# ─── homeassistant.core ────────────────────────────────────────────────────────
hc = sys.modules["homeassistant.core"]
hc.HomeAssistant = type("HomeAssistant", (object,), {"data": {}})
hc.callback = staticmethod(lambda f: f)
hc.Event = type("Event", (object,), {})
hc.State = type("State", (object,), {})

# ─── homeassistant.helpers.update_coordinator ────────────────────────────────────
hup = sys.modules["homeassistant.helpers.update_coordinator"]

def _coordinator_init(self, *args, **kwargs):
    pass

hup.DataUpdateCoordinator = type("DataUpdateCoordinator", (object,), {"__init__": _coordinator_init})
hup.UpdateFailed = type("UpdateFailed", (Exception, object), {})

class _CoordinatorEntity(Generic[_T], object):
    __class_getitem__ = classmethod(lambda cls, item: _CoordinatorEntity)
    def __init__(self, coordinator, *args, **kwargs):
        self.coordinator = coordinator
        super().__init__(*args, **kwargs)
hup.CoordinatorEntity = _CoordinatorEntity

# ─── homeassistant.helpers.entity ───────────────────────────────────────────────
he = sys.modules["homeassistant.helpers.entity"]

class _Entity(object):
    _attr_name: str | None = None
    _attr_state: str | None = None
    _attr_icon: str | None = None
    _attr_extra_state_attributes: dict | None = None
    _attr_device_class: str | None = None
    _attr_unique_id: str | None = None
    _attr_available: bool = True
    _attr_should_poll: bool = False
    _attr_native_value: object | None = None
    _attr_native_unit_of_measurement: str | None = None

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def state(self) -> str | None:
        return self._attr_state

    @property
    def native_value(self) -> object | None:
        return self._attr_native_value

    @property
    def name(self) -> str | None:
        return self._attr_name

    @property
    def icon(self) -> str | None:
        return self._attr_icon

    @property
    def extra_state_attributes(self) -> dict | None:
        return self._attr_extra_state_attributes

    @property
    def device_class(self) -> str | None:
        return self._attr_device_class

    @property
    def available(self) -> bool:
        return self._attr_available

    async def async_update(self):
        pass

he.Entity = type("Entity", (object,), {
    "__init__": lambda self, **k: _Entity(**k).__init__(**k),
    "_attr_name": None,
    "_attr_state": None,
    "_attr_icon": None,
    "_attr_extra_state_attributes": None,
    "_attr_device_class": None,
    "_attr_unique_id": None,
    "_attr_available": True,
    "_attr_should_poll": False,
    "_attr_native_value": None,
    "_attr_native_unit_of_measurement": None,
    "state": property(lambda self: self._attr_state),
    "native_value": property(lambda self: self._attr_native_value),
    "name": property(lambda self: self._attr_name),
    "icon": property(lambda self: self._attr_icon),
    "extra_state_attributes": property(lambda self: self._attr_extra_state_attributes),
    "device_class": property(lambda self: self._attr_device_class),
    "available": property(lambda self: self._attr_available),
    "async_update": lambda self: None,
})

class _EntityCategory(object):
    DIAGNOSTIC = "diagnostic"
    CONFIG = "config"
    CONFIGURATOR = "configurator"

he.EntityCategory = _EntityCategory
he.DeviceInfo = type("DeviceInfo", (object,), {"__init__": lambda self, *a, **k: None})

# ─── homeassistant.helpers.device_registry ──────────────────────────────────────
hdr = sys.modules["homeassistant.helpers.device_registry"]
hdr.DeviceInfo = type("DeviceInfo", (object,), {"__init__": lambda self, *a, **k: None})

# ─── homeassistant.helpers.aiohttp_client ───────────────────────────────────────
haio = sys.modules["homeassistant.helpers.aiohttp_client"]


class _FakeSessionGet:
    """Fake session.get() returning an async context manager (for aiohttp protocol)."""
    def __init__(self, handler):
        self._handler = handler  # callable(url, headers, timeout) → coroutine

    async def __call__(self, url, headers=None, timeout=None):
        return await self._handler(url, headers, timeout)

    def __await__(self):
        return self._handler(None).__await__()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None


class _FakeSession:
    """Fake aiohttp client session with async context manager + get protocol."""
    def __init__(self, get_handler=None):
        self.get = _FakeSessionGet(get_handler or (lambda *a, **k: _FakeResponse(404, {})))

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None


class _FakeResponse:
    """Fake aiohttp response."""
    def __init__(self, status, json_data):
        self.status = status
        self._json = json_data

    async def json(self):
        return self._json

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None


async def _default_session_maker(hass):
    """Default session factory — returns a bare FakeSession."""
    return _FakeSession()


haio.async_get_clientsession = MagicMock(side_effect=_default_session_maker)
haio._FakeSession = _FakeSession  # expose for tests if needed
haio._FakeResponse = _FakeResponse  # expose for tests if needed

# ─── homeassistant.helpers.entity_platform ──────────────────────────────────────
hep = sys.modules["homeassistant.helpers.entity_platform"]
hep.AddEntitiesCallback = type("AddEntitiesCallback", (object,), {"__init__": lambda self, *a, **k: None})

# ─── homeassistant.helpers.storage ───────────────────────────────────────────────
hst = sys.modules["homeassistant.helpers.storage"]
hst.Store = type("Store", (object,), {"__init__": lambda self, *a, **k: None})

# ─── homeassistant.helpers.dispatcher ───────────────────────────────────────────
hdis = sys.modules["homeassistant.helpers.dispatcher"]
hdis.async_dispatcher_connect = MagicMock()
hdis.async_dispatcher_send = MagicMock()

# ─── homeassistant.helpers ──────────────────────────────────────────────────────
sys.modules["homeassistant.helpers"].cv = vol
sys.modules["homeassistant.helpers"].entity_registry = types.ModuleType("homeassistant.helpers.entity_registry")

# ─── homeassistant.util.dt ──────────────────────────────────────────────────────
_dt = types.ModuleType("homeassistant.util.dt")
_dt.as_utc = lambda s: s
_dt.as_local = lambda s: s
_dt.now = lambda: datetime.now(timezone.utc)
_dt.utcnow = lambda: datetime.now(timezone.utc)
_dt.get_age = lambda *a, **kw: "just now"
sys.modules["homeassistant.util.dt"] = _dt

# ─── homeassistant.components.sensor ─────────────────────────────────────────────
_hcs = sys.modules["homeassistant.components.sensor"]
_hcs.SensorEntity = type("SensorEntity", (object,), {"__init__": lambda self, *a, **k: None})
_hcs.SensorDeviceClass = type("SensorDeviceClass", (object,), {
    "ENERGY": "energy",
    "POWER": "power",
    "TEMPERATURE": "temperature",
    "HUMIDITY": "humidity",
    "BATTERY": "battery",
    "ILLUMINANCE": "illuminance",
    "MONETARY": "monetary",
    "TIMESTAMP": "timestamp",
    "DURATION": "duration",
    "DATA_SIZE": "data_size",
    "SWITCH": "switch",
    "VOLUME": "volume",
    "WEIGHT": "weight",
    "ENUM": "enum",
    "NONE": "None",
    "DATE": "date",
    "APPARENT_POWER": "apparent_power",
    "POWER_FACTOR": "power_factor",
})
_hcs.SensorStateClass = type("SensorStateClass", (object,), {
    "MEASUREMENT": "measurement",
    "TOTAL_INCREASING": "total_increasing",
    "TOTAL": "total",
})

# ─── homeassistant.components.binary_sensor ──────────────────────────────────────
_hcbs = sys.modules["homeassistant.components.binary_sensor"]
_hcbs.BinarySensorEntity = type("BinarySensorEntity", (object,), {"__init__": lambda self, *a, **k: None})
_hcbs.BinarySensorDeviceClass = type("BinarySensorDeviceClass", (object,), {
    "OCCUPANCY": "occupancy",
    "MOTION": "motion",
    "DOOR": "door",
    "WINDOW": "window",
    "SMOKE": "smoke",
    "CO": "carbon_monoxide",
    "MOISTURE": "moisture",
    "GAS": "gas",
    "SAFETY": "safety",
    "BATTERY": "battery",
    "POWER": "power",
    "LOCK": "lock",
    "PRESENCE": "presence",
    "TAMPER": "tamper",
    "CONNECTED": "connectivity",
    "COLD": "cold",
    "DRY": "dry",
    "HEAT": "heat",
    "LIGHT": "light",
    "NOT_HOME": "not_home",
    "OCCUPIED": "occupied",
    "PLAYING": "playing",
    "PROBLEM": "problem",
    "RUNNING": "running",
    "UNSAFE": "unsafe",
    "BELL": "bell",
    "CHARGING": "charging",
    "ENTRY": "entry",
    "JAMMING": "jamming",
    "CLOSED": "closed",
    "NONE": "none",
    "STATE_ON": "on",
    "STATE_OFF": "off",
    "__init__": lambda self, *a, **k: None,
})

# ─── remaining components ───────────────────────────────────────────────────────
for _comp, _cls_name in [
    ("select", "SelectEntity"),
    ("button", "ButtonEntity"),
    ("camera", "Camera"),
]:
    _m = sys.modules[f"homeassistant.components.{_comp}"]
    setattr(_m, _cls_name, type(_cls_name, (object,), {"__init__": lambda self, *a, **k: None}))

# ─── config_entries + const ────────────────────────────────────────────────────
sys.modules["homeassistant.config_entries"].ConfigEntry = type("ConfigEntry", (object,), {"__init__": lambda self, *a, **k: None})
_const = types.ModuleType("homeassistant.const")
_const.EVENT_HOMEASSISTANT_START = "homeassistant.start"
sys.modules["homeassistant.const"] = _const

# ─── config_validation = voluptuous ──────────────────────────────────────────────
sys.modules["homeassistant.helpers.config_validation"] = vol

# ─── custom_components stub (for sensor unit tests) ─────────────────────────────
_copilot_ha_root = os.path.join(os.path.dirname(__file__), "..", "custom_components", "copilot_ha")
_copilot_ha = stub("custom_components.copilot_ha")
_copilot_ha.__path__ = [_copilot_ha_root]
# Stub child packages so relative imports resolve
for _sub in ("sensors", "core", "api"):
    _submod = stub(f"custom_components.copilot_ha.{_sub}")
    _submod.__path__ = [os.path.join(_copilot_ha_root, _sub)]

# ─── Sensor test fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def coordinator():
    """Minimal coordinator mock for sensor unit tests."""
    from unittest.mock import MagicMock
    coord = MagicMock()
    coord.api = MagicMock()
    coord.data = {}
    coord._config = {"host": "testhost", "port": 8909, "token": "testtoken"}
    return coord
