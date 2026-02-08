"""Trend Master AI Agent - orchestrates tech stack trend analysis.

Main entry point for:
- Tag-based trend analysis
- Weekly collection scheduling
- LLM-powered summarization
- RAG-based querying
"""

import logging
from datetime import UTC, datetime, timedelta

from advisor.llm.client import OpenRouterClient
from advisor.trends.data_collector import DataCollector
from advisor.trends.models import RawTrendData, TrendInsight, TrendSource
from advisor.trends.rag_manager import RAGManager

logger = logging.getLogger(__name__)

# Weekly collection interval
COLLECTION_INTERVAL_DAYS = 7

SUMMARIZATION_PROMPT = """Analyze the following technology trend data for "{tag}" and provide a concise summary.

Data sources:
- Web search results: {serper_count} items
- GitHub repositories: {github_count} items
- Hacker News discussions: {hn_count} items

Raw data:
{raw_data}

Provide your analysis in the following JSON format:
{{
    "key_points": ["5-7 concise bullet points about the current state and direction"],
    "momentum": "rising|stable|declining",
    "risks": ["max 3 key risks or concerns"],
    "opportunities": ["max 3 key opportunities"],
    "direction": "1-2 sentences on where this tech is heading"
}}

Focus on:
- Current direction and maturity
- Architectural shifts and ecosystem growth
- Competing alternatives
- Long-term potential

Be concise - summarize trends, don't list features."""


class TrendMaster:
    """Main AI agent for tech stack trend analysis."""

    def __init__(
        self,
        llm_client: OpenRouterClient | None = None,
        data_collector: DataCollector | None = None,
        rag_manager: RAGManager | None = None,
    ) -> None:
        """Initialize TrendMaster with dependencies.

        Args:
            llm_client: Optional LLM client for summarization.
            data_collector: Optional data collector.
            rag_manager: Optional RAG manager.
        """
        self._llm = llm_client or OpenRouterClient()
        self._collector = data_collector or DataCollector()
        self._rag = rag_manager or RAGManager()

    async def analyze_tag(self, tag: str, force_refresh: bool = False) -> TrendInsight:
        """Analyze trends for a specific tag.

        Uses cached data if available within weekly window.
        Otherwise triggers fresh collection.

        Args:
            tag: Technology tag to analyze (e.g., "langchain", "react")
            force_refresh: If True, bypass cache and collect fresh data.

        Returns:
            TrendInsight with analysis results.
        """
        tag = tag.lower().strip()

        # Check for recent cached data
        if not force_refresh:
            cached = await self._rag.get_recent_for_tag(
                tag, days=COLLECTION_INTERVAL_DAYS
            )
            if cached:
                logger.info(f"Using cached insight for '{tag}'")
                return cached

        # Collect fresh data
        logger.info(f"Collecting fresh data for '{tag}'")
        raw_data = await self._collector.collect_for_tag(tag)

        # Summarize with LLM
        insight = await self._summarize_data(raw_data)

        # Store in RAG
        await self._rag.store_insight(insight)

        return insight

    async def query_trends(self, tag: str) -> list[TrendInsight]:
        """Query stored trends for a tag.

        Returns historical insights without triggering new collection.

        Args:
            tag: Tag to query.

        Returns:
            List of TrendInsights for the tag.
        """
        return await self._rag.search_by_tag(tag.lower().strip())

    async def run_weekly_collection(self, tags: list[str]) -> dict[str, TrendInsight]:
        """Run batch collection for multiple tags.

        Use this for scheduled weekly updates.

        Args:
            tags: List of tags to collect.

        Returns:
            Dict mapping tags to their insights.
        """
        results: dict[str, TrendInsight] = {}

        for tag in tags:
            try:
                insight = await self.analyze_tag(tag, force_refresh=True)
                results[tag] = insight
            except Exception as e:
                logger.error(f"Failed to analyze '{tag}': {e}")

        return results

    def should_collect(self, last_collection: datetime | None) -> bool:
        """Check if collection is needed based on weekly schedule.

        Args:
            last_collection: Datetime of last collection.

        Returns:
            True if collection is needed.
        """
        if last_collection is None:
            return True

        cutoff = datetime.now(UTC) - timedelta(days=COLLECTION_INTERVAL_DAYS)
        return last_collection < cutoff

    async def _summarize_data(self, raw_data: RawTrendData) -> TrendInsight:
        """Summarize raw data using LLM.

        Args:
            raw_data: Collected raw data.

        Returns:
            Summarized TrendInsight.
        """
        # Build context for LLM
        context_parts = []

        if raw_data.serper_results:
            context_parts.append("## Web Search Results")
            for item in raw_data.serper_results[:5]:
                context_parts.append(
                    f"- {item.get('title', '')}: {item.get('snippet', '')}"
                )

        if raw_data.github_repos:
            context_parts.append("\n## GitHub Repositories")
            for repo in raw_data.github_repos[:5]:
                context_parts.append(
                    f"- {repo.get('name', '')} ({repo.get('stars', 0)} stars): "
                    f"{repo.get('description', '')}"
                )

        if raw_data.hn_items:
            context_parts.append("\n## Hacker News Discussions")
            for item in raw_data.hn_items[:5]:
                context_parts.append(
                    f"- {item.get('title', '')} ({item.get('points', 0)} points)"
                )

        raw_context = "\n".join(context_parts)

        prompt = SUMMARIZATION_PROMPT.format(
            tag=raw_data.tag,
            serper_count=len(raw_data.serper_results),
            github_count=len(raw_data.github_repos),
            hn_count=len(raw_data.hn_items),
            raw_data=raw_context,
        )

        try:
            result = await self._llm.complete(
                prompt=prompt,
                temperature=0.3,
                max_tokens=1024,
                parse_json=True,
            )

            analysis = result["content"]

            # Extract top sources with links and dates
            sources = self._extract_sources(raw_data)

            return TrendInsight(
                tag=raw_data.tag,
                key_points=analysis.get("key_points", [])[:7],
                momentum=analysis.get("momentum", "stable"),
                risks=analysis.get("risks", [])[:3],
                opportunities=analysis.get("opportunities", [])[:3],
                direction=analysis.get("direction", ""),
                sources=sources,
                sources_count=(
                    len(raw_data.serper_results)
                    + len(raw_data.github_repos)
                    + len(raw_data.hn_items)
                ),
                collected_at=raw_data.collected_at,
            )

        except Exception as e:
            logger.error(f"LLM summarization failed: {e}")
            sources = self._extract_sources(raw_data)
            return TrendInsight(
                tag=raw_data.tag,
                key_points=[
                    f"Data collected from {len(raw_data.serper_results)} web sources"
                ],
                momentum="unknown",
                sources=sources,
                sources_count=(
                    len(raw_data.serper_results)
                    + len(raw_data.github_repos)
                    + len(raw_data.hn_items)
                ),
                collected_at=raw_data.collected_at,
            )

    def _extract_sources(self, raw_data: RawTrendData) -> list[TrendSource]:
        """Extract top sources with links and dates."""
        sources: list[TrendSource] = []

        # Add web sources
        for item in raw_data.serper_results[:3]:
            sources.append(
                TrendSource(
                    title=item.get("title", "")[:80],
                    url=item.get("link", ""),
                    source_type="web",
                    date="",
                    score=item.get("position", 0),
                )
            )

        # Add GitHub repos
        for repo in raw_data.github_repos[:3]:
            sources.append(
                TrendSource(
                    title=repo.get("name", ""),
                    url=repo.get("url", ""),
                    source_type="github",
                    date=repo.get("updated_at", "")[:10],
                    score=repo.get("stars", 0),
                )
            )

        # Add HN discussions
        for item in raw_data.hn_items[:3]:
            sources.append(
                TrendSource(
                    title=item.get("title", "")[:80],
                    url=item.get("url", "") or f"https://news.ycombinator.com/item?id={item.get('objectID', '')}",
                    source_type="hn",
                    date=item.get("created_at", "")[:10],
                    score=item.get("points", 0),
                )
            )

        return sources
