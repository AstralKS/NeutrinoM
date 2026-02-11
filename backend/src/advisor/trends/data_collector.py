"""Multi-source data collector for trend analysis.

Fetches data from:
- Serper API (Google search)
- GitHub API (trending repos)
- Hacker News API (existing aggregator)

All API keys are loaded from environment, never hardcoded.
Optimized with parallel async fetching for performance.
"""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

import httpx

from advisor.config import get_settings
from advisor.trends.models import RawTrendData

logger = logging.getLogger(__name__)

SERPER_API_URL = "https://google.serper.dev/search"
GITHUB_API_URL = "https://api.github.com"
HN_API_BASE = "https://hacker-news.firebaseio.com/v0"


class DataCollector:
    """Collects trend data from multiple sources with parallel fetching."""

    def __init__(self, timeout: float = 15.0) -> None:
        """Initialize with timeout settings.

        Args:
            timeout: HTTP request timeout (reduced for faster failures).
        """
        self._timeout = timeout
        self._settings = get_settings()

    async def collect_for_tag(self, tag: str) -> RawTrendData:
        """Collect data for a specific tag from all sources in parallel.

        Uses asyncio.gather for ~3x faster collection.

        Args:
            tag: Technology tag to search for (e.g., "langchain", "react")

        Returns:
            RawTrendData containing results from all sources.
        """
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            # Parallel fetch - all sources at once
            serper_task = self._search_serper(client, tag)
            github_task = self._search_github(client, tag)
            hn_task = self._search_hn(client, tag)

            serper_results, github_repos, hn_items = await asyncio.gather(
                serper_task,
                github_task,
                hn_task,
                return_exceptions=True,
            )

            # Handle any exceptions gracefully
            if isinstance(serper_results, Exception):
                logger.error(f"Serper failed: {serper_results}")
                serper_results = []
            if isinstance(github_repos, Exception):
                logger.error(f"GitHub failed: {github_repos}")
                github_repos = []
            if isinstance(hn_items, Exception):
                logger.error(f"HN failed: {hn_items}")
                hn_items = []

            return RawTrendData(
                tag=tag,
                serper_results=serper_results,
                github_repos=github_repos,
                hn_items=hn_items,
                collected_at=datetime.now(UTC),
            )

    async def _search_serper(
        self,
        client: httpx.AsyncClient,
        tag: str,
    ) -> list[dict[str, Any]]:
        """Search Google via Serper API.

        API key is loaded from environment settings.
        """
        if not self._settings.serper_api_key:
            logger.warning("SERPER_API_KEY not configured, skipping web search")
            return []

        try:
            # Build search query for trend analysis + version info
            query = f"{tag} latest version release trends 2026"

            headers = {
                "X-API-KEY": self._settings.serper_api_key,
                "Content-Type": "application/json",
            }
            payload = {"q": query, "num": 10}

            response = await client.post(
                SERPER_API_URL,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()

            data = response.json()
            organic_results = data.get("organic", [])

            # Extract minimal relevant fields
            results = []
            for item in organic_results[:10]:
                results.append(
                    {
                        "title": item.get("title", ""),
                        "snippet": item.get("snippet", ""),
                        "link": item.get("link", ""),
                        "position": item.get("position", 0),
                    }
                )

            logger.info(f"Serper: Found {len(results)} results for '{tag}'")
            return results

        except Exception as e:
            logger.error(f"Serper search failed: {e}")
            return []

    async def _search_github(
        self,
        client: httpx.AsyncClient,
        tag: str,
    ) -> list[dict[str, Any]]:
        """Search GitHub for repositories related to the tag."""
        try:
            # Search for recently updated repos with the tag
            params = {
                "q": f"{tag} in:name,description,topics",
                "sort": "stars",
                "order": "desc",
                "per_page": 10,
            }

            response = await client.get(
                f"{GITHUB_API_URL}/search/repositories",
                params=params,
            )
            response.raise_for_status()

            data = response.json()
            repos = data.get("items", [])

            # Extract minimal relevant fields
            results = []
            for repo in repos[:10]:
                results.append(
                    {
                        "name": repo.get("full_name", ""),
                        "description": repo.get("description", "") or "",
                        "stars": repo.get("stargazers_count", 0),
                        "forks": repo.get("forks_count", 0),
                        "language": repo.get("language", ""),
                        "url": repo.get("html_url", ""),
                        "updated_at": repo.get("updated_at", ""),
                        "topics": repo.get("topics", [])[:5],
                    }
                )

            logger.info(f"GitHub: Found {len(results)} repos for '{tag}'")
            return results

        except Exception as e:
            logger.error(f"GitHub search failed: {e}")
            return []

    async def _search_hn(
        self,
        client: httpx.AsyncClient,
        tag: str,
    ) -> list[dict[str, Any]]:
        """Search Hacker News via Algolia API for tag mentions."""
        try:
            # Use Algolia HN Search API
            params = {
                "query": tag,
                "tags": "story",
                "hitsPerPage": 15,
            }

            response = await client.get(
                "https://hn.algolia.com/api/v1/search",
                params=params,
            )
            response.raise_for_status()

            data = response.json()
            hits = data.get("hits", [])

            # Extract minimal relevant fields
            results = []
            for hit in hits[:10]:
                results.append(
                    {
                        "title": hit.get("title", ""),
                        "url": hit.get("url", ""),
                        "points": hit.get("points", 0),
                        "num_comments": hit.get("num_comments", 0),
                        "author": hit.get("author", ""),
                        "created_at": hit.get("created_at", ""),
                        "objectID": hit.get("objectID", ""),
                    }
                )

            logger.info(f"HN: Found {len(results)} stories for '{tag}'")
            return results

        except Exception as e:
            logger.error(f"HN search failed: {e}")
            return []
