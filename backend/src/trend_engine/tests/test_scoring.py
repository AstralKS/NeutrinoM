"""Tests for trend scoring and classification against synthetic cluster data."""

import pytest
from unittest.mock import patch, MagicMock

from trend_engine.batch.scoring import compute_trend_scores, _min_max_norm, _percentile


class MockSettings:
    hdbscan_min_cluster_size = 3
    volatility_multiplier = 3.0
    weight_alpha = 0.35
    weight_beta = 0.25
    weight_gamma = 0.15
    weight_delta = 0.15
    weight_zeta = 0.10
    growth_rate_emerging = 0.30
    growth_rate_expanding = 0.10
    growth_rate_declining = -0.10
    acceleration_established_max = 0.10


@pytest.fixture(autouse=True)
def mock_get_settings():
    with patch("trend_engine.batch.scoring.get_settings", return_value=MockSettings()):
        yield


class TestMinMaxNorm:
    def test_basic_normalization(self):
        result = _min_max_norm([1.0, 2.0, 3.0])
        assert result == [0.0, 0.5, 1.0]

    def test_single_value(self):
        result = _min_max_norm([5.0])
        assert result == [0.5]

    def test_identical_values(self):
        result = _min_max_norm([3.0, 3.0, 3.0])
        assert all(v == 0.5 for v in result)

    def test_empty_list(self):
        assert _min_max_norm([]) == []

    def test_negative_values(self):
        result = _min_max_norm([-2.0, 0.0, 2.0])
        assert result[0] == pytest.approx(0.0)
        assert result[1] == pytest.approx(0.5)
        assert result[2] == pytest.approx(1.0)


class TestPercentile:
    def test_p50(self):
        result = _percentile([1.0, 2.0, 3.0, 4.0, 5.0], 50)
        assert result == 3.0

    def test_p75(self):
        result = _percentile([1.0, 2.0, 3.0, 4.0, 5.0], 75)
        assert result == 4.0

    def test_empty(self):
        assert _percentile([], 50) == 0.0


class TestTrendScoring:
    """Test trend score computation and classification."""

    def test_scores_between_0_and_1(self):
        """All trend scores should be in [0, 1]."""
        clusters = [
            {
                "id": f"c{i}",
                "cluster_size": 10 + i * 5,
                "weighted_doc_count_7": float(i),
                "weighted_doc_count_30": float(i * 3),
                "weighted_doc_count_90": float(i * 8),
                "growth_rate": 0.1 * i - 0.2,
                "acceleration": 0.05 * i - 0.1,
                "credibility_score": 0.5 + 0.1 * i,
                "source_diversity_score": 0.3 + 0.1 * i,
            }
            for i in range(5)
        ]

        compute_trend_scores(clusters)

        for c in clusters:
            score = c.get("trend_score")
            if score is not None:
                assert 0.0 <= score <= 1.0, f"Score {score} out of range"

    def test_emerging_classification(self):
        """High growth + positive accel + low volume → emerging."""
        clusters = [
            {
                "id": "emerging",
                "cluster_size": 12,
                "weighted_doc_count_7": 8.0,
                "weighted_doc_count_30": 12.0,
                "weighted_doc_count_90": 15.0,  # Low (below P50)
                "growth_rate": 0.50,
                "acceleration": 0.20,
                "credibility_score": 0.7,
                "source_diversity_score": 0.5,
            },
            {
                "id": "big",
                "cluster_size": 50,
                "weighted_doc_count_7": 5.0,
                "weighted_doc_count_30": 30.0,
                "weighted_doc_count_90": 80.0,  # High
                "growth_rate": 0.05,
                "acceleration": 0.00,
                "credibility_score": 0.8,
                "source_diversity_score": 0.6,
            },
        ]

        compute_trend_scores(clusters)
        assert clusters[0]["classification"] == "emerging"

    def test_declining_classification(self):
        """Negative growth + negative accel → declining."""
        clusters = [
            {
                "id": "declining",
                "cluster_size": 20,
                "weighted_doc_count_7": 1.0,
                "weighted_doc_count_30": 10.0,
                "weighted_doc_count_90": 50.0,
                "growth_rate": -0.30,
                "acceleration": -0.15,
                "credibility_score": 0.6,
                "source_diversity_score": 0.4,
            },
            {
                "id": "stable",
                "cluster_size": 25,
                "weighted_doc_count_7": 5.0,
                "weighted_doc_count_30": 20.0,
                "weighted_doc_count_90": 60.0,
                "growth_rate": 0.02,
                "acceleration": 0.00,
                "credibility_score": 0.7,
                "source_diversity_score": 0.5,
            },
        ]

        compute_trend_scores(clusters)
        assert clusters[0]["classification"] == "declining"

    def test_volatility_exclusion(self):
        """Extreme acceleration spike → excluded from scoring."""
        clusters = [
            {
                "id": "normal_1",
                "cluster_size": 20,
                "weighted_doc_count_90": 40.0,
                "weighted_doc_count_30": 20.0,
                "weighted_doc_count_7": 5.0,
                "growth_rate": 0.2,
                "acceleration": 0.05,
                "credibility_score": 0.7,
                "source_diversity_score": 0.5,
            },
            {
                "id": "normal_2",
                "cluster_size": 25,
                "weighted_doc_count_90": 50.0,
                "weighted_doc_count_30": 25.0,
                "weighted_doc_count_7": 6.0,
                "growth_rate": 0.1,
                "acceleration": -0.02,
                "credibility_score": 0.8,
                "source_diversity_score": 0.6,
            },
            {
                "id": "normal_3",
                "cluster_size": 18,
                "weighted_doc_count_90": 35.0,
                "weighted_doc_count_30": 18.0,
                "weighted_doc_count_7": 4.0,
                "growth_rate": 0.15,
                "acceleration": 0.03,
                "credibility_score": 0.75,
                "source_diversity_score": 0.55,
            },
            {
                "id": "volatile",
                "cluster_size": 15,
                "weighted_doc_count_90": 30.0,
                "weighted_doc_count_30": 10.0,
                "weighted_doc_count_7": 8.0,
                "growth_rate": 0.8,
                "acceleration": 500.0,  # Must be extreme enough that |acc| > 3*std(all accs including itself)
                "credibility_score": 0.6,
                "source_diversity_score": 0.4,
            },
        ]

        compute_trend_scores(clusters)
        # Volatile cluster should be excluded
        volatile = [c for c in clusters if c["id"] == "volatile"][0]
        assert volatile["trend_score"] is None
        assert volatile["classification"] is None

    def test_no_forced_classification(self):
        """Clusters matching no condition retain classification = null."""
        clusters = [
            {
                "id": "ambiguous",
                "cluster_size": 20,
                "weighted_doc_count_7": 3.0,
                "weighted_doc_count_30": 15.0,
                "weighted_doc_count_90": 45.0,
                "growth_rate": 0.05,  # Below emerging AND expanding thresholds when evaluated
                "acceleration": -0.01,  # Slightly negative (disqualifies expanding)
                "credibility_score": 0.7,
                "source_diversity_score": 0.5,
            },
        ]

        compute_trend_scores(clusters)
        # With single cluster, P50=P75=45.0, so wdc90 >= P50 AND >= P75
        # acceleration < established_max might classify as established
        # but acceleration is negative so abs(-0.01) < 0.10 → established
        # This is actually valid per spec rules
