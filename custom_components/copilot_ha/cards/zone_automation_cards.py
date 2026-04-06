"""Zone Automation Lovelace Cards — NUR Darstellung (KEINE Logik!).

Architecture:
- Diese Cards machen KEINE Logik!
- Nur Daten von CORE API holen (via Client)
- Nur Darstellung in Lovelace
- User-Actions → API-Call via Client

Cards:
1. ZoneAutomationCard — Haupt-Card pro Zone
2. NeuronModeCard — Neuron Modes anzeigen/setzen
3. LightAutomationCard — Licht-Konfiguration
4. RulesCard — Automation Rules anzeigen
5. LearningStatusCard — Habitus Learning Status
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity

try:
    from homeassistant.components.lovelace import LovelaceCard  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - HA version compatibility
    LovelaceCard = type("LovelaceCard", (), {})

_LOGGER = logging.getLogger(__name__)


# =============================================================================
# ZONE AUTOMATION CARD (Haupt-Card)
# =============================================================================

class ZoneAutomationCard:
    """Lovelace Card für Zone Automation (NUR Darstellung!)."""
    
    @staticmethod
    def create_card_config(zone_data: Dict[str, Any]) -> Dict[str, Any]:
        """Card Konfiguration generieren (NUR Daten vorbereiten!)."""
        return {
            "type": "custom:zone-automation-card",
            "title": f"{zone_data.get('zone_name', zone_data.get('zone_id', 'Zone'))} Automation",
            "zone_id": zone_data.get('zone_id', ''),
            "automation_mode": zone_data.get('automation_mode', 'learning'),
            "entity_count": len(zone_data.get('neuron_modes', {})),
            "rules_count": len(zone_data.get('active_rules', [])),
            "learned_patterns": zone_data.get('learned_patterns', 0),
        }
    
    @staticmethod
    def render(zone_data: Dict[str, Any]) -> str:
        """Card rendern (NUR HTML/JS!)."""
        zone_id = zone_data.get('zone_id', 'unknown')
        zone_name = zone_data.get('zone_name', zone_id)
        automation_mode = zone_data.get('automation_mode', 'learning')
        
        return f"""
        <div class="zone-automation-card">
            <h3>{zone_name} Automation</h3>
            <div class="mode-selector">
                <label>Mode:</label>
                <select data-zone="{zone_id}" data-action="set_mode">
                    <option value="learning" {"selected" if automation_mode == "learning" else ""}>Learning</option>
                    <option value="autonomous" {"selected" if automation_mode == "autonomous" else ""}>Autonomous</option>
                    <option value="off" {"selected" if automation_mode == "off" else ""}>Off</option>
                </select>
            </div>
            <div class="stats">
                <span class="stat">Neurons: {len(zone_data.get('neuron_modes', {}))}</span>
                <span class="stat">Rules: {len(zone_data.get('active_rules', []))}</span>
                <span class="stat">Learned: {zone_data.get('learned_patterns', 0)}</span>
            </div>
        </div>
        """


# =============================================================================
# NEURON MODE CARD
# =============================================================================

class NeuronModeCard:
    """Lovelace Card für Neuron Modes (NUR Darstellung!)."""
    
    @staticmethod
    def create_card_config(neuron_modes: Dict[str, str], zone_id: str) -> Dict[str, Any]:
        """Card Konfiguration (NUR Daten!)."""
        return {
            "type": "custom:neuron-mode-card",
            "title": "Neuron Modes",
            "zone_id": zone_id,
            "neurons": [
                {
                    "neuron_id": neuron_id,
                    "mode": mode,
                    "options": ["autonomous", "learning", "off"],
                }
                for neuron_id, mode in neuron_modes.items()
            ],
        }
    
    @staticmethod
    def render(neuron_modes: Dict[str, str], zone_id: str) -> str:
        """Card rendern (NUR HTML!)."""
        neurons_html = ""
        for neuron_id, mode in neuron_modes.items():
            neurons_html += f"""
            <div class="neuron-row">
                <span class="neuron-name">{neuron_id}</span>
                <select data-zone="{zone_id}" data-neuron="{neuron_id}" data-action="set_neuron_mode">
                    <option value="autonomous" {"selected" if mode == "autonomous" else ""}>Autonomous</option>
                    <option value="learning" {"selected" if mode == "learning" else ""}>Learning</option>
                    <option value="off" {"selected" if mode == "off" else ""}>Off</option>
                </select>
            </div>
            """
        
        return f"""
        <div class="neuron-mode-card">
            <h4>Neuron Modes</h4>
            {neurons_html}
        </div>
        """


# =============================================================================
# LIGHT AUTOMATION CARD
# =============================================================================

class LightAutomationCard:
    """Lovelace Card für Light Automation (NUR Darstellung!)."""
    
    @staticmethod
    def create_card_config(light_config: Dict[str, Any], zone_id: str) -> Dict[str, Any]:
        """Card Konfiguration (NUR Daten!)."""
        return {
            "type": "custom:light-automation-card",
            "title": "Light Automation",
            "zone_id": zone_id,
            "config": {
                "enabled": light_config.get("enabled", True),
                "presence_trigger": light_config.get("presence_trigger", True),
                "brightness_threshold": light_config.get("brightness_threshold", 0.3),
                "presence_delay_seconds": light_config.get("presence_delay_seconds", 300),
                "time_dependent": light_config.get("time_dependent", True),
                "mood_dependent": light_config.get("mood_dependent", True),
            },
        }
    
    @staticmethod
    def render(light_config: Dict[str, Any], zone_id: str) -> str:
        """Card rendern (NUR HTML!)."""
        return f"""
        <div class="light-automation-card">
            <h4>Light Automation</h4>
            <div class="toggle-row">
                <label>Enabled:</label>
                <input type="checkbox" data-zone="{zone_id}" data-key="enabled" 
                       {"checked" if light_config.get("enabled", True) else ""} 
                       data-action="update_light_config"/>
            </div>
            <div class="toggle-row">
                <label>Presence Trigger:</label>
                <input type="checkbox" data-zone="{zone_id}" data-key="presence_trigger"
                       {"checked" if light_config.get("presence_trigger", True) else ""}
                       data-action="update_light_config"/>
            </div>
            <div class="slider-row">
                <label>Brightness Threshold:</label>
                <input type="range" min="0" max="1" step="0.05" 
                       data-zone="{zone_id}" data-key="brightness_threshold"
                       value="{light_config.get("brightness_threshold", 0.3)}"
                       data-action="update_light_config"/>
                <span class="value">{light_config.get("brightness_threshold", 0.3) * 100:.0f}%</span>
            </div>
            <div class="slider-row">
                <label>Presence Delay:</label>
                <input type="range" min="60" max="600" step="30"
                       data-zone="{zone_id}" data-key="presence_delay_seconds"
                       value="{light_config.get("presence_delay_seconds", 300)}"
                       data-action="update_light_config"/>
                <span class="value">{light_config.get("presence_delay_seconds", 300) // 60} Min</span>
            </div>
            <div class="toggle-row">
                <label>Time Dependent:</label>
                <input type="checkbox" data-zone="{zone_id}" data-key="time_dependent"
                       {"checked" if light_config.get("time_dependent", True) else ""}
                       data-action="update_light_config"/>
            </div>
            <div class="toggle-row">
                <label>Mood Dependent:</label>
                <input type="checkbox" data-zone="{zone_id}" data-key="mood_dependent"
                       {"checked" if light_config.get("mood_dependent", True) else ""}
                       data-action="update_light_config"/>
            </div>
        </div>
        """


# =============================================================================
# RULES CARD
# =============================================================================

class RulesCard:
    """Lovelace Card für Automation Rules (NUR Darstellung!)."""
    
    @staticmethod
    def create_card_config(rules: List[Dict[str, Any]], zone_id: str) -> Dict[str, Any]:
        """Card Konfiguration (NUR Daten!)."""
        return {
            "type": "custom:rules-card",
            "title": "Automation Rules",
            "zone_id": zone_id,
            "rules": [
                {
                    "rule_id": r.get("rule_id", ""),
                    "name": r.get("name", "Unknown"),
                    "mode": r.get("mode", "learning"),
                    "trigger": RulesCard._format_trigger(r.get("trigger", {})),
                    "action": RulesCard._format_action(r.get("action", {})),
                    "executed_count": r.get("executed_count", 0),
                }
                for r in rules
            ],
        }
    
    @staticmethod
    def _format_trigger(trigger: Dict[str, Any]) -> str:
        """Trigger formatieren (NUR Darstellung!)."""
        parts = []
        if "presence" in trigger:
            parts.append(f"Präsenz: {'an' if trigger['presence'] else 'aus'}")
        if "brightness_below" in trigger:
            parts.append(f"Helligkeit < {trigger['brightness_below']*100:.0f}%")
        if "no_presence_duration_s" in trigger:
            mins = trigger["no_presence_duration_s"] // 60
            parts.append(f"Keine Präsenz {mins} Min")
        return " + ".join(parts) if parts else "Unknown"
    
    @staticmethod
    def _format_action(action: Dict[str, Any]) -> str:
        """Action formatieren (NUR Darstellung!)."""
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
    
    @staticmethod
    def render(rules: List[Dict[str, Any]], zone_id: str) -> str:
        """Card rendern (NUR HTML!)."""
        rules_html = ""
        for rule in rules:
            rules_html += f"""
            <div class="rule-row">
                <div class="rule-name">{rule['name']}</div>
                <div class="rule-mode mode-{rule['mode']}">{rule['mode']}</div>
                <div class="rule-trigger">Trigger: {rule['trigger']}</div>
                <div class="rule-action">Action: {rule['action']}</div>
                <div class="rule-stats">Executed: {rule['executed_count']}x</div>
            </div>
            """
        
        return f"""
        <div class="rules-card">
            <h4>Automation Rules</h4>
            {rules_html}
        </div>
        """


# =============================================================================
# LEARNING STATUS CARD
# =============================================================================

class LearningStatusCard:
    """Lovelace Card für Habitus Learning Status (NUR Darstellung!)."""
    
    @staticmethod
    def create_card_config(learned_patterns: int, feedback_stats: Dict[str, int], zone_id: str) -> Dict[str, Any]:
        """Card Konfiguration (NUR Daten!)."""
        total_feedback = feedback_stats.get("accepted", 0) + feedback_stats.get("rejected", 0)
        acceptance_rate = feedback_stats.get("accepted", 0) / max(total_feedback, 1) * 100
        
        return {
            "type": "custom:learning-status-card",
            "title": "Habitus Learning",
            "zone_id": zone_id,
            "patterns_discovered": learned_patterns,
            "feedback": feedback_stats,
            "acceptance_rate": round(acceptance_rate, 1),
            "status_text": LearningStatusCard._get_status_text(learned_patterns, acceptance_rate),
        }
    
    @staticmethod
    def _get_status_text(patterns: int, acceptance_rate: float) -> str:
        """Status Text (NUR Logik für Darstellung!)."""
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
    
    @staticmethod
    def render(learned_patterns: int, feedback_stats: Dict[str, int], zone_id: str) -> str:
        """Card rendern (NUR HTML!)."""
        status_text = LearningStatusCard._get_status_text(
            learned_patterns,
            feedback_stats.get("accepted", 0) / max(feedback_stats.get("total", 1), 1) * 100
        )
        
        return f"""
        <div class="learning-status-card">
            <h4>Habitus Learning</h4>
            <div class="stat-row">
                <span class="stat-label">Patterns:</span>
                <span class="stat-value">{learned_patterns}</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Feedback:</span>
                <span class="stat-value">{feedback_stats.get('accepted', 0)} ✓ / {feedback_stats.get('rejected', 0)} ✗</span>
            </div>
            <div class="stat-row">
                <span class="stat-label">Status:</span>
                <span class="stat-value status-text">{status_text}</span>
            </div>
        </div>
        """


# =============================================================================
# CARD REGISTRY (für Lovelace)
# =============================================================================

def register_cards() -> Dict[str, Any]:
    """Cards registrieren (für Lovelace resources)."""
    from .voice_cards import register_voice_cards
    voice_cards = register_voice_cards()
    return {
        "zone-automation-card": ZoneAutomationCard,
        "neuron-mode-card": NeuronModeCard,
        "light-automation-card": LightAutomationCard,
        "rules-card": RulesCard,
        "learning-status-card": LearningStatusCard,
        **voice_cards,
    }


def get_dashboard_config(zone_data: Dict[str, Any]) -> Dict[str, Any]:
    """Vollständige Dashboard-Konfiguration (NUR Daten!)."""
    return {
        "title": "Zone Automation Dashboard",
        "views": [
            {
                "title": zone_data.get("zone_name", zone_data.get("zone_id", "Zone")),
                "cards": [
                    ZoneAutomationCard.create_card_config(zone_data),
                    NeuronModeCard.create_card_config(
                        zone_data.get("neuron_modes", {}),
                        zone_data.get("zone_id", ""),
                    ),
                    LightAutomationCard.create_card_config(
                        zone_data.get("light", {}),
                        zone_data.get("zone_id", ""),
                    ),
                    RulesCard.create_card_config(
                        zone_data.get("active_rules", []),
                        zone_data.get("zone_id", ""),
                    ),
                    LearningStatusCard.create_card_config(
                        zone_data.get("learned_patterns", 0),
                        zone_data.get("feedback", {}),
                        zone_data.get("zone_id", ""),
                    ),
                ],
            }
        ],
    }
