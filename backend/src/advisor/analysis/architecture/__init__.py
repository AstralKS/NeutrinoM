"""Deep architecture analysis module.

This module provides comprehensive architecture analysis using:
- AST-based dependency graph building
- Dynamic Token-Based Splitting for efficient LLM usage
- Pattern detection (design, state, cache, data flow)
"""

from .analyzer import DeepArchitectureAnalyzer
from .context_extractor import ContextExtractor
from .graph_engine import GraphEngine
from .llm_client import LLMArchitectureClient
from .models import (
    AnalysisBatch,
    ArchitecturalViolation,
    CachePattern,
    DataFlowPattern,
    DeepArchitectureAnalysis,
    DependencyNode,
    DesignPattern,
    FileCategory,
    StatePattern,
)

__all__ = [
    # Main analyzer
    "DeepArchitectureAnalyzer",
    # Component classes
    "GraphEngine",
    "ContextExtractor",
    "LLMArchitectureClient",
    # Models
    "DeepArchitectureAnalysis",
    "DependencyNode",
    "FileCategory",
    "AnalysisBatch",
    "DataFlowPattern",
    "StatePattern",
    "CachePattern",
    "DesignPattern",
    "ArchitecturalViolation",
]
