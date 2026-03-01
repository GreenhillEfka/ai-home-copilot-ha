"""Simple Tests for LLM Fallback Chain - standalone without HA dependencies."""

import pytest
import asyncio
import sys
from unittest.mock import MagicMock, AsyncMock, patch

# Create all necessary mocks BEFORE importing the module
homeassistant_mock = MagicMock()
sys.modules['homeassistant'] = homeassistant_mock
sys.modules['homeassistant.components'] = MagicMock()
sys.modules['homeassistant.components.conversation'] = MagicMock()
sys.modules['homeassistant.config_entries'] = MagicMock()
sys.modules['homeassistant.const'] = MagicMock()
sys.modules['homeassistant.core'] = MagicMock()
sys.modules['homeassistant.exceptions'] = MagicMock()
sys.modules['homeassistant.helpers'] = MagicMock()
sys.modules['homeassistant.helpers.typing'] = MagicMock()

# Mock aiohttp
aiohttp_mock = MagicMock()
aiohttp_mock.ClientSession = MagicMock()
aiohttp_mock.ClientTimeout = MagicMock()
sys.modules['aiohttp'] = aiohttp_mock

# Mock the llm_provider module
llm_provider_mock = MagicMock()
llm_provider_mock.BaseLLMProvider = MagicMock()
sys.modules['custom_components.pilotSuite_rag_conversation.llm_provider'] = llm_provider_mock

# Mock providers module
providers_mock = MagicMock()
providers_mock.OpenAIProvider = MagicMock()
providers_mock.OllamaProvider = MagicMock()
providers_mock.OllamaTinyProvider = MagicMock()
sys.modules['custom_components'] = MagicMock()
sys.modules['custom_components.pilotSuite_rag_conversation'] = MagicMock()
sys.modules['custom_components.pilotSuite_rag_conversation.providers'] = providers_mock

# Now import the actual module
import importlib.util
spec = importlib.util.spec_from_file_location(
    "llm_fallback",
    "/config/.openclaw/workspace/custom_components/pilotSuite_rag_conversation/llm_fallback.py"
)
llm_fallback = importlib.util.module_from_spec(spec)
spec.loader.exec_module(llm_fallback)

LLMFallbackChain = llm_fallback.LLMFallbackChain
FallbackConfig = llm_fallback.FallbackConfig
create_fallback_chain_from_yaml = llm_fallback.create_fallback_chain_from_yaml


class MockProvider:
    """Mock provider for testing."""
    
    def __init__(self, name: str, should_fail: bool = False, timeout: bool = False):
        self.name = name
        self.should_fail = should_fail
        self.timeout = timeout
        self.call_count = 0
    
    async def generate(self, prompt: str) -> str:
        self.call_count += 1
        
        if self.timeout:
            raise asyncio.TimeoutError(f"{self.name} timed out")
        
        if self.should_fail:
            raise Exception(f"{self.name} failed")
        
        return f"Response from {self.name}"


@pytest.mark.asyncio
async def test_single_provider_success():
    """Test successful generation with single provider."""
    config = FallbackConfig(
        fallback_enabled=True,
        fallback_order=["openai"],
        openai_api_key="test-key",
    )
    
    with patch.object(llm_fallback, 'OpenAIProvider') as MockOpenAI:
        mock_provider = MockProvider("OpenAI", should_fail=False)
        MockOpenAI.return_value = mock_provider
        
        chain = LLMFallbackChain(config)
        response = await chain.generate("Test prompt")
        
        assert response == "Response from OpenAI"
        assert mock_provider.call_count == 1


@pytest.mark.asyncio
async def test_fallback_on_timeout():
    """Test fallback when first provider times out."""
    config = FallbackConfig(
        fallback_enabled=True,
        fallback_order=["openai", "ollama"],
        openai_api_key="test-key",
        ollama_url="http://localhost:11434",
    )
    
    with patch.object(llm_fallback, 'OpenAIProvider') as MockOpenAI, \
         patch.object(llm_fallback, 'OllamaProvider') as MockOllama:
        
        mock_openai = MockProvider("OpenAI", timeout=True)
        mock_ollama = MockProvider("Ollama", should_fail=False)
        
        MockOpenAI.return_value = mock_openai
        MockOllama.return_value = mock_ollama
        
        chain = LLMFallbackChain(config)
        response = await chain.generate("Test prompt")
        
        assert response == "Response from Ollama"
        assert mock_openai.call_count == 1
        assert mock_ollama.call_count == 1


@pytest.mark.asyncio
async def test_fallback_on_error():
    """Test fallback when first provider fails with error."""
    config = FallbackConfig(
        fallback_enabled=True,
        fallback_order=["openai", "ollama", "ollama_tiny"],
        openai_api_key="test-key",
    )
    
    with patch.object(llm_fallback, 'OpenAIProvider') as MockOpenAI, \
         patch.object(llm_fallback, 'OllamaProvider') as MockOllama:
        
        mock_openai = MockProvider("OpenAI", should_fail=True)
        mock_ollama = MockProvider("Ollama", should_fail=True)
        mock_ollama_tiny = MockProvider("Ollama", should_fail=False)
        
        MockOpenAI.side_effect = [mock_openai, mock_ollama_tiny]
        MockOllama.return_value = mock_ollama
        
        chain = LLMFallbackChain(config)
        response = await chain.generate("Test prompt")
        
        assert response == "Response from Ollama"
        assert mock_openai.call_count == 1
        assert mock_ollama.call_count == 1
        assert mock_ollama_tiny.call_count == 1


@pytest.mark.asyncio
async def test_all_providers_fail():
    """Test exception when all providers fail."""
    config = FallbackConfig(
        fallback_enabled=True,
        fallback_order=["openai", "ollama"],
        openai_api_key="test-key",
    )
    
    with patch.object(llm_fallback, 'OpenAIProvider') as MockOpenAI, \
         patch.object(llm_fallback, 'OllamaProvider') as MockOllama:
        
        mock_openai = MockProvider("OpenAI", should_fail=True)
        mock_ollama = MockProvider("Ollama", should_fail=True)
        
        MockOpenAI.return_value = mock_openai
        MockOllama.return_value = mock_ollama
        
        chain = LLMFallbackChain(config)
        
        with pytest.raises(Exception, match="failed"):
            await chain.generate("Test prompt")
        
        assert mock_openai.call_count == 1
        assert mock_ollama.call_count == 1


@pytest.mark.asyncio
async def test_fallback_disabled():
    """Test that fallback is disabled when configured."""
    config = FallbackConfig(
        fallback_enabled=False,
        fallback_order=["openai", "ollama"],
        openai_api_key="test-key",
    )
    
    with patch.object(llm_fallback, 'OpenAIProvider') as MockOpenAI:
        mock_openai = MockProvider("OpenAI", should_fail=False)
        MockOpenAI.return_value = mock_openai
        
        chain = LLMFallbackChain(config)
        response = await chain.generate("Test prompt")
        
        assert response == "Response from OpenAI"
        assert mock_openai.call_count == 1


def test_create_from_yaml():
    """Test creating fallback chain from YAML config."""
    yaml_config = {
        "fallback_enabled": True,
        "fallback_order": ["ollama", "openai"],
        "provider": "gpt-4-turbo",
        "openai_api_key": "test-key",
        "ollama_url": "http://localhost:11434",
        "ollama_model": "qwen3.5",
        "ollama_tiny_model": "qwen3.5:7b",
        "timeout_seconds": 60,
    }
    
    chain = create_fallback_chain_from_yaml(yaml_config)
    
    assert chain.config.fallback_enabled is True
    assert chain.config.fallback_order == ["ollama", "openai"]
    assert chain.config.provider == "gpt-4-turbo"
    assert chain.config.timeout_seconds == 60
    assert len(chain.providers) == 2


def test_get_available_providers():
    """Test getting list of available providers."""
    config = FallbackConfig(
        fallback_enabled=True,
        fallback_order=["openai", "ollama"],
        openai_api_key="test-key",
    )
    
    with patch.object(llm_fallback, 'OpenAIProvider') as MockOpenAI, \
         patch.object(llm_fallback, 'OllamaProvider') as MockOllama:
        
        MockOpenAI.return_value = MockProvider("OpenAI")
        MockOllama.return_value = MockProvider("Ollama")
        
        chain = LLMFallbackChain(config)
        providers = chain.get_available_providers()
        
        assert providers == ["OpenAI", "Ollama"]


def test_default_fallback_order():
    """Test default fallback order when not specified."""
    config = FallbackConfig()
    
    assert config.fallback_order == ["openai", "ollama", "ollama_tiny"]
    assert config.fallback_enabled is True
    assert config.timeout_seconds == 30
