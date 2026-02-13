"""Trend intelligence package — agentic search pipeline.

Public API:
- TrendPipeline: Main entry point for trend analysis
- TrendMaster: Backward-compat alias for TrendPipeline
- RAGStore: Vector storage for trend insights
- RAGManager: Backward-compat alias for RAGStore
"""

from advisor.trends.models import (
    RawTrendData,
    TrendInsight,
    TrendSourceInfo,
)
from advisor.trends.pipeline import TrendMaster, TrendPipeline
from advisor.trends.rag_store import RAGStore

# Backward compatibility alias
RAGManager = RAGStore

__all__ = [
    "TrendPipeline",
    "TrendMaster",
    "RAGStore",
    "RAGManager",
    "TrendInsight",
    "TrendSourceInfo",
    "RawTrendData",
]
