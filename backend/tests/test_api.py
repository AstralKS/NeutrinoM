"""Tests for FastAPI endpoints.

Run: uv run pytest tests/test_api.py -v
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock

from advisor.api.endpoints import app
from advisor.database.models import AnalysisRecord, TechStackInfo


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """Test health endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_format(self, client):
        """Test health response has correct format."""
        response = client.get("/health")
        data = response.json()
        
        assert "status" in data
        assert "version" in data
        assert data["status"] == "healthy"


class TestAnalyzeEndpoint:
    """Tests for analyze endpoint."""

    def test_analyze_validates_input(self, client):
        """Test that analyze endpoint validates input."""
        # Missing required field
        response = client.post("/analyze", json={})
        assert response.status_code == 422  # Validation error

    def test_analyze_with_valid_input(self, client):
        """Test analyze with valid input (mocked)."""
        mock_record = AnalysisRecord(
            repo_url="https://github.com/test/repo",
            repo_name="test/repo",
            model_used="test-model",
            tech_stack=TechStackInfo(languages=["Python"]),
            technical_summary="Tech summary",
            executive_summary="Exec summary",
        )

        with (
            patch(
                "advisor.api.endpoints.AnalysisOrchestrator"
            ) as MockOrchestrator,
            patch(
                "advisor.api.endpoints.get_supabase_client"
            ) as MockSupabase,
            patch(
                "advisor.api.endpoints.AnalysisRepository"
            ) as MockRepo,
        ):
            mock_orchestrator = MagicMock()
            mock_orchestrator.analyze = AsyncMock(return_value=mock_record)
            MockOrchestrator.return_value = mock_orchestrator

            mock_repo = MagicMock()
            mock_repo.create = AsyncMock(return_value=mock_record)
            MockRepo.return_value = mock_repo

            response = client.post(
                "/analyze",
                json={"repo_url": "https://github.com/test/repo"},
            )

            assert response.status_code == 202
            data = response.json()
            assert data["success"] is True
            assert "technical_summary" in data
            assert "executive_summary" in data


class TestListAnalysesEndpoint:
    """Tests for list analyses endpoint."""

    def test_list_analyses_format(self, client):
        """Test list endpoint response format (mocked)."""
        with (
            patch(
                "advisor.api.endpoints.get_supabase_client"
            ) as MockSupabase,
            patch(
                "advisor.api.endpoints.AnalysisRepository"
            ) as MockRepo,
        ):
            mock_repo = MagicMock()
            mock_repo.list_recent = AsyncMock(return_value=[])
            MockRepo.return_value = mock_repo

            response = client.get("/analyses")
            
            assert response.status_code == 200
            data = response.json()
            assert "analyses" in data
            assert "count" in data
