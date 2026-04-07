"""Schema-Validierung für Security-Module (pro Zone)."""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator
from typing import Literal


class SecuritySensor(BaseModel):
    """Ein Sicherheitssensor (Bewegung, Tür, Fenster, etc.)."""

    sensor_id: str = Field(..., pattern=r"^[a-z0-9_]{1,64}$")
    name: str = Field(..., min_length=1, max_length=128)
    type: Literal[
        "motion", "door", "window", "glass", "smoke", "co", "water", "vibration", "button"
    ]
    entity_id: str = Field(..., max_length=256)
    arm_zone: int = Field(default=1, ge=1, le=4)
    bypass_allowed: bool = Field(default=False)


class SecuritySiren(BaseModel):
    """Eine Sirene/Akustische Warnung."""

    siren_id: str = Field(..., pattern=r"^[a-z0-9_]{1,64}$")
    name: str = Field(..., min_length=1, max_length=128)
    entity_id: str = Field(..., max_length=256)
    type: Literal["siren", "strobe", "combined"]


class SecurityModuleSchema(BaseModel):
    """Validierte Konfiguration für ein Security-Modul."""

    module_id: str = Field(..., pattern=r"^security_[a-z0-9_]{1,120}$")
    zone_id: str = Field(..., pattern=r"^[a-z0-9_]{1,64}$")
    name: str = Field(..., min_length=1, max_length=128)
    sensors: list[SecuritySensor] = Field(..., min_length=1, max_length=64)
    sirens: list[SecuritySiren] = Field(default_factory=list, max_length=8)
    panel_entity_id: str | None = Field(default=None, max_length=256)
    # Modus: 'alarm' = Alarmanlage, 'awareness' = nur Benachrichtigung, 'access' = Zugangskontrolle
    security_mode: Literal["alarm", "awareness", "access"] = Field(default="alarm")
    alarm_delay_entry_s: float = Field(default=30.0, ge=0, le=300)
    alarm_delay_exit_s: float = Field(default=60.0, ge=0, le=300)
    # Alarm-Sirenen-Dauer in Sekunden
    alarm_duration_s: float = Field(default=180.0, ge=10, le=600)
    notify_on_bypass: bool = Field(default=True)
    notify_on_restore: bool = Field(default=True)
    # Erlaubte Armierungs-Levels
    allowed_states: list[str] = Field(
        default_factory=lambda: ["disarmed", "armed_home", "armed_away", "armed_night"],
        max_length=8
    )

    @field_validator("sensors")
    @classmethod
    def sensors_not_empty(cls, v: list[SecuritySensor]) -> list[SecuritySensor]:
        if not v:
            raise ValueError("sensors cannot be empty")
        return v

    @field_validator("sensors")
    @classmethod
    def unique_sensor_ids(cls, v: list[SecuritySensor]) -> list[SecuritySensor]:
        ids = [s.sensor_id for s in v]
        if len(ids) != len(set(ids)):
            raise ValueError("sensor_ids must be unique within a module")
        return v

    @field_validator("sirens")
    @classmethod
    def unique_siren_ids(cls, v: list[SecuritySiren]) -> list[SecuritySiren]:
        ids = [s.siren_id for s in v]
        if len(ids) != len(set(ids)):
            raise ValueError("siren_ids must be unique within a module")
        return v
