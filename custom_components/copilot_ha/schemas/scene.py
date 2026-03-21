"""Schema-Validierung für Scene-Module (pro Zone)."""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Any, Literal


class SceneAction(BaseModel):
    """Eine einzelne Aktion innerhalb einer Scene."""

    entity_id: str = Field(..., max_length=256)
    action: str = Field(..., max_length=64)  # e.g. "turn_on", "turn_off", "set_value"
    params: dict[str, Any] = Field(default_factory=dict)


class Scene(BaseModel):
    """Eine benannte Scene innerhalb eines Scene-Moduls."""

    scene_id: str = Field(..., pattern=r"^[a-z0-9_]{1,32}$")
    name: str = Field(..., min_length=1, max_length=128)
    icon: str | None = Field(default=None, max_length=32)
    actions: list[SceneAction] = Field(..., min_length=1, max_length=64)
    tags: list[str] = Field(default_factory=list, max_length=10)
    # Sekunden, die die Aktionen dauern sollen (für Animation/Ausklang)
    transition_s: float = Field(default=0.0, ge=0, le=3600)


class SceneModuleSchema(BaseModel):
    """Validierte Konfiguration für ein Scene-Modul."""

    module_id: str = Field(..., pattern=r"^scene_[a-z0-9_]{1,120}$")
    zone_id: str = Field(..., pattern=r"^[a-z0-9_]{1,64}$")
    name: str = Field(..., min_length=1, max_length=128)
    scenes: list[Scene] = Field(..., min_length=1, max_length=64)
    default_scene: str | None = Field(default=None, max_length=32)
    # Ob Szenen nur direkt (True) oder auch per Zeitsteuerung (False) auslösbar sind
    manual_only: bool = Field(default=False)
    scene_timeout_s: float = Field(default=0.0, ge=0, le=86400)

    @field_validator("default_scene")
    @classmethod
    def default_scene_exists(cls, v: str | None, info) -> str | None:
        if v is None:
            return v
        scenes = info.data.get("scenes", [])
        if not any(s.scene_id == v for s in scenes):
            raise ValueError(f"default_scene '{v}' not in scenes list")
        return v

    @field_validator("scenes")
    @classmethod
    def unique_scene_ids(cls, v: list[Scene]) -> list[Scene]:
        ids = [s.scene_id for s in v]
        if len(ids) != len(set(ids)):
            raise ValueError("scene_ids must be unique within a module")
        return v
