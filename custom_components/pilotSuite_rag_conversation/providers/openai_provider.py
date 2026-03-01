"""OpenAI GPT-4 Provider implementation."""

import asyncio
import aiohttp
import logging
from typing import Optional

from ..llm_provider import BaseLLMProvider

_LOGGER = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT-4 provider implementation."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4",
        base_url: str = "https://api.openai.com/v1",
        timeout_seconds: int = 30,
    ):
        """Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-4)
            base_url: OpenAI API base URL
            timeout_seconds: Request timeout in seconds
        """
        super().__init__(name="OpenAI", base_url=base_url, api_key=api_key, model=model)
        self._timeout_seconds = timeout_seconds

    async def generate(self, prompt: str) -> str:
        """Generate a response using OpenAI GPT-4.
        
        Args:
            prompt: The input prompt to generate a response for
            
        Returns:
            The generated response text
            
        Raises:
            Exception: If generation fails
        """
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 2048,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self._timeout_seconds),
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"OpenAI API error {response.status}: {error_text}")
                    
                    data = await response.json()
                    generated_text = data["choices"][0]["message"]["content"]
                    
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
