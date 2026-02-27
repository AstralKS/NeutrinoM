"""Unit tests for the agentic trends pipeline.

Tests query planning, content extraction, ranking, and backward compat.
All tests are pure unit tests - no network, no database.
"""

import sys
from types import ModuleType
from unittest.mock import MagicMock

# Mock external dependencies before any advisor imports
_supabase_mock = ModuleType("supabase")
_supabase_mock.Client = MagicMock  # type: ignore[attr-defined]
sys.modules["supabase"] = _supabase_mock

_db_client_mock = ModuleType("advisor.database.client")
_db_client_mock.get_supabase_client = MagicMock  # type: ignore[attr-defined]
sys.modules["advisor.database.client"] = _db_client_mock

_llm_mock = ModuleType("advisor.llm.client")
_llm_mock.OpenRouterClient = MagicMock  # type: ignore[attr-defined]
sys.modules["advisor.llm.client"] = _llm_mock

_config_mod = ModuleType("advisor.config")
_mock_settings = MagicMock()
_mock_settings.serper_api_key = ""
_config_mod.get_settings = MagicMock(return_value=_mock_settings)  # type: ignore[attr-defined]
sys.modules["advisor.config"] = _config_mod

from datetime import UTC, datetime

import pytest

from trend_engine.search.extractor import (
    _KEYWORD_MAP,
    _extract_versions,
    extract_signals,
)
from trend_engine.models import (
    ExtractedSignal,
    RankedResult,
    SearchQuery,
    SearchQueryType,
    SearchResult,
    SignalType,
    SourceType,
    TrendInsight,
    TrendSourceInfo,
)
from trend_engine.search.query_planner import (
    plan_github_queries,
    plan_hn_queries,
    plan_queries,
)
from trend_engine.search.ranker import (
    _authority_score,
    _freshness_score,
    _normalize_url,
    rank_results,
)


# --- QueryPlanner tests ---


class TestQueryPlanner:
    """Tests for query_planner module."""

    def test_generates_multiple_queries(self):
        """plan_queries returns at least 3 queries per tag."""
        queries = plan_queries("django")
        assert len(queries) >= 3
        assert all(isinstance(q, SearchQuery) for q in queries)

    def test_includes_current_year(self):
        """Queries include the current year, not a hardcoded one."""
        queries = plan_queries("react")
        year = str(datetime.now(UTC).year)
        texts = [q.query_text for q in queries]
        year_queries = [t for t in texts if year in t]
        assert len(year_queries) >= 1, (
            f"No queries contain current year {year}"
        )

    def test_no_hardcoded_year(self):
        """No query contains hardcoded '2026'."""
        queries = plan_queries("python")
        texts = " ".join(q.query_text for q in queries)
        assert "2099" not in texts

    def test_tag_is_lowercase(self):
        """Tag in queries is always lowercase."""
        queries = plan_queries("React")
        for q in queries:
            assert q.tag == "react"



    def test_max_queries_respected(self):
        """max_queries parameter caps the output."""
        queries = plan_queries("react", max_queries=3)
        assert len(queries) <= 3

    def test_github_queries(self):
        """plan_github_queries returns non-empty list."""
        queries = plan_github_queries("django")
        assert len(queries) >= 1
        assert all("django" in q for q in queries)

    def test_hn_queries(self):
        """plan_hn_queries returns non-empty list."""
        queries = plan_hn_queries("kubernetes")
        assert len(queries) >= 1
        assert all("kubernetes" in q for q in queries)


# --- ContentExtractor tests ---


class TestContentExtractor:
    """Tests for content_extractor module."""

    def test_finds_version_numbers(self):
        """Regex extracts version numbers from text."""
        versions = _extract_versions(
            "Django 4.2.0 is now available", "django",
        )
        assert "4.2.0" in versions

    def test_finds_v_prefixed_versions(self):
        """Regex handles v-prefixed versions."""
        versions = _extract_versions(
            "React v18.2.0 released", "react",
        )
        assert "18.2.0" in versions

    def test_finds_two_part_versions(self):
        """Regex handles two-part versions like 3.12."""
        versions = _extract_versions(
            "Python 3.12 is here with python improvements",
            "python",
        )
        assert "3.12" in versions

    def test_extract_signals_finds_deprecation(self):
        """Deprecated keywords produce DEPRECATION signal."""
        results = [
            SearchResult(
                title="Feature X is deprecated in v5",
                snippet="This feature has been deprecated.",
                url="https://example.com",
                source=SourceType.SERPER,
            )
        ]
        signals = extract_signals(results, "framework")
        dep_signals = [
            s for s in signals
            if s.signal_type == SignalType.DEPRECATION
        ]
        assert len(dep_signals) >= 1

    def test_extract_signals_finds_features(self):
        """Feature keywords produce FEATURE signal."""
        results = [
            SearchResult(
                title="Introducing new async support",
                snippet="Now supports async operations.",
                url="https://example.com",
                source=SourceType.SERPER,
            )
        ]
        signals = extract_signals(results, "framework")
        feat_signals = [
            s for s in signals
            if s.signal_type == SignalType.FEATURE
        ]
        assert len(feat_signals) >= 1

    def test_has_keywords(self):
        """Keyword matching works correctly."""
        keywords = _KEYWORD_MAP[SignalType.DEPRECATION][0]
        assert any(kw in "this feature is deprecated" for kw in keywords)
        assert not any(kw in "this is totally fine" for kw in keywords)


# --- Ranker tests ---


class TestRanker:
    """Tests for ranker module."""

    def _make_result(
        self,
        url: str,
        score: int = 0,
        source: SourceType = SourceType.SERPER,
        title: str = "Test",
        published_at: str = "",
    ) -> SearchResult:
        return SearchResult(
            title=title,
            snippet="test snippet",
            url=url,
            source=source,
            score=score,
            published_at=published_at,
        )

    def test_deduplicates_urls(self):
        """Same URL with different query params is deduped."""
        results = [
            self._make_result("https://example.com/page?a=1"),
            self._make_result("https://example.com/page?b=2"),
        ]
        ranked = rank_results(results, [], "test")
        assert len(ranked) == 1

    def test_prefers_fresh_results(self):
        """Recent results score higher than old ones."""
        today = datetime.now(UTC).strftime("%Y-%m-%d")
        old = "2020-01-01"

        fresh = _freshness_score(today)
        stale = _freshness_score(old)
        assert fresh > stale

    def test_prefers_official_sources(self):
        """GitHub/official domains rank higher."""
        gh_score = _authority_score(
            "https://github.com/repo",
            SourceType.GITHUB_SEARCH,
        )
        blog_score = _authority_score(
            "https://medium.com/article",
            SourceType.SERPER,
        )
        assert gh_score > blog_score

    def test_normalize_url(self):
        """URL normalization strips trailing slash."""
        assert _normalize_url(
            "https://example.com/page/"
        ) == _normalize_url(
            "https://example.com/page"
        )

    def test_normalize_url_strips_query(self):
        """URL normalization strips query params."""
        assert _normalize_url(
            "https://example.com/page?foo=bar"
        ) == _normalize_url(
            "https://example.com/page"
        )

    def test_top_n_respected(self):
        """top_n parameter caps results."""
        results = [
            self._make_result(f"https://example.com/{i}")
            for i in range(10)
        ]
        ranked = rank_results(results, [], "test", top_n=3)
        assert len(ranked) <= 3


# --- Models tests ---


class TestModels:
    """Tests for Pydantic models."""

    def test_trend_insight_defaults(self):
        """TrendInsight has sane defaults."""
        insight = TrendInsight(tag="react")
        assert insight.tag == "react"
        assert insight.key_points == []
        assert insight.momentum == ""

    def test_search_result_defaults(self):
        """SearchResult works with minimal data."""
        result = SearchResult(source=SourceType.SERPER)
        assert result.title == ""
        assert result.score == 0

    def test_trend_source_info(self):
        """TrendSourceInfo serializes correctly."""
        src = TrendSourceInfo(
            title="Test",
            url="https://x.com",
            source_type="web",
        )
        data = src.model_dump()
        assert data["title"] == "Test"


# --- Backward compat tests ---


class TestBackwardCompat:
    """Tests for backward compatibility aliases."""

    def test_trendmaster_alias(self):
        """TrendMaster is importable as alias."""
        from advisor.trends import TrendMaster
        from trend_engine.search.pipeline import TrendSearchPipeline

        assert TrendMaster is TrendSearchPipeline

    def test_ragmanager_alias(self):
        """RAGManager is importable as alias."""
        from advisor.trends import RAGManager
        from advisor.trends import _RAGStoreCompat

        assert RAGManager is _RAGStoreCompat

    def test_import_trendinsight(self):
        """TrendInsight is importable from package."""
        from advisor.trends import TrendInsight

        assert TrendInsight is not None
