"""Enhanced neuron input handling for HA integration."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN

_LOGGER = logging.getLogger(__name__)


class NeuronInputHandler:
    """Handles neuron input data from Home Assistant."""
    
    def __init__(self, hass: HomeAssistant):
        """Initialize the neuron input handler."""
        self.hass = hass
        self._tracked_entities: set[str] = set()
        self._state_cache: Dict[str, State] = {}
        self._callbacks: List[callable] = []
        
    async def async_setup(self) -> None:
        """Set up the neuron input handler."""
        _LOGGER.info("Setting up neuron input handler")
        
    def add_callback(self, callback: callable) -> None:
        """Add a callback for when neuron inputs change."""
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: callable) -> None:
        """Remove a callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def track_entity(self, entity_id: str) -> None:
        """Track an entity for neuron input."""
        if entity_id not in self._tracked_entities:
            self._tracked_entities.add(entity_id)
            _LOGGER.debug("Tracking entity for neuron input: %s", entity_id)
    
    def track_entities(self, entity_ids: List[str]) -> None:
        """Track multiple entities for neuron input."""
        for entity_id in entity_ids:
            self.track_entity(entity_id)
    
    def get_tracked_entities(self) -> List[str]:
        """Get all tracked entities."""
        return list(self._tracked_entities)
    
    def get_state(self, entity_id: str) -> Optional[State]:
        """Get the current state of an entity."""
        # First check cache
        if entity_id in self._state_cache:
            return self._state_cache[entity_id]
        
        # Then check HA
        state = self.hass.states.get(entity_id)
        if state:
            self._state_cache[entity_id] = state
            return state
        
        return None
    
    def get_states(self) -> Dict[str, State]:
        """Get states for all tracked entities."""
        states = {}
        for entity_id in self._tracked_entities:
            state = self.get_state(entity_id)
            if state:
                states[entity_id] = state
        return states
    
    def get_normalized_states(self) -> Dict[str, Any]:
        """Get normalized states for neuron evaluation."""
        normalized = {}
        for entity_id in self._tracked_entities:
            state = self.get_state(entity_id)
            if state and state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN):
                normalized[entity_id] = {
                    "state": state.state,
                    "attributes": dict(state.attributes),
                    "last_updated": state.last_updated.isoformat() if state.last_updated else None,
                    "last_changed": state.last_changed.isoformat() if state.last_changed else None
                }
        return normalized
    
    def get_context(self) -> Dict[str, Any]:
        """Get evaluation context for neurons."""
        now = datetime.now(timezone.utc)
        
        return {
            "states": self.get_normalized_states(),
            "now": now,
            "presence": self._get_presence_context(),
            "sun": self._get_sun_context(),
            "weather": self._get_weather_context(),
            "history": {},  # Would be populated with historical data
            "neurons": {},  # Will be populated by neuron manager
            "household": {},  # Would be populated with household data
            "present_persons": self._get_present_persons()
        }
    
    def _get_presence_context(self) -> Dict[str, Any]:
        """Get presence context for neuron evaluation."""
        presence = {}
        
        # Look for person entities
        for entity_id in self._tracked_entities:
            if entity_id.startswith("person."):
                state = self.get_state(entity_id)
                if state and state.state == "home":
                    # Extract person name from entity_id
                    person_name = entity_id.split(".", 1)[1]
                    presence[person_name] = {
                        "state": "home",
                        "last_seen": state.last_changed.isoformat() if state.last_changed else None
                    }
        
        return presence
    
    def _get_sun_context(self) -> Dict[str, Any]:
        """Get sun context for neuron evaluation."""
        sun_context = {}
        
        # Look for sun entity
        sun_state = self.get_state("sun.sun")
        if sun_state:
            sun_context["state"] = sun_state.state  # "above_horizon" or "below_horizon"
            sun_context["azimuth"] = sun_state.attributes.get("azimuth")
            sun_context["elevation"] = sun_state.attributes.get("elevation")
        
        return sun_context
    
    def _get_weather_context(self) -> Dict[str, Any]:
        """Get weather context for neuron evaluation."""
        weather_context = {}
        
        # Look for weather entity
        for entity_id in self._tracked_entities:
            if entity_id.startswith("weather."):
                state = self.get_state(entity_id)
                if state:
                    weather_context["state"] = state.state
                    weather_context["temperature"] = state.attributes.get("temperature")
                    weather_context["humidity"] = state.attributes.get("humidity")
                    weather_context["pressure"] = state.attributes.get("pressure")
                    break
        
        return weather_context
    
    def _get_present_persons(self) -> List[str]:
        """Get list of present persons."""
        present = []
        
        for entity_id in self._tracked_entities:
            if entity_id.startswith("person."):
                state = self.get_state(entity_id)
                if state and state.state == "home":
                    present.append(entity_id)
        
        return present
    
    async def async_update_state(self, entity_id: str, new_state: State) -> None:
        """Handle state update for a tracked entity."""
        # Update cache
        self._state_cache[entity_id] = new_state
        
        # Notify callbacks
        context = self.get_context()
        for callback in self._callbacks:
            try:
                await callback(entity_id, new_state, context)
            except Exception as e:
                _LOGGER.error("Error in neuron input callback: %s", e)
    
    def clear_cache(self) -> None:
        """Clear the state cache."""
        self._state_cache.clear()


async def async_create_neuron_input_handler(hass: HomeAssistant) -> NeuronInputHandler:
    """Factory function to create a neuron input handler."""
    handler = NeuronInputHandler(hass)
    await handler.async_setup()
    return handler


def get_neuron_input_handler(hass: HomeAssistant) -> Optional[NeuronInputHandler]:
    """Get the neuron input handler from hass data."""
    if hasattr(hass, "data") and "neuron_input_handler" in hass.data:
        return hass.data["neuron_input_handler"]
    return None


def set_neuron_input_handler(hass: HomeAssistant, handler: NeuronInputHandler) -> None:
    """Set the neuron input handler in hass data."""
    if not hasattr(hass, "data"):
        hass.data = {}
    hass.data["neuron_input_handler"] = handler