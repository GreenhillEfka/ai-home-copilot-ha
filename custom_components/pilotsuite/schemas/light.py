"""Schema-Validierung für Licht-Module (pro Zone)."""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator
from typing import Literal


class LightCapability(BaseModel):
    """Unterstützte Licht-Fähigkeiten."""

    dimming: bool = Field(default=True)
    color_temp: bool = Field(default=False)
    rgb_color: bool = Field(default=False)
    transition_s: float = Field(default=0.0, ge=0, le=3600)
    flicker_on_start: bool = Field(default=False)


class LightModuleSchema(BaseModel):
    """Validierte Konfiguration für ein Licht-Modul."""

    module_id: str = Field(..., pattern=r"^light_[a-z0-9_]{1,120}$")
    zone_id: str = Field(..., pattern=r"^[a-z0-9_]{1,64}$")
    name: str = Field(..., min_length=1, max_length=128)
    entity_ids: list[str] = Field(..., min_length=1, max_length=64)
    capability: LightCapability = Field(default_factory=LightCapability)
    default_brightness: int = Field(default=255, ge=0, le=255)
    default_transition_s: float = Field(default=0.0, ge=0, le=3600)
    scene_default: str | None = Field(default=None, max_length=64)
    # 'auto' = Tageszeit-gesteuert, 'motion' = Bewegungsmelder, 'manual' = nur manuell
    control_mode: Literal["auto", "motion", "manual"] = Field(default="manual")
    min_brightness: int = Field(default=1, ge=0, le=255)
    max_brightness: int = Field(default=255, ge=0, le=255)

    @field_validator("max_brightness")
    @classmethod
    def max_ge_min(cls, v: int, info) -> int:
        min_b = info.data.get("min_brightness", 0)
        if v < min_b:
            raise ValueError(f"max_brightness ({v}) must be >= min_brightness ({min_b})")
        return v

    @field_validator("entity_ids")
    @classmethod
    def entity_ids_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("entity_ids cannot be empty")
        return v
