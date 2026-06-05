"""Multi-source search — parallel data fetching from Serper, GitHub, HN.

Each source returns a list of SearchResult objects.
All sources are fetched in parallel via asyncio.gather.
Uses shared httpx.AsyncClient with connection pooling for performance.
"""

import asyncio
import logging
import os
from typing import Any

import httpx

from trend_engine.config import get_settings
from trend_engine.models import SearchResult, SourceType

logger = logging.getLogger(__name__)

SERPER_API_URL = "https://google.serper.dev/search"
GITHUB_API_URL = "https://api.github.com"
HN_ALGOLIA_URL = "https://hn.algolia.com/api/v1"

# Concurrency controls
_MAX_CONCURRENT = 3
_STAGGER_SECS = 0.15  # Reduced from 0.3 — pool handles back-pressure


async def search_all(
    serper_queries: list[str],
    github_queries: list[str],
    hn_queries: list[str],
    *,
    timeout: float = 25.0,
    client: httpx.AsyncClient | None = None,
) -> list[SearchResult]:
    """Run all source searches in parallel and merge results.

    Args:
        serper_queries: Text queries for Google via Serper.
        github_queries: Search terms for GitHub API.
        hn_queries: Search terms for HN Algolia.
        timeout: HTTP request timeout in seconds.
        client: Optional shared httpx.AsyncClient (recommended).

    Returns:
        Merged list of SearchResult from all sources.
    """
    own_client = client is None
    if own_client:
        client = httpx.AsyncClient(
            timeout=timeout,
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=5),
        )

    try:
        results = await asyncio.gather(
            _search_serper_batch(client, serper_queries),
            _search_github_batch(client, github_queries),
            _search_hn_batch(client, hn_queries),
            return_exceptions=True,
        )
    finally:
        if own_client:
            await client.aclose()

    all_results: list[SearchResult] = []
    for result in results:
        if isinstance(result, Exception):
            logger.warning(f"Source search failed: {result}")
            continue
        all_results.extend(result)

    logger.info(f"SearchSources: collected {len(all_results)} results")
    return all_results


# ── Serper (Google Search) ─────────────────────────────────────────


async def _search_serper_batch(
    client: httpx.AsyncClient,
    queries: list[str],
) -> list[SearchResult]:
    """Run Serper queries with batched concurrency."""
    settings = get_settings()
    api_key = settings.serper_api_key if hasattr(settings, "serper_api_key") else ""
    if not api_key:
        logger.warning("SERPER_API_KEY not set, skipping web search")
        return []

    queries = queries[:10]
    sem = asyncio.Semaphore(_MAX_CONCURRENT)

    async def _one(q: str) -> list[SearchResult]:
        async with sem:
            res = await _search_serper_single(client, q, api_key)
            await asyncio.sleep(_STAGGER_SECS)
            return res

    nested = await asyncio.gather(
        *[_one(q) for q in queries], return_exceptions=True
    )
    out: list[SearchResult] = []
    for batch in nested:
        if isinstance(batch, Exception):
            logger.warning(f"Serper query failed: {batch}")
        else:
            out.extend(batch)
    return out


async def _search_serper_single(
    client: httpx.AsyncClient, query: str, api_key: str
) -> list[SearchResult]:
    try:
        resp = await client.post(
            SERPER_API_URL,
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={"q": query, "num": 5},
        )
        resp.raise_for_status()
        data = resp.json()
        return [
            SearchResult(
                title=item.get("title", ""),
                snippet=item.get("snippet", ""),
                url=item.get("link", ""),
                source=SourceType.SERPER,
                score=item.get("position", 0),
                raw_data=item,
            )
            for item in data.get("organic", [])[:5]
        ]
    except Exception as e:
        logger.error(f"Serper search failed for '{query}': {e}")
        return []


# ── GitHub (Repos) ─────────────────────────────────────────────────


async def _search_github_batch(
    client: httpx.AsyncClient, queries: list[str]
) -> list[SearchResult]:
    queries = queries[:5]
    sem = asyncio.Semaphore(_MAX_CONCURRENT)

    async def _one(q: str) -> list[SearchResult]:
        async with sem:
            res = await _search_github_repos(client, q)
            await asyncio.sleep(_STAGGER_SECS)
            return res

    nested = await asyncio.gather(
        *[_one(q) for q in queries], return_exceptions=True
    )
    results: list[SearchResult] = []
    seen_urls: set[str] = set()
    for batch in nested:
        if isinstance(batch, Exception):
            logger.warning(f"GitHub query failed: {batch}")
            continue
        for r in batch:
            if r.url not in seen_urls:
                seen_urls.add(r.url)
                results.append(r)
    return results


async def _search_github_repos(
    client: httpx.AsyncClient, query: str
) -> list[SearchResult]:
    try:
        headers: dict[str, str] = {"Accept": "application/vnd.github.v3+json"}
        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            headers["Authorization"] = f"Bearer {github_token}"

        resp = await client.get(
            f"{GITHUB_API_URL}/search/repositories",
            params={"q": query, "sort": "stars", "order": "desc", "per_page": 5},
            headers=headers,
        )
        resp.raise_for_status()
        return [_repo_to_result(r) for r in resp.json().get("items", [])[:5]]
    except Exception as e:
        logger.error(f"GitHub search failed for '{query}': {e}")
        return []


def _repo_to_result(repo: dict[str, Any]) -> SearchResult:
    return SearchResult(
        title=repo.get("full_name", ""),
        snippet=repo.get("description", "") or "",
        url=repo.get("html_url", ""),
        source=SourceType.GITHUB_SEARCH,
        score=repo.get("stargazers_count", 0),
        published_at=repo.get("updated_at", "")[:10],
        raw_data={
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "language": repo.get("language", ""),
            "topics": repo.get("topics", [])[:5],
        },
    )


# ── Hacker News (Algolia) ─────────────────────────────────────────


async def _search_hn_batch(
    client: httpx.AsyncClient, queries: list[str]
) -> list[SearchResult]:
    nested = await asyncio.gather(
        *[_search_hn_single(client, q) for q in queries],
        return_exceptions=True,
    )
    results: list[SearchResult] = []
    seen_ids: set[str] = set()
    for batch in nested:
        if isinstance(batch, Exception):
            logger.warning(f"HN query failed: {batch}")
            continue
        for r in batch:
            oid = r.raw_data.get("objectID", "")
            if oid and oid not in seen_ids:
                seen_ids.add(oid)
                results.append(r)
            elif not oid:
                results.append(r)
    return results


async def _search_hn_single(
    client: httpx.AsyncClient, query: str
) -> list[SearchResult]:
    try:
        resp = await client.get(
            f"{HN_ALGOLIA_URL}/search",
            params={"query": query, "tags": "story", "hitsPerPage": 10},
        )
        resp.raise_for_status()
        hits = resp.json().get("hits", [])
        return [
            SearchResult(
                title=hit.get("title", ""),
                snippet="",
                url=(
                    hit.get("url", "")
                    or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"
                ),
                source=SourceType.HACKER_NEWS,
                score=hit.get("points", 0) or 0,
                published_at=hit.get("created_at", "")[:10],
                raw_data={
                    "objectID": hit.get("objectID", ""),
                    "num_comments": hit.get("num_comments", 0),
                    "author": hit.get("author", ""),
                },
            )
            for hit in hits[:5]
        ]
    except Exception as e:
        logger.error(f"HN search failed for '{query}': {e}")
        return []
