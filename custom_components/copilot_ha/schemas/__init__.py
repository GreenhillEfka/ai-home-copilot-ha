"""Schema-Paket für CopilotHA Module-per-Zone Validierung."""
from .light import LightModuleSchema
from .audio import AudioModuleSchema
from .climate import ClimateModuleSchema
from .cover import CoverModuleSchema
from .energy import EnergyModuleSchema
from .scene import SceneModuleSchema
from .security import SecurityModuleSchema
from .zone import ZoneConfig, ZoneConfigCollection

__all__ = [
    "LightModuleSchema",
    "AudioModuleSchema",
    "ClimateModuleSchema",
    "CoverModuleSchema",
    "EnergyModuleSchema",
    "SceneModuleSchema",
    "SecurityModuleSchema",
    "ZoneConfig",
    "ZoneConfigCollection",
]
