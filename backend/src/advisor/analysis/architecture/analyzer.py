"""Deep architecture analyzer - clean conductor class."""

import logging
from typing import Any

from advisor.database.models import TechStackInfo

from .context_extractor import ContextExtractor
from .graph_engine import GraphEngine
from .llm_client import LLMArchitectureClient
from .models import DeepArchitectureAnalysis

logger = logging.getLogger(__name__)


class DeepArchitectureAnalyzer:
    """Performs deep architecture analysis using Hybrid AST + LLM approach.

    This is the "conductor" that orchestrates:
    - GraphEngine for dependency math
    - ContextExtractor for file parsing
    - LLMArchitectureClient for AI analysis
    """

    def __init__(self, api_key: str | None = None, model_name: str = "gpt-4o"):
        """Initialize the analyzer.

        Args:
            api_key: OpenAI API key. Falls back to OPENAI_API_KEY env var.
            model_name: Model to use for LLM analysis.
        """
        self.graph_engine = GraphEngine()
        self.extractor = ContextExtractor(model_name)
        self.llm_client = LLMArchitectureClient(api_key, model_name)

    def analyze(
        self, file_contents: dict[str, str], tech_stack: TechStackInfo,
    ) -> DeepArchitectureAnalysis:
        """Perform deep architecture analysis with Dynamic Token-Based Splitting.

        Args:
            file_contents: Map of file paths to content.
            tech_stack: Detected technology stack.

        Returns:
            Complete deep architecture analysis.
        """
        logger.info(f"Starting deep architecture analysis on {len(file_contents)} files")

        # 1. Build dependency graph (Math)
        graph = self.graph_engine.build_graph(file_contents, self.extractor)

        # 2. Graph analysis (fast, deterministic)
        entry_points = self.graph_engine.find_entry_points(graph)
        utilities = self.graph_engine.find_shared_utilities(graph)
        circular = self.graph_engine.find_circular_deps(graph)
        coupling = self.graph_engine.calculate_coupling(graph)
        mermaid = self.graph_engine.generate_mermaid(graph)

        # 3. Categorize files and prepare batches (Parsing)
        categorized = self.extractor.categorize_files(file_contents)
        batches = self.extractor.prepare_batches(categorized)

        # 4. LLM analysis with smart batching (AI)
        llm_results = self.llm_client.analyze_batches(batches, graph, file_contents)

        logger.info("Deep architecture analysis complete")

        # 5. Combine and return
        return DeepArchitectureAnalysis(
            dependency_graph=graph,
            data_flow_patterns=llm_results.get("data_flow_patterns", []),
            state_patterns=llm_results.get("state_patterns", []),
            cache_patterns=llm_results.get("cache_patterns", []),
            design_patterns=llm_results.get("design_patterns", []),
            architectural_violations=llm_results.get("architectural_violations", []),
            entry_points=entry_points,
            shared_utilities=utilities,
            circular_dependencies=circular,
            coupling_score=coupling,
            architecture_type=llm_results.get("architecture_type", "Unknown"),
            mermaid_diagram=mermaid,
        )
