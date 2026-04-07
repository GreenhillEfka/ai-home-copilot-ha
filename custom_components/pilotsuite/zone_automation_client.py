"""Zone Automation Client — HA Client für CORE API.

DIESES MODUL ist NUR ein Client für die CORE API.
KEINE Business-Logik in HA — nur API-Calls + Darstellung!

Architecture:
- HA ruft CORE API auf (REST)
- HA zeigt Daten an (Lovelace Cards)
- HA sendet Events an CORE (state_changed)
- HA macht KEINE Logik-Entscheidungen
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
import threading
import aiohttp
import asyncio

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)


class ZoneAutomationClient:
    """Client für Zone Automation CORE API.
    
    WICHTIG: Dieses Modul macht KEINE Logik!
    - Nur API-Calls an CORE
    - Nur Daten für Lovelace vorbereiten
    - Nur Events an CORE senden
    """
    
    def __init__(self, hass: HomeAssistant, core_url: str, api_token: str):
        self._hass = hass
        self._core_url = core_url.rstrip('/')
        self._api_token = api_token
        self._session: Optional[aiohttp.ClientSession] = None
        self._lock = threading.Lock()
        self._cache: Dict[str, Any] = {}
        self._cache_timestamp: Dict[str, float] = {}
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """HTTP Session holen."""
        if self._session is None or self._session.closed:
            self._session = async_get_clientsession(self._hass)
        return self._session
    
    def _get_headers(self) -> Dict[str, str]:
        """Headers für API-Calls."""
        return {
            "Authorization": f"Bearer {self._api_token}",
            "Content-Type": "application/json",
        }
    
    async def get_dashboard(self) -> Dict[str, Any]:
        """Dashboard Daten von CORE holen."""
        try:
            session = await self._get_session()
            url = f"{self._core_url}/api/v1/zone-automation/dashboard"
            
            async with session.get(url, headers=self._get_headers()) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    with self._lock:
                        self._cache['dashboard'] = data
                        self._cache_timestamp['dashboard'] = asyncio.get_event_loop().time()
                    return data
                else:
                    _LOGGER.error(f"Dashboard API error: {resp.status}")
                    return {"error": f"API error: {resp.status}"}
        except Exception as e:
            _LOGGER.error(f"Dashboard fetch failed: {e}")
            return {"error": str(e)}
    
    async def get_zone(self, zone_id: str) -> Dict[str, Any]:
        """Zone Details von CORE holen."""
        try:
            session = await self._get_session()
            url = f"{self._core_url}/api/v1/zone-automation/zones/{zone_id}"
            
            async with session.get(url, headers=self._get_headers()) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    with self._lock:
                        self._cache[f'zone_{zone_id}'] = data
                        self._cache_timestamp[f'zone_{zone_id}'] = asyncio.get_event_loop().time()
                    return data
                else:
                    return {"error": f"API error: {resp.status}"}
        except Exception as e:
            _LOGGER.error(f"Zone fetch failed: {e}")
            return {"error": str(e)}
    
    async def set_zone_config(self, zone_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Zone Config an CORE senden."""
        try:
            session = await self._get_session()
            url = f"{self._core_url}/api/v1/zone-automation/zones/{zone_id}/config"
            
            async with session.put(url, json=config, headers=self._get_headers()) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    return {"error": f"API error: {resp.status}"}
        except Exception as e:
            _LOGGER.error(f"Zone config update failed: {e}")
            return {"error": str(e)}
    
    async def set_neuron_mode(self, zone_id: str, neuron_id: str, mode: str) -> Dict[str, Any]:
        """Neuron Mode an CORE senden."""
        try:
            session = await self._get_session()
            url = f"{self._core_url}/api/v1/zone-automation/zones/{zone_id}/neuron/{neuron_id}/mode"
            
            async with session.put(url, json={"mode": mode}, headers=self._get_headers()) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    return {"error": f"API error: {resp.status}"}
        except Exception as e:
            _LOGGER.error(f"Neuron mode update failed: {e}")
            return {"error": str(e)}
    
    async def get_rules(self, zone_id: str) -> Dict[str, Any]:
        """Rules von CORE holen."""
        try:
            session = await self._get_session()
            url = f"{self._core_url}/api/v1/zone-automation/zones/{zone_id}/rules"
            
            async with session.get(url, headers=self._get_headers()) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    return {"error": f"API error: {resp.status}"}
        except Exception as e:
            _LOGGER.error(f"Rules fetch failed: {e}")
            return {"error": str(e)}
    
    async def send_event(self, zone_id: str, event_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Event an CORE senden (wenn HA state_changed)."""
        try:
            session = await self._get_session()
            url = f"{self._core_url}/api/v1/zone-automation/zones/{zone_id}/event"
            
            async with session.post(
                url,
                json={"event_type": event_type, "context": context},
                headers=self._get_headers()
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    return {"error": f"API error: {resp.status}"}
        except Exception as e:
            _LOGGER.error(f"Event send failed: {e}")
            return {"error": str(e)}
    
    async def test_rule(self, zone_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Rule testen (Simulation)."""
        try:
            session = await self._get_session()
            url = f"{self._core_url}/api/v1/zone-automation/zones/{zone_id}/test"
            
            async with session.post(
                url,
                json={"context": context},
                headers=self._get_headers()
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    return {"error": f"API error: {resp.status}"}
        except Exception as e:
            _LOGGER.error(f"Rule test failed: {e}")
            return {"error": str(e)}
    
    def get_cached(self, key: str, max_age_seconds: float = 60.0) -> Optional[Dict[str, Any]]:
        """Cached Daten holen (wenn aktuell)."""
        with self._lock:
            if key in self._cache:
                age = asyncio.get_event_loop().time() - self._cache_timestamp.get(key, 0)
                if age < max_age_seconds:
                    return self._cache[key]
        return None
    
    async def close(self) -> None:
        """Session schließen."""
        if self._session and not self._session.closed:
            await self._session.close()


# =============================================================================
# Lovelace Card Data Preparation (NUR Darstellung!)
# =============================================================================

def prepare_neuron_mode_card_data(zone_data: Dict[str, Any]) -> Dict[str, Any]:
    """Daten für Neuron Mode Card vorbereiten (NUR Darstellung!)."""
    return {
        "type": "custom:neuron-mode-selector",
        "title": f"{zone_data.get('zone_name', 'Zone')} Neuron Modes",
        "zone_id": zone_data.get('zone_id', ''),
        "neurons": [
            {
                "neuron_id": neuron_id,
                "mode": mode,
                "options": ["autonomous", "learning", "off"],
            }
            for neuron_id, mode in zone_data.get('neuron_modes', {}).items()
        ],
    }


def prepare_light_automation_card_data(zone_data: Dict[str, Any]) -> Dict[str, Any]:
    """Daten für Light Automation Card vorbereiten (NUR Darstellung!)."""
    light_config = zone_data.get('light', {})
    
    return {
        "type": "custom:light-automation-config",
        "title": "Light Automation",
        "zone_id": zone_data.get('zone_id', ''),
        "config": light_config,
        "sliders": [
            {
                "key": "brightness_threshold",
                "label": "Brightness Threshold",
                "min": 0.0,
                "max": 1.0,
                "step": 0.05,
                "value": light_config.get("brightness_threshold", 0.3),
            },
            {
                "key": "presence_delay_seconds",
                "label": "Presence Delay (seconds)",
                "min": 60,
                "max": 600,
                "step": 30,
                "value": light_config.get("presence_delay_seconds", 300),
            },
        ],
        "toggles": [
            {"key": "enabled", "label": "Enabled", "value": light_config.get("enabled", True)},
            {"key": "presence_trigger", "label": "Presence Trigger", "value": light_config.get("presence_trigger", True)},
            {"key": "time_dependent", "label": "Time Dependent", "value": light_config.get("time_dependent", True)},
            {"key": "mood_dependent", "label": "Mood Dependent", "value": light_config.get("mood_dependent", True)},
        ],
    }


def prepare_rules_card_data(rules_data: Dict[str, Any]) -> Dict[str, Any]:
    """Daten für Rules Card vorbereiten (NUR Darstellung!)."""
    rules = rules_data.get('rules', [])
    
    def format_trigger(trigger: Dict[str, Any]) -> str:
        parts = []
        if "presence" in trigger:
            parts.append(f"Präsenz: {'an' if trigger['presence'] else 'aus'}")
        if "brightness_below" in trigger:
            parts.append(f"Helligkeit < {trigger['brightness_below']*100:.0f}%")
        if "no_presence_duration_s" in trigger:
            mins = trigger["no_presence_duration_s"] // 60
            parts.append(f"Keine Präsenz {mins} Min")
        return " + ".join(parts) if parts else "Unknown"
    
    def format_action(action: Dict[str, Any]) -> str:
        module = action.get("module", "unknown")
        command = action.get("command", "unknown")
        params = action.get("parameters", {})
        
        if module == "light" and command == "turn_on":
            brightness = params.get("brightness_pct", 100)
            return f"Licht an ({brightness}%)"
        elif module == "light" and command == "turn_off":
            return "Licht aus"
        else:
            return f"{module}: {command}"
    
    return {
        "type": "custom:automation-rules-card",
        "title": "Automation Rules",
        "zone_id": rules_data.get('zone_id', ''),
        "rules": [
            {
                "rule_id": rule.get("rule_id", ""),
                "name": rule.get("name", "Unknown"),
                "description": rule.get("description", ""),
                "mode": rule.get("mode", "learning"),
                "trigger": format_trigger(rule.get("trigger", {})),
                "action": format_action(rule.get("action", {})),
                "executed_count": rule.get("executed_count", 0),
                "last_executed": rule.get("last_executed"),
            }
            for rule in rules
        ],
    }


# =============================================================================
# Singleton (pro HA Instanz)
# =============================================================================

_clients: Dict[str, ZoneAutomationClient] = {}


def get_zone_automation_client(hass: HomeAssistant, core_url: str, api_token: str) -> ZoneAutomationClient:
    """Client holen/erstellen."""
    key = f"{core_url}:{api_token}"
    
    if key not in _clients:
        _clients[key] = ZoneAutomationClient(hass, core_url, api_token)
    
    return _clients[key]
