"""Tests for LLM models and client."""

from advisor.llm.models import AvailableModels, ModelCapability


class TestAvailableModels:
    """Tests for model registry."""

    def test_get_all_returns_models(self):
        """Test that get_all returns a list of models."""
        models = AvailableModels.get_all()
        assert len(models) > 0

    def test_get_default_returns_model(self):
        """Test that get_default returns a model."""
        model = AvailableModels.get_default()
        assert model is not None
        assert model.id is not None

    def test_get_fallback_order_returns_ids(self):
        """Test that fallback order returns model IDs."""
        ids = AvailableModels.get_fallback_order()
        assert len(ids) > 0
        assert all(isinstance(id, str) for id in ids)

    def test_get_for_capability(self):
        """Test filtering models by capability."""
        models = AvailableModels.get_for_capability(ModelCapability.ANALYSIS)
        assert len(models) > 0
        for model in models:
            assert ModelCapability.ANALYSIS in model.capabilities

    def test_get_by_id_found(self):
        """Test getting model by ID when exists."""
        default = AvailableModels.get_default()
        found = AvailableModels.get_by_id(default.id)
        assert found is not None
        assert found.id == default.id

    def test_get_by_id_not_found(self):
        """Test getting model by ID when not exists."""
        found = AvailableModels.get_by_id("nonexistent-model")
        assert found is None
