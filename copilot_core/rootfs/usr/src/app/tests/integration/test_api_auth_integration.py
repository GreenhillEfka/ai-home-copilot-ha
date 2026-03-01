"""
Integration Test: API Authentication & Security
Tests authentication flows, token validation, and security middleware.
"""
import pytest
import time
from datetime import datetime, timedelta


class TestAuthIntegration:
    """Integration tests for authentication system."""
    
    def test_auth_token_lifecycle(self, test_client, valid_auth_token):
        """Test complete auth token lifecycle: creation, validation, expiration."""
        # Create token
        create_response = test_client.post('/api/auth/token', json={
            'username': 'test_user',
            'password': 'test_password'
        })
        assert create_response.status_code == 200
        token_data = create_response.get_json()
        assert 'access_token' in token_data
        
        # Validate token
        headers = {'Authorization': f"Bearer {token_data['access_token']}"}
        validate_response = test_client.get('/api/auth/validate', headers=headers)
        assert validate_response.status_code == 200
        
        # Test token expiration
        time.sleep(65)  # Wait for token to expire (60s TTL)
        expired_response = test_client.get('/api/auth/validate', headers=headers)
        assert expired_response.status_code == 401
    
    def test_auth_middleware_protected_routes(self, test_client):
        """Test that protected routes require authentication."""
        protected_routes = [
            '/api/dashboard/status',
            '/api/automation/list',
            '/api/events/recent'
        ]
        
        for route in protected_routes:
            response = test_client.get(route)
            assert response.status_code in [401, 403], f"Route {route} should require auth"
    
    def test_multi_auth_method_support(self, test_client, valid_auth_token):
        """Test support for multiple authentication methods."""
        # Test Bearer token
        bearer_headers = {'Authorization': f"Bearer {valid_auth_token}"}
        bearer_response = test_client.get('/api/auth/validate', headers=bearer_headers)
        assert bearer_response.status_code == 200
        
        # Test X-Auth-Token header
        xauth_headers = {'X-Auth-Token': valid_auth_token}
        xauth_response = test_client.get('/api/auth/validate', headers=xauth_headers)
        assert xauth_response.status_code == 200
    
    def test_auth_rate_limiting(self, test_client):
        """Test authentication rate limiting."""
        # Make multiple failed auth attempts
        for i in range(10):
            response = test_client.post('/api/auth/token', json={
                'username': 'test_user',
                'password': 'wrong_password'
            })
        
        # Should be rate limited
        rate_limited_response = test_client.post('/api/auth/token', json={
            'username': 'test_user',
            'password': 'wrong_password'
        })
        assert rate_limited_response.status_code == 429


class TestSecurityMiddlewareIntegration:
    """Integration tests for security middleware."""
    
    def test_cors_headers(self, test_client):
        """Test CORS headers are properly set."""
        response = test_client.options('/api/auth/token', 
                                      headers={'Origin': 'http://localhost:3000'})
        assert 'Access-Control-Allow-Origin' in response.headers
    
    def test_security_headers(self, test_client):
        """Test security headers are present."""
        response = test_client.get('/api/status')
        assert response.status_code == 200
        
        # Check for common security headers
        security_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'Strict-Transport-Security'
        ]
        for header in security_headers:
            assert header in response.headers, f"Missing security header: {header}"
