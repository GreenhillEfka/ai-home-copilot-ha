"""Modular Dashboard HA — Frontend/User Visualization (SOTA 2026).

HA-spezifische Dashboard-Komponenten:
1. Intelligence Score Card
2. Zone Activity Heatmap
3. Mood & Context Card
4. Suggestions Card
5. Network Health Card
6. Learning Progress Card
7. Quick Actions Card
8. Update Status Card

SOTA 2026:
- Lovelace Card Integration
- Real-time Entity Updates
- One-Click Actions
- Mobile Responsive
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
import threading

_LOGGER = logging.getLogger(__name__)


# =============================================================================
# LOVELACE CARD CONFIGS
# =============================================================================

@dataclass
class LovelaceCardConfig:
    """Lovelace Card Konfiguration."""
    
    card_type: str
    title: str
    entities: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    
    def to_yaml(self) -> str:
        """YAML für Lovelace."""
        lines = [
            f"type: {self.card_type}",
            f"title: {self.title}",
        ]
        
        if self.entities:
            lines.append("entities:")
            for entity in self.entities:
                lines.append(f"  - {entity}")
        
        for key, value in self.config.items():
            lines.append(f"{key}: {value}")
        
        return "\n".join(lines)


# =============================================================================
# INTELLIGENCE SCORE CARD
# =============================================================================

class IntelligenceScoreCard:
    """Intelligence Score Lovelace Card."""
    
    def __init__(self, hass):
        self._hass = hass
        self._score = 0.0
        self._level = "Novice"
        self._lock = threading.Lock()
    
    def update_score(self, score: float, level: str) -> None:
        """Score updaten."""
        with self._lock:
            self._score = score
            self._level = level
    
    def get_card_config(self) -> LovelaceCardConfig:
        """Card Konfiguration."""
        with self._lock:
            # Color based on score
            if self._score >= 80:
                color = "#22c55e"  # Green
            elif self._score >= 60:
                color = "#eab308"  # Yellow
            else:
                color = "#ef4444"  # Red
            
            return LovelaceCardConfig(
                card_type="gauge",
                title="Intelligence Score",
                config={
                    "entity": "sensor.pilotsuite_intelligence_score",
                    "min": 0,
                    "max": 100,
                    "needle": True,
                    "segments": [
                        {"from": 0, "to": 40, "color": "#ef4444"},
                        {"from": 40, "to": 70, "color": "#eab308"},
                        {"from": 70, "to": 100, "color": "#22c55e"},
                    ],
                    "value": round(self._score, 1),
                },
            )
    
    def get_status_text(self) -> str:
        """Status Text."""
        with self._lock:
            descriptions = {
                "Expert": "System lernt autonom und trifft präzise Vorhersagen",
                "Advanced": "System erkennt Muster und schlägt Automationen vor",
                "Intermediate": "System sammelt Daten und lernt Grundlagen",
                "Beginner": "System wird konfiguriert und beobachtet",
                "Novice": "System startet und initialisiert",
            }
            return f"{self._level}: {descriptions.get(self._level, '')}"


# =============================================================================
# ZONE ACTIVITY HEATMAP
# =============================================================================

class ZoneActivityHeatmap:
    """Zone Activity Heatmap Card."""
    
    def __init__(self, hass):
        self._hass = hass
        self._zone_data: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def update_zone(self, zone_id: str, activity: float, entities: List[str]) -> None:
        """Zone updaten."""
        with self._lock:
            self._zone_data[zone_id] = {
                "activity": activity,
                "entities": entities,
                "last_update": datetime.now(timezone.utc).isoformat(),
            }
    
    def get_card_config(self) -> LovelaceCardConfig:
        """Card Konfiguration."""
        with self._lock:
            # Generate entities list
            all_entities = []
            for zone_data in self._zone_data.values():
                all_entities.extend(zone_data.get("entities", []))
            
            return LovelaceCardConfig(
                card_type="custom:heatmap-card",
                title="Zone Activity",
                entities=all_entities[:20],  # Max 20 entities
                config={
                    "zones": [
                        {
                            "zone_id": zone_id,
                            "activity": data["activity"],
                            "color": self._get_activity_color(data["activity"]),
                        }
                        for zone_id, data in self._zone_data.items()
                    ],
                    "color_scale": {
                        "low": "#22c55e",
                        "medium": "#eab308",
                        "high": "#ef4444",
                    },
                },
            )
    
    def _get_activity_color(self, activity: float) -> str:
        """Activity zu Farbe."""
        if activity < 0.3:
            return "#22c55e"  # Green
        elif activity < 0.7:
            return "#eab308"  # Yellow
        else:
            return "#ef4444"  # Red


# =============================================================================
# MOOD & CONTEXT CARD
# =============================================================================

class MoodContextCard:
    """Mood & Context Card."""
    
    def __init__(self, hass):
        self._hass = hass
        self._mood_dimensions: Dict[str, float] = {}
        self._context_factors: List[str] = []
        self._lock = threading.Lock()
    
    def update_mood(self, dimensions: Dict[str, float], context: List[str]) -> None:
        """Mood updaten."""
        with self._lock:
            self._mood_dimensions = dimensions
            self._context_factors = context
    
    def get_card_config(self) -> LovelaceCardConfig:
        """Card Konfiguration."""
        with self._lock:
            return LovelaceCardConfig(
                card_type="custom:mood-card",
                title="Mood & Context",
                config={
                    "dimensions": self._mood_dimensions,
                    "context": self._context_factors,
                    "radar_chart": True,
                    "show_trend": True,
                },
            )
    
    def get_radar_data(self) -> Dict[str, Any]:
        """Radar Chart Daten."""
        with self._lock:
            return {
                "labels": list(self._mood_dimensions.keys()),
                "values": list(self._mood_dimensions.values()),
                "max": 1.0,
            }


# =============================================================================
# SUGGESTIONS CARD
# =============================================================================

class SuggestionsCard:
    """Suggestions Card mit Accept/Reject."""
    
    def __init__(self, hass):
        self._hass = hass
        self._suggestions: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
    
    def add_suggestion(self, suggestion: Dict[str, Any]) -> None:
        """Suggestion hinzufügen."""
        with self._lock:
            self._suggestions.append({
                **suggestion,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "pending",
            })
    
    def accept_suggestion(self, suggestion_id: str) -> None:
        """Suggestion akzeptieren."""
        with self._lock:
            for s in self._suggestions:
                if s.get("id") == suggestion_id:
                    s["status"] = "accepted"
                    break
    
    def reject_suggestion(self, suggestion_id: str) -> None:
        """Suggestion ablehnen."""
        with self._lock:
            for s in self._suggestions:
                if s.get("id") == suggestion_id:
                    s["status"] = "rejected"
                    break
    
    def get_card_config(self) -> LovelaceCardConfig:
        """Card Konfiguration."""
        with self._lock:
            pending = [s for s in self._suggestions if s.get("status") == "pending"]
            
            return LovelaceCardConfig(
                card_type="custom:suggestions-card",
                title="Smart Suggestions",
                config={
                    "suggestions": pending[:5],  # Show 5 pending
                    "show_accept_buttons": True,
                    "show_reject_buttons": True,
                    "auto_dismiss_seconds": 3600,
                },
            )


# =============================================================================
# NETWORK HEALTH CARD
# =============================================================================

class NetworkHealthCard:
    """Network Health Card (Z-Wave, ZigBee, Thread)."""
    
    def __init__(self, hass):
        self._hass = hass
        self._networks: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def update_network(self, protocol: str, nodes: int, health: float, messages: int) -> None:
        """Network updaten."""
        with self._lock:
            self._networks[protocol] = {
                "nodes": nodes,
                "health": health,
                "messages": messages,
                "last_update": datetime.now(timezone.utc).isoformat(),
            }
    
    def get_card_config(self) -> LovelaceCardConfig:
        """Card Konfiguration."""
        with self._lock:
            return LovelaceCardConfig(
                card_type="custom:network-health-card",
                title="Network Health",
                config={
                    "networks": [
                        {
                            "protocol": protocol,
                            "icon": self._get_protocol_icon(protocol),
                            "nodes": data["nodes"],
                            "health": round(data["health"] * 100, 1),
                            "color": self._get_health_color(data["health"]),
                        }
                        for protocol, data in self._networks.items()
                    ],
                    "show_topology_link": True,
                },
            )
    
    def _get_protocol_icon(self, protocol: str) -> str:
        """Protocol Icon."""
        icons = {
            "zwave": "mdi:z-wave",
            "zigbee": "mdi:zigbee",
            "thread": "mdi:thread",
        }
        return icons.get(protocol, "mdi:network")
    
    def _get_health_color(self, health: float) -> str:
        """Health zu Farbe."""
        if health >= 0.8:
            return "#22c55e"
        elif health >= 0.5:
            return "#eab308"
        else:
            return "#ef4444"


# =============================================================================
# LEARNING PROGRESS CARD
# =============================================================================

class LearningProgressCard:
    """Learning Progress Card."""
    
    def __init__(self, hass):
        self._hass = hass
        self._patterns_discovered = 0
        self._feedback_total = 0
        self._feedback_accepted = 0
        self._learning_velocity = 0.0
        self._lock = threading.Lock()
    
    def update_progress(
        self,
        patterns: int,
        feedback_total: int,
        feedback_accepted: int,
        velocity: float,
    ) -> None:
        """Progress updaten."""
        with self._lock:
            self._patterns_discovered = patterns
            self._feedback_total = feedback_total
            self._feedback_accepted = feedback_accepted
            self._learning_velocity = velocity
    
    def get_card_config(self) -> LovelaceCardConfig:
        """Card Konfiguration."""
        with self._lock:
            acceptance_rate = self._feedback_accepted / max(self._feedback_total, 1)
            
            return LovelaceCardConfig(
                card_type="custom:learning-progress-card",
                title="Learning Progress",
                config={
                    "patterns_discovered": self._patterns_discovered,
                    "feedback_acceptance_rate": round(acceptance_rate * 100, 1),
                    "learning_velocity": round(self._learning_velocity, 3),
                    "show_history_chart": True,
                    "show_milestone": True,
                    "next_milestone": self._get_next_milestone(),
                },
            )
    
    def _get_next_milestone(self) -> str:
        """Nächstes Milestone."""
        with self._lock:
            if self._patterns_discovered < 10:
                return "10 Patterns entdecken"
            elif self._patterns_discovered < 50:
                return "50 Patterns entdecken"
            elif self._patterns_discovered < 100:
                return "100 Patterns entdecken"
            else:
                return "Expert Level erreichen"


# =============================================================================
# UPDATE STATUS CARD
# =============================================================================

class UpdateStatusCard:
    """Update Status Card mit One-Click Update."""
    
    def __init__(self, hass):
        self._hass = hass
        self._updates_available = 0
        self._components: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def check_updates(self, updates: Dict[str, Dict[str, Any]]) -> None:
        """Updates prüfen."""
        with self._lock:
            self._components = updates
            self._updates_available = sum(
                1 for u in updates.values() if u.get("is_available", False)
            )
    
    def trigger_update(self, component: str) -> Dict[str, Any]:
        """Update auslösen."""
        # In production: Call service
        return {
            "success": True,
            "component": component,
            "message": f"Update für {component} gestartet",
        }
    
    def get_card_config(self) -> LovelaceCardConfig:
        """Card Konfiguration."""
        with self._lock:
            return LovelaceCardConfig(
                card_type="custom:update-status-card",
                title="System Updates",
                config={
                    "updates_available": self._updates_available,
                    "components": [
                        {
                            "name": name,
                            "current": data.get("current_version", "unknown"),
                            "available": data.get("available_version", ""),
                            "is_available": data.get("is_available", False),
                            "is_critical": data.get("is_critical", False),
                        }
                        for name, data in self._components.items()
                    ],
                    "show_update_button": True,
                    "auto_check_interval_hours": 24,
                },
            )


# =============================================================================
# MODULAR DASHBOARD HA (Main Class)
# =============================================================================

class ModularDashboardHA:
    """HA Dashboard Manager."""
    
    def __init__(self, hass):
        self._hass = hass
        self._intelligence_card = IntelligenceScoreCard(hass)
        self._zone_heatmap = ZoneActivityHeatmap(hass)
        self._mood_card = MoodContextCard(hass)
        self._suggestions_card = SuggestionsCard(hass)
        self._network_card = NetworkHealthCard(hass)
        self._learning_card = LearningProgressCard(hass)
        self._update_card = UpdateStatusCard(hass)
        self._lock = threading.Lock()
    
    def intelligence(self) -> IntelligenceScoreCard:
        return self._intelligence_card
    
    def zone_heatmap(self) -> ZoneActivityHeatmap:
        return self._zone_heatmap
    
    def mood(self) -> MoodContextCard:
        return self._mood_card
    
    def suggestions(self) -> SuggestionsCard:
        return self._suggestions_card
    
    def network(self) -> NetworkHealthCard:
        return self._network_card
    
    def learning(self) -> LearningProgressCard:
        return self._learning_card
    
    def updates(self) -> UpdateStatusCard:
        return self._update_card
    
    def get_full_dashboard_config(self) -> Dict[str, Any]:
        """Vollständige Dashboard Konfiguration."""
        return {
            "title": "PilotSuite Dashboard",
            "views": [
                {
                    "title": "Overview",
                    "cards": [
                        self._intelligence_card.get_card_config().to_dict() if hasattr(self._intelligence_card.get_card_config(), 'to_dict') else asdict(self._intelligence_card.get_card_config()),
                        self._zone_heatmap.get_card_config().to_dict() if hasattr(self._zone_heatmap.get_card_config(), 'to_dict') else asdict(self._zone_heatmap.get_card_config()),
                        self._mood_card.get_card_config().to_dict() if hasattr(self._mood_card.get_card_config(), 'to_dict') else asdict(self._mood_card.get_card_config()),
                    ],
                },
                {
                    "title": "Suggestions",
                    "cards": [
                        self._suggestions_card.get_card_config().to_dict() if hasattr(self._suggestions_card.get_card_config(), 'to_dict') else asdict(self._suggestions_card.get_card_config()),
                    ],
                },
                {
                    "title": "Network",
                    "cards": [
                        self._network_card.get_card_config().to_dict() if hasattr(self._network_card.get_card_config(), 'to_dict') else asdict(self._network_card.get_card_config()),
                    ],
                },
                {
                    "title": "Learning",
                    "cards": [
                        self._learning_card.get_card_config().to_dict() if hasattr(self._learning_card.get_card_config(), 'to_dict') else asdict(self._learning_card.get_card_config()),
                        self._update_card.get_card_config().to_dict() if hasattr(self._update_card.get_card_config(), 'to_dict') else asdict(self._update_card.get_card_config()),
                    ],
                },
            ],
        }
    
    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "cards": 7,
            "views": 4,
            "intelligence_score": self._intelligence_card._score,
            "zones_tracked": len(self._zone_heatmap._zone_data),
            "suggestions_pending": len([s for s in self._suggestions_card._suggestions if s.get("status") == "pending"]),
            "networks_monitored": len(self._network_card._networks),
            "updates_available": self._update_card._updates_available,
        }


# =============================================================================
# Helper functions
# =============================================================================

def asdict(obj) -> Dict[str, Any]:
    """Simple asdict implementation."""
    if hasattr(obj, '__dict__'):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
    return {}


# =============================================================================
# Singleton
# =============================================================================

_ha_dashboard_instance: Optional[ModularDashboardHA] = None


def get_modular_dashboard_ha(hass) -> ModularDashboardHA:
    """Singleton-Zugriff auf ModularDashboardHA."""
    global _ha_dashboard_instance
    
    if _ha_dashboard_instance is None:
        _ha_dashboard_instance = ModularDashboardHA(hass)
    
    return _ha_dashboard_instance
