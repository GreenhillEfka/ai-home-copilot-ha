"""Schema-Validierung für Climate-Module (pro Zone)."""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator
from typing import Literal


class ClimatePreset(BaseModel):
    """Ein Climate-Preset (z.B. Komfort, Eco)."""

    preset_id: str = Field(..., pattern=r"^[a-z0-9_]{1,32}$")
    name: str = Field(..., min_length=1, max_length=64)
    temperature: float = Field(..., ge=5.0, le=40.0)
    humidity_target: float | None = Field(default=None, ge=0, le=100)
    fan_mode: str | None = Field(default=None, max_length=32)
    hvac_mode: str | None = Field(default=None, max_length=32)


class ClimateModuleSchema(BaseModel):
    """Validierte Konfiguration für ein Climate-Modul."""

    module_id: str = Field(..., pattern=r"^climate_[a-z0-9_]{1,120}$")
    zone_id: str = Field(..., pattern=r"^[a-z0-9_]{1,64}$")
    name: str = Field(..., min_length=1, max_length=128)
    entity_ids: list[str] = Field(..., min_length=1, max_length=64)
    presets: list[ClimatePreset] = Field(default_factory=list, max_length=16)
    default_preset: str | None = Field(default=None, max_length=32)
    min_temp: float = Field(default=5.0, ge=5.0, le=40.0)
    max_temp: float = Field(default=30.0, ge=5.0, le=40.0)
    temp_step: float = Field(default=0.5, ge=0.1, le=5.0)
    # Verhalten bei Fenster-öffnen
    window_mode: Literal["ignore", "eco", "shutdown"] = Field(default="eco")
    window_entity_ids: list[str] = Field(default_factory=list, max_length=16)
    schedule_enabled: bool = Field(default=False)
    # Erlaubte HVAC-Modi
    allowed_hvac_modes: list[str] = Field(
        default_factory=lambda: ["heat", "cool", "auto", "off"],
        max_length=8
    )

    @field_validator("max_temp")
    @classmethod
    def max_temp_ge_min(cls, v: float, info) -> float:
        min_t = info.data.get("min_temp", 5.0)
        if v < min_t:
            raise ValueError(f"max_temp ({v}) must be >= min_temp ({min_t})")
        return v

    @field_validator("default_preset")
    @classmethod
    def default_preset_exists(cls, v: str | None, info) -> str | None:
        if v is None:
            return v
        presets = info.data.get("presets", [])
        if not any(p.preset_id == v for p in presets):
            raise ValueError(f"default_preset '{v}' not in presets list")
        return v

    @field_validator("entity_ids")
    @classmethod
    def entity_ids_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("entity_ids cannot be empty")
        return v
