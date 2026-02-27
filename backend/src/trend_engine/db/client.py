"""Supabase REST client using a shared httpx.AsyncClient.

One client per process — no per-request instantiation.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from trend_engine.config import TrendEngineSettings, get_settings

logger = logging.getLogger(__name__)

# Module-level singleton — initialized in lifespan, reused everywhere.
_http_client: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    """Return the shared httpx.AsyncClient. Raises if not initialized."""
    if _http_client is None:
        raise RuntimeError(
            "HTTP client not initialized. Call init_http_client() first."
        )
    return _http_client


async def init_http_client() -> httpx.AsyncClient:
    """Create and store the shared httpx.AsyncClient."""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=httpx.Limits(max_connections=50, max_keepalive_connections=10),
        )
    return _http_client


async def close_http_client() -> None:
    """Gracefully close the shared httpx.AsyncClient."""
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None


class SupabaseDB:
    """Thin async wrapper around Supabase REST + SQL endpoints.

    All queries go through the shared httpx.AsyncClient.
    """

    def __init__(self, settings: TrendEngineSettings | None = None) -> None:
        self._settings = settings or get_settings()
        self._base = self._settings.supabase_url
        self._key = self._settings.supabase_service_key

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "apikey": self._key,
            "Authorization": f"Bearer {self._key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    @property
    def _client(self) -> httpx.AsyncClient:
        return get_http_client()

    # ── Table operations ──────────────────────────────────────────

    async def insert(
        self,
        table: str,
        data: dict[str, Any] | list[dict[str, Any]],
        *,
        on_conflict: str | None = None,
        upsert: bool = False,
    ) -> list[dict[str, Any]]:
        """Insert row(s) into a table. Returns inserted rows."""
        headers = {**self._headers}
        if upsert and on_conflict:
            headers["Prefer"] = (
                f"return=representation,resolution=merge-duplicates"
            )
        elif on_conflict:
            headers["Prefer"] = "return=representation,resolution=ignore-duplicates"

        url = f"{self._base}/rest/v1/{table}"
        if on_conflict:
            url += f"?on_conflict={on_conflict}"

        resp = await self._client.post(url, headers=headers, json=data)
        if resp.status_code == 409:
            return []  # duplicate — expected for dedup
        resp.raise_for_status()
        return resp.json()

    async def select(
        self,
        table: str,
        columns: str = "*",
        *,
        filters: dict[str, Any] | None = None,
        order: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """SELECT with optional filters, ordering, and limit."""
        url = f"{self._base}/rest/v1/{table}?select={columns}"
        if filters:
            for col, val in filters.items():
                url += f"&{col}={val}"
        if order:
            url += f"&order={order}"
        if limit:
            url += f"&limit={limit}"

        resp = await self._client.get(url, headers=self._headers)
        resp.raise_for_status()
        return resp.json()

    async def delete(
        self,
        table: str,
        filters: dict[str, str],
    ) -> list[dict[str, Any]]:
        """DELETE rows matching filters."""
        url = f"{self._base}/rest/v1/{table}"
        parts = [f"&{col}={val}" for col, val in filters.items()]
        url += "?" + "&".join(p.lstrip("&") for p in parts)

        resp = await self._client.delete(url, headers=self._headers)
        resp.raise_for_status()
        return resp.json() if resp.text else []

    async def rpc(
        self, fn_name: str, params: dict[str, Any] | None = None
    ) -> Any:
        """Call a Supabase RPC function."""
        url = f"{self._base}/rest/v1/rpc/{fn_name}"
        resp = await self._client.post(
            url, headers=self._headers, json=params or {}
        )
        resp.raise_for_status()
        return resp.json()

    async def execute_sql(self, sql: str) -> Any:
        """Execute raw SQL via Supabase pg endpoint (service role only)."""
        headers = {
            "apikey": self._key,
            "Authorization": f"Bearer {self._key}",
            "Content-Type": "application/json",
        }
        # Use the pg-meta SQL endpoint
        url = f"{self._base}/pg/query"
        resp = await self._client.post(url, headers=headers, json={"query": sql})
        if resp.status_code >= 400:
            logger.error(f"SQL error: {resp.text}")
        resp.raise_for_status()
        return resp.json()
