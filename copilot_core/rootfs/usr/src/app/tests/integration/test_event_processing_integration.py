"""
Integration Test: Event Processing Pipeline
Tests event ingestion, processing, and storage.
"""
import pytest
from datetime import datetime, timedelta
import time


class TestEventProcessingIntegration:
    """Integration tests for event processing."""
    
    def test_event_ingestion_pipeline(self, test_client, valid_auth_token):
        """Test complete event ingestion pipeline."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        # Submit event
        event_data = {
            'type': 'temperature_reading',
            'source': 'sensor.living_room',
            'data': {
                'temperature': 22.5,
                'humidity': 45.0,
                'timestamp': datetime.now().isoformat()
            }
        }
        
        response = test_client.post('/api/events/ingest', json=event_data, headers=headers)
        assert response.status_code == 201
        
        event_id = response.get_json()['event_id']
        assert event_id is not None
        
        # Verify event stored
        get_response = test_client.get(f'/api/events/{event_id}', headers=headers)
        assert get_response.status_code == 200
        assert get_response.get_json()['type'] == 'temperature_reading'
    
    def test_event_batch_processing(self, test_client, valid_auth_token):
        """Test batch event processing."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        # Submit batch of events
        batch_events = [
            {
                'type': 'temperature_reading',
                'source': 'sensor.zone_1',
                'data': {'temperature': 21.0}
            },
            {
                'type': 'temperature_reading',
                'source': 'sensor.zone_2',
                'data': {'temperature': 22.0}
            },
            {
                'type': 'temperature_reading',
                'source': 'sensor.zone_3',
                'data': {'temperature': 23.0}
            }
        ]
        
        response = test_client.post('/api/events/batch', json={'events': batch_events}, headers=headers)
        assert response.status_code == 201
        
        result = response.get_json()
        assert result['processed'] == 3
        assert len(result['event_ids']) == 3
    
    def test_event_filtering_and_query(self, test_client, valid_auth_token):
        """Test event filtering and querying."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        # Create test events
        for i in range(5):
            test_client.post('/api/events/ingest', json={
                'type': 'test_event',
                'source': f'sensor_{i}',
                'data': {'value': i}
            }, headers=headers)
        
        # Query events with filter
        response = test_client.get('/api/events?source=sensor_2', headers=headers)
        assert response.status_code == 200
        
        events = response.get_json()
        assert len(events) > 0
        assert all(e['source'] == 'sensor_2' for e in events)
    
    def test_event_aggregation(self, test_client, valid_auth_token):
        """Test event aggregation over time windows."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        # Submit multiple temperature events
        for i in range(10):
            test_client.post('/api/events/ingest', json={
                'type': 'temperature_reading',
                'source': 'sensor.main',
                'data': {'temperature': 20.0 + i * 0.5}
            }, headers=headers)
        
        # Get aggregated data
        response = test_client.get('/api/events/aggregate?window=1h&metric=temperature', headers=headers)
        assert response.status_code == 200
        
        aggregation = response.get_json()
        assert 'avg' in aggregation
        assert 'min' in aggregation
        assert 'max' in aggregation
        assert 'count' in aggregation
    
    def test_event_webhook_delivery(self, test_client, valid_auth_token):
        """Test event webhook delivery to external endpoints."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        # Register webhook
        webhook_response = test_client.post('/api/webhooks', json={
            'url': 'http://localhost:8080/webhook',
            'event_types': ['temperature_reading', 'motion_detected'],
            'active': True
        }, headers=headers)
        assert webhook_response.status_code == 201
        
        webhook_id = webhook_response.get_json()['webhook_id']
        
        # Trigger event
        test_client.post('/api/events/ingest', json={
            'type': 'temperature_reading',
            'source': 'sensor.test',
            'data': {'temperature': 25.0}
        }, headers=headers)
        
        # Verify webhook delivery (check logs or delivery status)
        delivery_response = test_client.get(f'/api/webhooks/{webhook_id}/deliveries', headers=headers)
        assert delivery_response.status_code == 200
    
    def test_event_retention_policy(self, test_client, valid_auth_token):
        """Test event retention policy enforcement."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        # Submit old event (simulate)
        old_timestamp = datetime.now() - timedelta(days=31)
        test_client.post('/api/events/ingest', json={
            'type': 'old_event',
            'source': 'sensor.test',
            'data': {'value': 1},
            'timestamp': old_timestamp.isoformat()
        }, headers=headers)
        
        # Run retention cleanup
        cleanup_response = test_client.post('/api/events/cleanup', json={
            'retention_days': 30
        }, headers=headers)
        assert cleanup_response.status_code == 200
        
        # Verify old events removed
        result = cleanup_response.get_json()
        assert 'deleted_count' in result


class TestEventStreamIntegration:
    """Integration tests for event streaming."""
    
    def test_event_stream_subscription(self, test_client, valid_auth_token, websocket_client):
        """Test subscribing to event stream."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        # Connect to event stream
        ws = websocket_client.connect('/ws/events', headers=headers)
        
        # Publish event
        test_client.post('/api/events/ingest', json={
            'type': 'stream_test',
            'source': 'test_source',
            'data': {'message': 'Hello stream'}
        }, headers=headers)
        
        # Should receive event
        message = ws.receive(timeout=5.0)
        assert message is not None
        assert message['type'] == 'stream_test'
    
    def test_event_stream_filtering(self, test_client, valid_auth_token, websocket_client):
        """Test event stream with filters."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        # Connect with filter
        ws = websocket_client.connect('/ws/events?filter=temperature', headers=headers)
        
        # Publish different event types
        test_client.post('/api/events/ingest', json={
            'type': 'temperature_reading',
            'source': 'sensor.test',
            'data': {'value': 22.0}
        }, headers=headers)
        
        test_client.post('/api/events/ingest', json={
            'type': 'motion_detected',
            'source': 'sensor.test',
            'data': {}
        }, headers=headers)
        
        # Should only receive temperature event
        message = ws.receive(timeout=5.0)
        assert message is not None
        assert message['type'] == 'temperature_reading'
