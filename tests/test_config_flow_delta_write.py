"""Tests for config flow delta-write pattern implementation."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from homeassistant.config_entries import ConfigEntry
from custom_components.copilot_ha.config_snapshot import async_apply_config_snapshot


class TestConfigFlowDeltaWrite:
    """Test delta-write pattern in config flow."""

    @patch('custom_components.copilot_ha.config_snapshot.async_set_zones_v2_from_raw')
    @patch('homeassistant.config_entries.ConfigEntries.async_update_entry')
    async def test_delta_write_only_updates_changed_options(self, mock_update_entry, mock_set_zones):
        """Test that delta-write only updates options when they actually change."""
        # Mock HA components
        hass = MagicMock()
        entry = MagicMock(spec=ConfigEntry)
        entry.entry_id = "test_entry"
        entry.options = {"existing_option": "value1", "unchanged_option": "keep_me"}
        entry.data = {"host": "localhost", "port": 8080}

        # Snapshot with only some fields changed
        snapshot = {
            "options": {
                "existing_option": "value1",  # unchanged
                "new_option": "value2",       # new
                "unchanged_option": "keep_me" # unchanged
            },
            "data": {
                "host": "localhost",   # unchanged
                "port": 9090,          # changed
            },
            "habitus_zones": []  # empty zones
        }

        # Apply snapshot
        await async_apply_config_snapshot(hass, entry, snapshot)

        # Verify zones were set
        mock_set_zones.assert_called_once_with(hass, "test_entry", [])

        # Verify config entry was updated twice (once for options, once for data)
        assert mock_update_entry.call_count == 2
        
        # Check first call (options update)
        first_call_args = mock_update_entry.call_args_list[0]
        assert first_call_args[0][0] == entry
        assert first_call_args[1]['options'] == {
            "existing_option": "value1",
            "new_option": "value2",
            "unchanged_option": "keep_me"
        }

        # Check second call (data update)
        second_call_args = mock_update_entry.call_args_list[1]
        assert second_call_args[0][0] == entry
        assert second_call_args[1]['data'] == {
            "host": "localhost",
            "port": 9090
        }

    @patch('custom_components.copilot_ha.config_snapshot.async_set_zones_v2_from_raw')
    @patch('homeassistant.config_entries.ConfigEntries.async_update_entry')
    async def test_delta_write_skips_identical_updates(self, mock_update_entry, mock_set_zones):
        """Test that delta-write skips updates when no changes exist."""
        # Mock HA components
        hass = MagicMock()
        entry = MagicMock(spec=ConfigEntry)
        entry.entry_id = "test_entry"
        entry.options = {"existing_option": "value1", "unchanged_option": "keep_me"}
        entry.data = {"host": "localhost", "port": 8080}

        # Snapshot with identical values
        snapshot = {
            "options": {
                "existing_option": "value1",  # unchanged
                "unchanged_option": "keep_me" # unchanged
            },
            "data": {
                "host": "localhost",   # unchanged
                "port": 8080,          # unchanged
            },
            "habitus_zones": []  # empty zones
        }

        # Apply snapshot
        await async_apply_config_snapshot(hass, entry, snapshot)

        # Verify zones were set
        mock_set_zones.assert_called_once_with(hass, "test_entry", [])

        # Verify config entry was NOT updated since nothing changed
        assert mock_update_entry.call_count == 0

    @patch('custom_components.copilot_ha.config_snapshot.async_set_zones_v2_from_raw')
    @patch('homeassistant.config_entries.ConfigEntries.async_update_entry')
    async def test_delta_write_handles_redacted_values(self, mock_update_entry, mock_set_zones):
        """Test that delta-write preserves existing secrets when snapshot has redacted values."""
        # Mock HA components
        hass = MagicMock()
        entry = MagicMock(spec=ConfigEntry)
        entry.entry_id = "test_entry"
        entry.options = {"token": "secret123", "host": "localhost"}
        entry.data = {"username": "user", "password": "pass123"}

        # Snapshot with redacted values
        snapshot = {
            "options": {
                "token": "<redacted>",  # should preserve existing
                "host": "newhost"       # should update
            },
            "data": {
                "username": "user",     # unchanged
                "password": "<redacted>" # should preserve existing
            },
            "habitus_zones": []
        }

        # Apply snapshot
        await async_apply_config_snapshot(hass, entry, snapshot)

        # Verify zones were set
        mock_set_zones.assert_called_once_with(hass, "test_entry", [])

        # Verify config entry was updated with preserved secrets
        assert mock_update_entry.call_count == 2
        
        # Check options update
        first_call_args = mock_update_entry.call_args_list[0]
        assert first_call_args[1]['options'] == {
            "token": "secret123",  # preserved
            "host": "newhost"      # updated
        }

        # Check data update
        second_call_args = mock_update_entry.call_args_list[1]
        assert second_call_args[1]['data'] == {
            "username": "user",    # unchanged
            "password": "pass123"  # preserved
        }