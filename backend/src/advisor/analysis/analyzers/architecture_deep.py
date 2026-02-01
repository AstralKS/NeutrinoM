"""Deep architecture analyzer - advanced architecture and data flow analysis.

Provides deeper insights into:
- Dependency graphs between modules
- Data flow patterns
- Database schema detection
- State management patterns
- Caching strategies
- Performance patterns
"""

import re
from collections import defaultdict

from pydantic import BaseModel, Field

from advisor.database.models import TechStackInfo


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

    pattern: str  # redux, zustand, context, mobx, pinia, vuex
    files: list[str] = Field(default_factory=list)
    complexity: str = "simple"  # simple, moderate, complex


class CachePattern(BaseModel):
    """Detected caching strategy."""

    type: str  # redis, in-memory, cdn, browser
    location: str  # server, client, edge
    files: list[str] = Field(default_factory=list)


class DeepArchitectureAnalysis(BaseModel):
    """Complete deep architecture analysis."""

    dependency_graph: dict[str, DependencyNode] = Field(default_factory=dict)
    data_flow_patterns: list[DataFlowPattern] = Field(default_factory=list)
    state_patterns: list[StatePattern] = Field(default_factory=list)
    cache_patterns: list[CachePattern] = Field(default_factory=list)
    entry_points: list[str] = Field(default_factory=list)
    shared_utilities: list[str] = Field(default_factory=list)
    circular_dependencies: list[tuple[str, str]] = Field(default_factory=list)
    coupling_score: float = 0.0  # 0-1, higher = more tightly coupled


# Patterns for detection
STATE_PATTERNS = {
    "redux": [r"createStore", r"configureStore", r"createSlice", r"@reduxjs/toolkit"],
    "zustand": [r"create\s*\(", r"zustand", r"useStore"],
    "context": [r"createContext", r"useContext", r"Provider"],
    "mobx": [r"observable", r"makeObservable", r"mobx"],
    "pinia": [r"defineStore", r"pinia"],
    "vuex": [r"createStore", r"vuex", r"mapState"],
    "recoil": [r"atom\s*\(", r"selector\s*\(", r"recoil"],
    "jotai": [r"atom\s*\(", r"jotai"],
}

CACHE_PATTERNS = {
    "redis": [r"redis", r"ioredis", r"redis\.createClient"],
    "memcached": [r"memcached", r"memcache"],
    "in_memory": [r"lru-cache", r"node-cache", r"cachetools"],
    "cdn": [r"cloudflare", r"fastly", r"akamai", r"cache-control"],
    "browser": [r"localStorage", r"sessionStorage", r"indexedDB"],
}


class DeepArchitectureAnalyzer:
    """Performs deep architecture analysis."""

    def analyze(
        self,
        file_contents: dict[str, str],
        tech_stack: TechStackInfo,
    ) -> DeepArchitectureAnalysis:
        """Perform deep architecture analysis.

        Args:
            file_contents: Map of file paths to content.
            tech_stack: Detected technology stack.

        Returns:
            Complete deep architecture analysis.
        """
        # Build dependency graph
        dep_graph = self._build_dependency_graph(file_contents)

        # Detect patterns
        data_flow = self._detect_data_flow(file_contents, dep_graph)
        state_patterns = self._detect_state_patterns(file_contents)
        cache_patterns = self._detect_cache_patterns(file_contents)

        # Analyze graph
        entry_points = self._find_entry_points(dep_graph)
        utilities = self._find_shared_utilities(dep_graph)
        circular = self._find_circular_deps(dep_graph)
        coupling = self._calculate_coupling(dep_graph)

        return DeepArchitectureAnalysis(
            dependency_graph=dep_graph,
            data_flow_patterns=data_flow,
            state_patterns=state_patterns,
            cache_patterns=cache_patterns,
            entry_points=entry_points,
            shared_utilities=utilities,
            circular_dependencies=circular,
            coupling_score=coupling,
        )

    def _build_dependency_graph(
        self,
        file_contents: dict[str, str],
    ) -> dict[str, DependencyNode]:
        """Build a dependency graph from imports."""
        graph: dict[str, DependencyNode] = {}

        for path, content in file_contents.items():
            imports = self._extract_imports(content, path)
            graph[path] = DependencyNode(path=path, imports=imports)

        # Build reverse mapping (imported_by)
        for path, node in graph.items():
            for imp in node.imports:
                if imp in graph:
                    graph[imp].imported_by.append(path)

        return graph

    def _extract_imports(self, content: str, file_path: str) -> list[str]:
        """Extract import statements from file."""
        imports: list[str] = []

        # Python imports
        py_patterns = [
            r'from\s+([\w.]+)\s+import',
            r'import\s+([\w.]+)',
        ]

        # JS/TS imports
        js_patterns = [
            r'import\s+.*\s+from\s+["\']([^"\']+)["\']',
            r'require\s*\(["\']([^"\']+)["\']\)',
        ]

        patterns = py_patterns if file_path.endswith(".py") else js_patterns

        for pattern in patterns:
            for match in re.finditer(pattern, content):
                imports.append(match.group(1))

        return imports

    def _detect_data_flow(
        self,
        file_contents: dict[str, str],
        dep_graph: dict[str, DependencyNode],
    ) -> list[DataFlowPattern]:
        """Detect data flow patterns."""
        patterns: list[DataFlowPattern] = []
        all_content = " ".join(file_contents.values()).lower()

        # API -> Service -> Database pattern
        has_api = any("routes" in p or "api" in p or "endpoint" in p for p in file_contents)
        has_service = any("service" in p for p in file_contents)
        has_db = "database" in all_content or "repository" in all_content

        if has_api and has_service and has_db:
            patterns.append(DataFlowPattern(
                name="Layered Architecture",
                description="API → Service → Database layered data flow",
                files_involved=[p for p in file_contents if any(k in p for k in ["route", "service", "repo"])],
                confidence=0.8,
            ))

        # Event-driven pattern
        if "emit" in all_content and ("on(" in all_content or "subscribe" in all_content):
            patterns.append(DataFlowPattern(
                name="Event-Driven",
                description="Event emission and subscription pattern detected",
                confidence=0.7,
            ))

        # Queue-based pattern
        if any(q in all_content for q in ["rabbitmq", "sqs", "bullmq", "celery"]):
            patterns.append(DataFlowPattern(
                name="Queue-Based",
                description="Asynchronous message queue processing",
                confidence=0.9,
            ))

        return patterns

    def _detect_state_patterns(
        self,
        file_contents: dict[str, str],
    ) -> list[StatePattern]:
        """Detect state management patterns."""
        patterns: list[StatePattern] = []
        all_content = " ".join(file_contents.values())

        for pattern_name, indicators in STATE_PATTERNS.items():
            matching_files = []
            for path, content in file_contents.items():
                if any(re.search(ind, content) for ind in indicators):
                    matching_files.append(path)

            if matching_files:
                complexity = "simple" if len(matching_files) < 3 else (
                    "moderate" if len(matching_files) < 8 else "complex"
                )
                patterns.append(StatePattern(
                    pattern=pattern_name,
                    files=matching_files,
                    complexity=complexity,
                ))

        return patterns

    def _detect_cache_patterns(
        self,
        file_contents: dict[str, str],
    ) -> list[CachePattern]:
        """Detect caching strategies."""
        patterns: list[CachePattern] = []

        for cache_type, indicators in CACHE_PATTERNS.items():
            matching_files = []
            for path, content in file_contents.items():
                content_lower = content.lower()
                if any(ind.lower() in content_lower for ind in indicators):
                    matching_files.append(path)

            if matching_files:
                location = "server" if cache_type in ["redis", "memcached", "in_memory"] else (
                    "edge" if cache_type == "cdn" else "client"
                )
                patterns.append(CachePattern(
                    type=cache_type,
                    location=location,
                    files=matching_files,
                ))

        return patterns

    def _find_entry_points(self, graph: dict[str, DependencyNode]) -> list[str]:
        """Find application entry points (not imported by others)."""
        entry_points = []
        for path, node in graph.items():
            if not node.imported_by:
                # Additional heuristics for entry points
                if any(k in path.lower() for k in ["main", "index", "app", "server", "__init__"]):
                    entry_points.append(path)
                    node.is_entry_point = True
        return entry_points

    def _find_shared_utilities(self, graph: dict[str, DependencyNode]) -> list[str]:
        """Find utility modules imported by many files."""
        utilities = []
        for path, node in graph.items():
            if len(node.imported_by) >= 3:
                if any(k in path.lower() for k in ["util", "helper", "common", "lib", "shared"]):
                    utilities.append(path)
                    node.is_utility = True
        return utilities

    def _find_circular_deps(
        self,
        graph: dict[str, DependencyNode],
    ) -> list[tuple[str, str]]:
        """Find circular dependencies."""
        circular: list[tuple[str, str]] = []

        for path, node in graph.items():
            for imp in node.imports:
                if imp in graph and path in graph[imp].imports:
                    pair = tuple(sorted([path, imp]))
                    if pair not in circular:
                        circular.append(pair)

        return circular

    def _calculate_coupling(self, graph: dict[str, DependencyNode]) -> float:
        """Calculate overall coupling score (0-1)."""
        if not graph:
            return 0.0

        total_deps = sum(len(node.imports) for node in graph.values())
        max_possible = len(graph) * (len(graph) - 1)

        if max_possible == 0:
            return 0.0

        return min(total_deps / max_possible, 1.0)
