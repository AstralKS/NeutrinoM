"""Trend intelligence package — thin re-export layer.

All functionality has been migrated to the ``trend_engine`` package.
This module exists solely for backward compatibility.
"""

from trend_engine.models import (
    RawTrendData,
    TrendInsight,
    TrendSourceInfo,
)
from trend_engine.search.pipeline import TrendSearchPipeline

# Primary export
TrendPipeline = TrendSearchPipeline

# Backward-compat aliases
TrendMaster = TrendSearchPipeline


class _RAGStoreCompat:
    """Thin shim that proxies RAGStore calls to TrendSearchPipeline cache methods.

    Only supports the subset of the RAGStore API used by orchestrator & report_agent:
    - get_recent_for_tag(tag, days)
    - search_by_tag(tag, limit)
    """

    async def get_recent_for_tag(
        self, tag: str, days: int = 7
    ) -> TrendInsight | None:
        pipeline = TrendSearchPipeline()
        return await pipeline._get_cached(tag, days)

    async def search_by_tag(
        self, tag: str, limit: int = 10
    ) -> list[TrendInsight]:
        pipeline = TrendSearchPipeline()
        return await pipeline.query_trends(tag)

    async def store_insight(self, insight: TrendInsight) -> str:
        pipeline = TrendSearchPipeline()
        await pipeline._store_cached(insight)
        return insight.id


RAGStore = _RAGStoreCompat
RAGManager = _RAGStoreCompat

__all__ = [
    "TrendPipeline",
    "TrendMaster",
    "TrendSearchPipeline",
    "RAGStore",
    "RAGManager",
    "TrendInsight",
    "TrendSourceInfo",
    "RawTrendData",
]
