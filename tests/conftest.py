"""conftest.py — stub homeassistant.* before any HA integration imports.

Every homeassistant sub-module must be in sys.modules as a proper ModuleType
BEFORE any import of the integration code runs — especially
homeassistant.helpers.aiohttp_client which is imported in many sensor files.
"""
from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock

# --- helper ---
def stub(name: str, is_pkg: bool = False) -> types.ModuleType:
    """Create and register a stub module."""
    mod = types.ModuleType(name)
    if is_pkg:
        mod.__path__ = []  # makes Python treat it as a package
    sys.modules[name] = mod
    return mod


# --- full homeassistant tree ---
stub("homeassistant", is_pkg=True)
stub("homeassistant.core", is_pkg=True)
stub("homeassistant.config_entries", is_pkg=True)
stub("homeassistant.helpers", is_pkg=True)
stub("homeassistant.helpers.area_registry", is_pkg=True)
stub("homeassistant.helpers.device_registry", is_pkg=True)
stub("homeassistant.helpers.entity_registry", is_pkg=True)
stub("homeassistant.helpers.service", is_pkg=True)
stub("homeassistant.helpers.entity_platform", is_pkg=True)
stub("homeassistant.helpers.update_coordinator", is_pkg=True)
stub("homeassistant.const", is_pkg=True)
stub("homeassistant.components", is_pkg=True)
stub("homeassistant.components.sensor", is_pkg=True)
stub("homeassistant.components.binary_sensor", is_pkg=True)
stub("homeassistant.components.select", is_pkg=True)
stub("homeassistant.components.button", is_pkg=True)
stub("homeassistant.util", is_pkg=True)
stub("homeassistant.util.yaml", is_pkg=True)
stub("homeassistant.util.json", is_pkg=True)
stub("homeassistant.exceptions", is_pkg=True)
stub("homeassistant.helpers.aiohttp_client", is_pkg=False)  # critical!

# --- populate classes / functions that sensor files inherit / call ---
import voluptuous as vol  # noqa: E402

# homeassistant.core
hc = sys.modules["homeassistant.core"]
hc.HomeAssistant = type("HomeAssistant", (), {"data": {}})
hc.callback = lambda f: f

# homeassistant.config_entries
hce = sys.modules["homeassistant.config_entries"]
hce.ConfigEntry = type("ConfigEntry", (), {})

# homeassistant.helpers.aiohttp_client  <-- the one that's actually imported!
haio = sys.modules["homeassistant.helpers.aiohttp_client"]
haio.async_get_clientsession = MagicMock(return_value=MagicMock())

# homeassistant.helpers.update_coordinator
hup = sys.modules["homeassistant.helpers.update_coordinator"]
hup.CoordinatorEntity = type("CoordinatorEntity", (), {})

# homeassistant.helpers.entity_platform
hep = sys.modules["homeassistant.helpers.entity_platform"]
hep.AddEntitiesCallback = type("AddEntitiesCallback", (), {})

# homeassistant.helpers.config_validation  <-- used by coordinator.py
sys.modules["homeassistant.helpers.config_validation"] = vol

# homeassistant.components.sensor
hcs = sys.modules["homeassistant.components.sensor"]
hcs.SensorEntity = type("SensorEntity", (), {})

# homeassistant.components.binary_sensor
hcbs = sys.modules["homeassistant.components.binary_sensor"]
hcbs.BinarySensorEntity = type("BinarySensorEntity", (), {})

# homeassistant.components.select
hcsel = sys.modules["homeassistant.components.select"]
hcsel.SelectEntity = type("SelectEntity", (), {})

# homeassistant.components.button
hcb = sys.modules["homeassistant.components.button"]
hcb.ButtonEntity = type("ButtonEntity", (), {})
