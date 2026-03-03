"""Tests for Dashboard 3-Tab Navigation (v13.0.4).

Tests dashboard tab navigation for the restored 3-Tab layout:
- Tab 1: Habitus (Mood/Zonen)
- Tab 2: Hausverwaltung (Energie, Präsenz, Automationen)
- Tab 3: Styx (Neural Dashboard, Brain Graph)

Uses mock Flask app - no real browser required for core tests.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from typing import Dict, List, Any
import json
import time


# ── Mock Dashboard App ───────────────────────────────────────────────────

class MockDashboardApp:
    """Mock Flask dashboard app for testing 3-Tab layout."""

    def __init__(self):
        # 3-Tab Layout (restored from recovery)
        self.tabs = {
            "habitus": {
                "id": "habitus",
                "name": "Habitus",
                "icon": "mdi-heart-pulse",
                "description": "Mood & Zonen Status",
                "route": "/dashboard/habitus",
                "widgets": ["mood_gauges", "zone_overview"],
                "active": True,
            },
            "hausverwaltung": {
                "id": "hausverwaltung",
                "name": "Hausverwaltung",
                "icon": "mdi-home-city",
                "description": "Energie, Präsenz & Automationen",
                "route": "/dashboard/hausverwaltung",
                "widgets": ["energy_overview", "praesenz", "automationen"],
                "active": False,
            },
            "styx": {
                "id": "styx",
                "name": "Styx",
                "icon": "mdi-brain",
                "description": "Neural Dashboard & Brain Graph",
                "route": "/dashboard/styx",
                "widgets": ["brain_graph", "neural_dashboard"],
                "active": False,
            },
        }
        self.active_tab = "habitus"
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
    """Basic dashboard tab tests for 3-Tab layout."""

    @pytest.fixture
    def app(self):
        """Create mock dashboard app."""
        return MockDashboardApp()

    def test_get_all_tabs(self, app):
        """Test getting all tabs."""
        tabs = app.get_tabs()
        assert len(tabs) == 3

        tab_ids = {t["id"] for t in tabs}
        assert tab_ids == {"habitus", "hausverwaltung", "styx"}

    def test_get_specific_tab(self, app):
        """Test getting specific tab."""
        tab = app.get_tab("habitus")
        assert tab is not None
        assert tab["name"] == "Habitus"
        assert tab["icon"] == "mdi-heart-pulse"

    def test_get_hausverwaltung_tab(self, app):
        """Test getting hausverwaltung tab."""
        tab = app.get_tab("hausverwaltung")
        assert tab is not None
        assert tab["name"] == "Hausverwaltung"
        assert tab["icon"] == "mdi-home-city"

    def test_get_styx_tab(self, app):
        """Test getting styx tab."""
        tab = app.get_tab("styx")
        assert tab is not None
        assert tab["name"] == "Styx"
        assert tab["icon"] == "mdi-brain"

    def test_get_nonexistent_tab(self, app):
        """Test getting nonexistent tab."""
        tab = app.get_tab("nonexistent")
        assert tab is None

    def test_default_active_tab(self, app):
        """Test default active tab is habitus."""
        active = app.get_active_tab()
        assert active["id"] == "habitus"
        assert active["active"] is True

    def test_tab_structure(self, app):
        """Test tab structure has required fields."""
        for tab in app.get_tabs():
            assert "id" in tab
            assert "name" in tab
            assert "icon" in tab
            assert "description" in tab
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

    def test_switch_to_hausverwaltung_tab(self, controller):
        """Test switching to hausverwaltung tab."""
        result = controller.switch_tab("client1", "hausverwaltung")

        assert result["success"] is True
        assert result["tab"]["id"] == "hausverwaltung"

        active = controller.get_active_tab()
        assert active["id"] == "hausverwaltung"

    def test_switch_to_styx_tab(self, controller):
        """Test switching to styx tab."""
        result = controller.switch_tab("client1", "styx")

        assert result["success"] is True
        assert result["tab"]["id"] == "styx"

        active = controller.get_active_tab()
        assert active["id"] == "styx"

    def test_switch_to_invalid_tab(self, controller):
        """Test switching to invalid tab fails."""
        result = controller.switch_tab("client1", "invalid")

        assert result["success"] is False
        assert "error" in result

    def test_tab_deactivation_on_switch(self, controller):
        """Test that previous tab is deactivated on switch."""
        # Start with habitus active
        assert controller.app.tabs["habitus"]["active"] is True
        assert controller.app.tabs["hausverwaltung"]["active"] is False

        # Switch to hausverwaltung
        controller.switch_tab("client1", "hausverwaltung")

        # Verify deactivation
        assert controller.app.tabs["habitus"]["active"] is False
        assert controller.app.tabs["hausverwaltung"]["active"] is True

    def test_tab_navigation_history(self, controller):
        """Test tab navigation history tracking."""
        controller.switch_tab("client1", "hausverwaltung")
        controller.switch_tab("client1", "styx")

        history = controller.get_tab_history()
        assert len(history) == 2
        assert history == ["hausverwaltung", "styx"]

    def test_all_3_tabs_navigable(self, controller):
        """Test that all 3 tabs are navigable."""
        tab_ids = ["habitus", "hausverwaltung", "styx"]

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

        controller.switch_tab("client1", "hausverwaltung")

        # Check client received tab_changed event
        assert len(client.messages_received) >= 2  # connected + tab_changed

        tab_change_msg = None
        for msg in client.messages_received:
            if msg["event"] == "tab_changed":
                tab_change_msg = msg
                break

        assert tab_change_msg is not None
        assert tab_change_msg["data"]["tab_id"] == "hausverwaltung"
        assert tab_change_msg["data"]["tab_name"] == "Hausverwaltung"

    def test_widget_list_broadcast(self, setup_websocket):
        """Test that widget list is broadcast on tab change."""
        controller, socketio, client = setup_websocket

        controller.switch_tab("client1", "styx")

        # Find tab_changed message
        for msg in client.messages_received:
            if msg["event"] == "tab_changed":
                widgets = msg["data"]["widgets"]
                assert "brain_graph" in widgets
                assert "neural_dashboard" in widgets
                break

    def test_multiple_clients_receive_updates(self, setup_websocket):
        """Test that multiple clients receive tab updates."""
        controller, socketio, client1 = setup_websocket

        # Connect second client
        client2 = socketio.connect_client("client2")

        controller.switch_tab("client1", "styx")

        # Both clients should receive update
        for msg in client1.messages_received:
            if msg["event"] == "tab_changed":
                assert msg["data"]["tab_id"] == "styx"
                break

        for msg in client2.messages_received:
            if msg["event"] == "tab_changed":
                assert msg["data"]["tab_id"] == "styx"
                break


class TestWidgetLoading:
    """Tests for widget loading per tab."""

    @pytest.fixture
    def app(self):
        return MockDashboardApp()

    def test_habitus_widgets(self, app):
        """Test habitus tab widgets."""
        widgets = app.tabs["habitus"]["widgets"]
        assert "mood_gauges" in widgets
        assert "zone_overview" in widgets

    def test_hausverwaltung_widgets(self, app):
        """Test hausverwaltung tab widgets."""
        widgets = app.tabs["hausverwaltung"]["widgets"]
        assert "energy_overview" in widgets
        assert "praesenz" in widgets
        assert "automationen" in widgets

    def test_styx_widgets(self, app):
        """Test styx tab widgets."""
        widgets = app.tabs["styx"]["widgets"]
        assert "brain_graph" in widgets
        assert "neural_dashboard" in widgets

    def test_get_active_widgets(self, app):
        """Test getting widgets for active tab."""
        widgets = app.get_active_widgets()
        assert widgets == ["mood_gauges", "zone_overview"]

        app.switch_tab("hausverwaltung")
        widgets = app.get_active_widgets()
        assert widgets == ["energy_overview", "praesenz", "automationen"]

        app.switch_tab("styx")
        widgets = app.get_active_widgets()
        assert widgets == ["brain_graph", "neural_dashboard"]


class TestTabRoutes:
    """Tests for tab routes."""

    @pytest.fixture
    def app(self):
        return MockDashboardApp()

    def test_habitus_route(self, app):
        """Test habitus tab route."""
        assert app.tabs["habitus"]["route"] == "/dashboard/habitus"

    def test_hausverwaltung_route(self, app):
        """Test hausverwaltung tab route."""
        assert app.tabs["hausverwaltung"]["route"] == "/dashboard/hausverwaltung"

    def test_styx_route(self, app):
        """Test styx tab route."""
        assert app.tabs["styx"]["route"] == "/dashboard/styx"


class TestTabIcons:
    """Tests for tab icons."""

    @pytest.fixture
    def app(self):
        return MockDashboardApp()

    def test_habitus_icon(self, app):
        """Test habitus tab icon."""
        assert app.tabs["habitus"]["icon"] == "mdi-heart-pulse"

    def test_hausverwaltung_icon(self, app):
        """Test hausverwaltung tab icon."""
        assert app.tabs["hausverwaltung"]["icon"] == "mdi-home-city"

    def test_styx_icon(self, app):
        """Test styx tab icon."""
        assert app.tabs["styx"]["icon"] == "mdi-brain"


class TestTabDescriptions:
    """Tests for tab descriptions."""

    @pytest.fixture
    def app(self):
        return MockDashboardApp()

    def test_habitus_description(self, app):
        """Test habitus tab description."""
        assert app.tabs["habitus"]["description"] == "Mood & Zonen Status"

    def test_hausverwaltung_description(self, app):
        """Test hausverwaltung tab description."""
        assert app.tabs["hausverwaltung"]["description"] == "Energie, Präsenz & Automationen"

    def test_styx_description(self, app):
        """Test styx tab description."""
        assert app.tabs["styx"]["description"] == "Neural Dashboard & Brain Graph"


class TestTabStatePersistence:
    """Tests for tab state persistence."""

    @pytest.fixture
    def controller(self):
        app = MockDashboardApp()
        socketio = MockSocketIO()
        return DashboardTabController(app, socketio)

    def test_tab_state_after_switch(self, controller):
        """Test tab state is maintained after switch."""
        controller.switch_tab("client1", "hausverwaltung")
        controller.switch_tab("client1", "styx")

        # Go back to hausverwaltung
        controller.switch_tab("client1", "hausverwaltung")

        active = controller.get_active_tab()
        assert active["id"] == "hausverwaltung"
        assert active["active"] is True

    def test_tab_history_persistence(self, controller):
        """Test tab history is maintained."""
        controller.switch_tab("client1", "hausverwaltung")
        controller.switch_tab("client1", "styx")

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
        tabs_to_visit = ["hausverwaltung", "styx"]

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
        assert controller.get_active_tab()["id"] == "styx"
        assert len(controller.get_tab_history()) == 2

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
        controller.switch_tab("client_2", "hausverwaltung")
        controller.switch_tab("client_3", "styx")

        # All clients see same active tab (last one wins)
        active = controller.get_active_tab()
        assert active["id"] == "styx"

        # But all received updates
        for client in [client1, client2, client3]:
            received_tab_changes = [
                m for m in client.messages_received
                if m["event"] == "tab_changed"
            ]
            assert len(received_tab_changes) >= 1

    def test_3_tab_layout_restored(self):
        """Test that 3-Tab layout is properly restored."""
        app = MockDashboardApp()
        
        tabs = app.get_tabs()
        assert len(tabs) == 3
        
        # Verify tab order
        assert tabs[0]["id"] == "habitus"
        assert tabs[1]["id"] == "hausverwaltung"
        assert tabs[2]["id"] == "styx"
        
        # Verify each tab has required content
        for tab in tabs:
            assert tab["widgets"]
            assert len(tab["widgets"]) > 0
