"""Tests for LLM Providers (OpenAI, Ollama, OllamaTiny)."""

import pytest
import asyncio
import logging
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from aiohttp import ClientError

# Now import from the package
from custom_components.pilotSuite_rag_conversation.providers import (
    OpenAIProvider,
    OllamaProvider,
    OllamaTinyProvider,
)


# =============================================================================
# OpenAIProvider Tests
# =============================================================================

@pytest.mark.asyncio
async def test_openai_provider_generate_success():
    """Test OpenAIProvider.generate() with successful response."""
    provider = OpenAIProvider(api_key="test-key", model="gpt-4")
    
    mock_response_data = {
        "choices": [
            {
                "message": {
                    "content": "This is a test response from OpenAI"
                }
            }
        ]
    }
    
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=mock_response_data)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_session = AsyncMock()
    mock_session.post = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        result = await provider.generate("Test prompt")
        
        assert result == "This is a test response from OpenAI"
        mock_session.post.assert_called_once()


@pytest.mark.asyncio
async def test_openai_provider_timeout_handling():
    """Test OpenAIProvider timeout handling."""
    provider = OpenAIProvider(api_key="test-key", model="gpt-4", timeout_seconds=30)
    
    mock_response = AsyncMock()
    mock_response.__aenter__ = AsyncMock(side_effect=asyncio.TimeoutError("Request timed out"))
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_session = AsyncMock()
    mock_session.post = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        with pytest.raises(asyncio.TimeoutError, match="timed out"):
            await provider.generate("Test prompt")


@pytest.mark.asyncio
async def test_openai_provider_http_error():
    """Test OpenAIProvider HTTP error handling."""
    provider = OpenAIProvider(api_key="test-key", model="gpt-4")
    
    mock_response = AsyncMock()
    mock_response.status = 401
    mock_response.text = AsyncMock(return_value="Unauthorized")
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_session = AsyncMock()
    mock_session.post = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        with pytest.raises(Exception, match="OpenAI API error 401"):
            await provider.generate("Test prompt")


@pytest.mark.asyncio
async def test_openai_provider_connection_error():
    """Test OpenAIProvider connection error handling."""
    provider = OpenAIProvider(api_key="test-key", model="gpt-4")
    
    mock_response = AsyncMock()
    mock_response.__aenter__ = AsyncMock(side_effect=ClientError("Connection failed"))
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_session = AsyncMock()
    mock_session.post = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        with pytest.raises(ClientError, match="Connection failed"):
            await provider.generate("Test prompt")


# =============================================================================
# OllamaProvider Tests
# =============================================================================

@pytest.mark.asyncio
async def test_ollama_provider_generate_success():
    """Test OllamaProvider.generate() with successful response."""
    provider = OllamaProvider(base_url="http://localhost:11434", model="qwen3.5")
    
    mock_response_data = {
        "response": "This is a test response from Ollama"
    }
    
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=mock_response_data)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_session = AsyncMock()
    mock_session.post = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        result = await provider.generate("Test prompt")
        
        assert result == "This is a test response from Ollama"
        mock_session.post.assert_called_once()


@pytest.mark.asyncio
async def test_ollama_provider_timeout_handling():
    """Test OllamaProvider timeout handling."""
    provider = OllamaProvider(base_url="http://localhost:11434", model="qwen3.5", timeout_seconds=30)
    
    mock_response = AsyncMock()
    mock_response.__aenter__ = AsyncMock(side_effect=asyncio.TimeoutError("Request timed out"))
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_session = AsyncMock()
    mock_session.post = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        with pytest.raises(asyncio.TimeoutError, match="timed out"):
            await provider.generate("Test prompt")


@pytest.mark.asyncio
async def test_ollama_provider_http_error():
    """Test OllamaProvider HTTP error handling."""
    provider = OllamaProvider(base_url="http://localhost:11434", model="qwen3.5")
    
    mock_response = AsyncMock()
    mock_response.status = 500
    mock_response.text = AsyncMock(return_value="Internal Server Error")
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_session = AsyncMock()
    mock_session.post = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        with pytest.raises(Exception, match="Ollama API error 500"):
            await provider.generate("Test prompt")


@pytest.mark.asyncio
async def test_ollama_provider_connection_error():
    """Test OllamaProvider connection error handling."""
    provider = OllamaProvider(base_url="http://localhost:11434", model="qwen3.5")
    
    mock_response = AsyncMock()
    mock_response.__aenter__ = AsyncMock(side_effect=ClientError("Connection refused"))
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_session = AsyncMock()
    mock_session.post = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        with pytest.raises(ClientError, match="Connection refused"):
            await provider.generate("Test prompt")


# =============================================================================
# OllamaTinyProvider Tests
# =============================================================================

@pytest.mark.asyncio
async def test_ollama_tiny_provider_generate_success():
    """Test OllamaTinyProvider.generate() with successful response."""
    provider = OllamaTinyProvider(base_url="http://localhost:11434", model="qwen2.5:1.5b")
    
    mock_response_data = {
        "response": "This is a test response from Ollama Tiny"
    }
    
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=mock_response_data)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_session = AsyncMock()
    mock_session.post = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        result = await provider.generate("Test prompt")
        
        assert result == "This is a test response from Ollama Tiny"
        mock_session.post.assert_called_once()


@pytest.mark.asyncio
async def test_ollama_tiny_provider_timeout_handling():
    """Test OllamaTinyProvider timeout handling."""
    provider = OllamaTinyProvider(base_url="http://localhost:11434", model="qwen2.5:1.5b", timeout_seconds=30)
    
    mock_response = AsyncMock()
    mock_response.__aenter__ = AsyncMock(side_effect=asyncio.TimeoutError("Request timed out"))
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_session = AsyncMock()
    mock_session.post = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        with pytest.raises(asyncio.TimeoutError, match="timed out"):
            await provider.generate("Test prompt")


@pytest.mark.asyncio
async def test_ollama_tiny_provider_http_error():
    """Test OllamaTinyProvider HTTP error handling."""
    provider = OllamaTinyProvider(base_url="http://localhost:11434", model="qwen2.5:1.5b")
    
    mock_response = AsyncMock()
    mock_response.status = 404
    mock_response.text = AsyncMock(return_value="Not Found")
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_session = AsyncMock()
    mock_session.post = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        with pytest.raises(Exception, match="Ollama Tiny API error 404"):
            await provider.generate("Test prompt")


@pytest.mark.asyncio
async def test_ollama_tiny_provider_connection_error():
    """Test OllamaTinyProvider connection error handling."""
    provider = OllamaTinyProvider(base_url="http://localhost:11434", model="qwen2.5:1.5b")
    
    mock_response = AsyncMock()
    mock_response.__aenter__ = AsyncMock(side_effect=ClientError("Connection refused"))
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_session = AsyncMock()
    mock_session.post = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        with pytest.raises(ClientError, match="Connection refused"):
            await provider.generate("Test prompt")


# =============================================================================
# Logging Tests
# =============================================================================

@pytest.mark.asyncio
async def test_provider_logging_on_success(caplog):
    """Test logging which provider was successful."""
    caplog.set_level(logging.INFO)
    
    provider = OpenAIProvider(api_key="test-key", model="gpt-4")
    
    mock_response_data = {
        "choices": [
            {
                "message": {
                    "content": "Test response"
                }
            }
        ]
    }
    
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json = AsyncMock(return_value=mock_response_data)
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=None)
    
    mock_session = AsyncMock()
    mock_session.post = MagicMock(return_value=mock_response)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        await provider.generate("Test prompt with 21 chars")
        
        # Check that success was logged
        assert any("[OpenAI] Generation successful" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_provider_logging_on_error(caplog):
    """Test logging when provider fails."""
    caplog.set_level(logging.ERROR)
    
    provider = OpenAIProvider(api_key="test-key", model="gpt-4")
    
    mock_session = AsyncMock()
    mock_session.post.side_effect = Exception("API Error")
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    with patch('aiohttp.ClientSession', return_value=mock_session):
        with pytest.raises(Exception):
            await provider.generate("Test prompt")
        
        # Check that error was logged
        assert any("[OpenAI] Generation failed" in record.message for record in caplog.records)
