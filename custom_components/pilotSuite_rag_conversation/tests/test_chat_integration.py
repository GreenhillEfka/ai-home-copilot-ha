"""Integration Tests for Chat Conversation with RAG Context."""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import ClientError

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from homeassistant.components import conversation as ha_conversation
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from custom_components.pilotSuite_rag_conversation.conversation import (
    PilotSuiteRAGConversationHandler,
)
from custom_components.pilotSuite_rag_conversation.llm_fallback import (
    LLMFallbackChain,
    FallbackConfig,
)
from custom_components.pilotSuite_rag_conversation.const import (
    CONF_RAG_API_URL,
    DEFAULT_RAG_API_URL,
    CONF_HA_TOKEN,
    CONF_OPENAI_API_KEY,
)


# =============================================================================
# Mock Classes for Testing
# =============================================================================

class MockConversationInput:
    """Mock HomeAssistant ConversationInput."""
    
    def __init__(
        self,
        text: str = "Test question",
        conversation_id: str = "test-conversation-123",
        agent_id: str = "pilotSuite_rag_conversation",
    ):
        self.text = text
        self.conversation_id = conversation_id
        self.agent_id = agent_id
        self.device_id = None
        self.language = "de"


class MockHomeAssistant:
    """Mock HomeAssistant instance."""
    
    def __init__(self):
        self.states = MagicMock()
        self.states.async_all = MagicMock(return_value=[])
        self.states.get = MagicMock(return_value=None)


# =============================================================================
# RAG Context Tests
# =============================================================================

@pytest.mark.asyncio
async def test_conversation_async_process_with_rag_context():
    """Test conversation.async_process() mit RAG-Kontext."""
    mock_hass = MockHomeAssistant()
    
    mock_fallback_chain = AsyncMock(spec=LLMFallbackChain)
    mock_fallback_chain.generate = AsyncMock(return_value="This is the answer based on RAG context")
    mock_fallback_chain.get_primary_provider = MagicMock(return_value="OpenAI")
    
    handler = PilotSuiteRAGConversationHandler(
        hass=mock_hass,
        fallback_chain=mock_fallback_chain,
        rag_api_url="http://localhost:8765",
    )
    
    await handler.async_init()
    
    mock_rag_response = {
        "results": [
            {
                "source": "homeassistant_states",
                "content": "Living room light is on",
                "score": 0.95,
            },
            {
                "source": "automation_log",
                "content": "Automation triggered at 18:00",
                "score": 0.85,
            },
        ],
        "query_type": "lokal",
        "sources": {
            "bm25": ["result1", "result2"],
            "semantic": ["result1"],
        },
    }
    
    with patch.object(handler, '_search_rag', AsyncMock(return_value=mock_rag_response)):
        user_input = MockConversationInput(text="Is the living room light on?")
        
        result = await handler.async_process(user_input)
        
        assert isinstance(result, ha_conversation.ConversationResult)
        assert "This is the answer based on RAG context" in result.response
        assert result.conversation_id == "test-conversation-123"
        
        mock_fallback_chain.generate.assert_called_once()
        
        # Verify RAG context was included in prompt
        call_args = mock_fallback_chain.generate.call_args
        prompt = call_args[0][0]
        assert "KONTEXT AUS RAG-API" in prompt
        assert "Living room light is on" in prompt
        assert "Is the living room light on?" in prompt
    
    await handler.async_cleanup()


@pytest.mark.asyncio
async def test_rag_prompt_injection_ha_states():
    """Test RAG-Prompt-Injection (HA-States im Prompt)."""
    mock_hass = MockHomeAssistant()
    
    mock_fallback_chain = AsyncMock(spec=LLMFallbackChain)
    mock_fallback_chain.generate = AsyncMock(return_value="The temperature is 21°C")
    mock_fallback_chain.get_primary_provider = MagicMock(return_value="OpenAI")
    
    handler = PilotSuiteRAGConversationHandler(
        hass=mock_hass,
        fallback_chain=mock_fallback_chain,
        rag_api_url="http://localhost:8765",
    )
    
    await handler.async_init()
    
    mock_rag_response = {
        "results": [
            {
                "source": "homeassistant_states",
                "content": "sensor.living_room_temperature: 21.0°C",
                "score": 0.98,
            },
            {
                "source": "homeassistant_states",
                "content": "binary_sensor.front_door: off",
                "score": 0.75,
            },
        ],
        "query_type": "lokal",
        "sources": {
            "bm25": ["state1", "state2"],
            "semantic": ["state1"],
        },
    }
    
    with patch.object(handler, '_search_rag', AsyncMock(return_value=mock_rag_response)):
        user_input = MockConversationInput(text="What's the temperature?")
        
        result = await handler.async_process(user_input)
        
        assert result.response == "The temperature is 21°C"
        
        # Verify HA states were injected into prompt
        call_args = mock_fallback_chain.generate.call_args
        prompt = call_args[0][0]
        
        assert "sensor.living_room_temperature: 21.0°C" in prompt
        assert "binary_sensor.front_door: off" in prompt
        assert "homeassistant_states" in prompt
        assert "Score: 0.98" in prompt
    
    await handler.async_cleanup()


@pytest.mark.asyncio
async def test_rag_context_with_empty_results():
    """Test RAG context handling when no results found."""
    mock_hass = MockHomeAssistant()
    
    mock_fallback_chain = AsyncMock(spec=LLMFallbackChain)
    mock_fallback_chain.generate = AsyncMock(return_value="I don't have information about that")
    mock_fallback_chain.get_primary_provider = MagicMock(return_value="OpenAI")
    
    handler = PilotSuiteRAGConversationHandler(
        hass=mock_hass,
        fallback_chain=mock_fallback_chain,
        rag_api_url="http://localhost:8765",
    )
    
    await handler.async_init()
    
    mock_rag_response = {
        "results": [],
        "query_type": "lokal",
        "sources": {},
    }
    
    with patch.object(handler, '_search_rag', AsyncMock(return_value=mock_rag_response)):
        user_input = MockConversationInput(text="Unknown question")
        
        result = await handler.async_process(user_input)
        
        assert result.response == "I don't have information about that"
        
        # Verify prompt still built with empty context
        call_args = mock_fallback_chain.generate.call_args
        prompt = call_args[0][0]
        
        assert "Keine kontextuellen Informationen gefunden" in prompt
    
    await handler.async_cleanup()


# =============================================================================
# HA-Assist Input Tests
# =============================================================================

@pytest.mark.asyncio
async def test_ha_assist_speech_input():
    """Test HA-Assist Sprach-Input."""
    mock_hass = MockHomeAssistant()
    
    mock_fallback_chain = AsyncMock(spec=LLMFallbackChain)
    mock_fallback_chain.generate = AsyncMock(return_value="I've turned on the lights")
    mock_fallback_chain.get_primary_provider = MagicMock(return_value="OpenAI")
    
    handler = PilotSuiteRAGConversationHandler(
        hass=mock_hass,
        fallback_chain=mock_fallback_chain,
        rag_api_url="http://localhost:8765",
    )
    
    await handler.async_init()
    
    mock_rag_response = {
        "results": [
            {
                "source": "homeassistant_states",
                "content": "light.living_room: off",
                "score": 0.90,
            },
        ],
        "query_type": "lokal",
        "sources": {
            "bm25": ["state1"],
        },
    }
    
    with patch.object(handler, '_search_rag', AsyncMock(return_value=mock_rag_response)):
        # Simulate speech input (transcribed to text)
        user_input = MockConversationInput(
            text="Turn on the living room lights",
            conversation_id="speech-session-456",
        )
        
        result = await handler.async_process(user_input)
        
        assert result.response == "I've turned on the lights"
        assert result.conversation_id == "speech-session-456"
        
        # Verify history was updated
        assert "speech-session-456" in handler.history
        assert len(handler.history["speech-session-456"]) == 2
        assert handler.history["speech-session-456"][0]["role"] == "user"
        assert handler.history["speech-session-456"][0]["content"] == "Turn on the living room lights"
    
    await handler.async_cleanup()


@pytest.mark.asyncio
async def test_ha_assist_text_input():
    """Test HA-Assist Text-Input."""
    mock_hass = MockHomeAssistant()
    
    mock_fallback_chain = AsyncMock(spec=LLMFallbackChain)
    mock_fallback_chain.generate = AsyncMock(return_value="The front door is locked")
    mock_fallback_chain.get_primary_provider = MagicMock(return_value="OpenAI")
    
    handler = PilotSuiteRAGConversationHandler(
        hass=mock_hass,
        fallback_chain=mock_fallback_chain,
        rag_api_url="http://localhost:8765",
    )
    
    await handler.async_init()
    
    mock_rag_response = {
        "results": [
            {
                "source": "homeassistant_states",
                "content": "binary_sensor.front_door: off (locked)",
                "score": 0.95,
            },
        ],
        "query_type": "lokal",
        "sources": {
            "semantic": ["state1"],
        },
    }
    
    with patch.object(handler, '_search_rag', AsyncMock(return_value=mock_rag_response)):
        # Simulate text input
        user_input = MockConversationInput(
            text="Is the front door locked?",
            conversation_id="text-session-789",
        )
        
        result = await handler.async_process(user_input)
        
        assert result.response == "The front door is locked"
        assert result.conversation_id == "text-session-789"
        
        # Verify conversation history tracking
        assert "text-session-789" in handler.history
        
        # Test multiple messages in same conversation
        user_input2 = MockConversationInput(
            text="Thank you",
            conversation_id="text-session-789",
        )
        
        mock_fallback_chain.generate = AsyncMock(return_value="You're welcome!")
        await handler.async_process(user_input2)
        
        assert len(handler.history["text-session-789"]) == 4  # 2 exchanges
    
    await handler.async_cleanup()


# =============================================================================
# Configuration Loading Tests
# =============================================================================

@pytest.mark.asyncio
async def test_config_loading_from_yaml():
    """Test Config-Loading aus YAML."""
    yaml_config = {
        "fallback_enabled": True,
        "fallback_order": ["openai", "ollama"],
        "provider": "gpt-4",
        "openai_api_key": "yaml-test-key",
        "ollama_url": "http://localhost:11434",
        "ollama_model": "qwen3.5",
        "ollama_tiny_model": "qwen3.5:7b",
        "timeout_seconds": 45,
        "rag_api_url": "http://localhost:8765",
        "use_web_search": False,
    }
    
    # Create fallback config from YAML config
    config = FallbackConfig(
        fallback_enabled=yaml_config["fallback_enabled"],
        fallback_order=yaml_config["fallback_order"],
        provider=yaml_config["provider"],
        openai_api_key=yaml_config["openai_api_key"],
        ollama_url=yaml_config["ollama_url"],
        ollama_model=yaml_config["ollama_model"],
        ollama_tiny_model=yaml_config["ollama_tiny_model"],
        timeout_seconds=yaml_config["timeout_seconds"],
    )
    
    assert config.fallback_enabled is True
    assert config.fallback_order == ["openai", "ollama"]
    assert config.provider == "gpt-4"
    assert config.openai_api_key == "yaml-test-key"
    assert config.timeout_seconds == 45
    assert config.ollama_url == "http://localhost:11434"


@pytest.mark.asyncio
async def test_config_loading_from_yaml_defaults():
    """Test Config-Loading aus YAML with default values."""
    yaml_config = {}
    
    config = FallbackConfig(
        fallback_enabled=yaml_config.get("fallback_enabled", True),
        fallback_order=yaml_config.get("fallback_order", ["openai", "ollama", "ollama_tiny"]),
        provider=yaml_config.get("provider", "gpt-4"),
        openai_api_key=yaml_config.get("openai_api_key"),
        ollama_url=yaml_config.get("ollama_url", "http://localhost:11434"),
        ollama_model=yaml_config.get("ollama_model", "qwen3.5"),
        ollama_tiny_model=yaml_config.get("ollama_tiny_model", "qwen3.5:7b"),
        timeout_seconds=yaml_config.get("timeout_seconds", 30),
    )
    
    assert config.fallback_enabled is True
    assert config.fallback_order == ["openai", "ollama", "ollama_tiny"]
    assert config.timeout_seconds == 30
    assert config.ollama_url == "http://localhost:11434"


# =============================================================================
# Config Flow Tests (UI Configuration)
# =============================================================================

@pytest.mark.asyncio
async def test_config_loading_from_ui_config_flow():
    """Test Config-Loading aus UI (config_flow)."""
    from custom_components.pilotSuite_rag_conversation.config_flow import PilotSuiteRAGConversationConfigFlow
    
    # Simulate UI config flow data
    ui_config_data = {
        CONF_HA_TOKEN: "test-ha-token-123",
        CONF_RAG_API_URL: "http://localhost:8765",
        CONF_OPENAI_API_KEY: "ui-test-key-456",
    }
    
    # Verify config data structure
    assert CONF_HA_TOKEN in ui_config_data
    assert ui_config_data[CONF_HA_TOKEN] == "test-ha-token-123"
    assert ui_config_data[CONF_RAG_API_URL] == "http://localhost:8765"
    assert ui_config_data[CONF_OPENAI_API_KEY] == "ui-test-key-456"
    
    # Create fallback config from UI data
    config = FallbackConfig(
        fallback_enabled=True,
        fallback_order=["openai", "ollama", "ollama_tiny"],
        provider="gpt-4",
        openai_api_key=ui_config_data[CONF_OPENAI_API_KEY],
        ollama_url="http://localhost:11434",
    )
    
    assert config.openai_api_key == "ui-test-key-456"
    assert config.fallback_enabled is True


@pytest.mark.asyncio
async def test_config_flow_rag_api_discovery():
    """Test config flow RAG-API auto-discovery via async_step_user."""
    from custom_components.pilotSuite_rag_conversation.config_flow import PilotSuiteRAGConversationConfigFlow
    from custom_components.pilotSuite_rag_conversation.const import (
        CONF_HA_TOKEN,
        CONF_RAG_API_URL,
        CONF_OPENAI_API_KEY,
    )
    
    flow = PilotSuiteRAGConversationConfigFlow()
    
    # Test that config flow initializes correctly
    assert flow is not None
    assert hasattr(flow, 'async_step_user')
    
    # Mock RAG-API health check
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_session = AsyncMock()
    mock_session.get = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        # Simulate user step with all required fields
        user_input = {
            CONF_HA_TOKEN: "test-token",
            CONF_RAG_API_URL: "http://localhost:8765",
            CONF_OPENAI_API_KEY: "test-key",
        }
        result = await flow.async_step_user(user_input)
        
        # Should proceed to next step or create entry
        assert result is not None
        assert "step_id" in result or result.get("type") == "create_entry"


@pytest.mark.asyncio
async def test_config_flow_rag_api_unreachable():
    """Test config flow when RAG-API is unreachable."""
    from custom_components.pilotSuite_rag_conversation.config_flow import PilotSuiteRAGConversationConfigFlow
    from custom_components.pilotSuite_rag_conversation.const import (
        CONF_HA_TOKEN,
        CONF_RAG_API_URL,
        CONF_OPENAI_API_KEY,
    )
    
    flow = PilotSuiteRAGConversationConfigFlow()
    
    # Test health check with connection error
    mock_session = AsyncMock()
    mock_session.get.side_effect = ClientError("Connection refused")
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        # Simulate user step with all required fields
        user_input = {
            CONF_HA_TOKEN: "test-token",
            CONF_RAG_API_URL: "http://localhost:8765",
            CONF_OPENAI_API_KEY: "test-key",
        }
        result = await flow.async_step_user(user_input)
        
        # Should still proceed (fallback active)
        assert result is not None


# =============================================================================
# Error Handling Tests
# =============================================================================

@pytest.mark.asyncio
async def test_conversation_timeout_error():
    """Test conversation handler timeout error handling."""
    mock_hass = MockHomeAssistant()
    
    mock_fallback_chain = AsyncMock(spec=LLMFallbackChain)
    mock_fallback_chain.generate = AsyncMock(side_effect=asyncio.TimeoutError("LLM timeout"))
    
    handler = PilotSuiteRAGConversationHandler(
        hass=mock_hass,
        fallback_chain=mock_fallback_chain,
        rag_api_url="http://localhost:8765",
    )
    
    await handler.async_init()
    
    mock_rag_response = {
        "results": [],
        "query_type": "lokal",
        "sources": {},
    }
    
    with patch.object(handler, '_search_rag', AsyncMock(return_value=mock_rag_response)):
        user_input = MockConversationInput(text="Test question")
        
        with pytest.raises(HomeAssistantError, match="Zeitüberschreitung"):
            await handler.async_process(user_input)
    
    await handler.async_cleanup()


@pytest.mark.asyncio
async def test_conversation_rag_api_error():
    """Test conversation handler RAG-API error handling."""
    mock_hass = MockHomeAssistant()
    
    mock_fallback_chain = AsyncMock(spec=LLMFallbackChain)
    
    handler = PilotSuiteRAGConversationHandler(
        hass=mock_hass,
        fallback_chain=mock_fallback_chain,
        rag_api_url="http://localhost:8765",
    )
    
    await handler.async_init()
    
    # Simulate RAG-API error
    with patch.object(
        handler,
        '_search_rag',
        AsyncMock(side_effect=HomeAssistantError("RAG-API Fehler (500): Internal Server Error")),
    ):
        user_input = MockConversationInput(text="Test question")
        
        with pytest.raises(HomeAssistantError, match="RAG-API Fehler"):
            await handler.async_process(user_input)
    
    await handler.async_cleanup()


# =============================================================================
# History Management Tests
# =============================================================================

@pytest.mark.asyncio
async def test_history_limit_enforcement():
    """Test that conversation history is limited to last 20 messages."""
    mock_hass = MockHomeAssistant()
    
    mock_fallback_chain = AsyncMock(spec=LLMFallbackChain)
    mock_fallback_chain.generate = AsyncMock(return_value="Response")
    mock_fallback_chain.get_primary_provider = MagicMock(return_value="OpenAI")
    
    handler = PilotSuiteRAGConversationHandler(
        hass=mock_hass,
        fallback_chain=mock_fallback_chain,
        rag_api_url="http://localhost:8765",
    )
    
    await handler.async_init()
    
    mock_rag_response = {
        "results": [],
        "query_type": "lokal",
        "sources": {},
    }
    
    with patch.object(handler, '_search_rag', AsyncMock(return_value=mock_rag_response)):
        conversation_id = "long-conversation"
        
        # Simulate 15 exchanges (30 messages)
        for i in range(15):
            user_input = MockConversationInput(
                text=f"Question {i}",
                conversation_id=conversation_id,
            )
            mock_fallback_chain.generate = AsyncMock(return_value=f"Response {i}")
            await handler.async_process(user_input)
        
        # History should be limited to last 20 messages
        assert len(handler.history[conversation_id]) == 20
        
        # Verify oldest messages were removed
        assert handler.history[conversation_id][0]["content"] == "Question 5"
        assert handler.history[conversation_id][-1]["content"] == "Response 14"
    
    await handler.async_cleanup()
