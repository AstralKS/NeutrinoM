"""OpenRouter client with multi-key rotation and fallback.

Handles API calls, rate limiting, and automatic failover.
"""

import json
import logging
import time
from typing import Any

import httpx

from advisor.config import get_settings
from advisor.llm.models import AvailableModels

logger = logging.getLogger(__name__)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterError(Exception):
    """Error from OpenRouter API."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class OpenRouterClient:
    """Client for OpenRouter API with key rotation and fallback.

    Features:
    - Multiple API key support with automatic rotation
    - Model fallback on failure
    - Rate limit handling with exponential backoff
    - Token usage tracking
    """

    def __init__(self) -> None:
        """Initialize client with API keys and shared HTTP session."""
        self._settings = get_settings()
        self._api_keys = self._settings.openrouter_api_keys
        self._current_key_index = 0
        self._total_tokens_used = 0
        self._http_client: httpx.AsyncClient | None = None

    def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create shared HTTP client (lazy init)."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=300.0)
        return self._http_client

    async def close(self) -> None:
        """Close the shared HTTP client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None

    @property
    def _current_key(self) -> str:
        """Get current API key."""
        return self._api_keys[self._current_key_index]

    def _rotate_key(self) -> bool:
        """Rotate to next API key.

        Returns:
            True if rotation successful, False if no more keys.
        """
        next_index = self._current_key_index + 1
        if next_index < len(self._api_keys):
            self._current_key_index = next_index
            logger.info(f"Rotated to API key {next_index + 1}")
            return True
        return False

    def _reset_key_rotation(self) -> None:
        """Reset to first API key."""
        self._current_key_index = 0

    async def complete(
        self,
        prompt: str,
        model_id: str | None = None,
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        parse_json: bool = False,
    ) -> dict[str, Any]:
        """Send completion request to OpenRouter.

        Args:
            prompt: User prompt to complete.
            model_id: Model to use (defaults to highest priority).
            system_prompt: Optional system prompt.
            temperature: Sampling temperature (lower = more deterministic).
            max_tokens: Maximum tokens in response.
            parse_json: If True, parse response as JSON.

        Returns:
            Dict with 'content', 'model', and 'usage' keys.

        Raises:
            OpenRouterError: If all API keys and models fail.
        """
        if model_id is None:
            model_id = AvailableModels.get_default().id

        models_to_try = [model_id] + [
            m for m in AvailableModels.get_fallback_order() if m != model_id
        ]

        last_error: Exception | None = None

        for model in models_to_try:
            # Reset key rotation for each model attempt
            self._reset_key_rotation()

            while True:
                try:
                    result = await self._make_request(
                        model=model,
                        prompt=prompt,
                        system_prompt=system_prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )

                    content = result["content"]
                    if parse_json:
                        content = self._parse_json_response(content)

                    return {
                        "content": content,
                        "model": model,
                        "usage": result.get("usage", {}),
                    }

                except OpenRouterError as e:
                    last_error = e
                    if e.status_code == 429 or e.status_code == 401:
                        # Rate limit or auth error - try next key
                        if not self._rotate_key():
                            break  # No more keys, try next model
                    else:
                        break  # Other error, try next model

                except Exception as e:
                    last_error = e
                    logger.warning(f"Error with model {model}: {e}")
                    break

        raise OpenRouterError(
            f"All models and keys exhausted. Last error: {last_error}"
        )

    async def _make_request(
        self,
        model: str,
        prompt: str,
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        """Make HTTP request to OpenRouter API."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self._current_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/ai-development-advisor",
            "X-Title": "AI Development Advisor",
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        client = self._get_http_client()
        start_time = time.perf_counter()

        response = await client.post(
            OPENROUTER_API_URL,
            headers=headers,
            json=payload,
        )

        duration_ms = round((time.perf_counter() - start_time) * 1000)

        if response.status_code != 200:
            raise OpenRouterError(
                f"API error: {response.text}",
                status_code=response.status_code,
            )

        data = response.json()

        if "error" in data:
            raise OpenRouterError(f"API error: {data['error']}")

        # Track usage
        usage = data.get("usage", {})
        self._total_tokens_used += usage.get("total_tokens", 0)

        logger.info(
            f"LLM call to {model} completed in {duration_ms}ms "
            f"(tokens: {usage.get('total_tokens', '?')})"
        )

        return {
            "content": data["choices"][0]["message"]["content"],
            "usage": usage,
            "duration_ms": duration_ms,
        }

    def _parse_json_response(self, content: str) -> Any:
        """Parse JSON from LLM response, handling markdown code blocks."""
        # Strip markdown code blocks if present
        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            # Remove first and last lines (code block markers)
            content = "\n".join(lines[1:-1])

        return json.loads(content)

    @property
    def total_tokens_used(self) -> int:
        """Get total tokens used across all requests."""
        return self._total_tokens_used
