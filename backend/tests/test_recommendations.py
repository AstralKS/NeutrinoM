"""Tests for recommendation engine."""

import pytest

from advisor.analysis.recommendations import RecommendationEngine
from advisor.database.models import (
    ArchitecturePattern,
    RiskItem,
    TechStackInfo,
)


class TestRecommendationEngine:
    """Tests for recommendation generation."""

    @pytest.fixture
    def engine(self):
        """Create engine instance."""
        return RecommendationEngine()

    def test_generate_recommendations(self, engine):
        """Test basic recommendation generation."""
        tech_stack = TechStackInfo(
            languages=["Python"],
            frameworks=["FastAPI"],
        )
        architecture = []
        risks = [
            RiskItem(
                category="maintainability",
                severity="high",
                title="Missing Test Coverage",
                description="No tests found",
                impact="High risk of bugs",
                recommendation="Add tests",
            )
        ]
        
        recommendations = engine.generate(tech_stack, architecture, risks)
        
        assert len(recommendations) > 0

    def test_recommendations_have_required_fields(self, engine):
        """Test that recommendations have all required fields."""
        tech_stack = TechStackInfo(languages=["JavaScript"])
        
        recommendations = engine.generate(tech_stack, [], [])
        
        for rec in recommendations:
            assert rec.title is not None
            assert rec.description is not None
            assert rec.priority in ["low", "medium", "high", "critical"]
            assert rec.effort_estimate in ["small", "medium", "large"]
            assert rec.category is not None

    def test_recommendations_based_on_risks(self, engine):
        """Test that recommendations respond to risks."""
        tech_stack = TechStackInfo()
        risks = [
            RiskItem(
                category="maintainability",
                severity="high",
                title="Missing Test Coverage",
                description="No tests",
                impact="Bugs",
                recommendation="Add tests",
            )
        ]
        
        recs = engine.generate(tech_stack, [], risks)
        rec_titles = [r.title for r in recs]
        
        # Should have testing-related recommendation
        assert any("test" in title.lower() for title in rec_titles)

    def test_empty_inputs(self, engine):
        """Test with empty inputs."""
        recommendations = engine.generate(TechStackInfo(), [], [])
        
        # Should still return some general recommendations
        assert isinstance(recommendations, list)

    def test_priority_ordering(self, engine):
        """Test recommendations are ordered by priority."""
        tech_stack = TechStackInfo(languages=["Python", "JavaScript"])
        risks = [
            RiskItem(
                category="security",
                severity="critical",
                title="Potential Hardcoded Secrets",
                description="Found secrets",
                impact="Security breach",
                recommendation="Use env vars",
            )
        ]
        
        recs = engine.generate(tech_stack, [], risks)
        
        if len(recs) > 1:
            priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            for i in range(len(recs) - 1):
                p1 = priority_order.get(recs[i].priority, 99)
                p2 = priority_order.get(recs[i + 1].priority, 99)
                assert p1 <= p2
