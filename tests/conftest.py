"""conftest.py — comprehensive homeassistant stub for CI runner.

Uses types.ModuleType with __path__ so every stub is treated as a real
package/sub-package by Python's import system. Stubs ALL homeassistant modules
that the integration's sensor + coordinator files import.
"""
from __future__ import annotations

import sys
import types
from datetime import datetime, timezone
from unittest.mock import MagicMock
import voluptuous as vol


def stub(name: str) -> types.ModuleType:
    mod = types.ModuleType(name)
    mod.__path__ = []
    sys.modules[name] = mod
    return mod


def leaf(name: str) -> types.ModuleType:
    mod = types.ModuleType(name)
    sys.modules[name] = mod
    return mod


# ─── full package tree ───────────────────────────────────────────────────────────
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
hc.HomeAssistant = type("HomeAssistant", (), {"data": {}})
hc.callback = lambda f: f
hc.Event = type("Event", (), {})
hc.State = type("State", (), {})

# ─── homeassistant.helpers.update_coordinator ───────────────────────────────────
hup = sys.modules["homeassistant.helpers.update_coordinator"]
hup.DataUpdateCoordinator = type("DataUpdateCoordinator", (), {})
hup.UpdateFailed = type("UpdateFailed", (Exception,), {})
hup.CoordinatorEntity = type("CoordinatorEntity", (), {})

# ─── homeassistant.helpers.entity ──────────────────────────────────────────────
he = sys.modules["homeassistant.helpers.entity"]
he.Entity = type("Entity", (), {})
he.EntityCategory = type("EntityCategory", (), {})
he.DeviceInfo = type("DeviceInfo", (), {})

# ─── homeassistant.helpers.device_registry ──────────────────────────────────────
hdr = sys.modules["homeassistant.helpers.device_registry"]
hdr.DeviceInfo = type("DeviceInfo", (), {})

# ─── homeassistant.helpers.aiohttp_client ─────────────────────────────────────
haio = sys.modules["homeassistant.helpers.aiohttp_client"]
haio.async_get_clientsession = MagicMock(return_value=MagicMock())

# ─── homeassistant.helpers.entity_platform ─────────────────────────────────────
hep = sys.modules["homeassistant.helpers.entity_platform"]
hep.AddEntitiesCallback = type("AddEntitiesCallback", (), {})

# ─── homeassistant.helpers.storage ─────────────────────────────────────────────
hst = sys.modules["homeassistant.helpers.storage"]
hst.Store = type("Store", (), {})

# ─── homeassistant.helpers.dispatcher ─────────────────────────────────────────
hdis = sys.modules["homeassistant.helpers.dispatcher"]
hdis.dispatcher_connect = MagicMock()
hdis.dispatcher_send = MagicMock()

# ─── homeassistant.helpers ─────────────────────────────────────────────────────
sys.modules["homeassistant.helpers"].cv = vol
sys.modules["homeassistant.helpers"].entity_registry = types.ModuleType("homeassistant.helpers.entity_registry")

# ─── homeassistant.util.dt ─────────────────────────────────────────────────────
_dt = types.ModuleType("homeassistant.util.dt")
_dt.as_utc = lambda s: s
_dt.as_local = lambda s: s
_dt.now = lambda: datetime.now(timezone.utc)
_dt.utcnow = lambda: datetime.now(timezone.utc)
_dt.get_age = lambda *a, **kw: "just now"
sys.modules["homeassistant.util.dt"] = _dt

# ─── homeassistant.components.* ─────────────────────────────────────────────────
_hcs = sys.modules["homeassistant.components.sensor"]
_hcs.SensorEntity = type("SensorEntity", (), {})
_hcs.SensorDeviceClass = type("SensorDeviceClass", (), {})

for _comp, _cls in [
    ("binary_sensor", "BinarySensorEntity"),
    ("select", "SelectEntity"),
    ("button", "ButtonEntity"),
    ("camera", "Camera"),
]:
    _m = sys.modules[f"homeassistant.components.{_comp}"]
    setattr(_m, _cls, type(_cls, (), {}))

# ─── config_entries + const ────────────────────────────────────────────────────
sys.modules["homeassistant.config_entries"].ConfigEntry = type("ConfigEntry", (), {})
_const = types.ModuleType("homeassistant.const")
_const.EVENT_HOMEASSISTANT_START = "homeassistant.start"
sys.modules["homeassistant.const"] = _const

# ─── config_validation = voluptuous ─────────────────────────────────────────────
sys.modules["homeassistant.helpers.config_validation"] = vol
