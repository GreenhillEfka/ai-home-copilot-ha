"""conftest.py — comprehensive homeassistant stub for CI runner.

Every stub class inherits from object so super().__init__() works.
Uses types.ModuleType with __path__ for proper package treatment.
"""
from __future__ import annotations

import sys
import types
from datetime import datetime, timezone
from typing import Generic, TypeVar
from unittest.mock import MagicMock
import voluptuous as vol

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


def cls(name: str, bases=(), ns=None):
    """Create a class inheriting from object so super().__init__ works."""
    return type(name, bases + (object,), ns or {})


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
hc.HomeAssistant = cls("HomeAssistant", (), {"data": {}})
hc.callback = staticmethod(lambda f: f)
hc.Event = cls("Event")
hc.State = cls("State")

# ─── homeassistant.helpers.update_coordinator ────────────────────────────────────
hup = sys.modules["homeassistant.helpers.update_coordinator"]
hup.DataUpdateCoordinator = cls("DataUpdateCoordinator")
hup.UpdateFailed = cls("UpdateFailed", (Exception,))

# CoordinatorEntity must support [] subscripting (is a Generic in real HA)
class _CoordEnt(Generic[_T]):
    __class_getitem__ = classmethod(lambda cls, item: _CoordEnt)
hup.CoordinatorEntity = _CoordEnt

# ─── homeassistant.helpers.entity ────────────────────────────────────────────────
he = sys.modules["homeassistant.helpers.entity"]
he.Entity = cls("Entity")
he.EntityCategory = cls("EntityCategory")
he.EntityCategory.DIAGNOSTIC = "diagnostic"
he.EntityCategory.CONFIG = "config"
he.EntityCategory.CONFIGURATOR = "configurator"
he.DeviceInfo = cls("DeviceInfo")

# ─── homeassistant.helpers.device_registry ──────────────────────────────────────
hdr = sys.modules["homeassistant.helpers.device_registry"]
hdr.DeviceInfo = cls("DeviceInfo")

# ─── homeassistant.helpers.aiohttp_client ───────────────────────────────────────
haio = sys.modules["homeassistant.helpers.aiohttp_client"]
haio.async_get_clientsession = MagicMock(return_value=MagicMock())

# ─── homeassistant.helpers.entity_platform ──────────────────────────────────────
hep = sys.modules["homeassistant.helpers.entity_platform"]
hep.AddEntitiesCallback = cls("AddEntitiesCallback")

# ─── homeassistant.helpers.storage ───────────────────────────────────────────────
hst = sys.modules["homeassistant.helpers.storage"]
hst.Store = cls("Store")

# ─── homeassistant.helpers.dispatcher ───────────────────────────────────────────
hdis = sys.modules["homeassistant.helpers.dispatcher"]
hdis.async_dispatcher_connect = MagicMock()
hdis.async_dispatcher_send = MagicMock()

# ─── homeassistant.helpers ───────────────────────────────────────────────────────
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
_hcs.SensorEntity = cls("SensorEntity")
_hcs.SensorDeviceClass = cls("SensorDeviceClass")

# ─── homeassistant.components.binary_sensor ──────────────────────────────────────
_hcbs = sys.modules["homeassistant.components.binary_sensor"]
_hcbs.BinarySensorEntity = cls("BinarySensorEntity")
_hcbs.BinarySensorDeviceClass = cls("BinarySensorDeviceClass")

# ─── remaining components ───────────────────────────────────────────────────────
for _comp, _cls_name in [
    ("select", "SelectEntity"),
    ("button", "ButtonEntity"),
    ("camera", "Camera"),
]:
    _m = sys.modules[f"homeassistant.components.{_comp}"]
    setattr(_m, _cls_name, cls(_cls_name))

# ─── config_entries + const ─────────────────────────────────────────────────────
sys.modules["homeassistant.config_entries"].ConfigEntry = cls("ConfigEntry")
_const = types.ModuleType("homeassistant.const")
_const.EVENT_HOMEASSISTANT_START = "homeassistant.start"
sys.modules["homeassistant.const"] = _const

# ─── config_validation = voluptuous ──────────────────────────────────────────────
sys.modules["homeassistant.helpers.config_validation"] = vol
