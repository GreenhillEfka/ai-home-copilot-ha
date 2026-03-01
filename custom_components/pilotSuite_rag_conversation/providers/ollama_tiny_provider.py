"""Ollama Tiny Provider implementation (qwen2.5:1.5b)."""

import asyncio
import aiohttp
import logging
from typing import Optional

from ..llm_provider import BaseLLMProvider

_LOGGER = logging.getLogger(__name__)


class OllamaTinyProvider(BaseLLMProvider):
    """Ollama Tiny provider implementation using qwen2.5:1.5b model."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5:1.5b",
        timeout_seconds: int = 30,
    ):
        """Initialize Ollama Tiny provider.
        
        Args:
            base_url: Ollama API base URL (default: http://localhost:11434)
            model: Model to use (default: qwen2.5:1.5b)
            timeout_seconds: Request timeout in seconds
        """
        super().__init__(name="Ollama-Tiny", base_url=base_url, model=model)
        self._timeout_seconds = timeout_seconds

    async def generate(self, prompt: str) -> str:
        """Generate a response using Ollama Tiny qwen2.5:1.5b.
        
        Args:
            prompt: The input prompt to generate a response for
            
        Returns:
            The generated response text
            
        Raises:
            Exception: If generation fails
        """
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 1024,
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self._timeout_seconds),
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Ollama Tiny API error {response.status}: {error_text}")
                    
                    data = await response.json()
                    generated_text = data.get("response", "")
                    
                    if not generated_text:
                        raise Exception("Ollama Tiny returned empty response")
                    
                    await self._log_success(len(prompt), len(generated_text))
                    return generated_text
                    
        except asyncio.TimeoutError:
            error = Exception(f"Request timed out after {self._timeout_seconds}s")
            await self._log_error(error)
            raise
        except aiohttp.ClientError as e:
            await self._log_error(e)
            raise
        except Exception as e:
            await self._log_error(e)
            raise
