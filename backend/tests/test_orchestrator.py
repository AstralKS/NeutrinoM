"""Integration tests for the analysis orchestrator.

Uses pytest with async support.
Run: uv run pytest tests/test_orchestrator.py -v
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from advisor.analysis.core.deep_review import DeepReviewResult
from advisor.analysis.orchestrator import AnalysisOrchestrator
from advisor.database.models import TechStackInfo, ExecutiveStats


class TestAnalysisOrchestrator:
    """Tests for AnalysisOrchestrator."""

    @pytest.fixture
    def mock_github_response(self):
        """Mock GitHub API responses."""
        return {
            "metadata": {
                "name": "test-repo",
                "default_branch": "main",
                "size": 1024,
            },
            "file_tree": [
                {"path": "package.json", "type": "blob", "size": 500},
                {"path": "src/index.ts", "type": "blob", "size": 1000},
                {"path": "README.md", "type": "blob", "size": 200},
            ],
            "package_json": """{
                "name": "test-app",
                "dependencies": {"react": "^18.0.0"}
            }""",
        }

    @pytest.fixture
    def mock_llm_response(self):
        """Mock LLM response."""
        return {
            "content": "This is a test summary for the repository.",
            "model": "test-model",
            "usage": {"total_tokens": 100},
        }

    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self):
        """Test orchestrator can be initialized."""
        orchestrator = AnalysisOrchestrator()
        assert orchestrator is not None
        assert orchestrator._github is not None
        assert orchestrator._llm is not None

    @pytest.mark.asyncio
    async def test_orchestrator_with_mocks(
        self, mock_github_response, mock_llm_response
    ):
        """Test full analysis with mocked dependencies."""
        with (
            patch(
                "advisor.analysis.orchestrator.GitHubClient"
            ) as MockGitHub,
            patch(
                "advisor.analysis.orchestrator.DeepReviewOrchestrator"
            ) as MockDeepReview,
        ):
            # Setup mocks
            mock_github = MagicMock()
            mock_github.get_repo_metadata = AsyncMock(
                return_value=mock_github_response["metadata"]
            )
            mock_github.get_file_tree = AsyncMock(
                return_value=mock_github_response["file_tree"]
            )
            mock_github.get_file_content = AsyncMock(
                return_value=mock_github_response["package_json"]
            )
            MockGitHub.return_value = mock_github
            MockGitHub.parse_repo_url = MagicMock(
                return_value=("owner", "repo")
            )

            mock_deep_review = MagicMock()
            mock_deep_review.review = AsyncMock(
                return_value=DeepReviewResult(
                    total_files=3,
                    total_tokens=1000,
                    compression_stats=None,
                    frontend_analysis=None,
                    backend_analysis=None,
                    infra_analysis=None,
                    aggregated_technical="Tech Summary",
                    aggregated_executive="Exec Summary",
                    executive_stats=ExecutiveStats(
                        overall_health_score=85,
                        radar_metrics={
                            "Security": 90,
                            "Scalability": 80,
                            "Maintainability": 85,
                            "Performance": 88,
                            "Modernity": 92
                        },
                        tech_debt_estimate_days=3,
                        risk_level="Low"
                    ),
                    model_used="test-model",
                    trend_context=""
                )
            )
            MockDeepReview.return_value = mock_deep_review

            # Run analysis
            orchestrator = AnalysisOrchestrator()
            result = await orchestrator.analyze(
                "https://github.com/owner/repo"
            )

            # Verify result
            assert result is not None
            assert result.repo_name == "owner/repo"
            assert result.model_used == "test-model"
            assert result.technical_summary is not None
            assert result.executive_summary is not None
            assert result.executive_stats is not None
            assert result.executive_stats.overall_health_score == 85
            assert result.executive_stats.risk_level == "Low"

    @pytest.mark.asyncio
    async def test_format_tech_stack(self):
        """Test tech stack formatting."""
        orchestrator = AnalysisOrchestrator()
        
        tech_stack = TechStackInfo(
            languages=["Python", "TypeScript"],
            frameworks=["FastAPI", "React"],
            databases=["PostgreSQL"],
            tools=["Docker"],
        )
        
        formatted = orchestrator._format_tech_stack(tech_stack)
        
        assert "Python" in formatted
        assert "FastAPI" in formatted
        assert "PostgreSQL" in formatted
        assert "Docker" in formatted

    @pytest.mark.asyncio
    async def test_format_empty_tech_stack(self):
        """Test formatting empty tech stack."""
        orchestrator = AnalysisOrchestrator()
        
        tech_stack = TechStackInfo()
        formatted = orchestrator._format_tech_stack(tech_stack)
        
        assert formatted == "Not detected"
