"""Pydantic-basierte Zone-Konfiguration."""
from __future__ import annotations

from pydantic import BaseModel, Field, model_validator
from typing import Any, Literal


class ZoneMetadata(BaseModel):
    """Metadaten einer Zone."""

    name: str = Field(..., min_length=1, max_length=64)
    floor: str | None = Field(default=None, max_length=32)
    area_sqm: float | None = Field(default=None, gt=0, le=10000)
    tags: list[str] = Field(default_factory=list, max_length=20)


class ZoneModuleEntry(BaseModel):
    """Ein einzelnes Modul innerhalb einer Zone."""

    module_id: str = Field(..., min_length=1, max_length=128)
    enabled: bool = Field(default=True)
    config: dict = Field(default_factory=dict)


class ZoneConfig(BaseModel):
    """Konfiguration einer einzelnen Zone."""

    zone_id: str = Field(..., pattern=r"^[a-z0-9_]{1,64}$")
    metadata: ZoneMetadata
    modules: dict[str, ZoneModuleEntry] = Field(default_factory=dict)

    # Modul-Typ Whitelist pro Zone (None = alle erlaubt)
    allowed_module_types: list[str] | None = Field(
        default=None,
        description="Wenn gesetzt, sind nur diese Modultypen erlaubt."
    )

    @model_validator(mode="after")
    def validate_module_types(self) -> "ZoneConfig":
        allowed = self.allowed_module_types
        if allowed is None:
            return self
        for mod_id in self.modules.keys():
            mod_type = mod_id.split("_", 1)[0] if "_" in mod_id else mod_id
            if mod_type not in allowed:
                raise ValueError(
                    f"Modultyp '{mod_type}' in Zone nicht erlaubt. "
                    f"Erlaubt: {allowed}"
                )
        return self


class ZoneConfigCollection(BaseModel):
    """Sammlung aller Zonen-Konfigurationen (top-level config)."""

    version: Literal[1] = Field(default=1)
    zones: dict[str, ZoneConfig] = Field(default_factory=dict)

    def get_zone(self, zone_id: str) -> ZoneConfig | None:
        return self.zones.get(zone_id)

    def all_zone_ids(self) -> list[str]:
        return list(self.zones.keys())


# Resolve forward references for Pydantic v2
ZoneConfigCollection.model_rebuild()
