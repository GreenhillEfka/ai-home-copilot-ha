"""Tests for services integration (PS-153).

Tests:
- Unified status service
- Refresh service
- Insights service
- Contract validation
- Multi-service integration
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from custom_components.copilot_ha.services_integration import (
    async_setup_pilotsuite_services,
    async_validate_all_contracts,
)


@pytest.mark.asyncio
async def test_setup_pilotsuite_services_registers_handlers():
    """Test setting up all PilotSuite services."""
    hass = MagicMock()
    hass.services = MagicMock()
    hass.services.async_register = MagicMock()
    hass.config_entries = MagicMock()
    hass.config_entries.async_entries = MagicMock(return_value=[])
    
    with patch("custom_components.copilot_ha.services_integration.async_setup_zone_health_services"):
        await async_setup_pilotsuite_services(hass)
    
    # Should register at least 3 unified services + health services
    assert hass.services.async_register.call_count >= 3


@pytest.mark.asyncio
async def test_validate_all_contracts_success():
    """Test contract validation returns success."""
    hass = MagicMock()
    
    mock_result = {
        "success": True,
        "core_openapi": {"valid": True, "message": "PASS"},
        "ha_openapi": {"valid": True, "message": "PASS"},
        "drift_check": {"valid": True, "message": "PASS"},
        "runtime": {"valid": True, "message": "PASS"},
    }
    
    with patch("custom_components.copilot_ha.contract_validation.async_validate_contracts", return_value=mock_result):
        result = await async_validate_all_contracts(hass)
    
    assert result["success"] is True
    assert result["core_openapi"]["valid"] is True
    assert result["ha_openapi"]["valid"] is True
    assert result["drift_check"]["valid"] is True
    assert result["runtime"]["valid"] is True


@pytest.mark.asyncio
async def test_validate_all_contracts_failure():
    """Test contract validation detects failures."""
    hass = MagicMock()
    
    mock_result = {
        "success": False,
        "core_openapi": {"valid": False, "message": "FAIL"},
        "ha_openapi": {"valid": True, "message": "PASS"},
        "drift_check": {"valid": True, "message": "PASS"},
        "runtime": {"valid": True, "message": "PASS"},
    }
    
    with patch("custom_components.copilot_ha.contract_validation.async_validate_contracts", return_value=mock_result):
        result = await async_validate_all_contracts(hass)
    
    assert result["success"] is False
    assert result["core_openapi"]["valid"] is False
