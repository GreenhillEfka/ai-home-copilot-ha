"""Root pytest configuration for PilotSuite Styx HA.

Sets up Python paths and HA stubs so all tests can run without
a full Home Assistant installation.
"""

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

# Project root
PROJECT_ROOT = Path(__file__).parent

# Add paths for importability
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "sdk" / "python"))
sys.path.insert(0, str(PROJECT_ROOT / "custom_components"))

# ---------------------------------------------------------------------------
# Fix core.sharing import — must happen BEFORE custom_components/copilot_ha
# gets imported, since copilot_ha/core/ would shadow the root core/ package.
# ---------------------------------------------------------------------------
_core_sharing_path = PROJECT_ROOT / "core" / "sharing"
if _core_sharing_path.exists() and "core" not in sys.modules:
    import importlib.util
    _core_init = PROJECT_ROOT / "core" / "__init__.py"
    if _core_init.exists():
        spec = importlib.util.spec_from_file_location(
            "core",
            str(_core_init),
            submodule_search_locations=[str(PROJECT_ROOT / "core")],
        )
        if spec and spec.loader:
            _core_mod = importlib.util.module_from_spec(spec)
            sys.modules["core"] = _core_mod
            spec.loader.exec_module(_core_mod)

# ---------------------------------------------------------------------------
# Stub 'homeassistant' package for test collection.
# ---------------------------------------------------------------------------
if "homeassistant" not in sys.modules:
    _ha_module_paths = [
        "homeassistant",
        "homeassistant.auth",
        "homeassistant.auth.models",
        "homeassistant.core",
        "homeassistant.config_entries",
        "homeassistant.const",
        "homeassistant.data_entry_flow",
        "homeassistant.exceptions",
        "homeassistant.loader",
        "homeassistant.helpers",
        "homeassistant.helpers.aiohttp_client",
        "homeassistant.helpers.area_registry",
        "homeassistant.helpers.config_validation",
        "homeassistant.helpers.device_registry",
        "homeassistant.helpers.dispatcher",
        "homeassistant.helpers.entity",
        "homeassistant.helpers.entity_platform",
        "homeassistant.helpers.entity_registry",
        "homeassistant.helpers.event",
        "homeassistant.helpers.selector",
        "homeassistant.helpers.storage",
        "homeassistant.helpers.template",
        "homeassistant.helpers.typing",
        "homeassistant.helpers.update_coordinator",
        "homeassistant.util",
        "homeassistant.util.dt",
        "homeassistant.components",
        "homeassistant.components.automation",
        "homeassistant.components.automation.storage",
        "homeassistant.components.binary_sensor",
        "homeassistant.components.button",
        "homeassistant.components.calendar",
        "homeassistant.components.camera",
        "homeassistant.components.conversation",
        "homeassistant.components.device_tracker",
        "homeassistant.components.diagnostics",
        "homeassistant.components.history",
        "homeassistant.components.http",
        "homeassistant.components.light",
        "homeassistant.components.media_player",
        "homeassistant.components.number",
        "homeassistant.components.persistent_notification",
        "homeassistant.components.person",
        "homeassistant.components.recorder",
        "homeassistant.components.recorder.history",
        "homeassistant.components.repairs",
        "homeassistant.components.select",
        "homeassistant.components.sensor",
        "homeassistant.components.stt",
        "homeassistant.components.switch",
        "homeassistant.components.text",
        "homeassistant.components.tts",
    ]

    # Create MagicMock for every module — register in sorted order
    _mocks: dict[str, MagicMock] = {}
    for mod_path in sorted(_ha_module_paths):
        parts = mod_path.split(".")
        if len(parts) > 1:
            parent_path = ".".join(parts[:-1])
            child_name = parts[-1]
            if parent_path in _mocks:
                child_mock = getattr(_mocks[parent_path], child_name)
                _mocks[mod_path] = child_mock
            else:
                _mocks[mod_path] = MagicMock(name=mod_path)
        else:
            _mocks[mod_path] = MagicMock(name=mod_path)
        sys.modules[mod_path] = _mocks[mod_path]

    # -----------------------------------------------------------------------
    # Replace MagicMock-based HA classes that are used as base classes with
    # real Python classes. MagicMock metaclass conflicts with `type` when
    # used in multiple inheritance.
    # -----------------------------------------------------------------------
    _config_entries = _mocks["homeassistant.config_entries"]

    class _ConfigEntry:
        """Stub ConfigEntry."""
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
            self.entry_id = kwargs.get("entry_id", "stub")
            self.domain = kwargs.get("domain", "copilot_ha")
            self.data = kwargs.get("data", {})
            self.options = kwargs.get("options", {})

    class _OptionsFlow:
        """Stub OptionsFlow base."""
        hass = None
        def async_show_form(self, **kwargs): pass
        def async_show_menu(self, **kwargs): pass
        def async_create_entry(self, **kwargs): pass
        def async_abort(self, **kwargs): pass

    class _ConfigFlow:
        """Stub ConfigFlow base."""
        hass = None
        def async_show_form(self, **kwargs): pass
        def async_create_entry(self, **kwargs): pass
        def async_abort(self, **kwargs): pass
        @staticmethod
        def async_get_options_flow(config_entry): pass

    _config_entries.ConfigEntry = _ConfigEntry
    _config_entries.OptionsFlow = _OptionsFlow
    _config_entries.ConfigFlow = _ConfigFlow
    _config_entries.SOURCE_USER = "user"
    _config_entries.SOURCE_REAUTH = "reauth"

    # FlowResult stub
    _data_entry_flow = _mocks["homeassistant.data_entry_flow"]
    _data_entry_flow.FlowResult = dict
    _data_entry_flow.FlowHandler = type("FlowHandler", (), {})
    _data_entry_flow.AbortFlow = type("AbortFlow", (Exception,), {})

    # Entity base classes (used in multiple inheritance)
    # Support Generic subscript: CoordinatorEntity["Type"]
    class _SubscriptableMeta(type):
        def __getitem__(cls, item):
            return cls

    class _Entity(metaclass=_SubscriptableMeta):
        _attr_unique_id = None
        _attr_name = None
        _attr_icon = None
        _attr_extra_state_attributes = {}
        _attr_entity_registry_enabled_default = True
        entity_id = ""
        hass = None
        def async_write_ha_state(self): pass

    class _SensorEntity(_Entity): pass
    class _BinarySensorEntity(_Entity): pass
    class _ButtonEntity(_Entity):
        async def async_press(self): pass
    class _SwitchEntity(_Entity): pass
    class _NumberEntity(_Entity): pass
    class _SelectEntity(_Entity): pass
    class _CameraEntity(_Entity): pass
    class _TextEntity(_Entity): pass

    _mocks["homeassistant.helpers.entity"].Entity = _Entity
    _mocks["homeassistant.helpers.entity"].EntityCategory = MagicMock()
    _mocks["homeassistant.components.sensor"].SensorEntity = _SensorEntity
    _mocks["homeassistant.components.sensor"].SensorDeviceClass = MagicMock()
    _mocks["homeassistant.components.sensor"].SensorStateClass = MagicMock()
    _mocks["homeassistant.components.binary_sensor"].BinarySensorEntity = _BinarySensorEntity
    _mocks["homeassistant.components.button"].ButtonEntity = _ButtonEntity
    _mocks["homeassistant.components.switch"].SwitchEntity = _SwitchEntity
    _mocks["homeassistant.components.number"].NumberEntity = _NumberEntity
    _mocks["homeassistant.components.select"].SelectEntity = _SelectEntity
    _mocks["homeassistant.components.camera"].Camera = _CameraEntity
    _mocks["homeassistant.components.text"].TextEntity = _TextEntity

    # UpdateCoordinator
    class _DataUpdateCoordinator(metaclass=_SubscriptableMeta):
        data = {}
        hass = None
        def __init__(self, *a, **kw): pass
        async def async_refresh(self): pass

    _mocks["homeassistant.helpers.update_coordinator"].DataUpdateCoordinator = _DataUpdateCoordinator
    _mocks["homeassistant.helpers.update_coordinator"].CoordinatorEntity = _Entity

    # Core HomeAssistant stub
    class _HomeAssistant:
        data = {}
        bus = MagicMock()
        states = MagicMock()
        services = MagicMock()
        config = MagicMock()
        loop = None
    _mocks["homeassistant.core"].HomeAssistant = _HomeAssistant

    # Exceptions
    _mocks["homeassistant.exceptions"].HomeAssistantError = type("HomeAssistantError", (Exception,), {})
    _mocks["homeassistant.exceptions"].ConfigEntryNotReady = type("ConfigEntryNotReady", (Exception,), {})
    _mocks["homeassistant.exceptions"].ConfigEntryAuthFailed = type("ConfigEntryAuthFailed", (Exception,), {})

    # conversation/stt/tts stubs
    class _ConversationEntity:
        hass = None
    _mocks["homeassistant.components.conversation"].ConversationEntity = _ConversationEntity

    class _SttProvider:
        hass = None
    _mocks["homeassistant.components.stt"].SpeechToTextEntity = _SttProvider
    _mocks["homeassistant.components.stt"].Provider = _SttProvider
    _mocks["homeassistant.components.stt"].AudioBitRates = MagicMock()
    _mocks["homeassistant.components.stt"].AudioChannels = MagicMock()
    _mocks["homeassistant.components.stt"].AudioCodecs = MagicMock()
    _mocks["homeassistant.components.stt"].AudioFormats = MagicMock()
    _mocks["homeassistant.components.stt"].AudioSampleRates = MagicMock()
    _mocks["homeassistant.components.stt"].SpeechMetadata = MagicMock()
    _mocks["homeassistant.components.stt"].SpeechResult = MagicMock()
    _mocks["homeassistant.components.stt"].SpeechResultState = MagicMock()

    class _TtsEntity:
        hass = None
    _mocks["homeassistant.components.tts"].TextToSpeechEntity = _TtsEntity
    _mocks["homeassistant.components.tts"].TtsAudioType = MagicMock()

    # Set real string values for homeassistant.const
    ha_const = _mocks["homeassistant.const"]
    for attr, val in {
        "CONF_HOST": "host", "CONF_PORT": "port", "CONF_NAME": "name",
        "CONF_TOKEN": "token", "CONF_URL": "url", "CONF_SCAN_INTERVAL": "scan_interval",
        "STATE_ON": "on", "STATE_OFF": "off", "STATE_HOME": "home",
        "STATE_NOT_HOME": "not_home", "STATE_UNKNOWN": "unknown",
        "STATE_UNAVAILABLE": "unavailable", "ATTR_ENTITY_ID": "entity_id",
        "ATTR_FRIENDLY_NAME": "friendly_name",
        "ATTR_UNIT_OF_MEASUREMENT": "unit_of_measurement",
        "PERCENTAGE": "%",
    }.items():
        setattr(ha_const, attr, val)

    # voluptuous stub
    if "voluptuous" not in sys.modules:
        vol = MagicMock(name="voluptuous")
        sys.modules["voluptuous"] = vol
        sys.modules["voluptuous.humanize"] = vol.humanize

    # aiohttp stub
    if "aiohttp" not in sys.modules:
        sys.modules["aiohttp"] = MagicMock(name="aiohttp")
        sys.modules["aiohttp.web"] = MagicMock(name="aiohttp.web")


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "e2e: end-to-end integration tests")
    config.addinivalue_line("markers", "unit: unit tests")
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "visual: visual regression tests")


# Exclude non-test files and irrelevant directories
collect_ignore_glob = [
    "custom_components/copilot_ha/button_test.py",  # entity file, not a test
    "node_modules/*",
    "qg_venv/*",
    "styx-fork-*/*",
    "ha-copilot-repo/*",
    "ai_home_copilot_hacs_repo/*",
]
