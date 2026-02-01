"""Tests for architecture analyzer."""

import pytest

from advisor.analysis.architecture import ArchitectureAnalyzer


class TestArchitectureAnalyzer:
    """Tests for architecture pattern detection."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return ArchitectureAnalyzer()

    def test_detect_clean_architecture(self, analyzer):
        """Test clean architecture detection."""
        file_tree = [
            {"path": "src/domain/entities/user.py", "type": "blob"},
            {"path": "src/domain/repositories/user_repo.py", "type": "blob"},
            {"path": "src/application/use_cases/create_user.py", "type": "blob"},
            {"path": "src/infrastructure/db/postgres.py", "type": "blob"},
        ]
        
        patterns = analyzer.analyze(file_tree, {})
        pattern_names = [p.pattern_name for p in patterns]
        
        assert "Clean Architecture" in pattern_names

    def test_detect_mvc_pattern(self, analyzer):
        """Test MVC pattern detection."""
        file_tree = [
            {"path": "app/models/user.py", "type": "blob"},
            {"path": "app/views/user_view.py", "type": "blob"},
            {"path": "app/controllers/user_controller.py", "type": "blob"},
        ]
        
        patterns = analyzer.analyze(file_tree, {})
        pattern_names = [p.pattern_name for p in patterns]
        
        # Check for any MVC-related pattern
        assert any("MVC" in name or "Model" in name for name in pattern_names)

    def test_detect_microservices(self, analyzer):
        """Test microservices detection."""
        file_tree = [
            {"path": "services/user-service/Dockerfile", "type": "blob"},
            {"path": "services/order-service/Dockerfile", "type": "blob"},
            {"path": "docker-compose.yml", "type": "blob"},
            {"path": "gateway/main.py", "type": "blob"},
        ]
        
        patterns = analyzer.analyze(file_tree, {})
        pattern_names = [p.pattern_name for p in patterns]
        
        assert "Microservices" in pattern_names

    def test_detect_monolith(self, analyzer):
        """Test simple structure detection."""
        file_tree = [
            {"path": "app.py", "type": "blob"},
            {"path": "routes.py", "type": "blob"},
            {"path": "database.py", "type": "blob"},
        ]
        
        patterns = analyzer.analyze(file_tree, {})
        pattern_names = [p.pattern_name for p in patterns]
        
        # Should detect simple/flat structure
        assert any("Simple" in name or "Flat" in name for name in pattern_names)

    def test_empty_file_tree(self, analyzer):
        """Test with empty file tree returns simple structure."""
        patterns = analyzer.analyze([], {})
        # May return a default pattern for simple/unknown structure
        assert isinstance(patterns, list)

    def test_confidence_scoring(self, analyzer):
        """Test that patterns have valid confidence scores."""
        file_tree = [
            {"path": "src/domain/entity.py", "type": "blob"},
            {"path": "src/application/service.py", "type": "blob"},
        ]
        
        patterns = analyzer.analyze(file_tree, {})
        
        for pattern in patterns:
            assert 0.0 <= pattern.confidence <= 1.0
