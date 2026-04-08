"""Module Interface Standard - PilotSuite

This defines the standard interface for all core modules.
All modules should follow this contract for consistency.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
from datetime import datetime


class HealthStatus(Enum):
    """Module health states."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthReport:
    """Standard health check result for a module."""
    status: HealthStatus = HealthStatus.UNKNOWN
    message: str = ""
    last_check: Optional[datetime] = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for API responses."""
        return {
            "status": self.status.value,
            "message": self.message,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "details": self.details,
        }


@dataclass
class ModuleState:
    """Standard module state."""
    module_id: str
    last_update: datetime
    data: dict[str, Any]
    error: Optional[str] = None


class ModuleInterface(ABC):
    """Base interface for all core modules."""

    @property
    @abstractmethod
    def module_id(self) -> str:
        """Unique module identifier."""
        pass

    @property
    @abstractmethod
    def state(self) -> ModuleState:
        """Current module state."""
        pass

    @abstractmethod
    async def async_init(self) -> None:
        """Initialize module."""
        pass

    @abstractmethod
    async def async_start(self) -> None:
        """Start module."""
        pass

    @abstractmethod
    async def async_stop(self) -> None:
        """Stop module."""
        pass

    async def async_health_check(self) -> HealthReport:
        """Return module health status.

        Default implementation returns HEALTHY if the module has been
        initialised (state exists). Override in subclasses for deeper
        checks (API connectivity, data freshness, etc.).
        """
        try:
            s = self.state
            if s.error:
                return HealthReport(
                    status=HealthStatus.DEGRADED,
                    message=s.error,
                    last_check=datetime.now(),
                    details={"module_id": s.module_id},
                )
            return HealthReport(
                status=HealthStatus.HEALTHY,
                message="OK",
                last_check=datetime.now(),
                details={"module_id": s.module_id, "last_update": s.last_update.isoformat()},
            )
        except Exception as exc:
            return HealthReport(
                status=HealthStatus.UNHEALTHY,
                message=str(exc),
                last_check=datetime.now(),
            )


class DataModule(ModuleInterface):
    """Module that processes data and produces outputs."""

    @abstractmethod
    async def async_process(self, data: dict[str, Any]) -> dict[str, Any]:
        """Process input data and return results."""
        pass


class ContextModule(ModuleInterface):
    """Module that provides context to other modules."""

    @abstractmethod
    async def async_get_context(self) -> dict[str, Any]:
        """Get current context data."""
        pass


# Standard module outputs
MODULE_OUTPUT_TYPES = {
    "mood": dict,          # Mood data
    "presence": dict,       # Presence data
    "energy": dict,        # Energy data
    "suggestion": dict,    # Automation suggestions
    "state": dict,         # General state
}
