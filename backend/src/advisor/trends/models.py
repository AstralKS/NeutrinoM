"""Data models for technology trend intelligence.

Represents trends from various sources (HN, GitHub, Dev.to)
and their relevance to user tech stacks.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class TrendSource(str, Enum):
    """Source of the technology trend."""

    HACKER_NEWS = "hacker_news"
    GITHUB_TRENDING = "github_trending"
    DEV_TO = "dev_to"
    PRODUCT_HUNT = "product_hunt"


class TrendCategory(str, Enum):
    """Category of the technology trend."""

    FRAMEWORK = "framework"
    TOOL = "tool"
    LANGUAGE = "language"
    LIBRARY = "library"
    PLATFORM = "platform"
    PRACTICE = "practice"
    AI_ML = "ai_ml"
    SECURITY = "security"
    DEVOPS = "devops"
    DATABASE = "database"
    GENERAL = "general"


class TrendItem(BaseModel):
    """A single technology trend item."""

    id: str = ""
    title: str
    url: str = ""
    source: TrendSource
    category: TrendCategory = TrendCategory.GENERAL
    score: int = 0  # Popularity score (upvotes, stars, reactions)
    comments: int = 0
    published_at: datetime | None = None
    fetched_at: datetime = Field(default_factory=datetime.utcnow)

    # Extracted metadata
    technologies: list[str] = Field(default_factory=list)
    summary: str = ""
    author: str = ""


class TrendMatch(BaseModel):
    """A trend matched to user's tech stack."""

    trend: TrendItem
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    matching_technologies: list[str] = Field(default_factory=list)
    opportunity_type: str = ""  # upgrade, new_feature, migration, best_practice
    business_impact: str = ""  # low, medium, high


class TrendReport(BaseModel):
    """Aggregated trend report for a stack."""

    generated_at: datetime = Field(default_factory=datetime.utcnow)
    total_trends_scanned: int = 0
    relevant_trends: list[TrendMatch] = Field(default_factory=list)
    top_technologies: list[str] = Field(default_factory=list)  # Most mentioned
    emerging_tools: list[str] = Field(default_factory=list)  # Rising in popularity
    recommendations: list[str] = Field(default_factory=list)


# Technology keywords for trend matching
TECH_KEYWORDS = {
    # Languages
    "python": ["python", "django", "flask", "fastapi", "pytorch"],
    "javascript": ["javascript", "js", "node", "deno", "bun", "typescript", "ts"],
    "rust": ["rust", "rustlang", "cargo"],
    "go": ["golang", "go ", "go-"],
    # Frameworks
    "react": ["react", "reactjs", "nextjs", "next.js", "remix"],
    "vue": ["vue", "vuejs", "nuxt"],
    "svelte": ["svelte", "sveltekit"],
    # AI/ML
    "ai": ["openai", "gpt", "llm", "langchain", "anthropic", "claude", "ai", "ml"],
    "vector_db": ["pinecone", "weaviate", "qdrant", "chroma", "pgvector"],
    # Infrastructure
    "cloud": ["aws", "gcp", "azure", "vercel", "cloudflare", "fly.io"],
    "database": ["postgres", "mongodb", "redis", "supabase", "planetscale", "turso"],
    "devops": ["docker", "kubernetes", "k8s", "terraform", "pulumi"],
}
