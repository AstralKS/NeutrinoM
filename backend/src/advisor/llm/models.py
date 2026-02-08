"""Available LLM models and their configurations.

Free models from OpenRouter with capability metadata.
"""

from enum import Enum

from pydantic import BaseModel


class ModelCapability(Enum):
    """Model capability categories."""

    ANALYSIS = "analysis"
    REASONING = "reasoning"
    CODING = "coding"
    SUMMARIZATION = "summarization"


class ModelInfo(BaseModel):
    """Model metadata and configuration."""

    id: str
    name: str
    context_length: int
    capabilities: list[ModelCapability]
    is_free: bool = True
    priority: int = 0  # Lower = higher priority for fallback


# Free models available on OpenRouter
AVAILABLE_MODELS: list[ModelInfo] = [
    ModelInfo(
        id="tngtech/deepseek-r1t2-chimera:free",
        name="DeepSeek R1T2 Chimera",
        context_length=128000,
        capabilities=[
            ModelCapability.ANALYSIS,
            ModelCapability.REASONING,
            ModelCapability.CODING,
        ],
        priority=0,
    ),
    ModelInfo(
        id="moonshotai/kimi-k2:free",
        name="Moonshot Kimi K2",
        context_length=128000,
        capabilities=[
            ModelCapability.ANALYSIS,
            ModelCapability.SUMMARIZATION,
        ],
        priority=1,
    ),
    ModelInfo(
        id="arcee-ai/trinity-large-preview:free",
        name="Arcee Trinity Large",
        context_length=128000,
        capabilities=[
            ModelCapability.ANALYSIS,
            ModelCapability.CODING,
        ],
        priority=2,
    ),
    ModelInfo(
        id="z-ai/glm-4.5-air:free",
        name="GLM 4.5 Air",
        context_length=128000,
        capabilities=[
            ModelCapability.ANALYSIS,
            ModelCapability.SUMMARIZATION,
        ],
        priority=3,
    ),
]


class AvailableModels:
    """Model registry and selection utilities."""

    @staticmethod
    def get_all() -> list[ModelInfo]:
        """Get all available models."""
        return AVAILABLE_MODELS

    @staticmethod
    def get_by_id(model_id: str) -> ModelInfo | None:
        """Get model by ID."""
        for model in AVAILABLE_MODELS:
            if model.id == model_id:
                return model
        return None

    @staticmethod
    def get_for_capability(capability: ModelCapability) -> list[ModelInfo]:
        """Get models with a specific capability, sorted by priority."""
        matching = [
            m for m in AVAILABLE_MODELS if capability in m.capabilities
        ]
        return sorted(matching, key=lambda m: m.priority)

    @staticmethod
    def get_default() -> ModelInfo:
        """Get the default (highest priority) model."""
        return AVAILABLE_MODELS[0]

    @staticmethod
    def get_fallback_order() -> list[str]:
        """Get model IDs in fallback priority order."""
        sorted_models = sorted(AVAILABLE_MODELS, key=lambda m: m.priority)
        return [m.id for m in sorted_models]
