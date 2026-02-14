"""
Core Setup - Service initialization and blueprint registration.

Extracted from main.py to follow modular architecture pattern.
"""

from flask import Flask

from copilot_core.api.v1 import log_fixer_tx
from copilot_core.api.v1 import tag_system
from copilot_core.api.v1 import events_ingest
from copilot_core.api.v1.events_ingest import set_post_ingest_callback
from copilot_core.brain_graph.api import brain_graph_bp, init_brain_graph_api
from copilot_core.brain_graph.service import BrainGraphService
from copilot_core.brain_graph.render import GraphRenderer
from copilot_core.ingest.event_processor import EventProcessor
from copilot_core.dev_surface.api import dev_surface_bp, init_dev_surface_api
from copilot_core.candidates.api import candidates_bp, init_candidates_api
from copilot_core.candidates.store import CandidateStore
from copilot_core.habitus.api import habitus_bp, init_habitus_api
from copilot_core.habitus.service import HabitusService
from copilot_core.mood.api import mood_bp, init_mood_api
from copilot_core.mood.service import MoodService
from copilot_core.system_health.api import system_health_bp
from copilot_core.system_health.service import SystemHealthService


def init_services(hass=None):
    """
    Initialize all core services and return them as a dict for testing/dependency injection.
    
    Args:
        hass: Home Assistant hass instance (required for SystemHealth)
    
    Returns:
        dict: Dictionary containing initialized services:
            - system_health_service: SystemHealthService instance (optional, requires hass)
            - brain_graph_service: BrainGraphService instance
            - graph_renderer: GraphRenderer instance
            - candidate_store: CandidateStore instance
            - habitus_service: HabitusService instance
            - mood_service: MoodService instance
            - event_processor: EventProcessor instance
    """
    # Initialize system health service (requires hass)
    system_health_service = None
    if hass:
        system_health_service = SystemHealthService(hass)

    # Initialize brain graph service
    brain_graph_service = BrainGraphService()
    graph_renderer = GraphRenderer()
    init_brain_graph_api(brain_graph_service, graph_renderer)

    # Initialize dev surface
    init_dev_surface_api(brain_graph_service)

    # Initialize candidates API and store
    candidate_store = CandidateStore()
    init_candidates_api(candidate_store)

    # Initialize habitus service and API
    habitus_service = HabitusService(brain_graph_service, candidate_store)
    init_habitus_api(habitus_service)

    # Initialize mood service and API
    mood_service = MoodService()
    init_mood_api(mood_service)

    # Initialize event processor: EventStore → BrainGraph pipeline
    event_processor = EventProcessor(brain_graph_service=brain_graph_service)
    set_post_ingest_callback(event_processor.process_events)

    return {
        "system_health_service": system_health_service,
        "brain_graph_service": brain_graph_service,
        "graph_renderer": graph_renderer,
        "candidate_store": candidate_store,
        "habitus_service": habitus_service,
        "mood_service": mood_service,
        "event_processor": event_processor,
    }


def register_blueprints(app: Flask, services: dict = None) -> None:
    """
    Register all API blueprints with the Flask app.
    
    Args:
        app: Flask application instance
        services: Optional services dict from init_services() for global access
    """
    app.register_blueprint(log_fixer_tx.bp)
    app.register_blueprint(tag_system.bp)
    app.register_blueprint(events_ingest.bp)
    app.register_blueprint(brain_graph_bp)
    app.register_blueprint(dev_surface_bp)
    app.register_blueprint(candidates_bp)
    app.register_blueprint(habitus_bp)
    app.register_blueprint(mood_bp)
    app.register_blueprint(system_health_bp)
    
    # Set global service instances for API access
    if services:
        from copilot_core import set_system_health_service
        if services.get("system_health_service"):
            set_system_health_service(services["system_health_service"])
