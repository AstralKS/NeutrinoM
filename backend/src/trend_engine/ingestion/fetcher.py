"""URL fetcher — rate-limited, robots.txt-respecting HTTP fetcher."""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict
from urllib.parse import urlparse

import httpx

from trend_engine.config import get_settings
from trend_engine.db.client import get_http_client

logger = logging.getLogger(__name__)


class RateLimiter:
    """Per-domain rate limiter."""

    def __init__(self, min_interval: float = 1.0) -> None:
        self._min_interval = min_interval
        self._last_request: dict[str, float] = defaultdict(float)
        self._locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def wait(self, domain: str) -> None:
        async with self._locks[domain]:
            elapsed = time.monotonic() - self._last_request[domain]
            if elapsed < self._min_interval:
                await asyncio.sleep(self._min_interval - elapsed)
            self._last_request[domain] = time.monotonic()


class Fetcher:
    """Async URL fetcher with rate limiting and robots.txt compliance."""

    def __init__(self) -> None:
        settings = get_settings()
        self._limiter = RateLimiter(settings.rate_limit_per_domain)
        self._robots_cache: dict[str, set[str]] = {}

    @property
    def _client(self) -> httpx.AsyncClient:
        return get_http_client()

    async def _check_robots(self, url: str) -> bool:
        """Rudimentary robots.txt check — respects Disallow for *."""
        parsed = urlparse(url)
        domain = parsed.netloc
        if domain not in self._robots_cache:
            try:
                robots_url = f"{parsed.scheme}://{domain}/robots.txt"
                resp = await self._client.get(robots_url, timeout=5.0)
                disallowed: set[str] = set()
                if resp.status_code == 200:
                    current_agent = False
                    for line in resp.text.splitlines():
                        line = line.strip()
                        if line.lower().startswith("user-agent:"):
                            agent = line.split(":", 1)[1].strip()
                            current_agent = agent == "*"
                        elif current_agent and line.lower().startswith("disallow:"):
                            path = line.split(":", 1)[1].strip()
                            if path:
                                disallowed.add(path)
                self._robots_cache[domain] = disallowed
            except Exception:
                self._robots_cache[domain] = set()

        path = parsed.path or "/"
        for disallowed_path in self._robots_cache.get(domain, set()):
            if path.startswith(disallowed_path):
                logger.info(f"Blocked by robots.txt: {url}")
                return False
        return True

    async def fetch(self, url: str) -> str | None:
        """Fetch URL content, respecting robots.txt and rate limits.

        Returns HTML text or None on failure.
        """
        if not await self._check_robots(url):
            return None

        domain = urlparse(url).netloc
        await self._limiter.wait(domain)

        try:
            resp = await self._client.get(
                url,
                follow_redirects=True,
                timeout=15.0,
                headers={
                    "User-Agent": "TrendIntelligenceBot/1.0 (+trend-engine)",
                },
            )
            if resp.status_code != 200:
                logger.warning(f"HTTP {resp.status_code} for {url}")
                return None
            return resp.text
        except httpx.HTTPError as exc:
            logger.error(f"Fetch error for {url}: {exc}")
            return None
