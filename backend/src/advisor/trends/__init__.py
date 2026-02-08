"""Trend intelligence package initialization."""

from advisor.trends.aggregator import TrendAggregator
from advisor.trends.data_collector import DataCollector
from advisor.trends.matcher import TrendMatcher
from advisor.trends.models import (
    RawTrendData,
    TrendInsight,
    TrendItem,
    TrendMatch,
    TrendReport,
    TrendSource,
)
from advisor.trends.rag_manager import RAGManager
from advisor.trends.trend_master import TrendMaster

__all__ = [
    "TrendAggregator",
    "TrendMatcher",
    "TrendItem",
    "TrendMatch",
    "TrendReport",
    "TrendMaster",
    "DataCollector",
    "RAGManager",
    "TrendInsight",
    "RawTrendData",
    "TrendSource",
]

