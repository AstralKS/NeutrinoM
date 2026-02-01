"""Analysis module - repository analysis and code review.

Organized into submodules:
- core/: Main orchestration and deep review logic  
- detectors/: Stack, feature, and integration detection
- analyzers/: Architecture, risk, business analysis

Usage:
    from advisor.analysis import AnalysisOrchestrator
    orchestrator = AnalysisOrchestrator()
    result = await orchestrator.analyze("https://github.com/owner/repo")
"""

# Only export core components that are actually used
from advisor.analysis.core import (
    AnalysisOrchestrator,
    DeepReviewOrchestrator, 
    TokenOptimizer,
)

__all__ = [
    "AnalysisOrchestrator",
    "DeepReviewOrchestrator",
    "TokenOptimizer",
]
