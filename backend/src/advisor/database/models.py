"""Pydantic models for database entities.

These models represent the structured data stored in Supabase.
All analysis output is stored as JSONB for flexibility.
"""

from datetime import datetime
import json
import re
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


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


class ProStat(BaseModel):
    """Visual stat widget to be rendered inline with report sections."""

    id: str = Field(description='e.g., "health", "roi", "risk"')
    label: str
    value: str | int
    trend: str = Field(description='e.g., "+12%", "Critical"')
    trend_direction: str = Field(description='"up", "down", "neutral"')


class DeepSection(BaseModel):
    """A single section of the interleaved executive report."""

    title: str
    detailed_markdown: str = Field(
        description="STRICT INSTRUCTION: Must be deep, comprehensive analysis (min 150 words per section). Do not summarize or bullet-point everything. Write like a senior McKinsey consultant."
    )
    associated_stat: ProStat | None = None


class ExecutiveStats(BaseModel):
    """Quantitative executive statistics with optional interleaved sections."""

    overall_health_score: int = Field(ge=0, le=100)
    radar_metrics: dict[str, int] = Field(
        description="Scores 0-100 for Security, Scalability, Maintainability, Performance, Modernity"
    )
    tech_debt_estimate_days: int = Field(ge=0)
    risk_level: str = Field(
        description="Risk level: Low, Medium, High, or Critical"
    )
    architecture_diagram: str | None = Field(
        default=None,
        description="Raw Mermaid.js flowchart string representing the system architecture",
    )

    # Interleaved executive report sections
    tldr_strip: dict[str, Any] | None = Field(
        default=None,
        description="Quick-glance KPIs: overall_health, tech_debt_days, risk_level, top_opportunity, etc.",
    )
    sections: list[DeepSection] = Field(
        default_factory=list,
        description="Ordered report sections with optional inline stat widgets",
    )

    @field_validator("risk_level", mode="before")
    @classmethod
    def normalize_risk_level(cls, v: str) -> str:
        """Normalize risk_level to title case (LLMs often return lowercase)."""
        if isinstance(v, str):
            normalized = v.strip().title()
            if normalized in ("Low", "Medium", "High", "Critical"):
                return normalized
            # Fallback for unexpected values
            return "Medium"
        return "Medium"


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
    user_id: UUID | None = None  # Link to auth.users for RLS
    repo_url: str
    repo_name: str
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    model_used: str

    # Structured analysis output
    tech_stack: TechStackInfo
    architecture_patterns: list[ArchitecturePattern] = Field(
        default_factory=list)
    risks_and_gaps: list[RiskItem] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)

    # NEW: Enhanced analysis output
    features: list[Feature] = Field(default_factory=list)
    business_model: BusinessModel | None = None
    integrations: list[Integration] = Field(default_factory=list)
    executive_stats: ExecutiveStats | None = None

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
        # Remove user_id if None (anonymous request)
        if data.get("user_id") is None:
            data.pop("user_id", None)
            
        # Serialize unmigrated dictionary columns into executive_summary to bypass schema validation
        meta = {
            "executive_stats": data.pop("executive_stats", None),
            "trend_data": data.pop("trend_data", None),
            "timeline": data.pop("timeline", None),
        }
        
        exec_sum = data.get("executive_summary", "")
        # Remove existing meta wrapper if present
        exec_sum = re.sub(r'\n\n<!-- __META__:.* -->$', '', exec_sum)
        
        # Append the new meta wrapper
        data["executive_summary"] = f"{exec_sum}\n\n<!-- __META__:{json.dumps(meta)} -->"
        
        return data

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> "AnalysisRecord":
        """Create instance from database row."""
        # Unpack serialized metadata from executive_summary
        exec_sum = row.get("executive_summary", "")
        match = re.search(r'\n\n<!-- __META__:(.*) -->$', exec_sum)
        
        if match:
            try:
                meta = json.loads(match.group(1))
                row["executive_summary"] = exec_sum[:match.start()]
                
                # Restore columns if they aren't natively in the row
                if "executive_stats" not in row or row["executive_stats"] is None:
                    row["executive_stats"] = meta.get("executive_stats")
                if "trend_data" not in row or row["trend_data"] is None:
                    row["trend_data"] = meta.get("trend_data")
                if "timeline" not in row or row["timeline"] is None:
                    row["timeline"] = meta.get("timeline")
            except json.JSONDecodeError:
                pass
                
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
        alias="github_token",
        description="GitHub access token for private repos (ephemeral, never stored)",
    )


class AnalysisResponse(BaseModel):
    """Response containing analysis results."""

    success: bool
    analysis_id: UUID | None = None
    message: str = ""
    technical_summary: str | None = None
    executive_summary: str | None = None
    executive_stats: ExecutiveStats | None = None
    repo_url: str | None = None
    model_used: str | None = None
    timeline: dict[str, Any] | None = None
    api_call_timings: list[dict[str, Any]] | None = None
    trend_data: dict[str, Any] | None = None
