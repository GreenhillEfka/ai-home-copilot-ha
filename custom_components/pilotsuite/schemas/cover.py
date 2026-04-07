"""Schema-Validierung für Cover-Module (pro Zone)."""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator
from typing import Literal


class CoverPosition(BaseModel):
    """Benannte Position für ein Cover (z.B. 'offen', 'geschlossen')."""

    position_id: str = Field(..., pattern=r"^[a-z0-9_]{1,32}$")
    name: str = Field(..., min_length=1, max_length=64)
    percentage: int = Field(..., ge=0, le=100)


class CoverModuleSchema(BaseModel):
    """Validierte Konfiguration für ein Cover-Modul."""

    module_id: str = Field(..., pattern=r"^cover_[a-z0-9_]{1,120}$")
    zone_id: str = Field(..., pattern=r"^[a-z0-9_]{1,64}$")
    name: str = Field(..., min_length=1, max_length=128)
    entity_ids: list[str] = Field(..., min_length=1, max_length=64)
    cover_type: Literal["blind", "roller", "shutter", "garage", "gate", "valve"] = Field(
        default="roller"
    )
    positions: list[CoverPosition] = Field(default_factory=list, max_length=10)
    default_position: str | None = Field(default=None, max_length=32)
    travel_time_s: float = Field(default=30.0, ge=0.5, le=600)
    # 'individual' = jedes Cover einzeln, 'group' = alle gleichzeitig
    control_mode: Literal["individual", "group"] = Field(default="individual")
    tilt_supported: bool = Field(default=False)
    tilt_entity_ids: list[str] = Field(default_factory=list, max_length=64)
    wind_protection_enabled: bool = Field(default=False)
    wind_speed_max_kmh: float = Field(default=50.0, ge=0, le=300)
    sun_protection_enabled: bool = Field(default=False)
    sun_elevation_threshold: float = Field(default=30.0, ge=0, le=90)

    @field_validator("default_position")
    @classmethod
    def default_position_exists(cls, v: str | None, info) -> str | None:
        if v is None:
            return v
        positions = info.data.get("positions", [])
        if not any(p.position_id == v for p in positions):
            raise ValueError(f"default_position '{v}' not in positions list")
        return v

    @field_validator("entity_ids")
    @classmethod
    def entity_ids_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("entity_ids cannot be empty")
        return v

    @field_validator("tilt_entity_ids")
    @classmethod
    def tilt_count_matches_covers(cls, v: list[str], info) -> list[str]:
        covers = info.data.get("entity_ids", [])
        if len(v) > len(covers):
            raise ValueError(
                f"tilt_entity_ids count ({len(v)}) cannot exceed entity_ids count ({len(covers)})"
            )
        return v
