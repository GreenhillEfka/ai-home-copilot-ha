"""HACS Gate UI Card for Lovelace — HA-181."""
from __future__ import annotations
import voluptuous as vol
from homeassistant.components.lovelace import LovelaceCard
from homeassistant.helpers import config_validation as cv

CARD_SCHEMA = vol.Schema({
    vol.Required("type"): "custom:pilotsuite-hacs-gate-card",
    vol.Optional("entity"): cv.entity_id,
    vol.Optional("title", default="PilotSuite HACS Gate"): str,
})

class HACSGateCard(LovelaceCard):
    """Lovelace card showing HACS gate status."""
    
    def __init__(self, config: dict):
        self._config = CARD_SCHEMA(config)
        self._gate_status = {"ok": False, "can_proceed": False}
    
    @staticmethod
    def get_schema():
        return CARD_SCHEMA
    
    @property
    def gate_status(self):
        return self._gate_status
    
    def update_status(self, status: dict):
        self._gate_status = status
    
    def render(self):
        gate = self._gate_status
        if not gate.get("ok"):
            return {"type": "error", "message": "Gate check failed"}
        if gate.get("can_proceed"):
            return {
                "type": "success",
                "title": self._config["title"],
                "message": f"Ready for update (v{gate.get('version', '?')})",
                "checks": gate.get("checks", {})
            }
        return {
            "type": "warning",
            "title": self._config["title"],
            "message": "Update blocked",
            "reason": gate.get("block_reason", "Unknown")
        }
