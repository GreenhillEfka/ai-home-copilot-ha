"""Comprehensive Tests for LLM Fallback Chain."""

import pytest
import asyncio
import logging
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from custom_components.pilotSuite_rag_conversation.llm_fallback import (
    LLMFallbackChain,
    FallbackConfig,
    create_fallback_chain_from_yaml,
)
from custom_components.pilotSuite_rag_conversation.providers import (
    OpenAIProvider,
    OllamaProvider,
    OllamaTinyProvider,
)


# =============================================================================
# Mock Provider for Testing
# =============================================================================

class MockProvider:
    """Mock provider for testing fallback behavior."""
    
    def __init__(
        self,
        name: str,
        should_fail: bool = False,
        timeout: bool = False,
        response_text: str = None,
    ):
        self.name = name
        self.should_fail = should_fail
        self.timeout = timeout
        self.response_text = response_text or f"Response from {name}"
        self.call_count = 0
    
    async def generate(self, prompt: str) -> str:
        self.call_count += 1
        
        if self.timeout:
            raise asyncio.TimeoutError(f"{self.name} timed out after 30s")
        
        if self.should_fail:
            raise Exception(f"{self.name} failed with error")
        
        return self.response_text


# =============================================================================
# Fallback Chain Success Scenarios
# =============================================================================

@pytest.mark.asyncio
async def test_fallback_openai_success_no_fallback_needed():
    """Test Fallback-Kette: OpenAI success → kein Fallback."""
    config = FallbackConfig(
        fallback_enabled=True,
        fallback_order=["openai", "ollama", "ollama_tiny"],
        openai_api_key="test-key",
    )
    
    with patch.object(OpenAIProvider, '__init__', lambda x, **kwargs: None), \
         patch.object(OllamaProvider, '__init__', lambda x, **kwargs: None), \
         patch.object(OllamaTinyProvider, '__init__', lambda x, **kwargs: None):
        
        mock_openai = MockProvider("OpenAI", should_fail=False)
        mock_ollama = MockProvider("Ollama", should_fail=False)
        mock_ollama_tiny = MockProvider("Ollama-Tiny", should_fail=False)
        
        config.providers = [mock_openai, mock_ollama, mock_ollama_tiny]
        
        chain = LLMFallbackChain.__new__(LLMFallbackChain)
        chain.config = config
        chain.providers = [mock_openai, mock_ollama, mock_ollama_tiny]
        
        response = await chain.generate("Test prompt")
        
        assert response == "Response from OpenAI"
        assert mock_openai.call_count == 1
        assert mock_ollama.call_count == 0
        assert mock_ollama_tiny.call_count == 0


@pytest.mark.asyncio
async def test_fallback_openai_timeout_ollama_success():
    """Test Fallback: OpenAI timeout → Ollama success."""
    config = FallbackConfig(
        fallback_enabled=True,
        fallback_order=["openai", "ollama", "ollama_tiny"],
        openai_api_key="test-key",
    )
    
    with patch.object(OpenAIProvider, '__init__', lambda x, **kwargs: None), \
         patch.object(OllamaProvider, '__init__', lambda x, **kwargs: None), \
         patch.object(OllamaTinyProvider, '__init__', lambda x, **kwargs: None):
        
        mock_openai = MockProvider("OpenAI", timeout=True)
        mock_ollama = MockProvider("Ollama", should_fail=False)
        mock_ollama_tiny = MockProvider("Ollama-Tiny", should_fail=False)
        
        config.providers = [mock_openai, mock_ollama, mock_ollama_tiny]
        
        chain = LLMFallbackChain.__new__(LLMFallbackChain)
        chain.config = config
        chain.providers = [mock_openai, mock_ollama, mock_ollama_tiny]
        
        response = await chain.generate("Test prompt")
        
        assert response == "Response from Ollama"
        assert mock_openai.call_count == 1
        assert mock_ollama.call_count == 1
        assert mock_ollama_tiny.call_count == 0


@pytest.mark.asyncio
async def test_fallback_openai_ollama_timeout_ollama_tiny_success():
    """Test Fallback: OpenAI + Ollama timeout → Ollama Tiny success."""
    config = FallbackConfig(
        fallback_enabled=True,
        fallback_order=["openai", "ollama", "ollama_tiny"],
        openai_api_key="test-key",
    )
    
    with patch.object(OpenAIProvider, '__init__', lambda x, **kwargs: None), \
         patch.object(OllamaProvider, '__init__', lambda x, **kwargs: None), \
         patch.object(OllamaTinyProvider, '__init__', lambda x, **kwargs: None):
        
        mock_openai = MockProvider("OpenAI", timeout=True)
        mock_ollama = MockProvider("Ollama", timeout=True)
        mock_ollama_tiny = MockProvider("Ollama-Tiny", should_fail=False)
        
        config.providers = [mock_openai, mock_ollama, mock_ollama_tiny]
        
        chain = LLMFallbackChain.__new__(LLMFallbackChain)
        chain.config = config
        chain.providers = [mock_openai, mock_ollama, mock_ollama_tiny]
        
        response = await chain.generate("Test prompt")
        
        assert response == "Response from Ollama-Tiny"
        assert mock_openai.call_count == 1
        assert mock_ollama.call_count == 1
        assert mock_ollama_tiny.call_count == 1


@pytest.mark.asyncio
async def test_fallback_all_timeout_raises_exception():
    """Test Fallback: ALLE timeout → Exception."""
    config = FallbackConfig(
        fallback_enabled=True,
        fallback_order=["openai", "ollama", "ollama_tiny"],
        openai_api_key="test-key",
    )
    
    with patch.object(OpenAIProvider, '__init__', lambda x, **kwargs: None), \
         patch.object(OllamaProvider, '__init__', lambda x, **kwargs: None), \
         patch.object(OllamaTinyProvider, '__init__', lambda x, **kwargs: None):
        
        mock_openai = MockProvider("OpenAI", timeout=True)
        mock_ollama = MockProvider("Ollama", timeout=True)
        mock_ollama_tiny = MockProvider("Ollama-Tiny", timeout=True)
        
        config.providers = [mock_openai, mock_ollama, mock_ollama_tiny]
        
        chain = LLMFallbackChain.__new__(LLMFallbackChain)
        chain.config = config
        chain.providers = [mock_openai, mock_ollama, mock_ollama_tiny]
        
        with pytest.raises(asyncio.TimeoutError, match="timed out"):
            await chain.generate("Test prompt")
        
        assert mock_openai.call_count == 1
        assert mock_ollama.call_count == 1
        assert mock_ollama_tiny.call_count == 1


# =============================================================================
# Configurable Fallback Order Tests
# =============================================================================

@pytest.mark.asyncio
async def test_fallback_configurable_order_ollama_first():
    """Test Fallback: Configurable fallback_order with Ollama first."""
    config = FallbackConfig(
        fallback_enabled=True,
        fallback_order=["ollama", "openai", "ollama_tiny"],
        openai_api_key="test-key",
    )
    
    with patch.object(OpenAIProvider, '__init__', lambda x, **kwargs: None), \
         patch.object(OllamaProvider, '__init__', lambda x, **kwargs: None), \
         patch.object(OllamaTinyProvider, '__init__', lambda x, **kwargs: None):
        
        mock_ollama = MockProvider("Ollama", timeout=True)
        mock_openai = MockProvider("OpenAI", should_fail=False)
        mock_ollama_tiny = MockProvider("Ollama-Tiny", should_fail=False)
        
        config.providers = [mock_ollama, mock_openai, mock_ollama_tiny]
        
        chain = LLMFallbackChain.__new__(LLMFallbackChain)
        chain.config = config
        chain.providers = [mock_ollama, mock_openai, mock_ollama_tiny]
        
        response = await chain.generate("Test prompt")
        
        assert response == "Response from OpenAI"
        assert mock_ollama.call_count == 1
        assert mock_openai.call_count == 1
        assert mock_ollama_tiny.call_count == 0


@pytest.mark.asyncio
async def test_fallback_configurable_order_ollama_tiny_only():
    """Test Fallback: Configurable fallback_order with only Ollama Tiny."""
    config = FallbackConfig(
        fallback_enabled=True,
        fallback_order=["ollama_tiny"],
        openai_api_key="test-key",
    )
    
    with patch.object(OllamaTinyProvider, '__init__', lambda x, **kwargs: None):
        
        mock_ollama_tiny = MockProvider("Ollama-Tiny", should_fail=False)
        
        config.providers = [mock_ollama_tiny]
        
        chain = LLMFallbackChain.__new__(LLMFallbackChain)
        chain.config = config
        chain.providers = [mock_ollama_tiny]
        
        response = await chain.generate("Test prompt")
        
        assert response == "Response from Ollama-Tiny"
        assert mock_ollama_tiny.call_count == 1


# =============================================================================
# Logging Tests
# =============================================================================

@pytest.mark.asyncio
async def test_logging_on_fallback_success(caplog):
    """Test Logging bei Fallback - success message logged."""
    caplog.set_level(logging.INFO)
    
    config = FallbackConfig(
        fallback_enabled=True,
        fallback_order=["openai", "ollama"],
        openai_api_key="test-key",
    )
    
    with patch.object(OpenAIProvider, '__init__', lambda x, **kwargs: None), \
         patch.object(OllamaProvider, '__init__', lambda x, **kwargs: None):
        
        mock_openai = MockProvider("OpenAI", timeout=True)
        mock_ollama = MockProvider("Ollama", should_fail=False)
        
        config.providers = [mock_openai, mock_ollama]
        
        chain = LLMFallbackChain.__new__(LLMFallbackChain)
        chain.config = config
        chain.providers = [mock_openai, mock_ollama]
        
        response = await chain.generate("Test prompt")
        
        assert response == "Response from Ollama"
        
        # Check that success was logged
        assert any("SUCCESS: Provider 'Ollama' generated response" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_logging_on_fallback_timeout(caplog):
    """Test Logging bei Fallback - timeout warning logged."""
    caplog.set_level(logging.WARNING)
    
    config = FallbackConfig(
        fallback_enabled=True,
        fallback_order=["openai", "ollama"],
        openai_api_key="test-key",
    )
    
    with patch.object(OpenAIProvider, '__init__', lambda x, **kwargs: None), \
         patch.object(OllamaProvider, '__init__', lambda x, **kwargs: None):
        
        mock_openai = MockProvider("OpenAI", timeout=True)
        mock_ollama = MockProvider("Ollama", should_fail=False)
        
        config.providers = [mock_openai, mock_ollama]
        
        chain = LLMFallbackChain.__new__(LLMFallbackChain)
        chain.config = config
        chain.providers = [mock_openai, mock_ollama]
        
        await chain.generate("Test prompt")
        
        # Check that timeout was logged
        assert any("TIMEOUT: Provider 'OpenAI' timed out" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_logging_on_fallback_error(caplog):
    """Test Logging bei Fallback - error warning logged."""
    caplog.set_level(logging.WARNING)
    
    config = FallbackConfig(
        fallback_enabled=True,
        fallback_order=["openai", "ollama"],
        openai_api_key="test-key",
    )
    
    with patch.object(OpenAIProvider, '__init__', lambda x, **kwargs: None), \
         patch.object(OllamaProvider, '__init__', lambda x, **kwargs: None):
        
        mock_openai = MockProvider("OpenAI", should_fail=True)
        mock_ollama = MockProvider("Ollama", should_fail=False)
        
        config.providers = [mock_openai, mock_ollama]
        
        chain = LLMFallbackChain.__new__(LLMFallbackChain)
        chain.config = config
        chain.providers = [mock_openai, mock_ollama]
        
        await chain.generate("Test prompt")
        
        # Check that error was logged
        assert any("ERROR: Provider 'OpenAI' failed" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_logging_all_providers_failed(caplog):
    """Test Logging when all providers fail."""
    caplog.set_level(logging.ERROR)
    
    config = FallbackConfig(
        fallback_enabled=True,
        fallback_order=["openai", "ollama"],
        openai_api_key="test-key",
    )
    
    with patch.object(OpenAIProvider, '__init__', lambda x, **kwargs: None), \
         patch.object(OllamaProvider, '__init__', lambda x, **kwargs: None):
        
        mock_openai = MockProvider("OpenAI", timeout=True)
        mock_ollama = MockProvider("Ollama", timeout=True)
        
        config.providers = [mock_openai, mock_ollama]
        
        chain = LLMFallbackChain.__new__(LLMFallbackChain)
        chain.config = config
        chain.providers = [mock_openai, mock_ollama]
        
        with pytest.raises(asyncio.TimeoutError):
            await chain.generate("Test prompt")
        
        # Check that failure was logged
        assert any("ALL PROVIDERS FAILED" in record.message for record in caplog.records)


# =============================================================================
# Async Timeout Tests (30s)
# =============================================================================

@pytest.mark.asyncio
async def test_async_timeout_per_provider_30s():
    """Test async Timeout pro Provider (30s)."""
    config = FallbackConfig(
        fallback_enabled=True,
        fallback_order=["openai", "ollama"],
        openai_api_key="test-key",
        timeout_seconds=30,
    )
    
    with patch.object(OpenAIProvider, '__init__', lambda x, **kwargs: None), \
         patch.object(OllamaProvider, '__init__', lambda x, **kwargs: None):
        
        mock_openai = MockProvider("OpenAI", timeout=True)
        mock_ollama = MockProvider("Ollama", should_fail=False)
        
        config.providers = [mock_openai, mock_ollama]
        
        chain = LLMFallbackChain.__new__(LLMFallbackChain)
        chain.config = config
        chain.providers = [mock_openai, mock_ollama]
        
        # Verify timeout is configured
        assert chain.config.timeout_seconds == 30
        
        response = await chain.generate("Test prompt")
        assert response == "Response from Ollama"


@pytest.mark.asyncio
async def test_fallback_with_mixed_errors():
    """Test Fallback with mixed error types (timeout + exception)."""
    config = FallbackConfig(
        fallback_enabled=True,
        fallback_order=["openai", "ollama", "ollama_tiny"],
        openai_api_key="test-key",
    )
    
    with patch.object(OpenAIProvider, '__init__', lambda x, **kwargs: None), \
         patch.object(OllamaProvider, '__init__', lambda x, **kwargs: None), \
         patch.object(OllamaTinyProvider, '__init__', lambda x, **kwargs: None):
        
        mock_openai = MockProvider("OpenAI", timeout=True)
        mock_ollama = MockProvider("Ollama", should_fail=True)
        mock_ollama_tiny = MockProvider("Ollama-Tiny", should_fail=False)
        
        config.providers = [mock_openai, mock_ollama, mock_ollama_tiny]
        
        chain = LLMFallbackChain.__new__(LLMFallbackChain)
        chain.config = config
        chain.providers = [mock_openai, mock_ollama, mock_ollama_tiny]
        
        response = await chain.generate("Test prompt")
        
        assert response == "Response from Ollama-Tiny"
        assert mock_openai.call_count == 1
        assert mock_ollama.call_count == 1
        assert mock_ollama_tiny.call_count == 1


# =============================================================================
# Fallback Disabled Tests
# =============================================================================

@pytest.mark.asyncio
async def test_fallback_disabled_uses_only_first_provider():
    """Test that fallback is disabled when configured."""
    config = FallbackConfig(
        fallback_enabled=False,
        fallback_order=["openai", "ollama"],
        openai_api_key="test-key",
    )
    
    with patch.object(OpenAIProvider, '__init__', lambda x, **kwargs: None):
        
        mock_openai = MockProvider("OpenAI", should_fail=False)
        
        config.providers = [mock_openai]
        
        chain = LLMFallbackChain.__new__(LLMFallbackChain)
        chain.config = config
        chain.providers = [mock_openai]
        
        response = await chain.generate("Test prompt")
        
        assert response == "Response from OpenAI"
        assert mock_openai.call_count == 1


# =============================================================================
# YAML Configuration Tests
# =============================================================================

def test_create_fallback_chain_from_yaml_default_config():
    """Test creating fallback chain from YAML with default config."""
    yaml_config = {
        "fallback_enabled": True,
        "fallback_order": ["openai", "ollama", "ollama_tiny"],
        "provider": "gpt-4",
        "openai_api_key": "test-key",
        "ollama_url": "http://localhost:11434",
        "ollama_model": "qwen3.5",
        "ollama_tiny_model": "qwen3.5:7b",
        "timeout_seconds": 30,
    }
    
    with patch.object(OpenAIProvider, '__init__', lambda x, **kwargs: None), \
         patch.object(OllamaProvider, '__init__', lambda x, **kwargs: None), \
         patch.object(OllamaTinyProvider, '__init__', lambda x, **kwargs: None):
        
        chain = create_fallback_chain_from_yaml(yaml_config)
        
        assert chain.config.fallback_enabled is True
        assert chain.config.fallback_order == ["openai", "ollama", "ollama_tiny"]
        assert chain.config.provider == "gpt-4"
        assert chain.config.timeout_seconds == 30
        assert len(chain.providers) == 3


def test_create_fallback_chain_from_yaml_custom_config():
    """Test creating fallback chain from YAML with custom config."""
    yaml_config = {
        "fallback_enabled": True,
        "fallback_order": ["ollama", "ollama_tiny"],
        "provider": "gpt-4-turbo",
        "openai_api_key": "test-key",
        "ollama_url": "http://localhost:11434",
        "ollama_model": "qwen2.5:7b",
        "ollama_tiny_model": "qwen2.5:1.5b",
        "timeout_seconds": 60,
    }
    
    with patch.object(OllamaProvider, '__init__', lambda x, **kwargs: None), \
         patch.object(OllamaTinyProvider, '__init__', lambda x, **kwargs: None):
        
        chain = create_fallback_chain_from_yaml(yaml_config)
        
        assert chain.config.fallback_enabled is True
        assert chain.config.fallback_order == ["ollama", "ollama_tiny"]
        assert chain.config.timeout_seconds == 60
        assert len(chain.providers) == 2


def test_create_fallback_chain_from_yaml_defaults():
    """Test creating fallback chain from YAML with missing values uses defaults."""
    yaml_config = {}
    
    with patch.object(OpenAIProvider, '__init__', lambda x, **kwargs: None), \
         patch.object(OllamaProvider, '__init__', lambda x, **kwargs: None), \
         patch.object(OllamaTinyProvider, '__init__', lambda x, **kwargs: None):
        
        chain = create_fallback_chain_from_yaml(yaml_config)
        
        assert chain.config.fallback_enabled is True
        assert chain.config.fallback_order == ["openai", "ollama", "ollama_tiny"]
        assert chain.config.timeout_seconds == 30


# =============================================================================
# Helper Method Tests
# =============================================================================

def test_get_available_providers():
    """Test getting list of available provider names."""
    config = FallbackConfig(
        fallback_enabled=True,
        fallback_order=["openai", "ollama"],
        openai_api_key="test-key",
    )
    
    with patch.object(OpenAIProvider, '__init__', lambda x, **kwargs: None), \
         patch.object(OllamaProvider, '__init__', lambda x, **kwargs: None):
        
        mock_openai = MockProvider("OpenAI")
        mock_ollama = MockProvider("Ollama")
        
        config.providers = [mock_openai, mock_ollama]
        
        chain = LLMFallbackChain.__new__(LLMFallbackChain)
        chain.config = config
        chain.providers = [mock_openai, mock_ollama]
        
        providers = chain.get_available_providers()
        
        assert providers == ["OpenAI", "Ollama"]


def test_get_primary_provider():
    """Test getting the primary (first) provider."""
    config = FallbackConfig(
        fallback_enabled=True,
        fallback_order=["openai", "ollama"],
        openai_api_key="test-key",
    )
    
    with patch.object(OpenAIProvider, '__init__', lambda x, **kwargs: None), \
         patch.object(OllamaProvider, '__init__', lambda x, **kwargs: None):
        
        mock_openai = MockProvider("OpenAI")
        mock_ollama = MockProvider("Ollama")
        
        config.providers = [mock_openai, mock_ollama]
        
        chain = LLMFallbackChain.__new__(LLMFallbackChain)
        chain.config = config
        chain.providers = [mock_openai, mock_ollama]
        
        primary = chain.get_primary_provider()
        
        assert primary == "OpenAI"


def test_get_primary_provider_empty():
    """Test getting primary provider when no providers available."""
    config = FallbackConfig(
        fallback_enabled=True,
        fallback_order=[],
        openai_api_key="test-key",
    )
    
    chain = LLMFallbackChain.__new__(LLMFallbackChain)
    chain.config = config
    chain.providers = []
    
    primary = chain.get_primary_provider()
    
    assert primary is None
