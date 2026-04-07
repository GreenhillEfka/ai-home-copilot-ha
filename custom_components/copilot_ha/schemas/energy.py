"""Schema-Validierung für Energy-Module (pro Zone)."""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator
from typing import Literal


class EnergySensor(BaseModel):
    """Ein einzelner Energiesensor."""

    sensor_id: str = Field(..., pattern=r"^[a-z0-9_]{1,64}$")
    name: str = Field(..., min_length=1, max_length=128)
    unit: Literal["kWh", "W", "A", "V", "kVA", "cos_phi"] = Field(default="kWh")
    entity_id: str = Field(..., max_length=256)
    cost_per_unit: float | None = Field(default=None, ge=0)


class EnergyModuleSchema(BaseModel):
    """Validierte Konfiguration für ein Energy-Modul."""

    module_id: str = Field(..., pattern=r"^energy_[a-z0-9_]{1,120}$")
    zone_id: str = Field(..., pattern=r"^[a-z0-9_]{1,64}$")
    name: str = Field(..., min_length=1, max_length=128)
    sensors: list[EnergySensor] = Field(..., min_length=1, max_length=32)
    cost_currency: str = Field(default="EUR", max_length=3)
    billing_period: Literal["monthly", "yearly"] = Field(default="monthly")
    budget_wh: float | None = Field(default=None, gt=0)
    budget_warning_pct: float = Field(default=80.0, ge=1, le=100)
    solar_generation_entity_id: str | None = Field(default=None, max_length=256)
    battery_storage_entity_id: str | None = Field(default=None, max_length=256)
    self_consumption_target_pct: float | None = Field(
        default=None, ge=0, le=100
    )

    @field_validator("sensors")
    @classmethod
    def sensors_not_empty(cls, v: list[EnergySensor]) -> list[EnergySensor]:
        if not v:
            raise ValueError("sensors cannot be empty")
        return v

    @field_validator("sensors")
    @classmethod
    def unique_sensor_ids(cls, v: list[EnergySensor]) -> list[EnergySensor]:
        ids = [s.sensor_id for s in v]
        if len(ids) != len(set(ids)):
            raise ValueError("sensor_ids must be unique within a module")
        return v
