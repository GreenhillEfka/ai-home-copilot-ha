"""
Dashboard Configuration for PilotSuite Styx
"""
import os

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    
    # Server settings
    HOST = '0.0.0.0'
    PORT = 8766
    
    # WebSocket settings (prep for live updates)
    WebSocket_ENABLED = True
    WebSocket_PORT = 8767
    
    # API endpoints
    RAG_API_URL = os.environ.get('RAG_API_URL', 'http://localhost:8765')
    CORE_API_URL = os.environ.get('CORE_API_URL', 'http://localhost:8909')
    CORE_AUTH_TOKEN = os.environ.get('COPILOT_AUTH_TOKEN', '')
    
    # Dashboard settings
    DASHBOARD_TITLE = 'PilotSuite Styx Dashboard'
    REFRESH_INTERVAL = 30  # seconds
    
    # Feature flags
    DEBUG_MODE = os.environ.get('DEBUG_MODE', 'false').lower() == 'true'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

# Config mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
