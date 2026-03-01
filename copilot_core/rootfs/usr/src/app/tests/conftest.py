"""Shared test fixtures for CoPilot Core tests."""
import pytest


@pytest.fixture(autouse=True)
def reset_all_before_test():
    """Reset all global registries before each test.

    This ensures complete isolation between tests, especially when
    different test modules create their own Flask apps and register
    blueprints independently.

    Runs automatically before EVERY test (autouse=True).
    """
    _reset_all_registries()
    yield
    # Optional cleanup after test
    _reset_all_registries()


@pytest.fixture(autouse=True)
def reset_auth_token_cache():
    """Reset the auth token cache before each test.

    Prevents token state leaking between test modules — the cache is a
    module-level variable with a 60s TTL, so a test that sets it will
    poison all subsequent tests that create a Flask test client.
    """
    try:
        import copilot_core.api.security as sec
        sec._token_cache = ("", 0.0)
    except ImportError:
        pass
    yield
    # Also reset after the test
    try:
        import copilot_core.api.security as sec
        sec._token_cache = ("", 0.0)
    except ImportError:
        pass


@pytest.fixture
def isolated_blueprint_test():
    """Fixture for tests that need isolated blueprint registries.

    Use this fixture when your test creates its own Flask app instance
    and registers blueprints directly (not importing from main.py).

    This fixture resets all global blueprint registries before AND after
    the test to ensure complete isolation.

    Example:
        def test_my_blueprint(isolated_blueprint_test):
            app = Flask(__name__)
            app.register_blueprint(my_bp)
            # ... test code ...

    NOT needed for tests that import from main.py (e.g., test_tag_api.py),
    as those share the main app instance and should NOT reset registries.
    """
    _reset_all_registries()
    yield
    _reset_all_registries()


def _reset_all_registries():
    """Helper to reset all known global registries.

    Used by isolated_blueprint_test fixture to ensure test isolation.
    """
    # Tags API
    try:
        import copilot_core.tags.api as tags_api
        tags_api._registry = None
    except (ImportError, AttributeError):
        pass

    # Candidates API
    try:
        import copilot_core.candidates.api as candidates_api
        candidates_api._candidate_store = None
    except (ImportError, AttributeError):
        pass

    # Automations API
    try:
        import copilot_core.automations.api as automations_api
        automations_api._engine = None
    except (ImportError, AttributeError):
        pass

    # Regional API
    try:
        import copilot_core.regional.api as regional_api
        regional_api._provider = None
        regional_api._warning_manager = None
        regional_api._fuel_tracker = None
        regional_api._tariff_engine = None
        regional_api._alert_engine = None
        regional_api._forecast_engine = None
        regional_api._battery_optimizer = None
        regional_api._heat_pump_controller = None
        regional_api._ev_charging_planner = None
        regional_api._gas_meter = None
    except (ImportError, AttributeError):
        pass

    # UniFi API
    try:
        import copilot_core.unifi.api as unifi_api
        unifi_api._unifi_service = None
    except (ImportError, AttributeError):
        pass

    # System Health API
    try:
        import copilot_core.system_health.api as health_api
        health_api._service = None
    except (ImportError, AttributeError):
        pass

    # Prediction API
    try:
        import copilot_core.prediction.api as pred_api
        pred_api._forecaster = None
        pred_api._optimizer = None
        pred_api._ts_forecaster = None
        pred_api._load_scheduler = None
        pred_api._schedule_planner = None
        pred_api._weather_optimizer = None
    except (ImportError, AttributeError):
        pass

    # Energy API
    try:
        import copilot_core.energy.api as energy_api
        energy_api._energy_service = None
        energy_api._cost_tracker = None
        energy_api._fingerprinter = None
        energy_api._report_generator = None
        energy_api._demand_response = None
    except (ImportError, AttributeError):
        pass

    # Energy init
    try:
        import copilot_core.energy as energy_mod
        energy_mod._energy_service = None
    except (ImportError, AttributeError):
        pass

    # Event Processor
    try:
        import copilot_core.ingest.event_processor as ep
        ep._processor = None
    except (ImportError, AttributeError):
        pass

    # Agent Config
    try:
        import copilot_core.agent_config as ac
        ac._config = None
        ac._llm_provider = None
        ac._conversation_module = None
        ac._start_time = None
    except (ImportError, AttributeError):
        pass

    # User Preferences
    try:
        import copilot_core.storage.user_preferences as up
        up._store = None
    except (ImportError, AttributeError):
        pass

    # Core init
    try:
        import copilot_core as core
        core._system_health_service = None
        core._unifi_service = None
    except (ImportError, AttributeError):
        pass

    # Phase 5: Sharing API (Cross-Home Sync)
    try:
        import copilot_core.sharing.api as sharing_api
        sharing_api._sync_service = None
        sharing_api._registry = None
        sharing_api._discovery = None
    except (ImportError, AttributeError):
        pass

    # Phase 5: Collective Intelligence API (Federated Learning)
    try:
        import copilot_core.collective_intelligence.api as fed_api
        fed_api._service = None
    except (ImportError, AttributeError):
        pass

    # Conversation API (LLM Provider)
    try:
        import copilot_core.api.v1.conversation as conv_api
        conv_api._llm_provider = None
        conv_api._mcp_tools = None
    except (ImportError, AttributeError):
        pass
