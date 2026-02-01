"""Trend intelligence package initialization."""

from advisor.trends.aggregator import TrendAggregator
from advisor.trends.matcher import TrendMatcher
from advisor.trends.models import TrendItem, TrendMatch, TrendReport

__all__ = [
    "TrendAggregator",
    "TrendMatcher",
    "TrendItem",
    "TrendMatch",
    "TrendReport",
]
