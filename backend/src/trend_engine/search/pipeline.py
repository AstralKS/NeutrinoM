"""Unified search pipeline — real-time trend analysis for technology tags.

Wires together:
1. RAG / DB cache check
2. Query planning (multi-query generation)
3. Parallel multi-source search
4. Signal extraction
5. Ranking & deduplication
6. LLM synthesis
7. Cache storage

Public API:
- TrendSearchPipeline.analyze_tag(tag) -> TrendInsight
- TrendSearchPipeline.query_trends(tag) -> list[TrendInsight]
"""

import asyncio
import hashlib
import logging
from datetime import UTC, datetime, timedelta

import httpx

from trend_engine.config import get_settings
from trend_engine.models import TrendInsight
from trend_engine.search import extractor, ranker, sources
from trend_engine.search.query_planner import (
    plan_github_queries,
    plan_hn_queries,
    plan_queries,
)
from trend_engine.search.synthesizer import synthesize

logger = logging.getLogger(__name__)


class TrendSearchPipeline:
    """Real-time search pipeline for tech stack trend analysis.

    Replaces the old advisor.trends.TrendPipeline with a cleaner
    implementation that uses trend_engine's DB and config.
    """

    def __init__(
        self,
        llm_client: object | None = None,
        db_client: object | None = None,
    ) -> None:
        self._llm = llm_client
        self._db = db_client
        self._http: httpx.AsyncClient | None = None
        self._settings = get_settings()

    @property
    def _http_client(self) -> httpx.AsyncClient:
        """Lazy-init shared HTTP client with connection pooling."""
        if self._http is None:
            self._http = httpx.AsyncClient(
                timeout=25.0,
                limits=httpx.Limits(
                    max_connections=20,
                    max_keepalive_connections=5,
                ),
            )
        return self._http

    def _get_llm(self) -> object:
        """Lazy-load LLM client."""
        if self._llm is None:
            from advisor.llm.client import OpenRouterClient
            self._llm = OpenRouterClient()
        return self._llm

    def _get_db(self) -> object | None:
        """Lazy-load DB client for caching."""
        if self._db is None:
            try:
                from trend_engine.db.repository import TrendRepository
                self._db = TrendRepository()
            except Exception:
                logger.debug("TrendRepository not available, caching disabled")
        return self._db

    async def analyze_tag(
        self,
        tag: str,
        force_refresh: bool = False,
    ) -> TrendInsight:
        """Run the full search pipeline for a technology tag.

        Steps:
        1. Check cache (skip if force_refresh)
        2. Generate sub-queries
        3. Execute parallel searches
        4. Extract signals
        5. Rank and deduplicate
        6. Synthesize via LLM
        7. Store in cache

        Args:
            tag: Technology tag (e.g., "react", "django").
            force_refresh: Bypass cache if True.

        Returns:
            TrendInsight with full analysis.
        """
        tag = tag.lower().strip()
        cache_days = self._settings.cache_max_days

        # Step 1: Check cache
        if not force_refresh:
            cached = await self._get_cached(tag, cache_days)
            if cached:
                logger.info(f"Cache hit for '{tag}'")
                return cached

        # Step 2: Plan queries
        logger.info(f"[Trend Engine] '{tag}' -> Generating Serper, GitHub, and HN queries...")
        sub_queries = plan_queries(tag)
        serper_texts = [q.query_text for q in sub_queries]
        github_texts = plan_github_queries(tag)
        hn_texts = plan_hn_queries(tag)

        # Step 3: Parallel multi-source search (shared HTTP client)
        logger.info(f"[Trend Engine] '{tag}' -> Executing {len(serper_texts) + len(github_texts) + len(hn_texts)} parallel web searches...")
        results = await sources.search_all(
            serper_queries=serper_texts,
            github_queries=github_texts,
            hn_queries=hn_texts,
            client=self._http_client,
        )
        logger.info(f"[Trend Engine] '{tag}' -> Web search complete. Retrieved {len(results)} raw results.")

        # Step 4: Extract signals
        logger.info(f"[Trend Engine] '{tag}' -> Extracting high-confidence signals (HDBSCAN / Deduplication)...")
        signals = extractor.extract_signals(results, tag)

        # Step 5: Rank and deduplicate
        logger.info(f"[Trend Engine] '{tag}' -> Ranking and deduplicating final results...")
        ranked = ranker.rank_results(results, signals, tag)

        # Step 6: Synthesize via LLM
        logger.info(f"[Trend Engine] '{tag}' -> Sending {len(ranked)} top results and {len(signals)} signals to OpenRouter LLM for synthesis...")
        insight = await synthesize(
            tag=tag,
            ranked_results=ranked,
            signals=signals,
            llm_client=self._get_llm(),
        )
        logger.info(f"[Trend Engine] '{tag}' -> LLM synthesis complete!")

        # Step 7: Cache (best-effort)
        try:
            await self._store_cached(insight)
        except Exception as e:
            logger.warning(f"Failed to cache insight for '{tag}': {e}")

        return insight

    async def query_trends(self, tag: str) -> list[TrendInsight]:
        """Query stored trends without triggering new collection."""
        db = self._get_db()
        if db is None:
            return []
        try:
            # Fall back to simple Supabase query if available
            from trend_engine.db.client import SupabaseDB
            sdb = SupabaseDB()
            rows = await sdb.select(
                "trend_insights",
                filters={"tag": f"eq.{tag.lower().strip()}"},
                order="collected_at.desc",
                limit=10,
            )
            return [TrendInsight.model_validate(r) for r in rows]
        except Exception as e:
            logger.debug(f"query_trends failed: {e}")
            return []

    async def run_batch(
        self,
        tags: list[str],
        force_refresh: bool = True,
        max_concurrent: int = 2,
    ) -> dict[str, TrendInsight]:
        """Run pipeline for multiple tags with semaphore-controlled concurrency."""
        sem = asyncio.Semaphore(max_concurrent)

        async def _one(tag: str) -> tuple[str, TrendInsight | None]:
            async with sem:
                try:
                    return (tag, await self.analyze_tag(tag, force_refresh=force_refresh))
                except Exception as e:
                    logger.error(f"Pipeline failed for '{tag}': {e}")
                    return (tag, None)

        pairs = await asyncio.gather(*[_one(t) for t in tags])
        return {tag: ins for tag, ins in pairs if ins is not None}

    def should_collect(self, last_collection: datetime | None) -> bool:
        """Check if collection is due based on schedule."""
        if last_collection is None:
            return True
        cutoff = datetime.now(UTC) - timedelta(days=self._settings.cache_max_days)
        return last_collection < cutoff

    async def close(self) -> None:
        """Clean up shared HTTP client."""
        if self._http:
            await self._http.aclose()
            self._http = None

    # ── Private helpers ─────────────────────────────────────────────

    async def _get_cached(
        self, tag: str, days: int
    ) -> TrendInsight | None:
        """Check cache for recent insight."""
        try:
            from trend_engine.db.client import SupabaseDB
            sdb = SupabaseDB()
            cutoff = (datetime.now(UTC) - timedelta(days=days)).isoformat()
            rows = await sdb.select(
                "trend_insights",
                filters={
                    "tag": f"eq.{tag}",
                    "collected_at": f"gte.{cutoff}",
                },
                order="collected_at.desc",
                limit=1,
            )
            if rows:
                return TrendInsight.model_validate(rows[0])
        except Exception as e:
            logger.debug(f"Cache check failed for '{tag}': {e}")
        return None

    async def _store_cached(self, insight: TrendInsight) -> None:
        """Store insight in cache."""
        try:
            from trend_engine.db.client import SupabaseDB
            sdb = SupabaseDB()
            insight.id = _generate_id(insight.tag, insight.collected_at)
            data = insight.model_dump(mode="json")
            data.pop("embedding", None)
            await sdb.insert("trend_insights", data, on_conflict="id", upsert=True)
            logger.info(f"Cached insight for '{insight.tag}'")
        except Exception as e:
            logger.debug(f"Cache store failed: {e}")


def _generate_id(tag: str, timestamp: datetime) -> str:
    content = f"{tag.lower()}:{timestamp.isoformat()}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


# Backward compatibility alias
TrendPipeline = TrendSearchPipeline
