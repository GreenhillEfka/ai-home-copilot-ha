"""Automation Suggestion Sensor for PilotSuite HA Integration.

Exposes automation suggestions count and top recommendations as a HA sensor.
Pure projection shell: all data comes from Core /api/v1/automations/suggestions.
No local semantic invention.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity

from ..entity import CopilotBaseEntity

_LOGGER = logging.getLogger(__name__)


class AutomationSuggestionSensor(CopilotBaseEntity, SensorEntity):
    """Sensor exposing automation suggestions count and top recommendations from Core."""

    _attr_name = "Automation Suggestions"
    _attr_icon = "mdi:robot"
    _attr_unique_id = "copilot_automation_suggestions"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._suggestion_data: dict[str, Any] | None = None

    async def async_update(self) -> None:
        """Fetch suggestions from Core API."""
        try:
            session = self.coordinator._session
            if session is None:
                return

            url = f"{self._core_base_url()}/api/v1/automations/suggestions"
            headers = self._core_headers()

            async with session.get(url, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    self._suggestion_data = await resp.json()
                else:
                    _LOGGER.debug("Automation API returned %s", resp.status)
        except Exception as e:
            _LOGGER.debug("Failed to fetch suggestions: %s", e)

    @property
    def native_value(self) -> str:
        """Return suggestion count as state."""
        data = self._suggestion_data
        if not data or not isinstance(data, dict):
            return "unavailable"
        if not data.get("ok"):
            return "unavailable"
        count = data.get("count", 0)
        if count == 0:
            return "Keine Vorschläge"
        if count == 1:
            return "1 Vorschlag"
        return f"{count} Vorschläge"

    @property
    def icon(self) -> str:
        """Return icon based on suggestion count."""
        data = self._suggestion_data
        if not data or not isinstance(data, dict):
            return "mdi:robot-off"
        if not data.get("ok"):
            return "mdi:robot-off"
        count = data.get("count", 0)
        if count == 0:
            return "mdi:check-circle"
        if count <= 3:
            return "mdi:robot"
        return "mdi:robot-expressive"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return suggestion details as attributes."""
        attrs: dict[str, Any] = {
            "source": "/api/v1/automations/suggestions",
        }

        data = self._suggestion_data
        if not data or not isinstance(data, dict) or not data.get("ok"):
            attrs["status"] = "unavailable"
            return attrs

        suggestions = data.get("suggestions", [])
        if not isinstance(suggestions, list):
            suggestions = []

        attrs["total_count"] = data.get("count", 0)
        attrs["status"] = "ok"

        categories: dict[str, int] = {}
        for s in suggestions:
            if not isinstance(s, dict):
                continue
            cat = s.get("category", "other")
            categories[cat] = categories.get(cat, 0) + 1
        if categories:
            attrs["by_category"] = categories

        top_suggestions = []
        for s in suggestions[:3]:
            if not isinstance(s, dict):
                continue
            top_suggestions.append(
                {
                    "id": s.get("id", ""),
                    "title": s.get("title", ""),
                    "category": s.get("category", "other"),
                    "confidence": s.get("confidence", 0.0),
                    "savings_eur": s.get("estimated_savings_eur"),
                }
            )
        if top_suggestions:
            attrs["top_suggestions"] = top_suggestions

        total_savings = 0.0
        for s in suggestions:
            if not isinstance(s, dict):
                continue
            savings = s.get("estimated_savings_eur")
            if isinstance(savings, (int, float)):
                total_savings += savings
        if total_savings > 0:
            attrs["total_potential_savings_eur"] = round(total_savings, 2)

        return attrs
