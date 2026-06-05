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


# Free models available on OpenRouter (ordered by priority)
# NOTE: nvidia/nemotron-3.5-content-safety was REMOVED — it's a safety
# classifier that only returns "User Safety: safe", not a code analysis model.
AVAILABLE_MODELS: list[ModelInfo] = [
    ModelInfo(
        id="google/gemini-2.0-flash-thinking-exp:free",
        name="Gemini 2.0 Flash Thinking",
        context_length=1000000,
        capabilities=[
            ModelCapability.ANALYSIS,
            ModelCapability.CODING,
            ModelCapability.REASONING,
            ModelCapability.SUMMARIZATION,
        ],
        priority=0,
    ),
    ModelInfo(
        id="meta-llama/llama-3.3-70b-instruct:free",
        name="Llama 3.3 70B",
        context_length=131000,
        capabilities=[
            ModelCapability.ANALYSIS,
            ModelCapability.CODING,
            ModelCapability.REASONING,
            ModelCapability.SUMMARIZATION,
        ],
        priority=1,
    ),
    ModelInfo(
        id="mistralai/mistral-small-24b-instruct-2501:free",
        name="Mistral Small 24B",
        context_length=32000,
        capabilities=[
            ModelCapability.ANALYSIS,
            ModelCapability.CODING,
            ModelCapability.REASONING,
            ModelCapability.SUMMARIZATION,
        ],
        priority=2,
    ),
    ModelInfo(
        id="qwen/qwen-2.5-coder-32b-instruct:free",
        name="Qwen 2.5 Coder",
        context_length=32000,
        capabilities=[
            ModelCapability.ANALYSIS,
            ModelCapability.REASONING,
            ModelCapability.CODING,
        ],
        priority=3,
    ),
    ModelInfo(
        id="google/gemma-2-9b-it:free",
        name="Gemma 2 9B",
        context_length=8000,
        capabilities=[
            ModelCapability.ANALYSIS,
            ModelCapability.SUMMARIZATION,
        ],
        priority=4,
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
        sorted_models = sorted(AVAILABLE_MODELS, key=lambda m: m.priority)
        return sorted_models[0]

    @staticmethod
    def get_fallback_order() -> list[str]:
        """Get model IDs in fallback priority order."""
        sorted_models = sorted(AVAILABLE_MODELS, key=lambda m: m.priority)
        return [m.id for m in sorted_models]

    @staticmethod
    def get_model_for_tokens(estimated_tokens: int) -> ModelInfo | None:
        """Get the best model that can fit the estimated token count.

        Args:
            estimated_tokens: Estimated total tokens (prompt + max response).

        Returns:
            Best fitting model, or None if no model can fit.
        """
        sorted_models = sorted(AVAILABLE_MODELS, key=lambda m: m.priority)
        for model in sorted_models:
            if model.context_length >= estimated_tokens:
                return model
        return None
