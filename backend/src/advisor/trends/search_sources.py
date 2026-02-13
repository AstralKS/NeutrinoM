"""Multi-source search — parallel data fetching from Serper, GitHub, HN.

Each source returns a list of SearchResult objects.
All sources are fetched in parallel via asyncio.gather.

Optimized: batched concurrency with short stagger instead of sequential 1.1s delays.
"""

import asyncio
import logging
from typing import Any

import httpx

from advisor.config import get_settings
from advisor.trends.models import SearchResult, SourceType

logger = logging.getLogger(__name__)

SERPER_API_URL = "https://google.serper.dev/search"
GITHUB_API_URL = "https://api.github.com"
HN_ALGOLIA_URL = "https://hn.algolia.com/api/v1"

# Concurrency controls
BATCH_CONCURRENCY = 3   # Max concurrent requests per source
BATCH_STAGGER = 0.3     # Seconds between batches


async def search_all(
    serper_queries: list[str],
    github_queries: list[str],
    hn_queries: list[str],
    *,
    timeout: float = 30.0,
) -> list[SearchResult]:
    """Run all source searches in parallel and merge results.

    Args:
        serper_queries: Text queries for Google via Serper.
        github_queries: Search terms for GitHub API.
        hn_queries: Search terms for HN Algolia.
        timeout: HTTP request timeout in seconds.

    Returns:
        Merged list of SearchResult from all sources.
    """
    async with httpx.AsyncClient(timeout=timeout) as client:
        tasks = [
            _search_serper_batch(client, serper_queries),
            _search_github_batch(client, github_queries),
            _search_hn_batch(client, hn_queries),
        ]
        results = await asyncio.gather(
            *tasks,
            return_exceptions=True,
        )

    all_results: list[SearchResult] = []
    for result in results:
        if isinstance(result, Exception):
            logger.warning(f"Source search failed: {result}")
            continue
        all_results.extend(result)

    logger.info(f"SearchSources: Collected {len(all_results)} results")
    return all_results


# --- Serper (Google Search) ---


async def _search_serper_batch(
    client: httpx.AsyncClient,
    queries: list[str],
) -> list[SearchResult]:
    """Run Serper queries with batched concurrency (3 at a time, 0.3s stagger)."""
    settings = get_settings()
    if not settings.serper_api_key:
        logger.warning("SERPER_API_KEY not set, skipping web search")
        return []

    queries = queries[:10]  # Hard cap
    sem = asyncio.Semaphore(BATCH_CONCURRENCY)

    async def _with_sem(q: str) -> list[SearchResult]:
        async with sem:
            result = await _search_serper_single(client, q, settings.serper_api_key)
            await asyncio.sleep(BATCH_STAGGER)
            return result

    nested = await asyncio.gather(
        *[_with_sem(q) for q in queries],
        return_exceptions=True,
    )

    results: list[SearchResult] = []
    for batch in nested:
        if isinstance(batch, Exception):
            logger.warning(f"Serper query failed: {batch}")
            continue
        results.extend(batch)
    return results


async def _search_serper_single(
    client: httpx.AsyncClient,
    query: str,
    api_key: str,
) -> list[SearchResult]:
    """Execute a single Serper search query."""
    try:
        resp = await client.post(
            SERPER_API_URL,
            headers={
                "X-API-KEY": api_key,
                "Content-Type": "application/json",
            },
            json={"q": query, "num": 5},
        )
        resp.raise_for_status()
        data = resp.json()

        results: list[SearchResult] = []
        for item in data.get("organic", [])[:5]:
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    snippet=item.get("snippet", ""),
                    url=item.get("link", ""),
                    source=SourceType.SERPER,
                    score=item.get("position", 0),
                    raw_data=item,
                )
            )
        return results
    except Exception as e:
        logger.error(f"Serper search failed for '{query}': {e}")
        return []


# --- GitHub (Repos) ---


async def _search_github_batch(
    client: httpx.AsyncClient,
    queries: list[str],
) -> list[SearchResult]:
    """Run GitHub repo searches with batched concurrency."""
    queries = queries[:5]  # Hard cap
    sem = asyncio.Semaphore(BATCH_CONCURRENCY)

    async def _with_sem(q: str) -> list[SearchResult]:
        async with sem:
            result = await _search_github_repos(client, q)
            await asyncio.sleep(BATCH_STAGGER)
            return result

    nested = await asyncio.gather(
        *[_with_sem(q) for q in queries],
        return_exceptions=True,
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
    client: httpx.AsyncClient,
    query: str,
) -> list[SearchResult]:
    """Search GitHub repositories."""
    import os
    try:
        headers: dict[str, str] = {"Accept": "application/vnd.github.v3+json"}
        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            headers["Authorization"] = f"Bearer {github_token}"

        resp = await client.get(
            f"{GITHUB_API_URL}/search/repositories",
            params={
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": 5,
            },
            headers=headers,
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])

        results: list[SearchResult] = []
        for repo in items[:5]:
            results.append(_repo_to_result(repo))
        return results
    except Exception as e:
        logger.error(f"GitHub search failed for '{query}': {e}")
        return []


def _repo_to_result(repo: dict[str, Any]) -> SearchResult:
    """Convert GitHub repo JSON to SearchResult."""
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


# --- Hacker News (Algolia) ---


async def _search_hn_batch(
    client: httpx.AsyncClient,
    queries: list[str],
) -> list[SearchResult]:
    """Run HN Algolia searches in parallel."""
    tasks = [_search_hn_single(client, q) for q in queries]
    nested = await asyncio.gather(*tasks, return_exceptions=True)

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
    client: httpx.AsyncClient,
    query: str,
) -> list[SearchResult]:
    """Search HN via Algolia API."""
    try:
        resp = await client.get(
            f"{HN_ALGOLIA_URL}/search",
            params={
                "query": query,
                "tags": "story",
                "hitsPerPage": 10,
            },
        )
        resp.raise_for_status()
        hits = resp.json().get("hits", [])

        results: list[SearchResult] = []
        for hit in hits[:5]:
            hn_url = (
                hit.get("url", "")
                or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"
            )
            results.append(
                SearchResult(
                    title=hit.get("title", ""),
                    snippet="",
                    url=hn_url,
                    source=SourceType.HACKER_NEWS,
                    score=hit.get("points", 0) or 0,
                    published_at=(hit.get("created_at", "")[:10]),
                    raw_data={
                        "objectID": hit.get("objectID", ""),
                        "num_comments": hit.get("num_comments", 0),
                        "author": hit.get("author", ""),
                    },
                )
            )
        return results
    except Exception as e:
        logger.error(f"HN search failed for '{query}': {e}")
        return []
