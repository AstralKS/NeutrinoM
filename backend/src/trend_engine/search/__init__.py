"""Real-time search sub-module for the Trend Intelligence Engine.

Provides web search, signal extraction, ranking, and LLM synthesis
for on-demand technology trend analysis.
"""

from trend_engine.search.pipeline import TrendSearchPipeline

__all__ = ["TrendSearchPipeline"]
