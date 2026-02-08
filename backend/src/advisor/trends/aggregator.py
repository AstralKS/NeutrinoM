"""Trend aggregator - fetches tech trends from multiple sources.

Sources:
- Hacker News: Top/Show/Ask stories via Firebase API
- Dev.to: Trending articles via REST API
- GitHub: Trending repos (scraped from trending page)

All sources are fetched in parallel for efficiency.
"""

import asyncio
import contextlib
import logging
import re
from datetime import datetime

import httpx

from advisor.trends.models import (
    TECH_KEYWORDS,
    TrendCategory,
    TrendItem,
    TrendSource,
)

logger = logging.getLogger(__name__)

# API endpoints
HN_API_BASE = "https://hacker-news.firebaseio.com/v0"
DEVTO_API_BASE = "https://dev.to/api"


class TrendAggregator:
    """Aggregates technology trends from multiple sources."""

    def __init__(self, timeout: float = 30.0) -> None:
        """Initialize with HTTP client settings."""
        self._timeout = timeout

    async def fetch_all_trends(
        self,
        max_per_source: int = 30,
    ) -> list[TrendItem]:
        """Fetch trends from all sources in parallel.

        Args:
            max_per_source: Maximum items to fetch per source.

        Returns:
            Combined list of trends from all sources.
        """
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            # Fetch from all sources concurrently
            results = await asyncio.gather(
                self._fetch_hacker_news(client, max_per_source),
                self._fetch_devto(client, max_per_source),
                self._fetch_github_trending(client, max_per_source),
                return_exceptions=True,
            )

            all_trends: list[TrendItem] = []
            for result in results:
                if isinstance(result, Exception):
                    logger.warning(f"Trend source failed: {result}")
                    continue
                all_trends.extend(result)

            # Sort by score
            all_trends.sort(key=lambda t: t.score, reverse=True)
            return all_trends

    async def _fetch_hacker_news(
        self,
        client: httpx.AsyncClient,
        limit: int,
    ) -> list[TrendItem]:
        """Fetch top stories from Hacker News."""
        trends: list[TrendItem] = []

        try:
            # Get top story IDs
            resp = await client.get(f"{HN_API_BASE}/topstories.json")
            resp.raise_for_status()
            story_ids = resp.json()[:limit]

            # Fetch story details in parallel (batched)
            tasks = [
                client.get(f"{HN_API_BASE}/item/{sid}.json")
                for sid in story_ids
            ]
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            for resp in responses:
                if isinstance(resp, Exception):
                    continue
                if resp.status_code != 200:
                    continue

                story = resp.json()
                if not story or story.get("type") != "story":
                    continue

                # Extract technologies from title
                title = story.get("title", "")
                technologies = self._extract_technologies(title)
                category = self._categorize_trend(title, technologies)

                trends.append(TrendItem(
                    id=f"hn_{story.get('id')}",
                    title=title,
                    url=story.get("url", f"https://news.ycombinator.com/item?id={story.get('id')}"),
                    source=TrendSource.HACKER_NEWS,
                    category=category,
                    score=story.get("score", 0),
                    comments=story.get("descendants", 0),
                    published_at=datetime.fromtimestamp(story.get("time", 0)),
                    technologies=technologies,
                    author=story.get("by", ""),
                ))

            logger.info(f"Fetched {len(trends)} trends from Hacker News")
        except Exception as e:
            logger.error(f"HN fetch failed: {e}")

        return trends

    async def _fetch_devto(
        self,
        client: httpx.AsyncClient,
        limit: int,
    ) -> list[TrendItem]:
        """Fetch trending articles from Dev.to."""
        trends: list[TrendItem] = []

        try:
            # Fetch top articles by reactions
            resp = await client.get(
                f"{DEVTO_API_BASE}/articles",
                params={"per_page": limit, "top": 7},  # Top from last 7 days
            )
            resp.raise_for_status()
            articles = resp.json()

            for article in articles:
                title = article.get("title", "")
                tags = article.get("tag_list", [])
                technologies = self._extract_technologies(
                    f"{title} {' '.join(tags)}"
                )
                category = self._categorize_trend(title, technologies)

                # Parse date
                published = None
                if article.get("published_at"):
                    with contextlib.suppress(ValueError, TypeError):
                        published = datetime.fromisoformat(
                            article["published_at"].replace("Z", "+00:00")
                        )

                trends.append(TrendItem(
                    id=f"devto_{article.get('id')}",
                    title=title,
                    url=article.get("url", ""),
                    source=TrendSource.DEV_TO,
                    category=category,
                    score=article.get("public_reactions_count", 0),
                    comments=article.get("comments_count", 0),
                    published_at=published,
                    technologies=technologies + tags[:3],
                    summary=article.get("description", ""),
                    author=article.get("user", {}).get("username", ""),
                ))

            logger.info(f"Fetched {len(trends)} trends from Dev.to")
        except Exception as e:
            logger.error(f"Dev.to fetch failed: {e}")

        return trends

    async def _fetch_github_trending(
        self,
        client: httpx.AsyncClient,
        limit: int,
    ) -> list[TrendItem]:
        """Fetch trending repositories from GitHub (via HTML parsing)."""
        trends: list[TrendItem] = []

        try:
            # GitHub trending page for all languages
            resp = await client.get(
                "https://github.com/trending",
                headers={"Accept": "text/html"},
            )
            resp.raise_for_status()
            html = resp.text

            # Parse trending repos (simplified regex parsing)
            repos = re.findall(
                r'<article class="Box-row"[^>]*>(.*?)</article>',
                html,
                re.DOTALL,
            )

            for _i, repo_html in enumerate(repos[:limit]):
                # Extract repo name
                repo_match = re.search(
                    r'href="/([^"]+)"[^>]*class="[^"]*Link[^"]*"',
                    repo_html,
                )
                if not repo_match:
                    continue

                repo_name = repo_match.group(1).strip()
                if repo_name.count("/") != 1:
                    continue

                # Extract description
                desc_match = re.search(
                    r'<p class="[^"]*text-gray[^"]*"[^>]*>([^<]+)</p>',
                    repo_html,
                )
                description = desc_match.group(1).strip() if desc_match else ""

                # Extract stars today
                stars_match = re.search(r'(\d+(?:,\d+)*)\s*stars', repo_html)
                stars = int(stars_match.group(1).replace(",", "")) if stars_match else 0

                # Extract language
                lang_match = re.search(
                    r'<span itemprop="programmingLanguage">([^<]+)</span>',
                    repo_html,
                )
                language = lang_match.group(1).strip() if lang_match else ""

                technologies = self._extract_technologies(
                    f"{repo_name} {description} {language}"
                )
                if language:
                    technologies.append(language.lower())

                trends.append(TrendItem(
                    id=f"gh_{repo_name.replace('/', '_')}",
                    title=f"{repo_name}: {description[:100]}" if description else repo_name,
                    url=f"https://github.com/{repo_name}",
                    source=TrendSource.GITHUB_TRENDING,
                    category=self._categorize_trend(description, technologies),
                    score=stars,
                    technologies=list(set(technologies)),
                    summary=description,
                ))

            logger.info(f"Fetched {len(trends)} trends from GitHub Trending")
        except Exception as e:
            logger.error(f"GitHub Trending fetch failed: {e}")

        return trends

    def _extract_technologies(self, text: str) -> list[str]:
        """Extract technology mentions from text."""
        text_lower = text.lower()
        found: list[str] = []

        for tech, keywords in TECH_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    found.append(tech)
                    break

        return list(set(found))

    def _categorize_trend(
        self,
        title: str,
        technologies: list[str],
    ) -> TrendCategory:
        """Categorize a trend based on content."""
        title_lower = title.lower()

        if any(t in technologies for t in ["ai", "vector_db"]):
            return TrendCategory.AI_ML
        if "security" in title_lower or "vulnerability" in title_lower:
            return TrendCategory.SECURITY
        if any(t in technologies for t in ["cloud", "devops"]):
            return TrendCategory.DEVOPS
        if "database" in technologies:
            return TrendCategory.DATABASE
        if any(t in technologies for t in ["react", "vue", "svelte"]):
            return TrendCategory.FRAMEWORK
        if any(t in technologies for t in ["python", "javascript", "rust", "go"]):
            return TrendCategory.LANGUAGE

        return TrendCategory.GENERAL
