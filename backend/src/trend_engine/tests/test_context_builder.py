"""Tests for TrendContextBuilder — mocked API calls, contract validation."""

import pytest
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock

import httpx


class TestTrendContextBuilder:
    """Test the AI agent integration contract."""

    @pytest.fixture
    def mock_responses(self):
        """Mock API responses for all three endpoints."""
        return {
            "similar": [
                {
                    "chunk_id": "chunk_1",
                    "chunk_text": "Vector databases are gaining traction...",
                    "document_id": "doc_1",
                    "source_name": "TechBlog",
                    "published_at": "2024-01-15T10:00:00Z",
                    "cluster_id": "cluster_abc",
                    "cluster_label": "Vector Database Integration",
                    "cluster_trend_score": 0.91,
                    "cluster_classification": "emerging",
                },
                {
                    "chunk_id": "chunk_2",
                    "chunk_text": "Legacy SQL patterns...",
                    "document_id": "doc_2",
                    "source_name": "DB Weekly",
                    "published_at": "2024-01-10T10:00:00Z",
                    "cluster_id": "cluster_def",
                    "cluster_label": "SQL Optimization",
                    "cluster_trend_score": 0.45,
                    "cluster_classification": "established",
                },
            ],
            "technical": {
                "cluster_id": "cluster_abc",
                "label": "Vector Database Integration",
                "classification": "emerging",
                "growth_metrics": {
                    "weighted_doc_count_7": 12.4,
                    "weighted_doc_count_30": 38.1,
                    "weighted_doc_count_90": 89.6,
                    "growth_rate": 0.64,
                    "acceleration": 0.18,
                },
                "architecture_snapshot": {
                    "detected_layers": ["Backend", "Database"],
                    "primary_patterns": ["pgvector RAG store"],
                    "dependency_graph": {"Backend API": ["Database"]},
                    "risk_zones": ["No caching layer"],
                    "confidence": 0.81,
                },
                "source_breakdown": [
                    {"source_name": "TechBlog", "doc_count": 14, "avg_source_weight": 0.9}
                ],
                "top_documents": [
                    {"title": "Vector DB Guide", "url": "https://example.com", "published_at": "2024-01-15T10:00:00Z"}
                ],
            },
            "executive": {
                "cluster_id": "cluster_abc",
                "label": "Vector Database Integration",
                "classification": "emerging",
                "trend_score": 0.91,
                "architecture_snapshot": {
                    "detected_layers": ["Backend", "Database"],
                    "primary_patterns": ["pgvector RAG store"],
                    "risk_zones": ["No caching layer"],
                },
                "market_stats": {
                    "adoption_velocity": "+34% over 90 days",
                    "market_penetration": "61% of surveyed developers",
                    "community_health_score": 0.87,
                    "data_sources": ["npm registry", "GitHub API"],
                    "scraped_at": "2024-01-15T10:00:00Z",
                },
                "business_signals": {
                    "longevity_risk": "low",
                    "migration_urgency": "none",
                    "investment_signal": "increasing adoption",
                },
                "representative_snippets": ["snippet1", "snippet2"],
            },
        }

    @pytest.mark.asyncio
    async def test_build_context_structure(self, mock_responses):
        """Output should match the TrendContext schema."""
        from trend_engine.agent.context_builder import TrendContextBuilder

        mock_client = AsyncMock(spec=httpx.AsyncClient)

        def mock_post(*args, **kwargs):
            resp = MagicMock()
            resp.status_code = 200
            resp.json.return_value = mock_responses["similar"]
            resp.raise_for_status = MagicMock()
            return resp

        def mock_get(*args, **kwargs):
            url = args[0] if args else kwargs.get("url", "")
            params = kwargs.get("params", {})
            resp = MagicMock()
            resp.status_code = 200
            resp.raise_for_status = MagicMock()
            if params.get("view") == "executive":
                resp.json.return_value = mock_responses["executive"]
            else:
                resp.json.return_value = mock_responses["technical"]
            return resp

        mock_client.post = AsyncMock(side_effect=mock_post)
        mock_client.get = AsyncMock(side_effect=mock_get)

        builder = TrendContextBuilder(
            api_base_url="http://test:8001",
            api_key="test-key",
            http_client=mock_client,
        )

        context = await builder.build_context("vector databases")

        # Validate structure
        assert context.query == "vector databases"
        assert context.retrieved_at is not None
        assert isinstance(context.related_trends, list)
        # Only emerging/expanding clusters are included
        assert len(context.related_trends) >= 1

        trend = context.related_trends[0]
        assert trend.label == "Vector Database Integration"
        assert trend.classification == "emerging"
        assert trend.trend_score == 0.91
        assert trend.growth_rate == 0.64
        assert trend.acceleration == 0.18
        assert trend.architecture_snapshot is not None

    @pytest.mark.asyncio
    async def test_excludes_non_target_classifications(self, mock_responses):
        """Only emerging and expanding clusters should be included."""
        from trend_engine.agent.context_builder import TrendContextBuilder

        # Modify: all results are "established" classification
        modified_similar = []
        for r in mock_responses["similar"]:
            r_copy = {**r, "cluster_classification": "established"}
            modified_similar.append(r_copy)

        mock_client = AsyncMock(spec=httpx.AsyncClient)

        def mock_post(*args, **kwargs):
            resp = MagicMock()
            resp.status_code = 200
            resp.json.return_value = modified_similar
            resp.raise_for_status = MagicMock()
            return resp

        mock_client.post = AsyncMock(side_effect=mock_post)

        builder = TrendContextBuilder(
            api_base_url="http://test:8001",
            api_key="test-key",
            http_client=mock_client,
        )

        context = await builder.build_context("vector databases")

        # No emerging/expanding → no related trends
        assert len(context.related_trends) == 0

    @pytest.mark.asyncio
    async def test_output_is_serializable(self, mock_responses):
        """TrendContext must be JSON-serializable."""
        from trend_engine.agent.context_builder import TrendContextBuilder

        mock_client = AsyncMock(spec=httpx.AsyncClient)

        def mock_post(*args, **kwargs):
            resp = MagicMock()
            resp.status_code = 200
            resp.json.return_value = mock_responses["similar"]
            resp.raise_for_status = MagicMock()
            return resp

        def mock_get(*args, **kwargs):
            params = kwargs.get("params", {})
            resp = MagicMock()
            resp.status_code = 200
            resp.raise_for_status = MagicMock()
            if params.get("view") == "executive":
                resp.json.return_value = mock_responses["executive"]
            else:
                resp.json.return_value = mock_responses["technical"]
            return resp

        mock_client.post = AsyncMock(side_effect=mock_post)
        mock_client.get = AsyncMock(side_effect=mock_get)

        builder = TrendContextBuilder(
            api_base_url="http://test:8001",
            api_key="test-key",
            http_client=mock_client,
        )

        context = await builder.build_context("test query")

        # Must be serializable to JSON
        json_str = context.model_dump_json()
        parsed = json.loads(json_str)
        assert "query" in parsed
        assert "retrieved_at" in parsed
        assert "related_trends" in parsed
