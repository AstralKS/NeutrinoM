"""Tests for risk analyzer."""

import pytest

from advisor.analysis.risk_analyzer import RiskAnalyzer
from advisor.database.models import TechStackInfo


class TestRiskAnalyzer:
    """Tests for risk detection."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return RiskAnalyzer()

    @pytest.fixture
    def empty_tech_stack(self):
        """Empty tech stack for testing."""
        return TechStackInfo()

    def test_detect_missing_tests(self, analyzer, empty_tech_stack):
        """Test detection of missing test files."""
        file_tree = [
            {"path": "src/main.py", "type": "blob"},
            {"path": "src/utils.py", "type": "blob"},
        ]
        
        risks = analyzer.analyze(file_tree, {}, empty_tech_stack)
        risk_titles = [r.title for r in risks]
        
        assert "Missing Test Coverage" in risk_titles

    def test_detect_hardcoded_secrets(self, analyzer, empty_tech_stack):
        """Test detection of hardcoded secrets."""
        file_tree = [{"path": "config.py", "type": "blob"}]
        file_contents = {
            "config.py": 'API_KEY = "sk-1234567890abcdef"\npassword="secret123"'
        }
        
        risks = analyzer.analyze(file_tree, file_contents, empty_tech_stack)
        risk_titles = [r.title for r in risks]
        
        assert "Potential Hardcoded Secrets" in risk_titles

    def test_detect_no_ci_cd(self, analyzer, empty_tech_stack):
        """Test detection of missing CI/CD."""
        file_tree = [
            {"path": "src/main.py", "type": "blob"},
        ]
        
        risks = analyzer.analyze(file_tree, {}, empty_tech_stack)
        risk_titles = [r.title for r in risks]
        
        assert "No CI/CD Configuration" in risk_titles

    def test_no_risk_with_proper_setup(self, analyzer, empty_tech_stack):
        """Test that proper setup has fewer risks."""
        file_tree = [
            {"path": "tests/test_main.py", "type": "blob"},
            {"path": ".github/workflows/ci.yml", "type": "blob"},
            {"path": "Dockerfile", "type": "blob"},
            {"path": "README.md", "type": "blob"},
        ]
        
        risks = analyzer.analyze(file_tree, {}, empty_tech_stack)
        
        # Should not have these risks
        risk_titles = [r.title for r in risks]
        assert "Missing Test Coverage" not in risk_titles
        assert "No CI/CD Configuration" not in risk_titles
        assert "No Containerization" not in risk_titles

    def test_multi_language_complexity(self, analyzer):
        """Test detection of multi-language complexity."""
        tech_stack = TechStackInfo(
            languages=["Python", "JavaScript", "Go", "Rust", "Ruby"],
        )
        
        risks = analyzer.analyze([], {}, tech_stack)
        risk_titles = [r.title for r in risks]
        
        assert "Multi-Language Complexity" in risk_titles

    def test_severity_ordering(self, analyzer, empty_tech_stack):
        """Test that risks are ordered by severity."""
        file_tree = [
            {"path": "config.py", "type": "blob"},
        ]
        file_contents = {
            "config.py": 'password="secret"'  # Critical risk
        }
        
        risks = analyzer.analyze(file_tree, file_contents, empty_tech_stack)
        
        if len(risks) > 1:
            severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            for i in range(len(risks) - 1):
                assert (
                    severity_order.get(risks[i].severity, 99)
                    <= severity_order.get(risks[i + 1].severity, 99)
                )
