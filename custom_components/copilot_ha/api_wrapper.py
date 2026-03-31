"""Complete PilotSuite API Wrapper — ALL 286+ APIs unified."""
from __future__ import annotations

from .api import CopilotApiClient
from .api_complete import (
    BrainGraphAPI, KnowledgeGraphAPI, HabitusAPI, NeuronsAPI, MoodAPI,
    NotificationsAPI, ZoneAutomationAPI, ProposalsAPI, AutomationAPI,
    RAGAPI, AnomalyAPI, EnergyAPI, WeatherAPI, CalendarAPI,
)
from .api_batch4 import MediaAPI, TagsAPI, HardwareAPI, CameraAPI
from .api_batch5 import StyxAPI, MultiHomeAPI, DashboardAPI, SystemAPI


class PilotSuiteAPI:
    """
    Complete PilotSuite API wrapper — ALL 286+ endpoints.
    
    Usage:
        api = PilotSuiteAPI(session, base_url, token)
        
        # Batch 1: Core
        await api.brain.get_graph_state()
        await api.kg.get_nodes()
        await api.habitus.get_rules()
        await api.neurons.list_neurons()
        await api.mood.get_mood_state()
        
        # Batch 2: Automation
        await api.notifications.list_notifications()
        await api.zones.list_zones()
        await api.proposals.list_proposals()
        await api.automation.list_automations()
        
        # Batch 3: Intelligence
        await api.rag.rag_chat("query")
        await api.anomaly.detect_anomalies(data)
        await api.energy.get_consumption_forecast()
        await api.weather.get_forecast()
        await api.calendar.get_todays_events()
        
        # Batch 4: Media & Hardware
        await api.media.get_media_zones()
        await api.tags.list_tags()
        await api.hardware.get_zigbee_status()
        await api.camera.list_cameras()
        
        # Batch 5: Styx & System
        await api.styx.styx_chat("message")
        await api.multihome.list_homes()
        await api.dashboard.get_dashboard()
        await api.system.get_debug_status()
    """
    
    def __init__(self, session, base_url: str, token: str = None):
        self.api = CopilotApiClient(session, base_url, token)
        
        # Batch 1: Core APIs
        self.brain = BrainGraphAPI(self.api)
        self.kg = KnowledgeGraphAPI(self.api)
        self.habitus = HabitusAPI(self.api)
        self.neurons = NeuronsAPI(self.api)
        self.mood = MoodAPI(self.api)
        
        # Batch 2: Automation APIs
        self.notifications = NotificationsAPI(self.api)
        self.zones = ZoneAutomationAPI(self.api)
        self.proposals = ProposalsAPI(self.api)
        self.automation = AutomationAPI(self.api)
        
        # Batch 3: Intelligence APIs
        self.rag = RAGAPI(self.api)
        self.anomaly = AnomalyAPI(self.api)
        self.energy = EnergyAPI(self.api)
        self.weather = WeatherAPI(self.api)
        self.calendar = CalendarAPI(self.api)
        
        # Batch 4: Media & Hardware
        self.media = MediaAPI(self.api)
        self.tags = TagsAPI(self.api)
        self.hardware = HardwareAPI(self.api)
        self.camera = CameraAPI(self.api)
        
        # Batch 5: Styx & System
        self.styx = StyxAPI(self.api)
        self.multihome = MultiHomeAPI(self.api)
        self.dashboard = DashboardAPI(self.api)
        self.system = SystemAPI(self.api)
    
    # Convenience methods for common operations
    async def get_status(self) -> dict:
        """Get complete system status."""
        return {
            "brain": await self.brain.get_graph_state(),
            "mood": await self.mood.get_mood_state(),
            "zones": await self.zones.list_zones(),
            "notifications": await self.notifications.list_notifications(limit=10),
            "energy": await self.energy.get_consumption_forecast(hours=24),
            "weather": await self.weather.get_current_weather(),
            "dashboard": await self.dashboard.get_dashboard(),
        }
    
    async def health_check(self) -> dict:
        """Complete health check."""
        return {
            "system": await self.system.get_debug_status(),
            "hardware": await self.hardware.get_ha_module_status(),
            "zigbee": await self.hardware.get_zigbee_status(),
            "zwave": await self.hardware.get_zwave_status(),
        }
