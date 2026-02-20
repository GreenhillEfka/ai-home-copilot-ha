"""
Tests for PilotSuite Python SDK.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock

from copilot_sdk import CoPilotClient, get_client


class TestCoPilotClient(unittest.TestCase):
    """Test cases for CoPilotClient."""

    def setUp(self):
        """Set up test fixtures."""
        self.base_url = "http://localhost:8123/api/copilot"
        self.client = CoPilotClient(base_url=self.base_url, auth_token="test-token")

    @patch("copilot_sdk.requests.Session")
    def test_init(self, mock_session):
        """Test client initialization."""
        session_instance = Mock()
        mock_session.return_value = session_instance

        client = CoPilotClient(
            base_url=self.base_url,
            auth_token="test-token",
        )

        self.assertEqual(client.base_url, self.base_url)
        self.assertEqual(client.auth_token, "test-token")
        session_instance.headers.update.assert_called()

    @patch("copilot_sdk.requests.Session")
    def test_submit_event(self, mock_session):
        """Test event submission."""
        session_instance = Mock()
        mock_session.return_value = session_instance

        response_mock = Mock()
        response_mock.raise_for_status = Mock()
        response_mock.json.return_value = {"event_id": "evt_123"}
        session_instance.request.return_value = response_mock

        result = self.client.submit_event("user_action", {"action": "light_on"})

        self.assertEqual(result, {"event_id": "evt_123"})
        session_instance.request.assert_called_once()

    def test_context_manager(self):
        """Test context manager (with statement)."""
        with patch("copilot_sdk.requests.Session") as mock_session:
            session_instance = Mock()
            mock_session.return_value = session_instance

            with CoPilotClient(base_url=self.base_url) as client:
                self.assertIsInstance(client, CoPilotClient)

            session_instance.close.assert_called_once()

    def test_get_client(self):
        """Test get_client convenience function."""
        with patch("copilot_sdk.CoPilotClient") as mock_client:
            get_client()
            mock_client.assert_called_once()


if __name__ == "__main__":
    unittest.main()
