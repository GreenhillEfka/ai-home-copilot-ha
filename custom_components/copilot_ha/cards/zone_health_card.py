"""Zone Health Dashboard Card — Visual health metrics display (PS-139).

Renders per-zone health cards with:
- Health score gauge (0-100)
- Temperature status with comfort indicator
- Humidity status with comfort indicator
- CO2 / Air quality badge
- Light status
- Overall health trend

Integrates with Home Assistant Lovelace dashboard.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from homeassistant.core import HomeAssistant

from .zone_health import ZoneHealthMetrics, TEMP_COMFORT_MIN, TEMP_COMFORT_MAX, HUMIDITY_COMFORT_MIN, HUMIDITY_COMFORT_MAX

_LOGGER = logging.getLogger(__name__)


@dataclass
class HealthCardConfig:
    """Configuration for a zone health card."""
    zone_id: str
    zone_name: str
    show_temperature: bool = True
    show_humidity: bool = True
    show_co2: bool = True
    show_light: bool = True
    show_score_gauge: bool = True
    color_scheme: str = "default"  # default, minimal, detailed
    refresh_interval_seconds: int = 60


@dataclass
class HealthCardState:
    """Current state of a health card."""
    zone_id: str
    zone_name: str
    health_score: float
    score_category: str  # excellent, good, fair, poor
    temperature_status: str  # normal, cold, hot
    humidity_status: str  # normal, dry, humid
    air_quality: str  # good, moderate, poor, unknown
    light_status: str  # normal, dim, bright
    last_updated: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))
    trend: str = "stable"  # improving, stable, declining


# Score categories
def _get_score_category(score: float) -> str:
    if score >= 90:
        return "excellent"
    if score >= 75:
        return "good"
    if score >= 50:
        return "fair"
    return "poor"


# Temperature status
def _get_temp_status(temp: float | None) -> str:
    if temp is None:
        return "unknown"
    if temp < TEMP_COMFORT_MIN:
        return "cold"
    if temp > TEMP_COMFORT_MAX:
        return "hot"
    return "normal"


# Humidity status
def _get_humidity_status(humid: float | None) -> str:
    if humid is None:
        return "unknown"
    if humid < HUMIDITY_COMFORT_MIN:
        return "dry"
    if humid > HUMIDITY_COMFORT_MAX:
        return "humid"
    return "normal"


# Light status (simplified thresholds)
def _get_light_status(lux: float | None) -> str:
    if lux is None:
        return "unknown"
    if lux < 100:
        return "dim"
    if lux > 1000:
        return "bright"
    return "normal"


def create_health_card_state(metrics: ZoneHealthMetrics) -> HealthCardState:
    """Convert health metrics to card state."""
    return HealthCardState(
        zone_id=metrics.zone_id,
        zone_name=metrics.zone_name,
        health_score=metrics.health_score,
        score_category=_get_score_category(metrics.health_score),
        temperature_status=_get_temp_status(metrics.temperature),
        humidity_status=_get_humidity_status(metrics.humidity),
        air_quality=metrics.air_quality,
        light_status=_get_light_status(metrics.lux),
        last_updated=metrics.last_updated,
        trend="stable",  # Would need historical data for real trend
    )


def render_health_card_html(state: HealthCardState, config: HealthCardConfig) -> str:
    """Render health card as HTML for Lovelace dashboard."""
    # Color mapping
    score_colors = {
        "excellent": "#4caf50",  # green
        "good": "#8bc34a",  # light green
        "fair": "#ff9800",  # orange
        "poor": "#f44336",  # red
    }
    
    status_icons = {
        "temperature": {
            "normal": "🌡️",
            "cold": "❄️",
            "hot": "🔥",
            "unknown": "❓",
        },
        "humidity": {
            "normal": "💧",
            "dry": "🏜️",
            "humid": "🌊",
            "unknown": "❓",
        },
        "air_quality": {
            "good": "✅",
            "moderate": "⚠️",
            "poor": "❌",
            "unknown": "❓",
        },
    }
    
    html = f"""
<div class="zone-health-card" data-zone="{state.zone_id}" style="
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 16px;
    margin: 8px;
    background: white;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
">
    <div class="card-header" style="
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    ">
        <h3 style="margin: 0; color: #333;">{state.zone_name}</h3>
        <div class="health-score" style="
            background: {score_colors.get(state.score_category, '#999')};
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-weight: bold;
        ">
            {state.health_score:.0f}
        </div>
    </div>
    
    <div class="metrics-grid" style="
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 8px;
    ">
"""
    
    # Temperature
    if config.show_temperature:
        temp_icon = status_icons["temperature"].get(state.temperature_status, "❓")
        temp_value = f"{state.temperature_status}"
        html += f"""
        <div class="metric temperature" style="
            padding: 8px;
            background: #f5f5f5;
            border-radius: 4px;
            text-align: center;
        ">
            <div class="metric-icon">{temp_icon}</div>
            <div class="metric-value">{temp_value}</div>
            <div class="metric-label">Temp</div>
        </div>
"""
    
    # Humidity
    if config.show_humidity:
        humid_icon = status_icons["humidity"].get(state.humidity_status, "❓")
        humid_value = f"{state.humidity_status}"
        html += f"""
        <div class="metric humidity" style="
            padding: 8px;
            background: #f5f5f5;
            border-radius: 4px;
            text-align: center;
        ">
            <div class="metric-icon">{humid_icon}</div>
            <div class="metric-value">{humid_value}</div>
            <div class="metric-label">Humidity</div>
        </div>
"""
    
    # Air Quality
    if config.show_co2:
        aq_icon = status_icons["air_quality"].get(state.air_quality, "❓")
        aq_value = f"{state.air_quality}"
        html += f"""
        <div class="metric air-quality" style="
            padding: 8px;
            background: #f5f5f5;
            border-radius: 4px;
            text-align: center;
        ">
            <div class="metric-icon">{aq_icon}</div>
            <div class="metric-value">{aq_value}</div>
            <div class="metric-label">Air Quality</div>
        </div>
"""
    
    # Light
    if config.show_light:
        light_icon = "💡" if state.light_status != "unknown" else "❓"
        light_value = f"{state.light_status}"
        html += f"""
        <div class="metric light" style="
            padding: 8px;
            background: #f5f5f5;
            border-radius: 4px;
            text-align: center;
        ">
            <div class="metric-icon">{light_icon}</div>
            <div class="metric-value">{light_value}</div>
            <div class="metric-label">Light</div>
        </div>
"""
    
    html += """
    </div>
    
    <div class="card-footer" style="
        margin-top: 12px;
        padding-top: 8px;
        border-top: 1px solid #eee;
        font-size: 12px;
        color: #666;
        text-align: right;
    ">
        Updated: """ + state.last_updated.strftime("%H:%M") + """
    </div>
</div>
"""
    
    return html


def render_health_card_markdown(state: HealthCardState, config: HealthCardConfig) -> str:
    """Render health card as markdown for Telegram/Discord."""
    score_emoji = {
        "excellent": "✨",
        "good": "✅",
        "fair": "⚠️",
        "poor": "❌",
    }
    
    temp_emoji = {
        "normal": "🌡️",
        "cold": "❄️",
        "hot": "🔥",
        "unknown": "❓",
    }
    
    humid_emoji = {
        "normal": "💧",
        "dry": "🏜️",
        "humid": "🌊",
        "unknown": "❓",
    }
    
    aq_emoji = {
        "good": "✅",
        "moderate": "⚠️",
        "poor": "❌",
        "unknown": "❓",
    }
    
    md = f"""**{state.zone_name}** {score_emoji.get(state.score_category, "❓")} *Health: {state.health_score:.0f}*

"""
    
    if config.show_temperature:
        temp_icon = temp_emoji.get(state.temperature_status, "❓")
        md += f"{temp_icon} Temp: {state.temperature_status}\n"
    
    if config.show_humidity:
        humid_icon = humid_emoji.get(state.humidity_status, "❓")
        md += f"{humid_icon} Humidity: {state.humidity_status}\n"
    
    if config.show_co2:
        aq_icon = aq_emoji.get(state.air_quality, "❓")
        md += f"{aq_icon} Air: {state.air_quality}\n"
    
    if config.show_light:
        light_icon = "💡" if state.light_status != "unknown" else "❓"
        md += f"{light_icon} Light: {state.light_status}\n"
    
    md += f"\n_Updated: {state.last_updated.strftime('%H:%M')}_"
    
    return md


async def async_render_all_zone_health_cards(
    hass: HomeAssistant,
    health_map: dict[str, ZoneHealthMetrics],
    output_format: str = "html",
) -> dict[str, str]:
    """Render health cards for all zones."""
    cards: dict[str, str] = {}
    
    for zone_id, metrics in health_map.items():
        state = create_health_card_state(metrics)
        config = HealthCardConfig(
            zone_id=zone_id,
            zone_name=metrics.zone_name,
        )
        
        if output_format == "html":
            cards[zone_id] = render_health_card_html(state, config)
        elif output_format == "markdown":
            cards[zone_id] = render_health_card_markdown(state, config)
        else:
            cards[zone_id] = render_health_card_html(state, config)
    
    return cards
