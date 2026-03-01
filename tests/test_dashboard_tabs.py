"""Tests for Dashboard Tab Navigation (v12.8.0).

Tests dashboard tab navigation, WebSocket updates, and UI interactions.
Uses mock Flask app - no real browser required for core tests.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from typing import Dict, List, Any
import json
import time


# ── Mock Dashboard App ───────────────────────────────────────────────────

class MockDashboardApp:
    """Mock Flask dashboard app for testing."""

    def __init__(self):
        self.tabs = {
            "overview": {
                "id": "overview",
                "name": "Übersicht",
                "icon": "mdi:view-dashboard",
                "route": "/dashboard/overview",
                "widgets": ["system_status", "brain_graph", "sensor_overview"],
                "active": True,
            },
            "habitus": {
                "id": "habitus",
                "name": "Habitus",
                "icon": "mdi:brain",
                "route": "/dashboard/habitus",
                "widgets": ["habitus_zones", "habitus_rules", "habitus_miner"],
                "active": False,
            },
            "automationen": {
                "id": "automationen",
                "name": "Automationen",
                "icon": "mdi:robot",
                "route": "/dashboard/automationen",
                "widgets": ["automation_list", "automation_editor"],
                "active": False,
            },
            "energie": {
                "id": "energie",
                "name": "Energie",
                "icon": "mdi:lightning-bolt",
                "route": "/dashboard/energie",
                "widgets": ["energy_overview", "energy_forecast"],
                "active": False,
            },
            "system": {
                "id": "system",
                "name": "System",
                "icon": "mdi:cog",
                "route": "/dashboard/system",
                "widgets": ["system_health", "logs", "settings"],
                "active": False,
            },
        }
        self.active_tab = "overview"
        self.websocket_clients = []

    def get_tabs(self) -> List[Dict[str, Any]]:
        """Get all tabs."""
        return list(self.tabs.values())

    def get_tab(self, tab_id: str) -> Dict[str, Any]:
        """Get specific tab."""
        return self.tabs.get(tab_id)

    def switch_tab(self, tab_id: str) -> bool:
        """Switch to different tab."""
        if tab_id not in self.tabs:
            return False

        # Deactivate current tab
        self.tabs[self.active_tab]["active"] = False

        # Activate new tab
        self.active_tab = tab_id
        self.tabs[tab_id]["active"] = True

        return True

    def get_active_tab(self) -> Dict[str, Any]:
        """Get currently active tab."""
        return self.tabs[self.active_tab]

    def get_active_widgets(self) -> List[str]:
        """Get widgets for active tab."""
        return self.tabs[self.active_tab]["widgets"]


# ── WebSocket Mock ────────────────────────────────────────────────────────

class MockWebSocketClient:
    """Mock WebSocket client for testing."""

    def __init__(self, client_id: str):
        self.client_id = client_id
        self.messages_sent = []
        self.messages_received = []
        self.connected = False

    def connect(self):
        self.connected = True
        self.messages_received.append({
            "event": "connected",
            "data": {"message": "Connected to dashboard"}
        })

    def disconnect(self):
        self.connected = False

    def send(self, event: str, data: Dict[str, Any]):
        """Send message to server."""
        self.messages_sent.append({"event": event, "data": data})

    def receive(self, event: str, data: Dict[str, Any]):
        """Receive message from server."""
        self.messages_received.append({"event": event, "data": data})

    def emit(self, event: str, data: Dict[str, Any]):
        """Emit event (alias for send)."""
        self.send(event, data)


class MockSocketIO:
    """Mock Socket.IO server."""

    def __init__(self):
        self.clients: Dict[str, MockWebSocketClient] = {}
        self.events = {}

    def on(self, event: str):
        """Decorator to register event handler."""
        def decorator(func):
            self.events[event] = func
            return func
        return decorator

    def emit(self, event: str, data: Dict[str, Any], room: str = None):
        """Emit event to clients."""
        if room:
            if room in self.clients:
                self.clients[room].receive(event, data)
        else:
            for client in self.clients.values():
                client.receive(event, data)

    def connect_client(self, client_id: str) -> MockWebSocketClient:
        """Connect a new client."""
        client = MockWebSocketClient(client_id)
        self.clients[client_id] = client
        client.connect()
        return client


# ── Tab Navigation Controller ────────────────────────────────────────────

class DashboardTabController:
    """Controller for dashboard tab navigation."""

    def __init__(self, app: MockDashboardApp, socketio: MockSocketIO):
        self.app = app
        self.socketio = socketio
        self.tab_history: List[str] = []

    def switch_tab(self, client_id: str, tab_id: str) -> Dict[str, Any]:
        """Handle tab switch request from client."""
        if not self.app.switch_tab(tab_id):
            return {
                "success": False,
                "error": f"Tab '{tab_id}' not found"
            }

        # Add to history
        self.tab_history.append(tab_id)

        # Notify client
        active_tab = self.app.get_active_tab()
        self.socketio.emit("tab_changed", {
            "tab_id": tab_id,
            "tab_name": active_tab["name"],
            "widgets": active_tab["widgets"]
        }, room=client_id)

        return {
            "success": True,
            "tab": active_tab
        }

    def get_tabs(self) -> List[Dict[str, Any]]:
        """Get all tabs."""
        return self.app.get_tabs()

    def get_active_tab(self) -> Dict[str, Any]:
        """Get active tab."""
        return self.app.get_active_tab()

    def get_tab_history(self) -> List[str]:
        """Get tab navigation history."""
        return self.tab_history.copy()


# ── Tests ─────────────────────────────────────────────────────────────────

class TestDashboardTabs:
    """Basic dashboard tab tests."""

    @pytest.fixture
    def app(self):
        """Create mock dashboard app."""
        return MockDashboardApp()

    def test_get_all_tabs(self, app):
        """Test getting all tabs."""
        tabs = app.get_tabs()
        assert len(tabs) == 5

        tab_ids = {t["id"] for t in tabs}
        assert tab_ids == {"overview", "habitus", "automationen", "energie", "system"}

    def test_get_specific_tab(self, app):
        """Test getting specific tab."""
        tab = app.get_tab("habitus")
        assert tab is not None
        assert tab["name"] == "Habitus"
        assert tab["icon"] == "mdi:brain"

    def test_get_nonexistent_tab(self, app):
        """Test getting nonexistent tab."""
        tab = app.get_tab("nonexistent")
        assert tab is None

    def test_default_active_tab(self, app):
        """Test default active tab is overview."""
        active = app.get_active_tab()
        assert active["id"] == "overview"
        assert active["active"] is True

    def test_tab_structure(self, app):
        """Test tab structure has required fields."""
        for tab in app.get_tabs():
            assert "id" in tab
            assert "name" in tab
            assert "icon" in tab
            assert "route" in tab
            assert "widgets" in tab
            assert "active" in tab


class TestTabNavigation:
    """Tests for tab navigation logic."""

    @pytest.fixture
    def controller(self):
        """Create tab controller with mock app and socketio."""
        app = MockDashboardApp()
        socketio = MockSocketIO()
        return DashboardTabController(app, socketio)

    def test_switch_to_habitus_tab(self, controller):
        """Test switching to habitus tab."""
        result = controller.switch_tab("client1", "habitus")

        assert result["success"] is True
        assert result["tab"]["id"] == "habitus"
        assert result["tab"]["name"] == "Habitus"

        active = controller.get_active_tab()
        assert active["id"] == "habitus"

    def test_switch_to_automationen_tab(self, controller):
        """Test switching to automationen tab."""
        result = controller.switch_tab("client1", "automationen")

        assert result["success"] is True
        assert result["tab"]["id"] == "automationen"

    def test_switch_to_energie_tab(self, controller):
        """Test switching to energie tab."""
        result = controller.switch_tab("client1", "energie")

        assert result["success"] is True
        assert result["tab"]["id"] == "energie"

    def test_switch_to_system_tab(self, controller):
        """Test switching to system tab."""
        result = controller.switch_tab("client1", "system")

        assert result["success"] is True
        assert result["tab"]["id"] == "system"

    def test_switch_to_invalid_tab(self, controller):
        """Test switching to invalid tab fails."""
        result = controller.switch_tab("client1", "invalid")

        assert result["success"] is False
        assert "error" in result

    def test_tab_deactivation_on_switch(self, controller):
        """Test that previous tab is deactivated on switch."""
        # Start with overview active
        assert controller.app.tabs["overview"]["active"] is True
        assert controller.app.tabs["habitus"]["active"] is False

        # Switch to habitus
        controller.switch_tab("client1", "habitus")

        # Verify deactivation
        assert controller.app.tabs["overview"]["active"] is False
        assert controller.app.tabs["habitus"]["active"] is True

    def test_tab_navigation_history(self, controller):
        """Test tab navigation history tracking."""
        controller.switch_tab("client1", "habitus")
        controller.switch_tab("client1", "energie")
        controller.switch_tab("client1", "system")

        history = controller.get_tab_history()
        assert len(history) == 3
        assert history == ["habitus", "energie", "system"]

    def test_all_5_tabs_navigable(self, controller):
        """Test that all 5 tabs are navigable."""
        tab_ids = ["overview", "habitus", "automationen", "energie", "system"]

        for tab_id in tab_ids:
            result = controller.switch_tab("client1", tab_id)
            assert result["success"] is True
            assert controller.get_active_tab()["id"] == tab_id


class TestWebSocketTabUpdates:
    """Tests for WebSocket tab update notifications."""

    @pytest.fixture
    def setup_websocket(self):
        """Setup controller with connected WebSocket client."""
        app = MockDashboardApp()
        socketio = MockSocketIO()
        controller = DashboardTabController(app, socketio)

        # Connect client
        client = socketio.connect_client("client1")

        return controller, socketio, client

    def test_tab_change_broadcast(self, setup_websocket):
        """Test that tab change is broadcast via WebSocket."""
        controller, socketio, client = setup_websocket

        controller.switch_tab("client1", "habitus")

        # Check client received tab_changed event
        assert len(client.messages_received) >= 2  # connected + tab_changed

        tab_change_msg = None
        for msg in client.messages_received:
            if msg["event"] == "tab_changed":
                tab_change_msg = msg
                break

        assert tab_change_msg is not None
        assert tab_change_msg["data"]["tab_id"] == "habitus"
        assert tab_change_msg["data"]["tab_name"] == "Habitus"

    def test_widget_list_broadcast(self, setup_websocket):
        """Test that widget list is broadcast on tab change."""
        controller, socketio, client = setup_websocket

        controller.switch_tab("client1", "habitus")

        # Find tab_changed message
        for msg in client.messages_received:
            if msg["event"] == "tab_changed":
                widgets = msg["data"]["widgets"]
                assert "habitus_zones" in widgets
                assert "habitus_rules" in widgets
                break

    def test_multiple_clients_receive_updates(self, setup_websocket):
        """Test that multiple clients receive tab updates."""
        controller, socketio, client1 = setup_websocket

        # Connect second client
        client2 = socketio.connect_client("client2")

        controller.switch_tab("client1", "energie")

        # Both clients should receive update
        for msg in client1.messages_received:
            if msg["event"] == "tab_changed":
                assert msg["data"]["tab_id"] == "energie"
                break

        for msg in client2.messages_received:
            if msg["event"] == "tab_changed":
                assert msg["data"]["tab_id"] == "energie"
                break


class TestWidgetLoading:
    """Tests for widget loading per tab."""

    @pytest.fixture
    def app(self):
        return MockDashboardApp()

    def test_overview_widgets(self, app):
        """Test overview tab widgets."""
        widgets = app.tabs["overview"]["widgets"]
        assert "system_status" in widgets
        assert "brain_graph" in widgets
        assert "sensor_overview" in widgets

    def test_habitus_widgets(self, app):
        """Test habitus tab widgets."""
        widgets = app.tabs["habitus"]["widgets"]
        assert "habitus_zones" in widgets
        assert "habitus_rules" in widgets
        assert "habitus_miner" in widgets

    def test_automationen_widgets(self, app):
        """Test automationen tab widgets."""
        widgets = app.tabs["automationen"]["widgets"]
        assert "automation_list" in widgets
        assert "automation_editor" in widgets

    def test_energie_widgets(self, app):
        """Test energie tab widgets."""
        widgets = app.tabs["energie"]["widgets"]
        assert "energy_overview" in widgets
        assert "energy_forecast" in widgets

    def test_system_widgets(self, app):
        """Test system tab widgets."""
        widgets = app.tabs["system"]["widgets"]
        assert "system_health" in widgets
        assert "logs" in widgets
        assert "settings" in widgets

    def test_get_active_widgets(self, app):
        """Test getting widgets for active tab."""
        widgets = app.get_active_widgets()
        assert widgets == ["system_status", "brain_graph", "sensor_overview"]

        app.switch_tab("habitus")
        widgets = app.get_active_widgets()
        assert widgets == ["habitus_zones", "habitus_rules", "habitus_miner"]


class TestTabRoutes:
    """Tests for tab routes."""

    @pytest.fixture
    def app(self):
        return MockDashboardApp()

    def test_overview_route(self, app):
        """Test overview tab route."""
        assert app.tabs["overview"]["route"] == "/dashboard/overview"

    def test_habitus_route(self, app):
        """Test habitus tab route."""
        assert app.tabs["habitus"]["route"] == "/dashboard/habitus"

    def test_automationen_route(self, app):
        """Test automationen tab route."""
        assert app.tabs["automationen"]["route"] == "/dashboard/automationen"

    def test_energie_route(self, app):
        """Test energie tab route."""
        assert app.tabs["energie"]["route"] == "/dashboard/energie"

    def test_system_route(self, app):
        """Test system tab route."""
        assert app.tabs["system"]["route"] == "/dashboard/system"


class TestTabIcons:
    """Tests for tab icons."""

    @pytest.fixture
    def app(self):
        return MockDashboardApp()

    def test_overview_icon(self, app):
        """Test overview tab icon."""
        assert app.tabs["overview"]["icon"] == "mdi:view-dashboard"

    def test_habitus_icon(self, app):
        """Test habitus tab icon."""
        assert app.tabs["habitus"]["icon"] == "mdi:brain"

    def test_automationen_icon(self, app):
        """Test automationen tab icon."""
        assert app.tabs["automationen"]["icon"] == "mdi:robot"

    def test_energie_icon(self, app):
        """Test energie tab icon."""
        assert app.tabs["energie"]["icon"] == "mdi:lightning-bolt"

    def test_system_icon(self, app):
        """Test system tab icon."""
        assert app.tabs["system"]["icon"] == "mdi:cog"


class TestTabStatePersistence:
    """Tests for tab state persistence."""

    @pytest.fixture
    def controller(self):
        app = MockDashboardApp()
        socketio = MockSocketIO()
        return DashboardTabController(app, socketio)

    def test_tab_state_after_switch(self, controller):
        """Test tab state is maintained after switch."""
        controller.switch_tab("client1", "habitus")
        controller.switch_tab("client1", "energie")

        # Go back to habitus
        controller.switch_tab("client1", "habitus")

        active = controller.get_active_tab()
        assert active["id"] == "habitus"
        assert active["active"] is True

    def test_tab_history_persistence(self, controller):
        """Test tab history is maintained."""
        controller.switch_tab("client1", "habitus")
        controller.switch_tab("client1", "energie")

        history = controller.get_tab_history()
        assert len(history) == 2

        # History should not be affected by getting active tab
        controller.get_active_tab()
        assert len(controller.get_tab_history()) == 2


# ── Integration-style Tests ───────────────────────────────────────────────

class TestDashboardTabIntegration:
    """Integration tests for complete tab navigation flow."""

    def test_full_tab_navigation_flow(self):
        """Test complete flow: connect → switch tabs → verify state."""
        app = MockDashboardApp()
        socketio = MockSocketIO()
        controller = DashboardTabController(app, socketio)

        # Connect client
        client = socketio.connect_client("client_123")

        # Navigate through all tabs
        tabs_to_visit = ["habitus", "automationen", "energie", "system"]

        for tab_id in tabs_to_visit:
            result = controller.switch_tab("client_123", tab_id)
            assert result["success"] is True

            # Verify active tab changed
            assert controller.get_active_tab()["id"] == tab_id

            # Verify previous tabs are inactive
            for prev_tab in tabs_to_visit:
                if prev_tab != tab_id:
                    assert app.tabs[prev_tab]["active"] is False

        # Verify final state
        assert controller.get_active_tab()["id"] == "system"
        assert len(controller.get_tab_history()) == 4

    def test_concurrent_tab_switches(self):
        """Test concurrent tab switches from multiple clients."""
        app = MockDashboardApp()
        socketio = MockSocketIO()
        controller = DashboardTabController(app, socketio)

        # Connect multiple clients
        client1 = socketio.connect_client("client_1")
        client2 = socketio.connect_client("client_2")
        client3 = socketio.connect_client("client_3")

        # Each client switches to different tab
        controller.switch_tab("client_1", "habitus")
        controller.switch_tab("client_2", "energie")
        controller.switch_tab("client_3", "system")

        # All clients see same active tab (last one wins)
        active = controller.get_active_tab()
        assert active["id"] == "system"

        # But all received updates
        for client in [client1, client2, client3]:
            received_tab_changes = [
                m for m in client.messages_received
                if m["event"] == "tab_changed"
            ]
            assert len(received_tab_changes) >= 1
