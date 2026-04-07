"""Sensor registration for Copilot HA.

All public sensors are imported here for discovery.
UnifiedAnomalyFramework is shared across: predictive_maintenance,
habit_learning, media_sensors, gas_meter.
"""

from .anomaly_detection_sensor import AnomalyDetectionSensor
from .anomaly_alert import AnomalyAlertSensor
from .appliance_fingerprint_sensor import ApplianceFingerprintSensor
from .area_presence_sensor import AreaPresenceSensor
from .area_presence_sensor_factory import async_build_area_presence_sensors
from .automation_suggestion_sensor import AutomationSuggestionSensor
from .automation_template_sensor import AutomationTemplateSensor
from .autonomy_status_sensor import AutonomyStatusSensor
from .battery_optimizer_sensor import BatteryOptimizerSensor
from .brain_activity_sensor import BrainActivitySensor
from .brain_architecture_sensor import BrainArchitectureSensor
from .comfort_index_sensor import ComfortIndexSensor
from .cross_dependency_sensor import CrossDependencySensor
from .demand_response_sensor import DemandResponseSensor
from .energy_advisor_sensor import EnergyAdvisorSensor
from .energy_cost_sensor import EnergyCostSensor
from .energy_forecast_sensor import EnergyForecastSensor
from .energy_insights import EnergyInsightSensor
from .energy_report_sensor import EnergyReportSensor
from .energy_sankey_sensor import EnergySankeySensor
from .energy_schedule_sensor import EnergyScheduleSensor
from .energy_sensors import EnergyProxySensor
from .environment_sensors import (
    LightLevelSensor,
    NoiseLevelSensor,
    WeatherContextSensor,
)
from .ev_charging_sensor import EVChargingSensor
from .fuel_price_sensor import FuelPriceSensor
from .gas_meter_sensor import GasMeterSensor, GasAnomalySensor
from .habit_learning_v2 import (
    HabitLearningSensor,
    HabitPredictionSensor,
    HabitAnomalySensor,
    HabitEfficiencySensor,
)
from .habitus_zone_sensor import HabitusZoneSensor
from .heat_pump_sensor import HeatPumpSensor
from .hub_dashboard_sensor import HubDashboardSensor
from .inspector_sensor import InspectorSensor
from .light_intelligence_sensor import LightIntelligenceSensor
from .media_follow_sensor import MediaFollowSensor
from .media_sensors import (
    MediaActivitySensor,
    MediaIntensitySensor,
    MediaAnomalySensor,
)
from .module_integration import ModuleIntegrationSensor
from .mood_sensor import MoodSensor
from .neuron_dashboard import NeuronDashboardSensor
from .neurons_14 import (
    PresenceRoomSensor,
    PresencePersonSensor,
    ActivityLevelSensor,
    ActivityStillnessSensor,
    TimeOfDaySensor,
    DayTypeSensor,
    RoutineStabilitySensor,
    CalendarLoadSensor,
    AttentionLoadSensor,
    StressProxySensor,
)
from .notification_intelligence_sensor import NotificationIntelligenceSensor
from .notification_sensor import NotificationSensor
from .onboarding_sensor import OnboardingSensor
from .predictive_automation import PredictiveAutomationSensor
from .predictive_maintenance_sensor import (
    PredictiveMaintenanceSensor,
    MaintenanceConfidenceSensor,
)
from .presence_intelligence_sensor import PresenceIntelligenceSensor
from .presence_sensors import PresenceRoomSensor, PresencePersonSensor
from .proactive_alert_sensor import ProactiveAlertSensor
from .regional_context_sensor import RegionalContextSensor
from .scene_intelligence_sensor import SceneIntelligenceSensor
from .system_integration_sensor import SystemIntegrationSensor
from .tariff_sensor import TariffSensor
from .time_sensors import TimeOfDaySensor, DayTypeSensor, RoutineStabilitySensor
from .voice_context import VoiceContextSensor
from .weather_optimizer_sensor import WeatherOptimizerSensor
from .weather_warning_sensor import WeatherWarningSensor
from .zone_mode_sensor import ZoneModeSensor
from .zone_presence_trigger import ZonePresenceTriggerSensor
from .voice_sensors import (
    VoiceCommandHistorySensor,
    VoicePipelineStatusSensor,
    VoiceSTTStatusSensor,
    VoiceTTSStatusSensor,
    VoiceCommandCountSensor,
    VoiceCommandsTodaySensor,
    VoiceLastCommandSensor,
)
from .anomaly_aggregation_sensor import (
    AnomalyAggregationSensor,
    AnomalyHealthScoreSensor,
    AnomalyCriticalCountSensor,
    AnomalyHighCountSensor,
    AnomalyMediumCountSensor,
    AnomalyCriticalListSensor,
)
from .agent_status_sensor import AgentStatusSensor
from .brain_activity_sensor import BrainActivitySensor

__all__ = [
    # Anomaly Framework
    "AnomalyDetectionSensor",
    "AnomalyAlertSensor",
    "AnomalyDetectionSensor",
    # Appliance
    "ApplianceFingerprintSensor",
    # Area Presence
    "AreaPresenceSensor",
    "create_area_presence_sensors",
    # Automation
    "AutomationSuggestionSensor",
    "AutomationTemplateSensor",
    "AutonomyStatusSensor",
    # Battery / Energy
    "BatteryOptimizerSensor",
    "EnergyAdvisorSensor",
    "EnergyCostSensor",
    "EnergyForecastSensor",
    "EnergyInsightsSensor",
    "EnergyProxySensor",
    "EnergyReportSensor",
    "EnergySankeySensor",
    "EnergyScheduleSensor",
    # Brain
    "BrainActivitySensor",
    "BrainArchitectureSensor",
    # Comfort / Environment
    "ComfortIndexSensor",
    "LightLevelSensor",
    "NoiseLevelSensor",
    "WeatherContextSensor",
    # Cross-cutting
    "CrossDependencySensor",
    "DemandResponseSensor",
    "ProactiveAlertSensor",
    # EV / Fuel
    "EVChargingSensor",
    "FuelPriceSensor",
    # Gas
    "GasMeterSensor",
    "GasAnomalySensor",
    # Habits
    "HabitLearningSensor",
    "HabitPredictionSensor",
    "HabitAnomalySensor",
    "HabitEfficiencySensor",
    # Habitus
    "HabitusZoneSensor",
    # Heat Pump
    "HeatPumpSensor",
    # Hub
    "HubDashboardSensor",
    # Inspector
    "InspectorSensor",
    # Light Intelligence
    "LightIntelligenceSensor",
    # Media
    "MediaActivitySensor",
    "MediaIntensitySensor",
    "MediaAnomalySensor",
    "MediaFollowSensor",
    # Module
    "ModuleIntegrationSensor",
    # Mood
    "MoodSensor",
    # Neurons (14)
    "PresenceRoomSensor",
    "PresencePersonSensor",
    "ActivityLevelSensor",
    "ActivityStillnessSensor",
    "TimeOfDaySensor",
    "DayTypeSensor",
    "RoutineStabilitySensor",
    "CalendarLoadSensor",
    "AttentionLoadSensor",
    "StressProxySensor",
    "EnergyProxySensor",
    # Neuron Dashboard
    "NeuronDashboardSensor",
    # Notifications
    "NotificationIntelligenceSensor",
    "NotificationSensor",
    # Onboarding
    "OnboardingSensor",
    # Predictive
    "PredictiveAutomationSensor",
    "PredictiveMaintenanceSensor",
    "MaintenanceConfidenceSensor",
    # Presence
    "PresenceIntelligenceSensor",
    # Regional
    "RegionalContextSensor",
    # Scene
    "SceneIntelligenceSensor",
    # System
    "SystemIntegrationSensor",
    # Tariff
    "TariffSensor",
    # Voice
    "VoiceContextSensor",
    # Weather
    "WeatherOptimizerSensor",
    "WeatherWarningSensor",
    # Zone
    "ZoneModeSensor",
    "ZonePresenceTriggerSensor",
    # Agent
    "AgentStatusSensor",
    # Voice
    "VoiceCommandHistorySensor",
    "VoicePipelineStatusSensor",
    "VoiceSTTStatusSensor",
    "VoiceTTSStatusSensor",
    "VoiceCommandCountSensor",
    "VoiceCommandsTodaySensor",
    "VoiceLastCommandSensor",
    # Anomaly Aggregation
    "AnomalyAggregationSensor",
    "AnomalyHealthScoreSensor",
    "AnomalyCriticalCountSensor",
    "AnomalyHighCountSensor",
    "AnomalyMediumCountSensor",
    "AnomalyCriticalListSensor",
]
