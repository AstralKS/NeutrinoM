"""Centralized configuration — every tunable parameter externalized.

Zero hardcoded constants in business logic. All values loadable from
environment variables or a .env file.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TrendEngineSettings(BaseSettings):
    """All tunables for the Trend Intelligence Engine."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="TREND_",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Supabase (dedicated project for trend engine) ──────────────
    supabase_url: str = Field(
        default="https://twaostoxlkgooursmkib.supabase.co",
        description="Supabase project URL for trend engine",
    )
    supabase_service_key: str = Field(
        default="sb_secret_h_9COH7lxsxfoEOseM0eyA_OR55J8ey",
        description="Supabase service role key",
    )

    # ── Embedding ──────────────────────────────────────────────────
    embedding_model: str = Field(
        default="openai/text-embedding-3-small",
        description="Embedding model identifier (OpenRouter path)",
    )
    embedding_dim: int = Field(
        default=1536,
        description="Embedding vector dimensionality",
    )
    embedding_batch_size: int = Field(
        default=64,
        description="Max texts per embedding API call",
    )

    # ── Real-time Search ───────────────────────────────────────────
    serper_api_key: str = Field(
        default="",
        description="Serper.dev API key for web search",
    )
    github_token: str = Field(
        default="",
        description="GitHub token for API search (optional, increases rate limit)",
    )
    cache_max_days: int = Field(
        default=7,
        description="Max age in days for cached trend insights",
    )

    # ── LLM (for cluster labeling, architecture snapshots) ─────────
    llm_model: str = Field(
        default="google/gemini-2.0-flash-001",
        description="LLM model for labeling and architecture inference",
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter API base URL",
    )
    openrouter_api_key: str = Field(
        default="",
        description="OpenRouter API key",
    )

    # ── Ingestion ──────────────────────────────────────────────────
    chunk_min_tokens: int = Field(default=300, description="Min chunk size in tokens")
    chunk_max_tokens: int = Field(default=800, description="Max chunk size in tokens")
    rate_limit_per_domain: float = Field(
        default=1.0,
        description="Minimum seconds between requests to same domain",
    )

    # ── Clustering (HDBSCAN) ───────────────────────────────────────
    hdbscan_min_cluster_size: int = Field(
        default=10,
        description="HDBSCAN min_cluster_size parameter",
    )
    hdbscan_min_samples: int = Field(
        default=5,
        description="HDBSCAN min_samples parameter",
    )
    single_source_dominance_threshold: float = Field(
        default=0.70,
        description="Max fraction of docs from one source before cluster rejection",
    )
    rolling_window_days: int = Field(
        default=90,
        description="Rolling window for clustering in days",
    )

    # ── Temporal Modeling ──────────────────────────────────────────
    decay_lambda: float = Field(
        default=0.05,
        description="Exponential decay lambda for recency weighting",
    )

    # ── Trend Scoring Weights ─────────────────────────────────────
    weight_alpha: float = Field(default=0.35, description="Weight for growth_rate")
    weight_beta: float = Field(default=0.25, description="Weight for acceleration")
    weight_gamma: float = Field(default=0.15, description="Weight for log(cluster_size)")
    weight_delta: float = Field(default=0.15, description="Weight for credibility")
    weight_zeta: float = Field(default=0.10, description="Weight for source diversity")

    # ── Classification Thresholds ─────────────────────────────────
    growth_rate_emerging: float = Field(
        default=0.30,
        description="Min growth_rate for 'emerging'",
    )
    growth_rate_expanding: float = Field(
        default=0.10,
        description="Min growth_rate for 'expanding'",
    )
    growth_rate_declining: float = Field(
        default=-0.10,
        description="Max growth_rate for 'declining'",
    )
    acceleration_established_max: float = Field(
        default=0.10,
        description="Max |acceleration| for 'established'",
    )

    # ── Exclusion Filters ─────────────────────────────────────────
    volatility_multiplier: float = Field(
        default=3.0,
        description="Multiplier of std(acceleration) for volatility flag",
    )

    # ── Labeling ──────────────────────────────────────────────────
    membership_shift_threshold: float = Field(
        default=0.30,
        description="Fraction of membership shift to trigger re-labeling",
    )
    label_top_k_chunks: int = Field(
        default=5,
        description="Number of centroid-nearest chunks for LLM labeling input",
    )

    # ── API ────────────────────────────────────────────────────────
    api_key: str = Field(
        default="trend-engine-dev-key",
        description="API key for trend engine endpoints",
    )
    api_host: str = Field(default="0.0.0.0", description="API bind host")
    api_port: int = Field(default=8001, description="API bind port")


@lru_cache
def get_settings() -> TrendEngineSettings:
    """Return cached settings singleton."""
    return TrendEngineSettings()
