"""
Integration Test: Notification System
Tests notification creation, delivery, and management.
"""
import pytest
from datetime import datetime, timedelta


class TestNotificationSystemIntegration:
    """Integration tests for notification system."""
    
    def test_notification_creation_and_delivery(self, test_client, valid_auth_token):
        """Test complete notification lifecycle."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        # Create notification
        create_response = test_client.post('/api/notifications', json={
            'title': 'Test Notification',
            'message': 'This is an integration test notification',
            'priority': 'normal',
            'channel': 'push'
        }, headers=headers)
        assert create_response.status_code == 201
        
        notification_id = create_response.get_json()['notification_id']
        
        # Get notification
        get_response = test_client.get(f'/api/notifications/{notification_id}', headers=headers)
        assert get_response.status_code == 200
        assert get_response.get_json()['title'] == 'Test Notification'
    
    def test_notification_channels(self, test_client, valid_auth_token):
        """Test notification delivery across multiple channels."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        channels = ['push', 'email', 'whatsapp', 'telegram']
        
        for channel in channels:
            response = test_client.post('/api/notifications', json={
                'title': f'Test {channel} notification',
                'message': f'Testing {channel} delivery',
                'priority': 'normal',
                'channel': channel
            }, headers=headers)
            assert response.status_code == 201
    
    def test_notification_scheduling(self, test_client, valid_auth_token):
        """Test scheduled notification delivery."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        # Schedule notification for future
        schedule_time = datetime.now() + timedelta(minutes=5)
        schedule_response = test_client.post('/api/notifications/schedule', json={
            'title': 'Scheduled Notification',
            'message': 'This should be delivered later',
            'scheduled_at': schedule_time.isoformat(),
            'channel': 'push'
        }, headers=headers)
        assert schedule_response.status_code == 201
        
        scheduled_id = schedule_response.get_json()['notification_id']
        
        # Get scheduled notification
        get_response = test_client.get(f'/api/notifications/{scheduled_id}', headers=headers)
        assert get_response.status_code == 200
        assert get_response.get_json()['status'] == 'scheduled'
    
    def test_notification_templates(self, test_client, valid_auth_token):
        """Test notification templates."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        # Get available templates
        templates_response = test_client.get('/api/notifications/templates', headers=headers)
        assert templates_response.status_code == 200
        
        templates = templates_response.get_json()
        assert len(templates) > 0
        
        # Use template
        if len(templates) > 0:
            template_id = templates[0]['id']
            use_response = test_client.post('/api/notifications/from_template', json={
                'template_id': template_id,
                'variables': {
                    'user_name': 'Test User',
                    'value': '42'
                }
            }, headers=headers)
            assert use_response.status_code == 201
    
    def test_notification_preferences(self, test_client, valid_auth_token):
        """Test user notification preferences."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        # Get preferences
        prefs_response = test_client.get('/api/notifications/preferences', headers=headers)
        assert prefs_response.status_code == 200
        
        # Update preferences
        update_response = test_client.put('/api/notifications/preferences', json={
            'channels': {
                'push': True,
                'email': False,
                'whatsapp': True
            },
            'quiet_hours': {
                'enabled': True,
                'start': '22:00',
                'end': '07:00'
            }
        }, headers=headers)
        assert update_response.status_code == 200
    
    def test_notification_batch_creation(self, test_client, valid_auth_token):
        """Test batch notification creation."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        notifications = [
            {
                'title': f'Batch Notification {i}',
                'message': f'Message {i}',
                'priority': 'normal'
            }
            for i in range(5)
        ]
        
        batch_response = test_client.post('/api/notifications/batch', json={
            'notifications': notifications
        }, headers=headers)
        assert batch_response.status_code == 201
        
        result = batch_response.get_json()
        assert result['created'] == 5
    
    def test_notification_history(self, test_client, valid_auth_token):
        """Test notification history retrieval."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        # Create some notifications
        for i in range(3):
            test_client.post('/api/notifications', json={
                'title': f'History Test {i}',
                'message': f'Message {i}',
                'priority': 'normal'
            }, headers=headers)
        
        # Get history
        history_response = test_client.get('/api/notifications/history?limit=10', headers=headers)
        assert history_response.status_code == 200
        
        history = history_response.get_json()
        assert isinstance(history, list)
        assert len(history) >= 3
    
    def test_notification_mark_as_read(self, test_client, valid_auth_token):
        """Test marking notifications as read."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        # Create notification
        create_response = test_client.post('/api/notifications', json={
            'title': 'Read Test',
            'message': 'Test marking as read',
            'priority': 'normal'
        }, headers=headers)
        notification_id = create_response.get_json()['notification_id']
        
        # Mark as read
        mark_response = test_client.put(f'/api/notifications/{notification_id}/read', headers=headers)
        assert mark_response.status_code == 200
        
        # Verify status
        get_response = test_client.get(f'/api/notifications/{notification_id}', headers=headers)
        assert get_response.get_json()['read'] is True
    
    def test_notification_unread_count(self, test_client, valid_auth_token):
        """Test unread notification count."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        # Get unread count
        count_response = test_client.get('/api/notifications/unread/count', headers=headers)
        assert count_response.status_code == 200
        
        count_data = count_response.get_json()
        assert 'count' in count_data
    
    def test_notification_categorization(self, test_client, valid_auth_token):
        """Test notification categorization and filtering."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        categories = ['alert', 'info', 'reminder', 'system']
        
        for category in categories:
            test_client.post('/api/notifications', json={
                'title': f'{category} notification',
                'message': f'Testing {category}',
                'category': category,
                'priority': 'normal'
            }, headers=headers)
        
        # Filter by category
        filter_response = test_client.get('/api/notifications?category=alert', headers=headers)
        assert filter_response.status_code == 200
        
        filtered = filter_response.get_json()
        assert all(n['category'] == 'alert' for n in filtered)


class TestNotificationIntelligenceIntegration:
    """Integration tests for intelligent notification features."""
    
    def test_notification_priority_escalation(self, test_client, valid_auth_token):
        """Test automatic priority escalation for unread notifications."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        # Create notification with low priority
        create_response = test_client.post('/api/notifications', json={
            'title': 'Escalation Test',
            'message': 'Should escalate if not read',
            'priority': 'low',
            'escalate_after_minutes': 1
        }, headers=headers)
        assert create_response.status_code == 201
    
    def test_notification_smart_grouping(self, test_client, valid_auth_token):
        """Test smart notification grouping."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        # Create similar notifications
        for i in range(5):
            test_client.post('/api/notifications', json={
                'title': 'Similar Notification',
                'message': f'Message variant {i}',
                'group_key': 'test_group'
            }, headers=headers)
        
        # Get grouped notifications
        group_response = test_client.get('/api/notifications/groups', headers=headers)
        assert group_response.status_code == 200
        
        groups = group_response.get_json()
        assert len(groups) > 0
