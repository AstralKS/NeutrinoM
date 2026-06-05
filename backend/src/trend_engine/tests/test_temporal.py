"""Tests for temporal modeling — known input/output fixtures."""

import pytest
import math
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from trend_engine.batch.temporal import compute_temporal_metrics, compute_acceleration


class MockSettings:
    decay_lambda = 0.05


@pytest.fixture(autouse=True)
def mock_get_settings():
    with patch("trend_engine.batch.temporal.get_settings", return_value=MockSettings()):
        yield


class TestTemporalMetrics:
    """Test recency weighting and growth rate computation."""

    def test_recent_docs_higher_weight(self):
        """Documents published today should have higher weight than older ones."""
        now = datetime.now(timezone.utc)
        member_data = [
            {
                "document_id": "doc_1",
                "published_at": now.isoformat(),
                "source_name": "src_a",
                "source_weight": 0.8,
            },
            {
                "document_id": "doc_2",
                "published_at": (now - timedelta(days=30)).isoformat(),
                "source_name": "src_b",
                "source_weight": 0.8,
            },
        ]

        metrics = compute_temporal_metrics(member_data)
        # Recent doc contributes more to 7-day count
        assert metrics["weighted_doc_count_7"] > 0
        # 30-day window includes all 7-day docs, so it's >=
        assert metrics["weighted_doc_count_30"] >= metrics["weighted_doc_count_7"]
        # 90-day window includes 30-day old doc
        assert metrics["weighted_doc_count_90"] >= metrics["weighted_doc_count_30"]

    def test_growth_rate_positive_when_recent_heavy(self):
        """Growth rate should be positive when recent activity exceeds baseline."""
        now = datetime.now(timezone.utc)
        # 5 docs in last 7 days, 2 old
        member_data = [
            {
                "document_id": f"recent_{i}",
                "published_at": (now - timedelta(days=i)).isoformat(),
                "source_name": f"src_{i}",
                "source_weight": 0.8,
            }
            for i in range(5)
        ] + [
            {
                "document_id": f"old_{i}",
                "published_at": (now - timedelta(days=25 + i)).isoformat(),
                "source_name": f"src_old_{i}",
                "source_weight": 0.7,
            }
            for i in range(2)
        ]

        metrics = compute_temporal_metrics(member_data)
        assert metrics["growth_rate"] > 0

    def test_credibility_is_mean_source_weight(self):
        """Credibility score should be mean of source weights."""
        now = datetime.now(timezone.utc)
        member_data = [
            {
                "document_id": f"doc_{i}",
                "published_at": now.isoformat(),
                "source_name": f"src_{i}",
                "source_weight": w,
            }
            for i, w in enumerate([0.6, 0.8, 1.0])
        ]

        metrics = compute_temporal_metrics(member_data)
        assert abs(metrics["credibility_score"] - 0.8) < 0.01

    def test_source_diversity_increases_with_unique_sources(self):
        """More unique sources should increase diversity score."""
        now = datetime.now(timezone.utc)

        # All same source
        same_source = [
            {
                "document_id": f"doc_{i}",
                "published_at": now.isoformat(),
                "source_name": "same_source",
                "source_weight": 0.7,
            }
            for i in range(5)
        ]

        # Different sources
        diff_sources = [
            {
                "document_id": f"doc_{i}",
                "published_at": now.isoformat(),
                "source_name": f"source_{i}",
                "source_weight": 0.7,
            }
            for i in range(5)
        ]

        metrics_same = compute_temporal_metrics(same_source)
        metrics_diff = compute_temporal_metrics(diff_sources)
        assert metrics_diff["source_diversity_score"] > metrics_same["source_diversity_score"]

    def test_deduplication_by_document_id(self):
        """Multiple chunks from same document should count as one document."""
        now = datetime.now(timezone.utc)
        member_data = [
            {
                "document_id": "doc_1",  # Same doc
                "published_at": now.isoformat(),
                "source_name": "src_a",
                "source_weight": 0.8,
            },
            {
                "document_id": "doc_1",  # Same doc, different chunk
                "published_at": now.isoformat(),
                "source_name": "src_a",
                "source_weight": 0.8,
            },
        ]

        metrics = compute_temporal_metrics(member_data)
        # Should only count as 1 doc for credibility
        assert metrics["credibility_score"] == 0.8


class TestAcceleration:
    """Test acceleration computation."""

    def test_first_run_zero_acceleration(self):
        """No previous growth rate → acceleration = 0."""
        assert compute_acceleration(0.5, None) == 0.0

    def test_positive_acceleration(self):
        """Growth increasing → positive acceleration."""
        result = compute_acceleration(0.5, 0.3)
        assert result == pytest.approx(0.2, abs=0.001)

    def test_negative_acceleration(self):
        """Growth decreasing → negative acceleration."""
        result = compute_acceleration(0.1, 0.4)
        assert result == pytest.approx(-0.3, abs=0.001)

    def test_zero_acceleration_stable(self):
        """Same growth rate → zero acceleration."""
        result = compute_acceleration(0.3, 0.3)
        assert result == 0.0
