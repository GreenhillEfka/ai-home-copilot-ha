"""Schema-Validierung für Audio-Module (pro Zone)."""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator
from typing import Literal


class AudioSource(BaseModel):
    """Eine Audio-Quelle."""

    source_id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=128)
    type: Literal["radio", "bluetooth", "stream", "line_in", "tts"]


class AudioModuleSchema(BaseModel):
    """Validierte Konfiguration für ein Audio-Modul."""

    module_id: str = Field(..., pattern=r"^audio_[a-z0-9_]{1,120}$")
    zone_id: str = Field(..., pattern=r"^[a-z0-9_]{1,64}$")
    name: str = Field(..., min_length=1, max_length=128)
    entity_ids: list[str] = Field(..., min_length=1, max_length=64)
    sources: list[AudioSource] = Field(default_factory=list, max_length=16)
    default_source: str | None = Field(default=None, max_length=64)
    default_volume: int = Field(default=30, ge=0, le=100)
    volume_step: int = Field(default=5, ge=1, le=50)
    fade_on_start_s: float = Field(default=1.5, ge=0, le=60)
    fade_on_stop_s: float = Field(default=1.0, ge=0, le=60)
    # 'single' = alle Speaker gleiches Audio, 'split' = individuell
    play_mode: Literal["single", "split"] = Field(default="single")
    enable_tts: bool = Field(default=False)
    tts_language: str = Field(default="de-DE", max_length=10)

    @field_validator("default_source")
    @classmethod
    def default_source_exists(cls, v: str | None, info) -> str | None:
        if v is None:
            return v
        sources = info.data.get("sources", [])
        if not any(s.source_id == v for s in sources):
            raise ValueError(f"default_source '{v}' not in sources list")
        return v

    @field_validator("entity_ids")
    @classmethod
    def entity_ids_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("entity_ids cannot be empty")
        return v
