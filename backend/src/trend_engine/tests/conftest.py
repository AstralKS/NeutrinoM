"""Test fixtures shared across test modules."""

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
        hdbscan_min_cluster_size=3,
        hdbscan_min_samples=2,
        decay_lambda=0.05,
        chunk_min_tokens=10,
        chunk_max_tokens=100,
        embedding_dim=4,
        api_key="test-api-key",
    )
