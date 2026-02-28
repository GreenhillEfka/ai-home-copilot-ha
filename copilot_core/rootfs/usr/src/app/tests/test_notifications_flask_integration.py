"""Flask Integration Tests for Notifications API Endpoints.

Tests the Flask blueprint endpoints for the notification system.
Requires Flask to be installed.
"""

import pytest

try:
    from flask import Flask
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    Flask = None

# Import notification components
try:
    from copilot_core.api.v1.notifications import (
        bp as notifications_bp,
        get_notification_manager,
        NotificationManager,
    )
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False
    notifications_bp = None

# Import security mock for testing
try:
    from unittest.mock import patch
except ImportError:
    patch = None


@pytest.fixture
def notification_manager():
    """Create a fresh notification manager for testing."""
    if not NOTIFICATIONS_AVAILABLE:
        pytest.skip("Notifications module not available")
    
    # Reset singleton
    import copilot_core.api.v1.notifications as notifications_module
    notifications_module._notification_manager = NotificationManager()
    return get_notification_manager()


@pytest.fixture
def test_app(notification_manager):
    """Create test Flask app with notifications blueprint."""
    if not FLASK_AVAILABLE:
        pytest.skip("Flask not installed")
    if not NOTIFICATIONS_AVAILABLE:
        pytest.skip("Notifications module not available")
    
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(notifications_bp)
    return app


@pytest.fixture
def client(test_app):
    """Create test client."""
    return test_app.test_client()


@pytest.mark.skipif(not FLASK_AVAILABLE, reason="Flask not installed")
@pytest.mark.skipif(not NOTIFICATIONS_AVAILABLE, reason="Notifications not available")
class TestNotificationsFlaskIntegration:
    """Test Flask integration for notifications API."""
    
    def test_send_notification_success(self, client, notification_manager, monkeypatch):
        """Test sending a notification successfully."""
        # Mock the token validation
        monkeypatch.setattr(
            'copilot_core.api.v1.notifications._validate_token',
            lambda request: True
        )
        
        response = client.post('/notifications/send', json={
            'title': 'Test Notification',
            'message': 'This is a test message',
            'priority': 'normal',
            'type': 'info'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'notification_id' in data['data']
    
    def test_send_notification_missing_title(self, client, monkeypatch):
        """Test sending notification without title fails."""
        monkeypatch.setattr(
            'copilot_core.api.v1.notifications._validate_token',
            lambda request: True
        )
        
        response = client.post('/notifications/send', json={
            'message': 'Missing title'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'Missing required field: title' in data['error']
    
    def test_send_notification_missing_message(self, client, monkeypatch):
        """Test sending notification without message fails."""
        monkeypatch.setattr(
            'copilot_core.api.v1.notifications._validate_token',
            lambda request: True
        )
        
        response = client.post('/notifications/send', json={
            'title': 'Missing message'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'Missing required field: message' in data['error']
    
    def test_send_notification_empty_body(self, client, monkeypatch):
        """Test sending notification with empty body fails."""
        monkeypatch.setattr(
            'copilot_core.api.v1.notifications._validate_token',
            lambda request: True
        )
        
        response = client.post('/notifications/send', json={})
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_get_notifications_empty(self, client, monkeypatch):
        """Test getting notifications when none exist."""
        monkeypatch.setattr(
            'copilot_core.api.v1.notifications._validate_token',
            lambda request: True
        )
        
        response = client.get('/notifications')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['notifications'] == []
        assert data['data']['unread_count'] == 0
        assert data['data']['total_count'] == 0
    
    def test_get_notifications_with_data(self, client, notification_manager, monkeypatch):
        """Test getting notifications with existing data."""
        monkeypatch.setattr(
            'copilot_core.api.v1.notifications._validate_token',
            lambda request: True
        )
        
        # Clear existing notifications first
        notification_manager.clear_notifications()
        
        # Create some notifications
        notification_manager.create_notification(
            title='Test 1',
            message='Message 1',
            type='info'
        )
        notification_manager.create_notification(
            title='Test 2',
            message='Message 2',
            type='alert'
        )
        
        response = client.get('/notifications')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['total_count'] == 2
        assert len(data['data']['notifications']) == 2
    
    def test_get_notifications_unread_only(self, client, notification_manager, monkeypatch):
        """Test getting only unread notifications."""
        monkeypatch.setattr(
            'copilot_core.api.v1.notifications._validate_token',
            lambda request: True
        )
        
        # Clear existing notifications first
        notification_manager.clear_notifications()
        
        # Create and mark one as read
        n1 = notification_manager.create_notification(title='Unread', message='Test')
        n2 = notification_manager.create_notification(title='Read', message='Test')
        notification_manager.mark_as_read(n2.id)
        
        response = client.get('/notifications?unread_only=true')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['data']['unread_count'] == 1
        assert len(data['data']['notifications']) == 1
    
    def test_get_notifications_by_type(self, client, notification_manager, monkeypatch):
        """Test filtering notifications by type."""
        monkeypatch.setattr(
            'copilot_core.api.v1.notifications._validate_token',
            lambda request: True
        )
        
        notification_manager.clear_notifications()
        notification_manager.create_notification(title='Info', message='Test', type='info')
        notification_manager.create_notification(title='Alert', message='Test', type='alert')
        notification_manager.create_notification(title='Info 2', message='Test', type='info')
        
        response = client.get('/notifications?type=info')
        
        assert response.status_code == 200
        data = response.get_json()
        # Filter returns only 'info' type notifications
        assert len(data['data']['notifications']) == 2
        assert all(n['type'] == 'info' for n in data['data']['notifications'])
    
    def test_mark_notification_read(self, client, notification_manager, monkeypatch):
        """Test marking a notification as read."""
        monkeypatch.setattr(
            'copilot_core.api.v1.notifications._validate_token',
            lambda request: True
        )
        
        notification = notification_manager.create_notification(
            title='Test',
            message='Message'
        )
        
        response = client.post(f'/notifications/{notification.id}/read')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['notification_id'] == notification.id
        
        # Verify it's marked as read
        assert notification.read is True
    
    def test_mark_notification_read_not_found(self, client, monkeypatch):
        """Test marking non-existent notification as read."""
        monkeypatch.setattr(
            'copilot_core.api.v1.notifications._validate_token',
            lambda request: True
        )
        
        response = client.post('/notifications/non-existent-id/read')
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
    
    def test_dismiss_notification(self, client, notification_manager, monkeypatch):
        """Test dismissing a notification."""
        monkeypatch.setattr(
            'copilot_core.api.v1.notifications._validate_token',
            lambda request: True
        )
        
        notification = notification_manager.create_notification(
            title='Test',
            message='Message'
        )
        
        response = client.delete(f'/notifications/{notification.id}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        
        # Verify it's dismissed
        assert notification.dismissed is True
    
    def test_dismiss_notification_not_found(self, client, monkeypatch):
        """Test dismissing non-existent notification."""
        monkeypatch.setattr(
            'copilot_core.api.v1.notifications._validate_token',
            lambda request: True
        )
        
        response = client.delete('/notifications/non-existent-id')
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
    
    def test_clear_notifications(self, client, notification_manager, monkeypatch):
        """Test clearing all notifications."""
        monkeypatch.setattr(
            'copilot_core.api.v1.notifications._validate_token',
            lambda request: True
        )
        
        notification_manager.create_notification(title='Test 1', message='Message')
        notification_manager.create_notification(title='Test 2', message='Message')
        notification_manager.create_notification(title='Test 3', message='Message')
        
        response = client.post('/notifications/clear')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['cleared_count'] == 3
    
    def test_clear_notifications_by_type(self, client, notification_manager, monkeypatch):
        """Test clearing notifications by type."""
        monkeypatch.setattr(
            'copilot_core.api.v1.notifications._validate_token',
            lambda request: True
        )
        
        notification_manager.create_notification(title='Info 1', message='Test', type='info')
        notification_manager.create_notification(title='Alert 1', message='Test', type='alert')
        notification_manager.create_notification(title='Info 2', message='Test', type='info')
        
        response = client.post('/notifications/clear', json={'type': 'info'})
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['cleared_count'] == 2
    
    def test_subscribe_device(self, client, monkeypatch):
        """Test subscribing a device."""
        monkeypatch.setattr(
            'copilot_core.api.v1.notifications._validate_token',
            lambda request: True
        )
        
        response = client.post('/notifications/subscribe', json={
            'device_id': 'test-device-123',
            'device_name': 'Test Phone',
            'device_type': 'mobile',
            'push_token': 'abc123token',
            'preferences': {
                'notify_mood': True,
                'notify_alerts': True,
                'notify_suggestions': False,
                'notify_system': False
            }
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['device_id'] == 'test-device-123'
        assert data['data']['device_name'] == 'Test Phone'
    
    def test_subscribe_device_missing_id(self, client, monkeypatch):
        """Test subscribing device without device_id fails."""
        monkeypatch.setattr(
            'copilot_core.api.v1.notifications._validate_token',
            lambda request: True
        )
        
        response = client.post('/notifications/subscribe', json={
            'device_name': 'Test Phone'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_unsubscribe_device(self, client, notification_manager, monkeypatch):
        """Test unsubscribing a device."""
        monkeypatch.setattr(
            'copilot_core.api.v1.notifications._validate_token',
            lambda request: True
        )
        
        # First subscribe
        notification_manager.subscribe_device(
            device_id='test-device-456',
            device_name='Test Device'
        )
        
        response = client.post('/notifications/unsubscribe', json={
            'device_id': 'test-device-456'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
    
    def test_unsubscribe_device_not_found(self, client, monkeypatch):
        """Test unsubscribing non-existent device."""
        monkeypatch.setattr(
            'copilot_core.api.v1.notifications._validate_token',
            lambda request: True
        )
        
        response = client.post('/notifications/unsubscribe', json={
            'device_id': 'non-existent-device'
        })
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
    
    def test_get_subscriptions(self, client, notification_manager, monkeypatch):
        """Test getting all subscriptions."""
        monkeypatch.setattr(
            'copilot_core.api.v1.notifications._validate_token',
            lambda request: True
        )
        
        notification_manager.subscribe_device('device-1', 'Device 1')
        notification_manager.subscribe_device('device-2', 'Device 2')
        
        response = client.get('/notifications/subscriptions')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['count'] == 2
    
    def test_update_subscription(self, client, notification_manager, monkeypatch):
        """Test updating subscription preferences."""
        monkeypatch.setattr(
            'copilot_core.api.v1.notifications._validate_token',
            lambda request: True
        )
        
        # First subscribe
        notification_manager.subscribe_device(
            device_id='device-update-test',
            device_name='Test Device',
            preferences={'notify_mood': True, 'notify_alerts': True}
        )
        
        response = client.put('/notifications/subscriptions/device-update-test', json={
            'enabled': False,
            'preferences': {
                'notify_mood': False,
                'notify_alerts': True
            }
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['enabled'] is False
    
    def test_update_subscription_not_found(self, client, monkeypatch):
        """Test updating non-existent subscription."""
        monkeypatch.setattr(
            'copilot_core.api.v1.notifications._validate_token',
            lambda request: True
        )
        
        response = client.put('/notifications/subscriptions/non-existent-device', json={
            'enabled': True
        })
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
    
    def test_auth_required(self, client, monkeypatch):
        """Test that authentication is required."""
        monkeypatch.setattr(
            'copilot_core.api.v1.notifications._validate_token',
            lambda request: False
        )
        
        response = client.get('/notifications')
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['error'] == 'unauthorized'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
