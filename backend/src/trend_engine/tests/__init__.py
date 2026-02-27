"""Test fixtures and shared test configuration."""

from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_settings():
    """Default settings for testing."""
    from trend_engine.config import TrendEngineSettings
    return TrendEngineSettings(
        supabase_url="https://test.supabase.co",
        supabase_service_key="test-key",
        openrouter_api_key="test-or-key",
        hdbscan_min_cluster_size=3,  # Lower for tests
        hdbscan_min_samples=2,
        decay_lambda=0.05,
        chunk_min_tokens=10,  # Lower for tests
        chunk_max_tokens=100,
        embedding_dim=4,  # Small for tests
        api_key="test-api-key",
    )


@pytest.fixture
def sample_documents():
    """Sample document data for testing."""
    now = datetime.now(timezone.utc)
    return [
        {
            "title": f"Test Doc {i}",
            "source_name": f"source_{i % 3}",
            "source_type": "rss",
            "published_at": (now - timedelta(days=i)).isoformat(),
            "source_weight": 0.5 + (i % 5) * 0.1,
            "raw_text": f"Raw text for document {i}",
            "clean_text": f"This is clean text for document number {i} about technology trends in AI and machine learning. " * 10,
            "content_hash": f"hash_{i:04d}",
        }
        for i in range(20)
    ]


@pytest.fixture
def sample_chunk_data():
    """Sample chunk data with embeddings for clustering tests."""
    now = datetime.now(timezone.utc)
    import random
    random.seed(42)

    chunks = []
    # Create 3 clusters of chunks with similar embeddings
    for cluster_idx in range(3):
        base_emb = [float(cluster_idx), 0.0, 0.0, 0.0]
        for i in range(5):
            emb = [
                base_emb[0] + random.uniform(-0.1, 0.1),
                base_emb[1] + random.uniform(-0.1, 0.1),
                base_emb[2] + random.uniform(-0.1, 0.1),
                base_emb[3] + random.uniform(-0.1, 0.1),
            ]
            chunks.append({
                "chunk_id": f"chunk_{cluster_idx}_{i}",
                "document_id": f"doc_{cluster_idx}_{i}",
                "chunk_text": f"Chunk about topic {cluster_idx}, variant {i}",
                "embedding": emb,
                "source_name": f"source_{(cluster_idx + i) % 4}",
                "source_type": "rss",
                "published_at": (now - timedelta(days=i * 3)).isoformat(),
                "source_weight": 0.7,
            })
    return chunks


@pytest.fixture
def sample_cluster_metrics():
    """Sample clusters with temporal metrics for scoring tests."""
    return [
        {
            "id": "cluster_1",
            "cluster_size": 20,
            "weighted_doc_count_7": 8.5,
            "weighted_doc_count_30": 25.0,
            "weighted_doc_count_90": 40.0,
            "growth_rate": 0.35,
            "acceleration": 0.15,
            "credibility_score": 0.85,
            "source_diversity_score": 0.6,
        },
        {
            "id": "cluster_2",
            "cluster_size": 50,
            "weighted_doc_count_7": 5.0,
            "weighted_doc_count_30": 30.0,
            "weighted_doc_count_90": 80.0,
            "growth_rate": 0.05,
            "acceleration": -0.02,
            "credibility_score": 0.9,
            "source_diversity_score": 0.8,
        },
        {
            "id": "cluster_3",
            "cluster_size": 15,
            "weighted_doc_count_7": 12.0,
            "weighted_doc_count_30": 15.0,
            "weighted_doc_count_90": 18.0,
            "growth_rate": 0.50,
            "acceleration": 0.30,
            "credibility_score": 0.7,
            "source_diversity_score": 0.4,
        },
        {
            "id": "cluster_4",
            "cluster_size": 30,
            "weighted_doc_count_7": 2.0,
            "weighted_doc_count_30": 20.0,
            "weighted_doc_count_90": 70.0,
            "growth_rate": -0.20,
            "acceleration": -0.10,
            "credibility_score": 0.6,
            "source_diversity_score": 0.5,
        },
    ]
