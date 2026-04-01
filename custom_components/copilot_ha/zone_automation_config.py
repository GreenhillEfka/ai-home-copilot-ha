"""Zone Automation Configuration — Grafische Konfiguration (SOTA 2026).

Implementiert grafische Konfiguration für:
1. Zone Automation Settings (learning/autonomous/off)
2. Neuron Modes pro Zone (autonomous/learning/off)
3. Light Automation (Präsenz + Helligkeit + Zeit + Stimmung)
4. Rule Visualization + Editing
5. Habitus Learning Status

Features:
- Lovelace Card für Konfiguration
- Real-time Status Updates
- One-Click Mode Switching
- Rule Preview + Testing
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
import threading

_LOGGER = logging.getLogger(__name__)


# =============================================================================
# ZONE AUTOMATION CARD CONFIG
# =============================================================================

@dataclass
class ZoneAutomationCardConfig:
    """Lovelace Card für Zone Automation."""
    
    zone_id: str
    zone_name: str
    automation_mode: str  # learning, autonomous, off
    neuron_modes: Dict[str, str] = field(default_factory=dict)
    light_config: Dict[str, Any] = field(default_factory=dict)
    active_rules: List[Dict[str, Any]] = field(default_factory=list)
    learned_patterns: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_lovelace_yaml(self) -> str:
        """Lovelace YAML generieren."""
        lines = [
            "type: custom:zone-automation-card",
            f"zone_id: {self.zone_id}",
            f"title: {self.zone_name} Automation",
            "automation_mode:",
            f"  current: {self.automation_mode}",
            "  options:",
            "    - learning",
            "    - autonomous",
            "    - off",
            "neurons:",
        ]
        
        for neuron_id, mode in self.neuron_modes.items():
            lines.append(f"  - entity_id: {neuron_id}")
            lines.append(f"    mode: {mode}")
        
        lines.extend([
            "light_automation:",
            f"  enabled: {self.light_config.get('enabled', True)}",
            f"  presence_trigger: {self.light_config.get('presence_trigger', True)}",
            f"  brightness_threshold: {self.light_config.get('brightness_threshold', 0.3)}",
            f"  presence_delay_seconds: {self.light_config.get('presence_delay_seconds', 300)}",
            f"  time_dependent: {self.light_config.get('time_dependent', True)}",
            f"  mood_dependent: {self.light_config.get('mood_dependent', True)}",
            "active_rules:",
        ])
        
        for rule in self.active_rules:
            lines.append(f"  - name: {rule.get('name', 'Unknown')}")
            lines.append(f"    mode: {rule.get('mode', 'learning')}")
            lines.append(f"    executed_count: {rule.get('executed_count', 0)}")
        
        lines.append(f"learned_patterns: {self.learned_patterns}")
        
        return "\n".join(lines)


# =============================================================================
# NEURON MODE SELECTOR
# =============================================================================

class NeuronModeSelector:
    """Selector für Neuron Modes."""
    
    def __init__(self, hass):
        self._hass = hass
        self._neuron_configs: Dict[str, Dict[str, str]] = {}
        self._lock = threading.Lock()
    
    def set_neuron_mode(
        self,
        zone_id: str,
        neuron_id: str,
        mode: str,
    ) -> Dict[str, Any]:
        """Neuron Mode setzen."""
        with self._lock:
            if zone_id not in self._neuron_configs:
                self._neuron_configs[zone_id] = {}
            
            self._neuron_configs[zone_id][neuron_id] = mode
        
        # Call service in HA
        self._hass.services.call(
            "copilot_ha",
            "set_neuron_mode",
            {
                "zone_id": zone_id,
                "neuron_id": neuron_id,
                "mode": mode,
            },
        )
        
        return {
            "success": True,
            "zone_id": zone_id,
            "neuron_id": neuron_id,
            "mode": mode,
        }
    
    def get_neuron_modes(self, zone_id: str) -> Dict[str, str]:
        """Neuron Modes für Zone."""
        with self._lock:
            return self._neuron_configs.get(zone_id, {}).copy()
    
    def are_all_autonomous(self, zone_id: str) -> bool:
        """Prüfen ob alle Neuronen autonomous."""
        with self._lock:
            modes = self._neuron_configs.get(zone_id, {}).values()
            if not modes:
                return False
            return all(m == "autonomous" for m in modes)
    
    def get_card_config(self, zone_id: str, zone_name: str) -> Dict[str, Any]:
        """Card Konfiguration."""
        with self._lock:
            modes = self._neuron_configs.get(zone_id, {})
            
            return {
                "type": "custom:neuron-mode-selector",
                "title": f"{zone_name} Neuron Modes",
                "zone_id": zone_id,
                "neurons": [
                    {
                        "neuron_id": neuron_id,
                        "mode": mode,
                        "options": ["autonomous", "learning", "off"],
                    }
                    for neuron_id, mode in modes.items()
                ],
                "all_autonomous": all(m == "autonomous" for m in modes.values()) if modes else False,
            }


# =============================================================================
# LIGHT AUTOMATION CONFIGURATOR
# =============================================================================

class LightAutomationConfigurator:
    """Konfigurator für Licht-Automationen."""
    
    def __init__(self, hass):
        self._hass = hass
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def configure_light_automation(
        self,
        zone_id: str,
        enabled: bool = True,
        presence_trigger: bool = True,
        brightness_threshold: float = 0.3,
        presence_delay_seconds: int = 300,
        time_dependent: bool = True,
        mood_dependent: bool = True,
        sunrise_offset_minutes: int = 30,
        sunset_offset_minutes: int = 30,
    ) -> Dict[str, Any]:
        """Licht-Automation konfigurieren."""
        config = {
            "enabled": enabled,
            "presence_trigger": presence_trigger,
            "brightness_threshold": brightness_threshold,
            "presence_delay_seconds": presence_delay_seconds,
            "time_dependent": time_dependent,
            "mood_dependent": mood_dependent,
            "sunrise_offset_minutes": sunrise_offset_minutes,
            "sunset_offset_minutes": sunset_offset_minutes,
        }
        
        with self._lock:
            self._configs[zone_id] = config
        
        # Call service in HA
        self._hass.services.call(
            "copilot_ha",
            "configure_light_automation",
            {
                "zone_id": zone_id,
                **config,
            },
        )
        
        return {
            "success": True,
            "zone_id": zone_id,
            "config": config,
        }
    
    def get_config(self, zone_id: str) -> Dict[str, Any]:
        """Config für Zone."""
        with self._lock:
            return self._configs.get(zone_id, {}).copy()
    
    def get_card_config(self, zone_id: str) -> Dict[str, Any]:
        """Card Konfiguration."""
        config = self.get_config(zone_id)
        
        return {
            "type": "custom:light-automation-config",
            "title": "Light Automation",
            "zone_id": zone_id,
            "config": config,
            "sliders": [
                {
                    "key": "brightness_threshold",
                    "label": "Brightness Threshold",
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.05,
                    "value": config.get("brightness_threshold", 0.3),
                },
                {
                    "key": "presence_delay_seconds",
                    "label": "Presence Delay (seconds)",
                    "min": 60,
                    "max": 600,
                    "step": 30,
                    "value": config.get("presence_delay_seconds", 300),
                },
            ],
            "toggles": [
                {"key": "enabled", "label": "Enabled", "value": config.get("enabled", True)},
                {"key": "presence_trigger", "label": "Presence Trigger", "value": config.get("presence_trigger", True)},
                {"key": "time_dependent", "label": "Time Dependent", "value": config.get("time_dependent", True)},
                {"key": "mood_dependent", "label": "Mood Dependent", "value": config.get("mood_dependent", True)},
            ],
        }


# =============================================================================
# RULE VISUALIZER
# =============================================================================

class RuleVisualizer:
    """Visualizer für Automation Rules."""
    
    def __init__(self, hass):
        self._hass = hass
        self._rules: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = threading.Lock()
    
    def update_rules(self, zone_id: str, rules: List[Dict[str, Any]]) -> None:
        """Rules updaten."""
        with self._lock:
            self._rules[zone_id] = rules
    
    def get_card_config(self, zone_id: str) -> Dict[str, Any]:
        """Card Konfiguration."""
        with self._lock:
            rules = self._rules.get(zone_id, [])
            
            return {
                "type": "custom:automation-rules-card",
                "title": "Automation Rules",
                "zone_id": zone_id,
                "rules": [
                    {
                        "rule_id": rule.get("rule_id", ""),
                        "name": rule.get("name", "Unknown"),
                        "description": rule.get("description", ""),
                        "mode": rule.get("mode", "learning"),
                        "trigger": self._format_trigger(rule.get("trigger", {})),
                        "action": self._format_action(rule.get("action", {})),
                        "executed_count": rule.get("executed_count", 0),
                        "last_executed": rule.get("last_executed"),
                    }
                    for rule in rules
                ],
            }
    
    def _format_trigger(self, trigger: Dict[str, Any]) -> str:
        """Trigger formatieren."""
        parts = []
        if "presence" in trigger:
            parts.append(f"Präsenz: {'an' if trigger['presence'] else 'aus'}")
        if "brightness_below" in trigger:
            parts.append(f"Helligkeit < {trigger['brightness_below']*100:.0f}%")
        if "no_presence_duration_s" in trigger:
            mins = trigger["no_presence_duration_s"] // 60
            parts.append(f"Keine Präsenz {mins} Min")
        return " + ".join(parts) if parts else "Unknown"
    
    def _format_action(self, action: Dict[str, Any]) -> str:
        """Action formatieren."""
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


# =============================================================================
# HABITUS LEARNING STATUS
# =============================================================================

class HabitusLearningStatus:
    """Status für Habitus Learning."""
    
    def __init__(self, hass):
        self._hass = hass
        self._zone_patterns: Dict[str, int] = {}
        self._zone_feedback: Dict[str, Dict[str, int]] = {}
        self._lock = threading.Lock()
    
    def update_patterns(self, zone_id: str, count: int) -> None:
        """Pattern Count updaten."""
        with self._lock:
            self._zone_patterns[zone_id] = count
    
    def update_feedback(self, zone_id: str, accepted: int, rejected: int) -> None:
        """Feedback updaten."""
        with self._lock:
            self._zone_feedback[zone_id] = {
                "accepted": accepted,
                "rejected": rejected,
                "total": accepted + rejected,
            }
    
    def get_card_config(self, zone_id: str) -> Dict[str, Any]:
        """Card Konfiguration."""
        with self._lock:
            patterns = self._zone_patterns.get(zone_id, 0)
            feedback = self._zone_feedback.get(zone_id, {"accepted": 0, "rejected": 0, "total": 0})
            
            acceptance_rate = feedback["accepted"] / max(feedback["total"], 1) * 100
            
            return {
                "type": "custom:habitus-learning-status",
                "title": "Habitus Learning",
                "zone_id": zone_id,
                "patterns_discovered": patterns,
                "feedback": feedback,
                "acceptance_rate": round(acceptance_rate, 1),
                "status_text": self._get_status_text(patterns, acceptance_rate),
            }
    
    def _get_status_text(self, patterns: int, acceptance_rate: float) -> str:
        """Status Text."""
        if patterns == 0:
            return "Noch keine Patterns gelernt"
        elif patterns < 5:
            return f"{patterns} Patterns gelernt (Anfänger)"
        elif patterns < 20:
            return f"{patterns} Patterns gelernt (Fortgeschritten)"
        elif acceptance_rate >= 80:
            return f"{patterns} Patterns gelernt (Experte - {acceptance_rate:.0f}% Akzeptanz)"
        else:
            return f"{patterns} Patterns gelernt ({acceptance_rate:.0f}% Akzeptanz)"


# =============================================================================
# ZONE AUTOMATION DASHBOARD (Main Class)
# =============================================================================

class ZoneAutomationDashboard:
    """Haupt-Dashboard für Zone Automation."""
    
    def __init__(self, hass):
        self._hass = hass
        self._neuron_selector = NeuronModeSelector(hass)
        self._light_configurator = LightAutomationConfigurator(hass)
        self._rule_visualizer = RuleVisualizer(hass)
        self._learning_status = HabitusLearningStatus(hass)
        self._lock = threading.Lock()
    
    def neuron_selector(self) -> NeuronModeSelector:
        return self._neuron_selector
    
    def light_configurator(self) -> LightAutomationConfigurator:
        return self._light_configurator
    
    def rule_visualizer(self) -> RuleVisualizer:
        return self._rule_visualizer
    
    def learning_status(self) -> HabitusLearningStatus:
        return self._learning_status
    
    def get_full_zone_config(self, zone_id: str, zone_name: str) -> Dict[str, Any]:
        """Vollständige Zone-Konfiguration."""
        return {
            "zone_id": zone_id,
            "zone_name": zone_name,
            "cards": {
                "neuron_modes": self._neuron_selector.get_card_config(zone_id),
                "light_automation": self._light_configurator.get_card_config(zone_id),
                "rules": self._rule_visualizer.get_card_config(zone_id),
                "learning": self._learning_status.get_card_config(zone_id),
            },
        }
    
    def get_all_zones_dashboard(self) -> Dict[str, Any]:
        """Dashboard für alle Zonen."""
        # In production: Get zones from HA
        zones = [
            {"zone_id": "living", "zone_name": "Wohnzimmer"},
            {"zone_id": "bath", "zone_name": "Bad"},
            {"zone_id": "kitchen", "zone_name": "Küche"},
            {"zone_id": "bedroom", "zone_name": "Schlafzimmer"},
        ]
        
        return {
            "title": "Zone Automation Dashboard",
            "zones": [
                self.get_full_zone_config(z["zone_id"], z["zone_name"])
                for z in zones
            ],
        }
    
    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "neuron_selector": len(self._neuron_selector._neuron_configs),
            "light_configs": len(self._light_configurator._configs),
            "rule_visualizer": len(self._rule_visualizer._rules),
        }


# =============================================================================
# Singleton
# =============================================================================

_dashboard_instance: Optional[ZoneAutomationDashboard] = None


def get_zone_automation_dashboard(hass) -> ZoneAutomationDashboard:
    """Singleton-Zugriff."""
    global _dashboard_instance
    
    if _dashboard_instance is None:
        _dashboard_instance = ZoneAutomationDashboard(hass)
    
    return _dashboard_instance
