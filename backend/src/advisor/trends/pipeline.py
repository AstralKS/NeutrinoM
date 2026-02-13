"""Pipeline — main orchestrator for the agentic trend search pipeline.

Wires together:
1. RAG cache check
2. Query planning (multi-query generation)
3. Parallel multi-source search
4. Signal extraction
5. Ranking & deduplication
6. LLM synthesis
7. RAG cache storage

Public API:
- TrendPipeline.analyze_tag(tag) -> TrendInsight
- TrendPipeline.query_trends(tag) -> list[TrendInsight]
"""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from advisor.llm.client import OpenRouterClient
from advisor.trends import content_extractor, ranker, search_sources
from advisor.trends.models import TrendInsight
from advisor.trends.query_planner import (
    plan_github_queries,
    plan_hn_queries,
    plan_queries,
)
from advisor.trends.rag_store import RAGStore
from advisor.trends.synthesizer import synthesize

logger = logging.getLogger(__name__)

# Weekly cache window
CACHE_MAX_DAYS = 7


class TrendPipeline:
    """Agentic search pipeline for tech stack trend analysis.

    Replaces the old TrendMaster with a multi-step pipeline.
    """

    def __init__(
        self,
        llm_client: OpenRouterClient | None = None,
        rag_store: RAGStore | None = None,
    ) -> None:
        """Initialize pipeline with dependencies.

        Args:
            llm_client: Optional LLM client for synthesis.
            rag_store: Optional RAG store for caching.
        """
        self._llm = llm_client or OpenRouterClient()
        self._rag = rag_store or RAGStore()

    async def analyze_tag(
        self,
        tag: str,
        force_refresh: bool = False,
    ) -> TrendInsight:
        """Run the full agentic pipeline for a technology tag.

        Steps:
        1. Check RAG cache (skip if force_refresh)
        2. Generate sub-queries (QueryPlanner)
        3. Execute parallel searches (SearchSources)
        4. Extract signals (ContentExtractor)
        5. Rank and deduplicate (Ranker)
        6. Synthesize via LLM (Synthesizer)
        7. Store result in RAG cache

        Args:
            tag: Technology tag (e.g., "react", "django").
            force_refresh: Bypass cache if True.

        Returns:
            TrendInsight with full analysis.
        """
        tag = tag.lower().strip()

        # Step 1: Check cache
        if not force_refresh:
            cached = await self._rag.get_recent_for_tag(
                tag,
                days=CACHE_MAX_DAYS,
            )
            if cached:
                logger.info(f"Cache hit for '{tag}'")
                return cached

        # Step 2: Plan queries
        logger.info(f"Pipeline: analyzing '{tag}'")
        sub_queries = plan_queries(tag)
        serper_texts = [q.query_text for q in sub_queries]
        github_texts = plan_github_queries(tag)
        hn_texts = plan_hn_queries(tag)

        # Step 3: Parallel multi-source search
        results = await search_sources.search_all(
            serper_queries=serper_texts,
            github_queries=github_texts,
            hn_queries=hn_texts,
        )

        # Step 4: Extract signals
        signals = content_extractor.extract_signals(
            results,
            tag,
        )

        # Step 5: Rank and deduplicate
        ranked = ranker.rank_results(results, signals, tag)

        # Step 6: Synthesize via LLM
        insight = await synthesize(
            tag=tag,
            ranked_results=ranked,
            signals=signals,
            llm_client=self._llm,
        )

        # Step 7: Store in RAG cache
        try:
            await self._rag.store_insight(insight)
        except Exception as e:
            logger.warning(f"Failed to cache insight for '{tag}': {e}")

        return insight

    async def query_trends(
        self,
        tag: str,
    ) -> list[TrendInsight]:
        """Query stored trends without triggering new collection.

        Args:
            tag: Tag to query.

        Returns:
            List of historical TrendInsights.
        """
        return await self._rag.search_by_tag(
            tag.lower().strip(),
        )

    async def run_batch(
        self,
        tags: list[str],
        force_refresh: bool = True,
        max_concurrent: int = 1,
    ) -> dict[str, TrendInsight]:
        """Run pipeline for multiple tags in parallel.

        Uses a semaphore to cap concurrency and avoid API rate limits.

        Args:
            tags: List of technology tags.
            force_refresh: Bypass cache for all tags.
            max_concurrent: Max tags to analyze in parallel.

        Returns:
            Dict mapping tags to their TrendInsights.
        """
        sem = asyncio.Semaphore(max_concurrent)

        async def _analyze_one(tag: str) -> tuple[str, TrendInsight | None]:
            async with sem:
                try:
                    insight = await self.analyze_tag(
                        tag,
                        force_refresh=force_refresh,
                    )
                    return (tag, insight)
                except Exception as e:
                    logger.error(f"Pipeline failed for '{tag}': {e}")
                    return (tag, None)

        pairs = await asyncio.gather(
            *[_analyze_one(t) for t in tags],
        )
        return {tag: ins for tag, ins in pairs if ins is not None}

    def should_collect(
        self,
        last_collection: datetime | None,
    ) -> bool:
        """Check if collection is due based on weekly schedule.

        Args:
            last_collection: Datetime of last collection.

        Returns:
            True if collection is needed.
        """
        if last_collection is None:
            return True
        cutoff = datetime.now(UTC) - timedelta(
            days=CACHE_MAX_DAYS,
        )
        return last_collection < cutoff


# Backward compatibility alias
TrendMaster = TrendPipeline
