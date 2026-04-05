"""Root conftest: mock homeassistant imports before HA integration tests load.

This allows pytest to run HA integration tests without a full HomeAssistant
installation by stubbing out all homeassistant.* imports at the conftest level.
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

# Stub every homeassistant.* module that the integration imports
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
    "homeassistant.const",
    "homeassistant.components",
    "homeassistant.components.http",
    "homeassistant.util.yaml",
    "homeassistant.util.json",
    "homeassistant.exceptions",
]:
    if _mod not in sys.modules:
        _stub = MagicMock()
        sys.modules[_mod] = _stub

# Stub HomeAssistant class
from homeassistant.core import HomeAssistant as _RealHA

class HomeAssistant(_RealHA):
    pass

# Stub key constants used in the integration
sys.modules["homeassistant"].core = MagicMock()
sys.modules["homeassistant"].core.HomeAssistant = HomeAssistant
sys.modules["homeassistant"].core import MagicMock()
sys.modules["homeassistant"].config_entries = MagicMock()
sys.modules["homeassistant"].const = MagicMock()
sys.modules["homeassistant"].helpers = MagicMock()
sys.modules["homeassistant"].helpers.config_validation = MagicMock()
sys.modules["homeassistant"].util = MagicMock()

# Fix for ConfigFlowValidator importing voluptuous
import voluptuous as vol
sys.modules["homeassistant"].helpers.config_validation = vol

# Make sure the integration can at least be parsed
import custom_components.copilot_ha  # noqa: F401
