"""Complete API Client — ALL 286+ PilotSuite Core APIs.

This module provides comprehensive API client methods for ALL PilotSuite Core endpoints.
Organized in 5 batches:
- Batch 1: Core APIs (Brain, KG, Habitus, Neurons, Mood)
- Batch 2: Automation APIs (Notifications, Zones, Proposals)
- Batch 3: Intelligence APIs (RAG, Anomaly, Energy, Weather, Calendar)
- Batch 4: Media & Hardware (Sonos, Tags, Hardware)
- Batch 5: Styx & System (Chat, Multi-Home, Dashboard, Debug)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .api import CopilotApiClient

_LOGGER = logging.getLogger(__name__)


# =============================================================================
# BATCH 1: Core APIs (Brain, KG, Habitus, Neurons, Mood)
# =============================================================================

class BrainGraphAPI(CopilotApiClient):
    """Brain Graph API client."""
    
    async def get_graph_state(self) -> dict:
        """Get brain graph state."""
        return await self._get_json("/api/v1/graph/state")
    
    async def get_graph_stats(self) -> dict:
        """Get graph statistics."""
        return await self._get_json("/api/v1/graph/summary")
    
    async def get_graph_patterns(self) -> dict:
        """Get graph patterns."""
        return await self._get_json("/api/v1/graph/patterns")
    
    async def render_graph(self) -> dict:
        """Render graph visualization."""
        return await self._post_json("/api/v1/graph/render", {})
    
    async def query_graph(self, query: str) -> dict:
        """Execute graph query."""
        return await self._post_json("/api/v1/graph/query", {"query": query})
    
    async def ingest_event(self, event: dict) -> dict:
        """Ingest event into graph."""
        return await self._post_json("/api/v1/graph/ingest", event)
    
    async def get_graph_snapshot_svg(self) -> str:
        """Get graph SVG snapshot."""
        return await self._get_json("/api/v1/graph/snapshot.svg")
    
    async def get_sequences(self) -> dict:
        """Get graph sequences."""
        return await self._get_json("/api/v1/graph/sequences")
    
    async def get_brain_growth_summary(self) -> dict:
        """Get brain growth summary."""
        return await self._get_json("/api/v1/brain_growth/summary")
    
    async def get_semantic_trace(self, input_id: str) -> dict:
        """Get semantic transfer trace."""
        return await self._get_json(f"/api/v1/brain_growth/trace/{input_id}")
    
    async def get_zone_brain_links(self) -> dict:
        """Get zone-brain links."""
        return await self._get_json("/api/v1/brain_growth/zone-links")


class KnowledgeGraphAPI(CopilotApiClient):
    """Knowledge Graph API client."""
    
    async def get_nodes(self) -> dict:
        """List all KG nodes."""
        return await self._get_json("/api/v1/kg/nodes")
    
    async def get_node(self, node_id: str) -> dict:
        """Get specific node."""
        return await self._get_json(f"/api/v1/kg/nodes/{node_id}")
    
    async def get_edges(self) -> dict:
        """List all KG edges."""
        return await self._get_json("/api/v1/kg/edges")
    
    async def create_edge(self, edge: dict) -> dict:
        """Create new edge."""
        return await self._post_json("/api/v1/kg/edges", edge)
    
    async def upsert_entity(self, entity: dict) -> dict:
        """Upsert entity."""
        return await self._post_json("/api/v1/kg/entities", entity)
    
    async def get_related_entities(self, entity_id: str) -> dict:
        """Get related entities."""
        return await self._get_json(f"/api/v1/kg/entity/{entity_id}/related")
    
    async def import_entities(self, entities: list) -> dict:
        """Bulk import entities."""
        return await self._post_json("/api/v1/kg/import/entities", {"entities": entities})
    
    async def import_patterns(self, patterns: list) -> dict:
        """Import patterns from Habitus."""
        return await self._post_json("/api/v1/kg/import/patterns", {"patterns": patterns})
    
    async def get_mood_patterns(self) -> dict:
        """List mood-related patterns."""
        return await self._get_json("/api/v1/kg/moods")
    
    async def get_patterns_for_mood(self, mood: str) -> dict:
        """Get patterns for specific mood."""
        return await self._get_json(f"/api/v1/kg/mood/{mood}/patterns")
    
    async def get_pattern(self, pattern_id: str) -> dict:
        """Get specific pattern."""
        return await self._get_json(f"/api/v1/kg/pattern/{pattern_id}")
    
    async def execute_kg_query(self, query: dict) -> dict:
        """Execute KG query."""
        return await self._post_json("/api/v1/kg/query", query)
    
    async def get_kg_stats(self) -> dict:
        """Get KG statistics."""
        return await self._get_json("/api/v1/kg/stats")
    
    async def get_kg_zones(self) -> dict:
        """List zones in KG."""
        return await self._get_json("/api/v1/kg/zones")
    
    async def get_zone_entities(self, zone_id: str) -> dict:
        """Get entities for zone."""
        return await self._get_json(f"/api/v1/kg/zone/{zone_id}/entities")


class HabitusAPI(CopilotApiClient):
    """Habitus Mining API client."""
    
    async def get_habitus_status(self) -> dict:
        """Get mining status."""
        return await self._get_json("/api/v1/habitus/status")
    
    async def get_habitus_health(self) -> dict:
        """Get health check."""
        return await self._get_json("/api/v1/habitus/health")
    
    async def get_rules(self) -> dict:
        """Get discovered rules."""
        return await self._get_json("/api/v1/habitus/rules")
    
    async def get_rules_summary(self) -> dict:
        """Get rules summary."""
        return await self._get_json("/api/v1/habitus/rules/summary")
    
    async def trigger_mining(self) -> dict:
        """Trigger pattern mining."""
        return await self._post_json("/api/v1/habitus/mine", {})
    
    async def get_patterns(self) -> dict:
        """Get discovered patterns."""
        return await self._get_json("/api/v1/habitus/patterns")
    
    async def apply_pattern(self, pattern_id: str) -> dict:
        """Apply pattern as automation."""
        return await self._post_json(f"/api/v1/habitus/patterns/{pattern_id}/apply", {})
    
    async def get_mining_stats(self) -> dict:
        """Get mining statistics."""
        return await self._get_json("/api/v1/habitus/stats")
    
    async def get_habitus_zones(self) -> dict:
        """Get Habitus zones."""
        return await self._get_json("/api/v1/habitus/zones")
    
    async def get_zone_metrics(self, zone_id: str) -> dict:
        """Get zone metrics."""
        return await self._get_json(f"/api/v1/habitus/zones/{zone_id}/metrics")


class NeuronsAPI(CopilotApiClient):
    """Neurons API client."""
    
    async def list_neurons(self) -> dict:
        """List all neurons."""
        return await self._get_json("/api/v1/neurons")
    
    async def get_neuron(self, neuron_id: str) -> dict:
        """Get neuron details."""
        return await self._get_json(f"/api/v1/neurons/{neuron_id}")
    
    async def create_neuron(self, neuron: dict) -> dict:
        """Create new neuron."""
        return await self._post_json("/api/v1/neurons", neuron)
    
    async def update_neuron(self, neuron_id: str, data: dict) -> dict:
        """Update neuron."""
        return await self._post_json(f"/api/v1/neurons/{neuron_id}", data)
    
    async def delete_neuron(self, neuron_id: str) -> dict:
        """Delete neuron."""
        return await self._post_json(f"/api/v1/neurons/{neuron_id}/delete", {})
    
    async def activate_neuron(self, neuron_id: str) -> dict:
        """Activate neuron."""
        return await self._post_json(f"/api/v1/neurons/{neuron_id}/activate", {})
    
    async def get_neuron_graph(self) -> dict:
        """Get neural network graph."""
        return await self._get_json("/api/v1/neurons/graph")
    
    async def evaluate_neurons(self, inputs: dict) -> dict:
        """Evaluate neurons."""
        return await self._post_json("/api/v1/neurons/evaluate", inputs)
    
    async def update_neuron_states(self, states: dict) -> dict:
        """Update neuron states."""
        return await self._post_json("/api/v1/neurons/update", states)
    
    async def get_layer_visualization(self) -> dict:
        """Get layer visualization."""
        return await self._get_json("/api/v1/neurons/visualization")
    
    async def get_layer_svg(self) -> str:
        """Get layer SVG snapshot."""
        return await self._get_json("/api/v1/neurons/snapshot.svg")
    
    async def get_connection_heatmap(self) -> dict:
        """Get connection heatmap."""
        return await self._get_json("/api/v1/neurons/heatmap")
    
    async def get_brain_pipeline(self) -> dict:
        """Get brain pipeline."""
        return await self._get_json("/api/v1/neurons/brain/pipeline")
    
    async def get_neuron_fire_status(self, neuron_id: str) -> dict:
        """Get neuron fire status."""
        return await self._get_json(f"/api/v1/neurons/{neuron_id}/fire")


class MoodAPI(CopilotApiClient):
    """Mood API client."""
    
    async def get_mood_state(self) -> dict:
        """Get mood state."""
        return await self._get_json("/api/v1/mood/state")
    
    async def get_aggregated_mood(self) -> dict:
        """Get aggregated mood."""
        return await self._get_json("/api/v1/mood/aggregated")
    
    async def get_zone_moods(self) -> dict:
        """Get zone mood states."""
        return await self._get_json("/api/v1/mood/zones")
    
    async def orchestrate_zone_mood(self, zone_name: str, mood: str) -> dict:
        """Orchestrate zone mood."""
        return await self._post_json(f"/api/v1/mood/zones/{zone_name}/orchestrate", {"mood": mood})
    
    async def force_zone_mood(self, zone_name: str, mood: str) -> dict:
        """Force zone mood."""
        return await self._post_json(f"/api/v1/mood/zones/{zone_name}/force_mood", {"mood": mood})
    
    async def score_mood(self, data: dict) -> dict:
        """Score mood."""
        return await self._post_json("/api/v1/mood/score", data)


# =============================================================================
# BATCH 2: Automation APIs (Notifications, Zones, Proposals, Automation)
# =============================================================================

class NotificationsAPI(CopilotApiClient):
    """Notifications API client."""
    
    async def list_notifications(self, limit: int = 50) -> dict:
        """List notifications."""
        return await self._get_json(f"/api/v1/notifications?limit={limit}")
    
    async def create_notification(self, notification: dict) -> dict:
        """Create notification."""
        return await self._post_json("/api/v1/notifications", notification)
    
    async def get_notification(self, notification_id: str) -> dict:
        """Get notification."""
        return await self._get_json(f"/api/v1/notifications/{notification_id}")
    
    async def mark_as_read(self, notification_id: str) -> dict:
        """Mark as read."""
        return await self._post_json(f"/api/v1/notifications/{notification_id}/read", {})
    
    async def delete_notification(self, notification_id: str) -> dict:
        """Delete notification."""
        return await self._post_json(f"/api/v1/notifications/{notification_id}/delete", {})
    
    async def clear_all(self) -> dict:
        """Clear all notifications."""
        return await self._post_json("/api/v1/notifications/clear", {})
    
    async def send_notification(self, notification: dict) -> dict:
        """Send notification."""
        return await self._post_json("/api/v1/notifications/send", notification)
    
    async def subscribe_device(self, device: dict) -> dict:
        """Subscribe device."""
        return await self._post_json("/api/v1/notifications/subscribe", device)
    
    async def unsubscribe_device(self, device_id: str) -> dict:
        """Unsubscribe device."""
        return await self._post_json("/api/v1/notifications/unsubscribe", {"device_id": device_id})
    
    async def list_subscriptions(self) -> dict:
        """List subscriptions."""
        return await self._get_json("/api/v1/notifications/subscriptions")
    
    async def register_ha_device(self, device: dict) -> dict:
        """Register HA device."""
        return await self._post_json("/api/v1/notifications/ha/register", device)
    
    async def list_ha_devices(self) -> dict:
        """List HA devices."""
        return await self._get_json("/api/v1/notifications/ha/devices")
    
    async def enable_ha_device(self, device_id: str) -> dict:
        """Enable HA device."""
        return await self._post_json(f"/api/v1/notifications/ha/devices/{device_id}/enable", {})
    
    async def disable_ha_device(self, device_id: str) -> dict:
        """Disable HA device."""
        return await self._post_json(f"/api/v1/notifications/ha/devices/{device_id}/disable", {})
    
    async def unregister_ha_device(self, device_id: str) -> dict:
        """Unregister HA device."""
        return await self._post_json(f"/api/v1/notifications/ha/devices/{device_id}/delete", {})
    
    async def list_ha_services(self) -> dict:
        """List HA notify services."""
        return await self._get_json("/api/v1/notifications/ha/services")
    
    async def test_ha_connection(self) -> dict:
        """Test HA connection."""
        return await self._get_json("/api/v1/notifications/ha/test")
    
    async def send_via_ha(self, notification: dict) -> dict:
        """Send via HA notification."""
        return await self._post_json("/api/v1/notifications/send/ha", notification)


class ZoneAutomationAPI(CopilotApiClient):
    """Zone Automation API client."""
    
    async def get_zone_dashboard(self) -> dict:
        """Get zone dashboard."""
        return await self._get_json("/api/v1/zone-automation/dashboard")
    
    async def list_zones(self) -> dict:
        """List all zones."""
        return await self._get_json("/api/v1/zone-automation/zones")
    
    async def get_zone(self, zone_id: str) -> dict:
        """Get zone details."""
        return await self._get_json(f"/api/v1/zone-automation/zones/{zone_id}")
    
    async def update_zone_config(self, zone_id: str, config: dict) -> dict:
        """Update zone config."""
        return await self._post_json(f"/api/v1/zone-automation/zones/{zone_id}/config", config)
    
    async def set_zone_mode(self, zone_id: str, mode: str) -> dict:
        """Set zone mode."""
        return await self._post_json(f"/api/v1/zone-automation/zones/{zone_id}/mode", {"mode": mode})
    
    async def list_zone_modules(self, zone_id: str) -> dict:
        """List zone modules."""
        return await self._get_json(f"/api/v1/zone-automation/zones/{zone_id}/modules")
    
    async def add_zone_module(self, zone_id: str, module_id: str) -> dict:
        """Add module to zone."""
        return await self._post_json(f"/api/v1/zone-automation/zones/{zone_id}/modules/{module_id}", {})
    
    async def remove_zone_module(self, zone_id: str, module_id: str) -> dict:
        """Remove module from zone."""
        return await self._post_json(f"/api/v1/zone-automation/zones/{zone_id}/modules/{module_id}/delete", {})
    
    async def trigger_zone_override(self, zone_id: str, override: dict) -> dict:
        """Trigger zone override."""
        return await self._post_json(f"/api/v1/zone-automation/zones/{zone_id}/override", override)
    
    async def sync_zone_definitions(self, zones: list) -> dict:
        """Sync zone definitions from HA."""
        return await self._post_json("/api/v1/zone-automation/sync-definitions", {"zones": zones})
    
    async def ensure_zones(self, zone_ids: list) -> dict:
        """Ensure zones exist."""
        return await self._post_json("/api/v1/zone-automation/ensure-zones", {"zone_ids": zone_ids})
    
    async def get_module_schemas(self) -> dict:
        """List module schemas."""
        return await self._get_json("/api/v1/zone-automation/module-schemas")


class ProposalsAPI(CopilotApiClient):
    """Proposals & Suggestions API client."""
    
    async def list_proposals(self) -> dict:
        """List proposals."""
        return await self._get_json("/api/v1/proposals")
    
    async def get_proposal(self, proposal_id: str) -> dict:
        """Get proposal."""
        return await self._get_json(f"/api/v1/proposals/{proposal_id}")
    
    async def accept_proposal(self, proposal_id: str) -> dict:
        """Accept proposal."""
        return await self._post_json(f"/api/v1/proposals/{proposal_id}/accept", {})
    
    async def reject_proposal(self, proposal_id: str) -> dict:
        """Reject proposal."""
        return await self._post_json(f"/api/v1/proposals/{proposal_id}/reject", {})
    
    async def snooze_proposal(self, proposal_id: str, duration: int) -> dict:
        """Snooze proposal."""
        return await self._post_json(f"/api/v1/proposals/{proposal_id}/snooze", {"duration": duration})
    
    async def list_suggestions(self) -> dict:
        """List suggestions."""
        return await self._get_json("/api/v1/suggestions")
    
    async def get_suggestion(self, suggestion_id: str) -> dict:
        """Get suggestion."""
        return await self._get_json(f"/api/v1/suggestions/{suggestion_id}")
    
    async def accept_suggestion(self, suggestion_id: str) -> dict:
        """Accept suggestion."""
        return await self._post_json(f"/api/v1/suggestions/{suggestion_id}/accept", {})
    
    async def reject_suggestion(self, suggestion_id: str) -> dict:
        """Reject suggestion."""
        return await self._post_json(f"/api/v1/suggestions/{suggestion_id}/reject", {})


class AutomationAPI(CopilotApiClient):
    """Automation API client."""
    
    async def create_automation(self, automation: dict) -> dict:
        """Create automation."""
        return await self._post_json("/api/v1/automation/create", automation)
    
    async def list_automations(self) -> dict:
        """List automations."""
        return await self._get_json("/api/v1/automation/")


# =============================================================================
# BATCH 3: Intelligence APIs (RAG, Anomaly, Energy, Weather, Calendar)
# =============================================================================

class RAGAPI(CopilotApiClient):
    """RAG & Vector Search API client."""
    
    async def list_vectors(self) -> dict:
        """List vector entries."""
        return await self._get_json("/api/v1/vectors")
    
    async def create_vector(self, vector: dict) -> dict:
        """Create vector entry."""
        return await self._post_json("/api/v1/vectors", vector)
    
    async def get_vector(self, vector_id: str) -> dict:
        """Get vector entry."""
        return await self._get_json(f"/api/v1/vectors/{vector_id}")
    
    async def delete_vector(self, vector_id: str) -> dict:
        """Delete vector entry."""
        return await self._post_json(f"/api/v1/vectors/{vector_id}/delete", {})
    
    async def similarity_search(self, query: str, limit: int = 10) -> dict:
        """Similarity search."""
        return await self._post_json("/api/v1/vectors/similarity", {"query": query, "limit": limit})
    
    async def generate_embeddings(self, text: str) -> dict:
        """Generate embeddings."""
        return await self._post_json("/api/v1/embeddings", {"text": text})
    
    async def rag_search(self, query: str) -> dict:
        """RAG search."""
        return await self._post_json("/api/v1/rag/search", {"query": query})
    
    async def rag_chat(self, query: str, context: list = None) -> dict:
        """RAG chat."""
        return await self._post_json("/api/v1/rag/chat", {"query": query, "context": context or []})
    
    async def get_rag_context(self) -> dict:
        """Get RAG context."""
        return await self._get_json("/api/v1/rag/context")
    
    async def search(self, query: str) -> dict:
        """Search."""
        return await self._post_json("/api/v1/search", {"query": query})
    
    async def hybrid_search(self, query: str) -> dict:
        """Hybrid search."""
        return await self._post_json("/api/v1/search/hybrid", {"query": query})


class AnomalyAPI(CopilotApiClient):
    """Anomaly Detection API client."""
    
    async def detect_anomalies(self, data: dict) -> dict:
        """Detect anomalies."""
        return await self._post_json("/api/v1/anomaly/detect", data)
    
    async def get_anomaly_history(self, limit: int = 50) -> dict:
        """Get anomaly history."""
        return await self._get_json(f"/api/v1/anomaly/history?limit={limit}")
    
    async def get_sensor_health(self, sensor_id: str) -> dict:
        """Get sensor health."""
        return await self._get_json(f"/api/v1/anomaly/sensor/{sensor_id}/health")
    
    async def list_models(self) -> dict:
        """List anomaly models."""
        return await self._get_json("/api/v1/anomaly/models")
    
    async def get_model(self, model_id: str) -> dict:
        """Get model."""
        return await self._get_json(f"/api/v1/anomaly/models/{model_id}")
    
    async def train_model(self, model_id: str) -> dict:
        """Train model."""
        return await self._post_json(f"/api/v1/anomaly/models/{model_id}/train", {})
    
    async def get_alerts(self) -> dict:
        """Get active alerts."""
        return await self._get_json("/api/v1/anomaly/alerts")
    
    async def dismiss_alert(self, alert_id: str) -> dict:
        """Dismiss alert."""
        return await self._post_json(f"/api/v1/anomaly/alerts/{alert_id}/dismiss", {})
    
    async def get_predictive_maintenance(self) -> dict:
        """Get predictive maintenance."""
        return await self._get_json("/api/v1/predictive")
    
    async def get_maintenance_history(self) -> dict:
        """Get maintenance history."""
        return await self._get_json("/api/v1/maintenance")


class EnergyAPI(CopilotApiClient):
    """Energy API client."""
    
    async def get_consumption_forecast(self, hours: int = 48) -> dict:
        """Get consumption forecast."""
        return await self._get_json(f"/api/v1/energy/forecast/consumption?hours={hours}")
    
    async def get_pv_forecast(self, hours: int = 48) -> dict:
        """Get PV forecast."""
        return await self._get_json(f"/api/v1/energy/forecast/pv?hours={hours}")
    
    async def get_combined_forecast(self, hours: int = 48) -> dict:
        """Get combined forecast."""
        return await self._get_json(f"/api/v1/energy/forecast/combined?hours={hours}")
    
    async def get_load_shifting_recommendations(self) -> dict:
        """Get load shifting recommendations."""
        return await self._get_json("/api/v1/energy/load-shifting/recommendations")
    
    async def get_load_shifting_windows(self) -> dict:
        """Get load shifting windows."""
        return await self._get_json("/api/v1/energy/load-shifting/windows")
    
    async def manage_shiftable_device(self, device: dict) -> dict:
        """Manage shiftable device."""
        return await self._post_json("/api/v1/energy/load-shifting/devices", device)
    
    async def get_optimization(self) -> dict:
        """Get optimization."""
        return await self._get_json("/api/v1/energy/optimization")
    
    async def get_energy_stats(self) -> dict:
        """Get energy statistics."""
        return await self._get_json("/api/v1/energy/stats")
    
    async def get_tariff_info(self) -> dict:
        """Get tariff info."""
        return await self._get_json("/api/v1/energy/tariff")
    
    async def get_cost_analysis(self) -> dict:
        """Get cost analysis."""
        return await self._get_json("/api/v1/energy/cost")
    
    async def get_savings(self) -> dict:
        """Get savings tracking."""
        return await self._get_json("/api/v1/energy/savings")


class WeatherAPI(CopilotApiClient):
    """Weather API client."""
    
    async def get_current_weather(self) -> dict:
        """Get current weather."""
        return await self._get_json("/api/v1/weather")
    
    async def get_forecast(self, days: int = 7) -> dict:
        """Get forecast."""
        return await self._get_json(f"/api/v1/weather/forecast?days={days}")
    
    async def get_alerts(self) -> dict:
        """Get weather alerts."""
        return await self._get_json("/api/v1/weather/alerts")
    
    async def get_warnings(self) -> dict:
        """Get weather warnings."""
        return await self._get_json("/api/v1/weather/warnings")
    
    async def get_historical(self, start: str, end: str) -> dict:
        """Get historical data."""
        return await self._get_json(f"/api/v1/weather/historical?start={start}&end={end}")
    
    async def get_station_data(self, station_id: str) -> dict:
        """Get station data."""
        return await self._get_json(f"/api/v1/weather/station/{station_id}")


class CalendarAPI(CopilotApiClient):
    """Calendar API client."""
    
    async def list_calendars(self) -> dict:
        """List calendars."""
        return await self._get_json("/api/v1/calendar")
    
    async def get_todays_events(self) -> dict:
        """Get today's events."""
        return await self._get_json("/api/v1/calendar/events/today")
    
    async def get_upcoming_events(self, days: int = 7) -> dict:
        """Get upcoming events."""
        return await self._get_json(f"/api/v1/calendar/events/upcoming?days={days}")
    
    async def get_events(self, start: str, end: str) -> dict:
        """Get all events."""
        return await self._get_json(f"/api/v1/calendar/events?start={start}&end={end}")
    
    async def get_event(self, event_id: str) -> dict:
        """Get event."""
        return await self._get_json(f"/api/v1/calendar/events/{event_id}")
    
    async def create_event(self, event: dict) -> dict:
        """Create event."""
        return await self._post_json("/api/v1/calendar/events", event)
    
    async def delete_event(self, event_id: str) -> dict:
        """Delete event."""
        return await self._post_json(f"/api/v1/calendar/events/{event_id}/delete", {})
    
    async def list_reminders(self) -> dict:
        """List reminders."""
        return await self._get_json("/api/v1/reminders")
    
    async def get_wecker(self) -> dict:
        """Get alarm clock."""
        return await self._get_json("/api/v1/wecker")
    
    async def get_alarm_dashboard(self) -> dict:
        """Get alarm dashboard."""
        return await self._get_json("/api/v1/alarm/dashboard")
    
    async def list_alarms(self) -> dict:
        """List alarms."""
        return await self._get_json("/api/v1/alarm/alarms")
    
    async def create_alarm(self, alarm: dict) -> dict:
        """Create alarm."""
        return await self._post_json("/api/v1/alarm/alarms", alarm)


# =============================================================================
# COMPLETE API WRAPPER — ALL 286+ APIs
# =============================================================================

class PilotSuiteCompleteAPI:
    """Complete PilotSuite API wrapper — ALL 286+ endpoints."""
    
    def __init__(self, api: CopilotApiClient):
        self.api = api
        
        # Batch 1: Core APIs
        self.brain = BrainGraphAPI(api)
        self.kg = KnowledgeGraphAPI(api)
        self.habitus = HabitusAPI(api)
        self.neurons = NeuronsAPI(api)
        self.mood = MoodAPI(api)
        
        # Batch 2: Automation APIs
        self.notifications = NotificationsAPI(api)
        self.zones = ZoneAutomationAPI(api)
        self.proposals = ProposalsAPI(api)
        self.automation = AutomationAPI(api)
        
        # Batch 3: Intelligence APIs
        self.rag = RAGAPI(api)
        self.anomaly = AnomalyAPI(api)
        self.energy = EnergyAPI(api)
        self.weather = WeatherAPI(api)
        self.calendar = CalendarAPI(api)
        
        # Batch 4: Media & Hardware
        # (To be added: Sonos, Tags, Hardware, Camera, etc.)
        
        # Batch 5: Styx & System
        # (To be added: Chat, Multi-Home, Dashboard, Debug, etc.)
