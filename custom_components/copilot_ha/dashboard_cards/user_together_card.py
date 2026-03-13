"""
User Together Card
==================

Generates a Lovelace UI card for multi-user zone clustering visualization.
Shows:
- Users in same zone ("zusammen sein" pattern)
- Time together tracking
- Zone clustering summary

Design: User clustering visualization withTogether indicators
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.core import HomeAssistant

from .zone_detector import ZoneDetector

_LOGGER = logging.getLogger(__name__)


@dataclass
class UserTogetherData:
    """User together data."""
    together_groups: list[list[str]]  # list of user_ids in same zone
    total_users: int
    users_home: int
    together_count: int  # number of users in groups of 2+
    most_common_zone: str | None = None
    together_since: float | None = None  # timestamp when current togetherness started
    total_together_minutes_today: float = 0.0  # accumulated minutes together today


def create_user_together_card(
    hass: HomeAssistant,
    together_data: UserTogetherData,
    zone_detector: ZoneDetector | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Create a User Together Card YAML configuration.
    
    Args:
        hass: Home Assistant instance
        together_data: User together data
        zone_detector: Optional ZoneDetector instance
        config: Optional configuration overrides
        
    Returns:
        Lovelace card configuration dict
    """
    card_config = {
        "type": "vertical-stack",
        "cards": [
            _create_together_header_card(together_data),
            _create_together_groups_card(together_data),
            _create_together_time_card(together_data),
        ],
    }
    
    # Apply custom configuration if provided
    if config:
        card_config.update(config)
        
    return card_config


def _create_together_header_card(together_data: UserTogetherData) -> dict[str, str]:
    """Create together header card."""
    together_count = together_data.together_count
    
    return {
        "type": "horizontal-stack",
        "cards": [
            {
                "type": "custom:hui-card",
                "title": f"👥 Zusammen sein ({together_count})",
                "icon": "mdi:account-group",
            },
        ],
    }


def _create_together_groups_card(together_data: UserTogetherData) -> dict[str, Any]:
    """Create together groups card."""
    groups_cards = []
    
    for i, group in enumerate(together_data.together_groups):
        if len(group) >= 2:
            users_text = ", ".join([uid.split(".", 1)[-1] for uid in group])
            groups_cards.append({
                "type": "custom:hui-entity-card",
                "entity": f"group.together_{i}",
                "name": f"👥 {len(group)} Personen",
                "icon": "mdi:account-multiple",
            })
            
    if not groups_cards:
        groups_cards.append({
            "type": "markdown",
            "content": "Keine Personen in derselben Zone",
        })
        
    return {
        "type": "custom:hui-card",
        "title": "Gruppen",
        "icon": "mdi:account-multiple-search",
        "cards": groups_cards,
    }


def _create_together_time_card(together_data: UserTogetherData) -> dict[str, Any]:
    """Create together time card with real duration tracking."""
    import time as _time

    time_items = []

    # Persons at home
    time_items.append({
        "type": "custom:hui-stat-card",
        "name": "Zeit zu Hause",
        "value": f"{together_data.users_home}/{together_data.total_users}",
        "unit": "Personen",
        "icon": "mdi:home-clock",
    })

    # Current together duration (live, based on together_since timestamp)
    if together_data.together_count >= 2 and together_data.together_since:
        elapsed_minutes = (_time.time() - together_data.together_since) / 60.0
        if elapsed_minutes >= 60:
            duration_text = f"{elapsed_minutes / 60:.1f} h"
        else:
            duration_text = f"{int(elapsed_minutes)} min"
        time_items.append({
            "type": "custom:hui-stat-card",
            "name": "Gemeinsam seit",
            "value": duration_text,
            "unit": "",
            "icon": "mdi:timer-outline",
        })

    # Accumulated today
    if together_data.total_together_minutes_today > 0:
        total_min = together_data.total_together_minutes_today
        if total_min >= 60:
            total_text = f"{total_min / 60:.1f} h"
        else:
            total_text = f"{int(total_min)} min"
        time_items.append({
            "type": "custom:hui-stat-card",
            "name": "Gemeinsam heute",
            "value": total_text,
            "unit": "",
            "icon": "mdi:calendar-clock",
        })

    # Together count stat
    if together_data.together_count >= 2:
        time_items.append({
            "type": "custom:hui-stat-card",
            "name": "Gemeinsam",
            "value": together_data.together_count,
            "unit": "Personen",
            "icon": "mdi:handshake",
        })
    else:
        time_items.append({
            "type": "custom:hui-stat-card",
            "name": "Gemeinsam",
            "value": "keine",
            "unit": "Gruppen",
            "icon": "mdi:account-off",
        })
        
    return {
        "type": "custom:hui-card",
        "title": "Statistiken",
        "icon": "mdi:chart-line",
        "cards": time_items,
    }


def get_user_together_card_yaml(together_data: UserTogetherData) -> str:
    """
    Get user together card as YAML string.
    
    Args:
        together_data: User together data
        
    Returns:
        YAML string for Lovelace configuration
    """
    card_dict = create_user_together_card(None, together_data)
    return _dict_to_yaml(card_dict)


def _dict_to_yaml(data: dict[str, Any], indent: int = 0) -> str:
    """Convert dict to YAML string (simple implementation)."""
    indent_str = "  " * indent
    lines = []
    
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{indent_str}- {key}:")
                lines.append(_dict_to_yaml(value, indent + 1))
            elif isinstance(value, list):
                lines.append(f"{indent_str}- {key}:")
                for item in value:
                    if isinstance(item, dict):
                        lines.append(_dict_to_yaml(item, indent + 1))
                    else:
                        lines.append(f"{indent_str}  - {item}")
            else:
                lines.append(f"{indent_str}- {key}: {value}")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                lines.append(_dict_to_yaml(item, indent))
            else:
                lines.append(f"{indent_str}- {item}")
    else:
        lines.append(f"{indent_str}{data}")
        
    return "\n".join(lines)
