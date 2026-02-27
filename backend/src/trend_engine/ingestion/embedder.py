"""Embedding client — generate embeddings via OpenRouter / configurable model.

Uses the shared httpx.AsyncClient. Model is pinned at init.
Changing the model requires a full re-index.

Includes an in-memory LRU cache (keyed by content hash) to avoid
re-embedding identical text chunks across ingestion runs.
"""

from __future__ import annotations

import hashlib
import logging
from collections import OrderedDict
from typing import Any

import httpx

from trend_engine.config import TrendEngineSettings, get_settings
from trend_engine.db.client import get_http_client

logger = logging.getLogger(__name__)

# Module-level LRU cache: content_hash -> embedding vector
_EMBED_CACHE: OrderedDict[str, list[float]] = OrderedDict()
_CACHE_MAX = 2048


def _cache_key(text: str) -> str:
    return hashlib.md5(text.encode(), usedforsecurity=False).hexdigest()


class Embedder:
    """Generate embeddings for text chunks via the configured model."""

    def __init__(self, settings: TrendEngineSettings | None = None) -> None:
        self._settings = settings or get_settings()
        self._model = self._settings.embedding_model
        self._dim = self._settings.embedding_dim
        self._batch_size = self._settings.embedding_batch_size
        self._base_url = self._settings.openrouter_base_url
        self._api_key = self._settings.openrouter_api_key

    @property
    def _client(self) -> httpx.AsyncClient:
        return get_http_client()

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts.

        Checks in-memory cache first, only sends uncached texts to the API.

        Returns:
            List of embedding vectors, same order as input texts.
        """
        # Separate cached vs uncached
        results: list[list[float] | None] = [None] * len(texts)
        uncached_indices: list[int] = []
        uncached_texts: list[str] = []

        for i, text in enumerate(texts):
            key = _cache_key(text)
            cached = _EMBED_CACHE.get(key)
            if cached is not None:
                _EMBED_CACHE.move_to_end(key)  # refresh LRU position
                results[i] = cached
            else:
                uncached_indices.append(i)
                uncached_texts.append(text)

        # Batch-embed only uncached texts
        if uncached_texts:
            all_new: list[list[float]] = []
            for batch_start in range(0, len(uncached_texts), self._batch_size):
                batch = uncached_texts[batch_start: batch_start + self._batch_size]
                embeddings = await self._embed_batch(batch)
                all_new.extend(embeddings)

            # Store results and update cache
            for idx, emb in zip(uncached_indices, all_new):
                results[idx] = emb
                key = _cache_key(texts[idx])
                _EMBED_CACHE[key] = emb
                if len(_EMBED_CACHE) > _CACHE_MAX:
                    _EMBED_CACHE.popitem(last=False)  # evict oldest

        cache_hits = len(texts) - len(uncached_texts)
        if cache_hits > 0:
            logger.debug(
                f"Embed cache: {cache_hits}/{len(texts)} hits"
            )

        return results  # type: ignore[return-value]

    async def embed_single(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        results = await self.embed_texts([text])
        return results[0]

    async def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Call the embedding API for a batch of texts."""
        try:
            resp = await self._client.post(
                f"{self._base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model,
                    "input": texts,
                },
                timeout=60.0,
            )
            resp.raise_for_status()
            data = resp.json()

            # OpenRouter/OpenAI format: data.data[i].embedding
            embeddings = [item["embedding"] for item in data["data"]]

            # Validate dimension
            for emb in embeddings:
                if len(emb) != self._dim:
                    raise ValueError(
                        f"Embedding dim mismatch: got {len(emb)}, "
                        f"expected {self._dim}"
                    )

            return embeddings

        except httpx.HTTPError as exc:
            logger.error(f"Embedding API error: {exc}")
            raise
        except (KeyError, IndexError) as exc:
            logger.error(f"Unexpected embedding response format: {exc}")
            raise
