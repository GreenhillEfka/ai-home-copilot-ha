"""Pytest configuration for PilotSuite Styx tests."""

import sys
import os
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "custom_components" / "copilot_ha"))

# Configure test fixtures
pytest_plugins = []

# Pytest configuration
def pytest_configure(config):
    """Configure pytest settings."""
    config.addinivalue_line(
        "markers", "e2e: end-to-end integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: integration tests"
    )
    config.addinivalue_line(
        "markers", "visual: visual regression tests"
    )
