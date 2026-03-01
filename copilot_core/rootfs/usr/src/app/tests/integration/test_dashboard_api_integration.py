"""
Integration Test: Dashboard API Endpoints
Tests dashboard data aggregation and real-time updates.
"""
import pytest
from datetime import datetime, timedelta


class TestDashboardIntegration:
    """Integration tests for dashboard functionality."""
    
    def test_dashboard_data_aggregation(self, test_client, valid_auth_token):
        """Test dashboard aggregates data from multiple sources."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        response = test_client.get('/api/dashboard/summary', headers=headers)
        assert response.status_code == 200
        
        dashboard_data = response.get_json()
        assert 'energy' in dashboard_data
        assert 'comfort' in dashboard_data
        assert 'notifications' in dashboard_data
        assert 'active_automations' in dashboard_data
    
    def test_dashboard_real_time_updates(self, test_client, valid_auth_token, websocket_client):
        """Test dashboard receives real-time updates via WebSocket."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        # Connect to WebSocket
        ws = websocket_client.connect('/ws/dashboard', headers=headers)
        
        # Trigger an event
        test_client.post('/api/events/test', json={
            'type': 'temperature_change',
            'value': 22.5
        }, headers=headers)
        
        # Should receive update
        message = ws.receive(timeout=5.0)
        assert message is not None
        assert 'temperature_change' in message
    
    def test_dashboard_zone_data(self, test_client, valid_auth_token):
        """Test dashboard zone-specific data."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        response = test_client.get('/api/dashboard/zones', headers=headers)
        assert response.status_code == 200
        
        zones_data = response.get_json()
        assert isinstance(zones_data, list)
        assert len(zones_data) > 0
        
        for zone in zones_data:
            assert 'zone_id' in zone
            assert 'name' in zone
            assert 'temperature' in zone
            assert 'humidity' in zone
    
    def test_dashboard_energy_metrics(self, test_client, valid_auth_token):
        """Test dashboard energy metrics calculation."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        response = test_client.get('/api/dashboard/energy', headers=headers)
        assert response.status_code == 200
        
        energy_data = response.get_json()
        assert 'current_consumption' in energy_data
        assert 'daily_total' in energy_data
        assert 'cost_estimate' in energy_data
        assert 'trend' in energy_data
    
    def test_dashboard_notifications_feed(self, test_client, valid_auth_token):
        """Test dashboard notifications feed."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        # Create a test notification
        test_client.post('/api/notifications', json={
            'title': 'Test Notification',
            'message': 'Integration test notification',
            'priority': 'normal'
        }, headers=headers)
        
        # Get notifications feed
        response = test_client.get('/api/dashboard/notifications', headers=headers)
        assert response.status_code == 200
        
        notifications = response.get_json()
        assert isinstance(notifications, list)
        assert len(notifications) > 0
        
        latest = notifications[0]
        assert latest['title'] == 'Test Notification'


class TestDashboardPerformanceIntegration:
    """Integration tests for dashboard performance."""
    
    def test_dashboard_response_time(self, test_client, valid_auth_token):
        """Test dashboard response time is acceptable."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        start_time = datetime.now()
        response = test_client.get('/api/dashboard/summary', headers=headers)
        elapsed = datetime.now() - start_time
        
        assert response.status_code == 200
        assert elapsed.total_seconds() < 2.0, "Dashboard response too slow"
    
    def test_dashboard_concurrent_requests(self, test_client, valid_auth_token):
        """Test dashboard handles concurrent requests."""
        import concurrent.futures
        
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        def fetch_dashboard():
            return test_client.get('/api/dashboard/summary', headers=headers)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(fetch_dashboard) for _ in range(10)]
            results = [f.result() for f in futures]
        
        # All requests should succeed
        assert all(r.status_code == 200 for r in results)
