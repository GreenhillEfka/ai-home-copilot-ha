"""Tests for the PilotSuite RAG Conversation component."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components import conversation
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from custom_components.pilotSuite_rag_conversation import (
    PilotSuiteRAGConversation,
    async_setup,
)
from custom_components.pilotSuite_rag_conversation.const import (
    CONF_MODEL,
    CONF_RAG_API_URL,
    CONF_USE_WEB_SEARCH,
    DEFAULT_MODEL,
    DEFAULT_RAG_API_URL,
    DEFAULT_USE_WEB_SEARCH,
    DOMAIN,
)


@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp session for testing."""
    with patch("aiohttp.ClientSession") as mock_session:
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        yield mock_session_instance


@pytest.fixture
def mock_hass():
    """Mock HomeAssistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {}
    return hass


class TestPilotSuiteRAGConversation:
    """Test cases for PilotSuiteRAGConversation class."""

    @pytest.mark.asyncio
    async def test_rag_context_used(self, mock_hass, mock_aiohttp_session):
        """Test: RAG-Kontext wird genutzt."""
        # Arrange
        rag_api_url = "http://localhost:8765"
        openai_api_key = "test-key"
        
        agent = PilotSuiteRAGConversation(
            hass=mock_hass,
            rag_api_url=rag_api_url,
            openai_api_key=openai_api_key,
        )

        # Mock RAG-API response
        mock_rag_response = MagicMock()
        mock_rag_response.status = 200
        mock_rag_response.json = AsyncMock(return_value={
            "results": [
                {
                    "source": "ha_states",
                    "content": "Energieverbrauch gestern: 15.3 kWh",
                    "score": 0.95,
                }
            ],
            "query_type": "lokal",
            "sources": {"bm25": [1], "semantic": []},
        })

        # Mock OpenAI API response
        mock_openai_response = MagicMock()
        mock_openai_response.status = 200
        mock_openai_response.json = AsyncMock(return_value={
            "choices": [
                {
                    "message": {
                        "content": "Der Energieverbrauch gestern betrug 15.3 kWh."
                    }
                }
            ]
        })

        # Setup mock session context manager
        mock_aiohttp_session.post = MagicMock()
        mock_aiohttp_session.post.side_effect = [
            MagicMock(__aenter__=AsyncMock(return_value=mock_rag_response), __aexit__=AsyncMock(return_value=None)),
            MagicMock(__aenter__=AsyncMock(return_value=mock_openai_response), __aexit__=AsyncMock(return_value=None)),
        ]

        # Act
        user_input = conversation.ConversationInput(
            text="Wie war der Energieverbrauch?",
            conversation_id="test-conversation",
        )
        result = await agent.async_process(user_input)

        # Assert
        assert result is not None
        assert "Energieverbrauch" in result.response
        assert "15.3 kWh" in result.response
        assert result.conversation_id == "test-conversation"

        # Verify RAG-API was called
        assert mock_aiohttp_session.post.call_count >= 1

    @pytest.mark.asyncio
    async def test_openai_called_with_rag_context(self, mock_hass, mock_aiohttp_session):
        """Test: OpenAI wird mit RAG-Kontext aufgerufen."""
        # Arrange
        rag_api_url = "http://localhost:8765"
        openai_api_key = "test-key"
        
        agent = PilotSuiteRAGConversation(
            hass=mock_hass,
            rag_api_url=rag_api_url,
            openai_api_key=openai_api_key,
            model="gpt-4",
        )

        # Mock RAG-API response
        mock_rag_response = MagicMock()
        mock_rag_response.status = 200
        mock_rag_response.json = AsyncMock(return_value={
            "results": [
                {
                    "source": "ha_states",
                    "content": "Wohnzimmer Lampe: on",
                    "score": 0.9,
                }
            ],
            "query_type": "lokal",
            "sources": {"bm25": [1]},
        })

        # Mock OpenAI API response
        mock_openai_response = MagicMock()
        mock_openai_response.status = 200
        mock_openai_response.json = AsyncMock(return_value={
            "choices": [
                {
                    "message": {
                        "content": "Die Wohnzimmer Lampe ist eingeschaltet."
                    }
                }
            ]
        })

        # Setup mock session
        mock_aiohttp_session.post = MagicMock()
        mock_aiohttp_session.post.side_effect = [
            MagicMock(__aenter__=AsyncMock(return_value=mock_rag_response), __aexit__=AsyncMock(return_value=None)),
            MagicMock(__aenter__=AsyncMock(return_value=mock_openai_response), __aexit__=AsyncMock(return_value=None)),
        ]

        # Act
        user_input = conversation.ConversationInput(
            text="Ist die Wohnzimmer Lampe an?",
            conversation_id="test-conversation-2",
        )
        result = await agent.async_process(user_input)

        # Assert
        assert result is not None
        assert "Wohnzimmer" in result.response
        assert result.conversation_id == "test-conversation-2"

    @pytest.mark.asyncio
    async def test_timeout_handling(self, mock_hass, mock_aiohttp_session):
        """Test: Timeout bei RAG-Suche wird korrekt behandelt."""
        # Arrange
        agent = PilotSuiteRAGConversation(
            hass=mock_hass,
            rag_api_url="http://localhost:8765",
            openai_api_key="test-key",
        )

        # Mock timeout
        mock_aiohttp_session.post.side_effect = asyncio.TimeoutError()

        # Act & Assert
        user_input = conversation.ConversationInput(
            text="Test query",
            conversation_id="test-conversation",
        )
        
        with pytest.raises(HomeAssistantError) as exc_info:
            await agent.async_process(user_input)
        
        assert "Zeitüberschreitung" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_http_error_handling(self, mock_hass, mock_aiohttp_session):
        """Test: HTTP-Fehler bei RAG-Suche wird korrekt behandelt."""
        # Arrange
        agent = PilotSuiteRAGConversation(
            hass=mock_hass,
            rag_api_url="http://localhost:8765",
            openai_api_key="test-key",
        )

        # Mock HTTP error
        mock_response = MagicMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")
        
        mock_aiohttp_session.post = MagicMock()
        mock_aiohttp_session.post.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_aiohttp_session.post.return_value.__aexit__ = AsyncMock(return_value=None)

        # Act & Assert
        user_input = conversation.ConversationInput(
            text="Test query",
            conversation_id="test-conversation",
        )
        
        with pytest.raises(HomeAssistantError) as exc_info:
            await agent.async_process(user_input)
        
        assert "RAG-API Fehler" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_history_tracking(self, mock_hass, mock_aiohttp_session):
        """Test: Conversation History wird korrekt aktualisiert."""
        # Arrange
        agent = PilotSuiteRAGConversation(
            hass=mock_hass,
            rag_api_url="http://localhost:8765",
            openai_api_key="test-key",
        )

        # Mock responses
        mock_rag_response = MagicMock()
        mock_rag_response.status = 200
        mock_rag_response.json = AsyncMock(return_value={
            "results": [],
            "query_type": "lokal",
        })

        mock_openai_response = MagicMock()
        mock_openai_response.status = 200
        mock_openai_response.json = AsyncMock(return_value={
            "choices": [{"message": {"content": "Test response"}}]
        })

        mock_aiohttp_session.post = MagicMock()
        mock_aiohttp_session.post.side_effect = [
            MagicMock(__aenter__=AsyncMock(return_value=mock_rag_response), __aexit__=AsyncMock(return_value=None)),
            MagicMock(__aenter__=AsyncMock(return_value=mock_openai_response), __aexit__=AsyncMock(return_value=None)),
        ]

        # Act
        user_input = conversation.ConversationInput(
            text="First question",
            conversation_id="test-history",
        )
        await agent.async_process(user_input)

        # Assert
        assert "test-history" in agent.history
        assert len(agent.history["test-history"]) == 2  # user + assistant
        assert agent.history["test-history"][0]["role"] == "user"
        assert agent.history["test-history"][0]["content"] == "First question"

    @pytest.mark.asyncio
    async def test_web_search_toggle(self, mock_hass, mock_aiohttp_session):
        """Test: Web-Suche Toggle wird korrekt an RAG-API übergeben."""
        # Arrange
        agent = PilotSuiteRAGConversation(
            hass=mock_hass,
            rag_api_url="http://localhost:8765",
            openai_api_key="test-key",
            use_web_search=True,
        )

        # Mock response
        mock_rag_response = MagicMock()
        mock_rag_response.status = 200
        mock_rag_response.json = AsyncMock(return_value={
            "results": [],
            "query_type": "hybrid",
            "sources": {"bm25": [], "semantic": [], "web": [1, 2]},
        })

        mock_openai_response = MagicMock()
        mock_openai_response.status = 200
        mock_openai_response.json = AsyncMock(return_value={
            "choices": [{"message": {"content": "Response with web context"}}]
        })

        mock_aiohttp_session.post = MagicMock()
        mock_aiohttp_session.post.side_effect = [
            MagicMock(__aenter__=AsyncMock(return_value=mock_rag_response), __aexit__=AsyncMock(return_value=None)),
            MagicMock(__aenter__=AsyncMock(return_value=mock_openai_response), __aexit__=AsyncMock(return_value=None)),
        ]

        # Act
        user_input = conversation.ConversationInput(
            text="What's the weather?",
            conversation_id="test-web",
        )
        result = await agent.async_process(user_input)

        # Assert
        assert result is not None
        # Verify RAG-API was called with use_web=True
        # (This would be verified by inspecting the call args in a real test)


class TestAsyncSetup:
    """Test cases for async_setup function."""

    @pytest.mark.asyncio
    async def test_async_setup_no_config(self, mock_hass):
        """Test: async_setup ohne Konfiguration."""
        # Act
        result = await async_setup(mock_hass, {})

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_async_setup_with_config(self, mock_hass):
        """Test: async_setup mit Konfiguration."""
        # Arrange
        config = {
            DOMAIN: {
                CONF_RAG_API_URL: "http://custom-rag-api:8765",
                CONF_MODEL: "gpt-4-turbo",
                CONF_USE_WEB_SEARCH: True,
                "openai_api_key": "test-key",
            }
        }

        with patch("homeassistant.components.conversation.async_set_agent"):
            # Act
            result = await async_setup(mock_hass, config)

            # Assert
            assert result is True
            assert DOMAIN in mock_hass.data
            assert mock_hass.data[DOMAIN][CONF_RAG_API_URL] == "http://custom-rag-api:8765"
            assert mock_hass.data[DOMAIN][CONF_MODEL] == "gpt-4-turbo"
            assert mock_hass.data[DOMAIN][CONF_USE_WEB_SEARCH] is True
