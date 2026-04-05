"""conftest.py — stub entire homeassistant package tree for CI.

Every sub-module must be registered in sys.modules BEFORE any import
of the integration code runs. Uses types.ModuleType with __path__ so
Python treats each stub as a real package, allowing
'from homeassistant.helpers.xxx import yyy' to work.
"""
from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock

import voluptuous as vol


def stub(name: str) -> types.ModuleType:
    """Create and register a stub module (treated as a package so sub-imports work)."""
    mod = types.ModuleType(name)
    mod.__path__ = []  # empty = package with no real sub-packages
    sys.modules[name] = mod
    return mod


def leaf(name: str) -> types.ModuleType:
    """Create and register a plain module (not a package)."""
    mod = types.ModuleType(name)
    sys.modules[name] = mod
    return mod


# ─── full homeassistant package tree ────────────────────────────────────────────
stub("homeassistant")
stub("homeassistant.core")
stub("homeassistant.config_entries")
stub("homeassistant.helpers")
stub("homeassistant.helpers.area_registry")
stub("homeassistant.helpers.device_registry")
stub("homeassistant.helpers.entity_registry")
stub("homeassistant.helpers.service")
stub("homeassistant.helpers.entity")          # Entity, EntityCategory
stub("homeassistant.helpers.entity_platform")  # AddEntitiesCallback
stub("homeassistant.helpers.update_coordinator")  # DataUpdateCoordinator, UpdateFailed
stub("homeassistant.helpers.aiohttp_client")   # async_get_clientsession
stub("homeassistant.const")
stub("homeassistant.components")
stub("homeassistant.components.sensor")
stub("homeassistant.components.binary_sensor")
stub("homeassistant.components.select")
stub("homeassistant.components.button")
stub("homeassistant.util")
leaf("homeassistant.util.dt")                 # dt alias used as 'homeassistant.util.dt'
stub("homeassistant.util.yaml")
stub("homeassistant.util.json")
leaf("homeassistant.exceptions")

# ─── populate homeassistant.core ────────────────────────────────────────────────
hc = sys.modules["homeassistant.core"]

class _HomeAssistant:
    data: dict = {}

class _FakeEvent:
    def __init__(self, **kw): vars(self).update(kw)

class _FakeState:
    def __init__(self, **kw): vars(self).update(kw)

hc.HomeAssistant = _HomeAssistant
hc.callback = lambda f: f
hc.Event = _FakeEvent
hc.State = _FakeState

# ─── populate homeassistant.helpers.update_coordinator ──────────────────────────
hup = sys.modules["homeassistant.helpers.update_coordinator"]
hup.DataUpdateCoordinator = type("DataUpdateCoordinator", (), {})
hup.UpdateFailed = type("UpdateFailed", (Exception,), {})
hup.CoordinatorEntity = type("CoordinatorEntity", (), {})

# ─── populate homeassistant.helpers.entity ─────────────────────────────────────
he = sys.modules["homeassistant.helpers.entity"]
he.Entity = type("Entity", (), {})
he.EntityCategory = type("EntityCategory", (), {})

# ─── populate homeassistant.helpers.aiohttp_client ─────────────────────────────
haio = sys.modules["homeassistant.helpers.aiohttp_client"]
haio.async_get_clientsession = MagicMock(return_value=MagicMock())

# ─── populate homeassistant.helpers.entity_platform ─────────────────────────────
hep = sys.modules["homeassistant.helpers.entity_platform"]
hep.AddEntitiesCallback = type("AddEntitiesCallback", (), {})

# ─── populate homeassistant.helpers (cv alias) ─────────────────────────────────
sys.modules["homeassistant.helpers"].cv = vol
sys.modules["homeassistant.helpers"].entity_registry = types.ModuleType("homeassistant.helpers.entity_registry")

# ─── populate homeassistant.util.dt ──────────────────────────────────────────
sys.modules["homeassistant.util.dt"] = types.ModuleType("homeassistant.util.dt")

# ─── populate homeassistant.components.* ─────────────────────────────────────
hcs = sys.modules["homeassistant.components.sensor"]
hcs.SensorEntity = type("SensorEntity", (), {})

hcbs = sys.modules["homeassistant.components.binary_sensor"]
hcbs.BinarySensorEntity = type("BinarySensorEntity", (), {})

hcsel = sys.modules["homeassistant.components.select"]
hcsel.SelectEntity = type("SelectEntity", (), {})

hcb = sys.modules["homeassistant.components.button"]
hcb.ButtonEntity = type("ButtonEntity", (), {})

# ─── populate config_entries ───────────────────────────────────────────────────
sys.modules["homeassistant.config_entries"].ConfigEntry = type("ConfigEntry", (), {})

# ─── populate const ────────────────────────────────────────────────────────────
sys.modules["homeassistant.const"] = types.ModuleType("homeassistant.const")

# ─── voluptuous as config_validation ──────────────────────────────────────────
sys.modules["homeassistant.helpers.config_validation"] = vol
