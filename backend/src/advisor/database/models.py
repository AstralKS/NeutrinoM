"""Pydantic models for database entities.

These models represent the structured data stored in Supabase.
All analysis output is stored as JSONB for flexibility.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class TechStackInfo(BaseModel):
    """Technology stack detection results."""

    languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    databases: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    package_managers: list[str] = Field(default_factory=list)
    versions: dict[str, str] = Field(default_factory=dict)


class ArchitecturePattern(BaseModel):
    """Architecture pattern detection result."""

    pattern_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)
    description: str = ""


class RiskItem(BaseModel):
    """Individual risk or gap identified."""

    category: str  # security, maintainability, scalability, etc.
    severity: str  # low, medium, high, critical
    title: str
    description: str
    impact: str
    recommendation: str


class Recommendation(BaseModel):
    """Forward-looking recommendation."""

    category: str  # architecture, tooling, process, etc.
    priority: str  # low, medium, high
    title: str
    description: str
    effort_estimate: str  # small, medium, large
    business_impact: str
    technical_steps: list[str] = Field(default_factory=list)


class Feature(BaseModel):
    """User-facing feature detected in codebase."""

    name: str
    description: str = ""
    endpoints: list[str] = Field(default_factory=list)
    integrations: list[str] = Field(default_factory=list)
    user_journey_stage: str = ""  # signup, onboarding, core, monetization


class BusinessModel(BaseModel):
    """Business model analysis results."""

    auth_type: str = ""
    auth_providers: list[str] = Field(default_factory=list)
    payment_integrations: list[str] = Field(default_factory=list)
    monetization_type: str = ""  # freemium, subscription, usage-based, one-time
    monetization_signals: list[str] = Field(default_factory=list)
    growth_mechanisms: list[str] = Field(default_factory=list)
    revenue_drivers: list[str] = Field(default_factory=list)
    user_tiers: list[str] = Field(default_factory=list)


class Integration(BaseModel):
    """External integration detected in codebase."""

    name: str
    category: str  # cloud, payment, auth, monitoring, analytics, communication
    detected_from: str = ""
    description: str = ""
    cost_tier: str = ""  # free, low, medium, high, enterprise


class RepositoryMetadata(BaseModel):
    """Minimal repository information."""

    url: str
    name: str
    owner: str
    default_branch: str = "main"
    file_count: int = 0
    total_size_bytes: int = 0
    primary_language: str | None = None


class AnalysisRecord(BaseModel):
    """Complete analysis record stored in database.

    This is the single source of truth for analysis results.
    PDF reports are derived from this data on demand.
    """

    id: UUID | None = None
    repo_url: str
    repo_name: str
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    model_used: str

    # Structured analysis output
    tech_stack: TechStackInfo
    architecture_patterns: list[ArchitecturePattern] = Field(default_factory=list)
    risks_and_gaps: list[RiskItem] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)

    # NEW: Enhanced analysis output
    features: list[Feature] = Field(default_factory=list)
    business_model: BusinessModel | None = None
    integrations: list[Integration] = Field(default_factory=list)

    # Dual outputs - derived from same analysis
    technical_summary: str
    executive_summary: str

    # Metadata
    analysis_duration_ms: int | None = None
    file_count: int | None = None
    files_analyzed: int | None = None  # Actual files with content fetched
    token_usage: dict[str, int] = Field(default_factory=dict)
    timeline: dict[str, Any] | None = None  # Phase-level timestamps
    trend_data: dict[str, Any] | None = None  # Trend intelligence context

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def to_db_dict(self) -> dict[str, Any]:
        """Convert to dictionary suitable for database insertion."""
        data = self.model_dump(mode="json")
        # Remove id if None (let database generate it)
        if data.get("id") is None:
            data.pop("id", None)
        return data

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> "AnalysisRecord":
        """Create instance from database row."""
        return cls.model_validate(row)


class AnalysisRequest(BaseModel):
    """Request to analyze a repository."""

    repo_url: str = Field(
        ...,
        description="GitHub repository URL",
        examples=["https://github.com/owner/repo"],
    )
    access_token: str | None = Field(
        default=None,
        description="GitHub access token for private repos (ephemeral, never stored)",
    )


class AnalysisResponse(BaseModel):
    """Response containing analysis results."""

    success: bool
    analysis_id: UUID | None = None
    message: str = ""
    technical_summary: str | None = None
    executive_summary: str | None = None
    repo_url: str | None = None
    model_used: str | None = None
    timeline: dict[str, Any] | None = None
    api_call_timings: list[dict[str, Any]] | None = None
    trend_data: dict[str, Any] | None = None
