"""Data models for deep architecture analysis."""

from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, Field


# =============================================================================
# FILE CATEGORIZATION
# =============================================================================

class FileCategory(Enum):
    """Category of a file based on its role in the codebase."""
    FRONTEND = "frontend"
    BACKEND = "backend"
    INFRA = "infra"


@dataclass
class AnalysisBatch:
    """Represents a single LLM API call batch."""
    category: str
    files: dict
    token_count: int = 0
    extracted_context: str = ""


# Token thresholds for batch splitting
BACKEND_TOKEN_THRESHOLD = 100_000
FRONTEND_TOKEN_THRESHOLD = 60_000
SMALL_APP_THRESHOLD = 100_000


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class DependencyNode(BaseModel):
    """A node in the dependency graph."""
    path: str
    imports: list[str] = Field(default_factory=list)
    imported_by: list[str] = Field(default_factory=list)
    is_entry_point: bool = False
    is_utility: bool = False


class DataFlowPattern(BaseModel):
    """Detected data flow pattern."""
    name: str
    description: str
    files_involved: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class StatePattern(BaseModel):
    """Detected state management pattern."""
    pattern: str
    files: list[str] = Field(default_factory=list)
    complexity: str = "simple"


class CachePattern(BaseModel):
    """Detected caching strategy."""
    type: str
    location: str
    files: list[str] = Field(default_factory=list)


class DesignPattern(BaseModel):
    """Detected design pattern."""
    name: str
    description: str
    files: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class ArchitecturalViolation(BaseModel):
    """Detected architectural violation."""
    rule: str
    description: str
    files_involved: list[str] = Field(default_factory=list)
    severity: str = "medium"


class DeepArchitectureAnalysis(BaseModel):
    """Complete deep architecture analysis."""
    dependency_graph: dict[str, DependencyNode] = Field(default_factory=dict)
    data_flow_patterns: list[DataFlowPattern] = Field(default_factory=list)
    state_patterns: list[StatePattern] = Field(default_factory=list)
    cache_patterns: list[CachePattern] = Field(default_factory=list)
    design_patterns: list[DesignPattern] = Field(default_factory=list)
    architectural_violations: list[ArchitecturalViolation] = Field(default_factory=list)
    entry_points: list[str] = Field(default_factory=list)
    shared_utilities: list[str] = Field(default_factory=list)
    circular_dependencies: list[tuple[str, str]] = Field(default_factory=list)
    coupling_score: float = 0.0
    architecture_type: str = ""
    mermaid_diagram: str = ""
