"""
Integration Test: System Health & Monitoring
Tests health checks, metrics collection, and alerting.
"""
import pytest
from datetime import datetime, timedelta


class TestSystemHealthIntegration:
    """Integration tests for system health monitoring."""
    
    def test_health_check_endpoint(self, test_client, valid_auth_token):
        """Test system health check endpoint."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        response = test_client.get('/api/health', headers=headers)
        assert response.status_code == 200
        
        health_data = response.get_json()
        assert 'status' in health_data
        assert 'timestamp' in health_data
        assert 'services' in health_data
    
    def test_component_health_status(self, test_client, valid_auth_token):
        """Test individual component health status."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        response = test_client.get('/api/health/components', headers=headers)
        assert response.status_code == 200
        
        components = response.get_json()
        assert isinstance(components, list)
        
        for component in components:
            assert 'name' in component
            assert 'status' in component
            assert 'last_check' in component
    
    def test_database_connectivity(self, test_client, valid_auth_token):
        """Test database connectivity health check."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        response = test_client.get('/api/health/database', headers=headers)
        assert response.status_code == 200
        
        db_health = response.get_json()
        assert 'connected' in db_health
        assert 'latency_ms' in db_health
    
    def test_external_service_health(self, test_client, valid_auth_token):
        """Test external service health checks."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        response = test_client.get('/api/health/external', headers=headers)
        assert response.status_code == 200
        
        external_services = response.get_json()
        assert isinstance(external_services, list)
        
        for service in external_services:
            assert 'name' in service
            assert 'reachable' in service
            assert 'response_time' in service


class TestMetricsIntegration:
    """Integration tests for metrics collection."""
    
    def test_metrics_endpoint(self, test_client, valid_auth_token):
        """Test metrics endpoint."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        response = test_client.get('/api/metrics', headers=headers)
        assert response.status_code == 200
        
        metrics = response.get_json()
        assert 'cpu_usage' in metrics
        assert 'memory_usage' in metrics
        assert 'disk_usage' in metrics
    
    def test_custom_metrics(self, test_client, valid_auth_token):
        """Test custom metrics collection."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        # Record custom metric
        record_response = test_client.post('/api/metrics/custom', json={
            'name': 'test_metric',
            'value': 42.0,
            'labels': {'environment': 'test'}
        }, headers=headers)
        assert record_response.status_code == 201
        
        # Query custom metric
        query_response = test_client.get('/api/metrics/custom?name=test_metric', headers=headers)
        assert query_response.status_code == 200
        
        metrics = query_response.get_json()
        assert len(metrics) > 0
    
    def test_metrics_aggregation(self, test_client, valid_auth_token):
        """Test metrics aggregation over time windows."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        # Get aggregated metrics
        response = test_client.get('/api/metrics/aggregate?window=1h', headers=headers)
        assert response.status_code == 200
        
        aggregated = response.get_json()
        assert 'avg' in aggregated
        assert 'min' in aggregated
        assert 'max' in aggregated


class TestAlertingIntegration:
    """Integration tests for alerting system."""
    
    def test_alert_creation(self, test_client, valid_auth_token):
        """Test creating system alerts."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        response = test_client.post('/api/alerts', json={
            'title': 'Test Alert',
            'message': 'Integration test alert',
            'severity': 'warning',
            'source': 'test_suite'
        }, headers=headers)
        assert response.status_code == 201
        
        alert_id = response.get_json()['alert_id']
        assert alert_id is not None
    
    def test_alert_rules(self, test_client, valid_auth_token):
        """Test alert rule management."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        # Create alert rule
        rule_response = test_client.post('/api/alerts/rules', json={
            'name': 'High CPU Rule',
            'condition': {
                'metric': 'cpu_usage',
                'operator': '>',
                'threshold': 80
            },
            'actions': [
                {
                    'type': 'notification',
                    'channel': 'push'
                }
            ]
        }, headers=headers)
        assert rule_response.status_code == 201
        
        # Get rules
        rules_response = test_client.get('/api/alerts/rules', headers=headers)
        assert rules_response.status_code == 200
        
        rules = rules_response.get_json()
        assert len(rules) > 0
    
    def test_alert_history(self, test_client, valid_auth_token):
        """Test alert history retrieval."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        # Get alert history
        history_response = test_client.get('/api/alerts/history?limit=10', headers=headers)
        assert history_response.status_code == 200
        
        history = history_response.get_json()
        assert isinstance(history, list)


class TestLoggingIntegration:
    """Integration tests for logging system."""
    
    def test_log_query(self, test_client, valid_auth_token):
        """Test log querying."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        response = test_client.get('/api/logs?level=info&limit=10', headers=headers)
        assert response.status_code == 200
        
        logs = response.get_json()
        assert isinstance(logs, list)
        
        if len(logs) > 0:
            log = logs[0]
            assert 'timestamp' in log
            assert 'level' in log
            assert 'message' in log
    
    def test_log_export(self, test_client, valid_auth_token):
        """Test log export functionality."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        export_response = test_client.post('/api/logs/export', json={
            'format': 'json',
            'time_range': {
                'start': (datetime.now() - timedelta(hours=1)).isoformat(),
                'end': datetime.now().isoformat()
            }
        }, headers=headers)
        assert export_response.status_code == 200
        
        export_data = export_response.get_json()
        assert 'export_id' in export_data
        assert 'download_url' in export_data


class TestPerformanceIntegration:
    """Integration tests for performance monitoring."""
    
    def test_response_time_tracking(self, test_client, valid_auth_token):
        """Test API response time tracking."""
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        # Make several requests
        response_times = []
        for i in range(5):
            start = datetime.now()
            test_client.get('/api/status', headers=headers)
            elapsed = (datetime.now() - start).total_seconds() * 1000
            response_times.append(elapsed)
        
        # Check response times are acceptable
        avg_time = sum(response_times) / len(response_times)
        assert avg_time < 1000, f"Average response time {avg_time}ms too slow"
    
    def test_concurrent_request_handling(self, test_client, valid_auth_token):
        """Test handling concurrent requests."""
        import concurrent.futures
        
        headers = {'Authorization': f"Bearer {valid_auth_token}"}
        
        def make_request():
            return test_client.get('/api/status', headers=headers)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [f.result() for f in futures]
        
        # All requests should succeed
        success_count = sum(1 for r in results if r.status_code == 200)
        assert success_count >= 18, f"Too many failures: {20 - success_count}"
