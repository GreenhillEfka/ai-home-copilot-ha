"""Overview cards for PilotSuite dashboards.

Cards:
- Dashboard Overview Card (main entry point)
- Neuron Status Card
- Mood Overview Card
- Zone Overview Card
- System Health Card
"""
from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..data_classes import DashboardData, NeuronStatus


def create_dashboard_overview_card(
    data: DashboardData,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create the main dashboard overview card stack."""
    config = config or {}

    return {
        "type": "vertical-stack",
        "title": config.get("title", "🏠 PilotSuite Dashboard"),
        "cards": [
            _create_neuron_status_card(data),
            _create_mood_overview_card(data),
            _create_zone_overview_card(data),
            _create_system_health_card(data),
        ],
        "card_mod": {
            "style": {
                "margin": "8px",
                "padding": "12px",
            }
        },
    }


def _group_neurons_by_status(neurons: list[NeuronStatus]) -> dict[str, list[NeuronStatus]]:
    groups: dict[str, list[NeuronStatus]] = {
        "active": [],
        "inactive": [],
        "warning": [],
        "error": [],
    }
    for neuron in neurons:
        groups.setdefault(neuron.status, []).append(neuron)
    return groups


def _create_neuron_status_card(data: DashboardData) -> dict[str, Any]:
    """Create neuron status overview card using standard Lovelace cards."""
    status_labels = {
        "active": "Aktiv",
        "inactive": "Inaktiv",
        "warning": "Warnung",
        "error": "Fehler",
    }
    status_icons = {
        "active": "mdi:check-circle",
        "inactive": "mdi:circle-outline",
        "warning": "mdi:alert-circle",
        "error": "mdi:close-circle",
    }

    cards: list[dict[str, Any]] = []
    for status, neurons in _group_neurons_by_status(data.neurons).items():
        if not neurons:
            continue
        cards.append(
            {
                "type": "markdown",
                "content": f"**{status_icons.get(status, 'mdi:brain')} {status_labels.get(status, status.title())}: {len(neurons)}**",
            }
        )
        cards.append(
            {
                "type": "grid",
                "columns": 2,
                "square": False,
                "cards": [
                    {
                        "type": "button",
                        "entity": neuron.entity_id,
                        "name": neuron.name,
                        "icon": neuron.icon,
                        "show_state": True,
                        "tap_action": {"action": "more-info"},
                        "hold_action": {
                            "action": "navigate",
                            "navigation_path": f"/dashboard-styx/neuron/{neuron.entity_id}",
                        },
                    }
                    for neuron in neurons[:6]
                ],
            }
        )

    if not cards:
        cards = [{"type": "markdown", "content": "**Keine Neuronen aktiv**"}]

    return {
        "type": "vertical-stack",
        "title": "🧠 Neuronen Status",
        "cards": cards,
    }


def _create_mood_overview_card(data: DashboardData) -> dict[str, Any]:
    """Create mood overview card with PilotSuite naming."""
    mood = data.mood or {}
    mood_name = mood.get("name_de") or mood.get("name") or "Unbekannt"
    confidence = mood.get("confidence")
    factors = mood.get("factors") or mood.get("emotions") or []

    summary_lines = [f"**Aktuelle Stimmung:** {mood_name}"]
    if confidence is not None:
        summary_lines.append(f"**Confidence:** {confidence:.0%}")
    if isinstance(factors, list) and factors:
        summary_lines.append(f"**Faktoren:** {', '.join(map(str, factors[:3]))}")

    return {
        "type": "vertical-stack",
        "title": "🎭 Stimmungsübersicht",
        "cards": [
            {
                "type": "entity",
                "entity": "sensor.pilotsuite_mood",
                "name": "PilotSuite Stimmung",
                "icon": mood.get("icon", "mdi:emoticon-outline"),
            },
            {
                "type": "markdown",
                "content": "\n".join(summary_lines),
            },
        ],
    }


def _create_zone_overview_card(data: DashboardData) -> dict[str, Any]:
    """Create zone overview card based on presence data."""
    rows: list[dict[str, Any]] = []

    for user_id, user_data in data.presence.users.items():
        zone_name = user_data.get("zone", "Unbekannt")
        status = user_data.get("status", "unknown")
        status_icon = {
            "home": "mdi:home",
            "away": "mdi:home-export-outline",
            "sleep": "mdi:sleep",
        }.get(status, "mdi:account")

        rows.append(
            {
                "entity": user_id,
                "name": f"{user_data.get('name', user_id)} · {zone_name}",
                "icon": status_icon,
            }
        )

    if not rows:
        rows = [{"type": "section", "label": "Keine Benutzer erkannt"}]

    return {
        "type": "vertical-stack",
        "title": "🏠 Zonenübersicht",
        "cards": [
            {
                "type": "markdown",
                "content": (
                    f"**Anwesend:** {data.presence.total_presence}  \n"
                    f"**Gäste:** {data.presence.guest_count}"
                ),
            },
            {
                "type": "entities",
                "entities": rows[:6],
            },
        ],
    }


def _create_system_health_card(data: DashboardData) -> dict[str, Any]:
    """Create system health card without non-standard Lovelace types."""
    health = data.system_health

    status_label = "Stabil"
    if health.health_score < 50:
        status_label = "Kritisch"
    elif health.health_score < 80:
        status_label = "Beobachten"

    alert_lines = []
    for alert in health.alerts[:5]:
        title = alert.get("title") or alert.get("message") or str(alert)
        alert_lines.append(f"- {title}")

    content = [
        f"**Health Score:** {health.health_score}/100 ({status_label})",
        f"**Neuronen aktiv:** {health.active_neurons}/{health.total_neurons}",
    ]
    if alert_lines:
        content.append("**Alerts:**")
        content.extend(alert_lines)

    return {
        "type": "vertical-stack",
        "title": "💚 System Status",
        "cards": [
            {
                "type": "entity",
                "entity": "sensor.pilotsuite_home_health_score",
                "name": "PilotSuite Home Health",
                "icon": "mdi:heart-pulse",
            },
            {
                "type": "markdown",
                "content": "\n".join(content),
            },
        ],
    }


__all__ = [
    "create_dashboard_overview_card",
    "_create_neuron_status_card",
    "_create_mood_overview_card",
    "_create_zone_overview_card",
    "_create_system_health_card",
]
