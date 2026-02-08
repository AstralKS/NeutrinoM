"""Deep architecture analyzer - Hybrid AST + LLM approach.

Uses Python's AST module for accurate import detection and LLM for semantic
analysis of architectural patterns, design patterns, and violations.
"""

import ast
import json
import logging
import os
import re
from collections import defaultdict
from typing import Any

from pydantic import BaseModel, Field

from advisor.database.models import TechStackInfo


logger = logging.getLogger(__name__)


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


class DesignPattern(BaseModel):
    """Detected design pattern."""

    name: str  # Singleton, Factory, Observer, etc.
    description: str
    files: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class ArchitecturalViolation(BaseModel):
    """Detected architectural violation."""

    rule: str
    description: str
    files_involved: list[str] = Field(default_factory=list)
    severity: str = "medium"  # low, medium, high


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
    coupling_score: float = 0.0  # 0-1, higher = more tightly coupled
    architecture_type: str = ""  # Layered, Microservices, Hexagonal, Monolith
    mermaid_diagram: str = ""  # Mermaid.js visualization


class DeepArchitectureAnalyzer:
    """Performs deep architecture analysis using Hybrid AST + LLM approach."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "gpt-4o",
    ) -> None:
        """Initialize the analyzer.

        Args:
            api_key: OpenAI API key. Falls back to OPENAI_API_KEY env var.
            model_name: Model to use for LLM analysis.
        """
        self._api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._model_name = model_name
        self._client = None

        if self._api_key:
            try:
                import openai
                self._client = openai.OpenAI(api_key=self._api_key)
            except ImportError:
                logger.warning("OpenAI package not installed")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")

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
        # Step 1: Build accurate dependency graph using AST
        dep_graph = self._build_dependency_graph(file_contents)

        # Step 2: Graph analysis (fast math-based operations)
        entry_points = self._find_entry_points(dep_graph)
        utilities = self._find_shared_utilities(dep_graph)
        circular = self._find_circular_deps(dep_graph)
        coupling = self._calculate_coupling(dep_graph)

        # Step 3: Generate Mermaid visualization
        mermaid = self._generate_mermaid(dep_graph)

        # Step 4: LLM-based semantic analysis
        llm_analysis = self._analyze_with_llm(dep_graph, file_contents)

        return DeepArchitectureAnalysis(
            dependency_graph=dep_graph,
            data_flow_patterns=llm_analysis.get("data_flow_patterns", []),
            state_patterns=llm_analysis.get("state_patterns", []),
            cache_patterns=llm_analysis.get("cache_patterns", []),
            design_patterns=llm_analysis.get("design_patterns", []),
            architectural_violations=llm_analysis.get("architectural_violations", []),
            entry_points=entry_points,
            shared_utilities=utilities,
            circular_dependencies=circular,
            coupling_score=coupling,
            architecture_type=llm_analysis.get("architecture_type", "Unknown"),
            mermaid_diagram=mermaid,
        )

    def _build_dependency_graph(
        self,
        file_contents: dict[str, str],
    ) -> dict[str, DependencyNode]:
        """Build a dependency graph from imports using AST."""
        graph: dict[str, DependencyNode] = {}

        for path, content in file_contents.items():
            imports = self._extract_imports(content, path)
            graph[path] = DependencyNode(path=path, imports=imports)

        # Build reverse mapping (imported_by)
        for path, node in graph.items():
            for imp in node.imports:
                # Normalize import to potential file path
                for graph_path in graph:
                    if self._import_matches_path(imp, graph_path):
                        graph[graph_path].imported_by.append(path)

        return graph

    def _extract_imports(self, content: str, file_path: str) -> list[str]:
        """Extract imports using AST for Python, regex for others."""
        if file_path.endswith(".py"):
            return self._extract_python_imports_ast(content)
        else:
            return self._extract_js_imports_regex(content)

    def _extract_python_imports_ast(self, content: str) -> list[str]:
        """Extract Python imports using AST for accuracy."""
        imports: list[str] = []

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)

        except SyntaxError as e:
            logger.debug(f"Failed to parse Python file: {e}")
            # Fallback to regex if AST fails
            return self._extract_python_imports_regex(content)

        return imports

    def _extract_python_imports_regex(self, content: str) -> list[str]:
        """Fallback regex-based Python import extraction."""
        imports: list[str] = []
        patterns = [
            r'^from\s+([\w.]+)\s+import',
            r'^import\s+([\w.]+)',
        ]

        for line in content.split("\n"):
            line = line.strip()
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    imports.append(match.group(1))
                    break

        return imports

    def _extract_js_imports_regex(self, content: str) -> list[str]:
        """Extract JS/TS imports using regex."""
        imports: list[str] = []

        patterns = [
            r'import\s+.*\s+from\s+["\']([^"\']+)["\']',
            r'require\s*\(["\']([^"\']+)["\']\)',
            r'import\s*\(["\']([^"\']+)["\']\)',  # Dynamic imports
        ]

        for pattern in patterns:
            for match in re.finditer(pattern, content):
                imports.append(match.group(1))

        return imports

    def _import_matches_path(self, import_name: str, file_path: str) -> bool:
        """Check if an import name could refer to a file path."""
        # Normalize paths
        import_parts = import_name.replace(".", "/").lower()
        path_lower = file_path.lower().replace("\\", "/")

        # Check if import is part of the path
        return import_parts in path_lower or path_lower.endswith(f"{import_parts}.py")

    def _prepare_graph_context(
        self,
        graph: dict[str, DependencyNode],
        file_contents: dict[str, str],
    ) -> str:
        """Prepare context for LLM analysis.

        Includes:
        - Dependency graph as adjacency list
        - Signatures of top hub files (most connections)
        """
        context_parts: list[str] = []

        # Part 1: Adjacency list representation
        context_parts.append("=== DEPENDENCY GRAPH ===")
        for path, node in graph.items():
            if node.imports:
                imports_str = ", ".join(node.imports[:10])  # Limit to 10
                context_parts.append(f"{path} -> [{imports_str}]")

        # Part 2: Find hub files (most connections)
        hub_scores = {}
        for path, node in graph.items():
            hub_scores[path] = len(node.imports) + len(node.imported_by)

        top_hubs = sorted(hub_scores.items(), key=lambda x: x[1], reverse=True)[:5]

        context_parts.append("\n=== HUB FILES (Most Connected) ===")
        for hub_path, score in top_hubs:
            context_parts.append(f"\n--- {hub_path} (connections: {score}) ---")

            if hub_path in file_contents:
                content = file_contents[hub_path]
                signatures = self._extract_signatures(content, hub_path)
                context_parts.append(signatures)

        return "\n".join(context_parts)

    def _extract_signatures(self, content: str, file_path: str) -> str:
        """Extract class and function signatures from a file."""
        signatures: list[str] = []

        if file_path.endswith(".py"):
            try:
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # Get class and its methods
                        methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                        methods_str = ", ".join(methods[:5])
                        signatures.append(f"class {node.name}: [{methods_str}]")

                    elif isinstance(node, ast.FunctionDef):
                        # Get function signature
                        args = [a.arg for a in node.args.args]
                        args_str = ", ".join(args[:5])
                        signatures.append(f"def {node.name}({args_str})")

            except SyntaxError:
                pass

        else:
            # JS/TS - use regex
            class_pattern = r'class\s+(\w+)'
            func_pattern = r'(?:function|async function)\s+(\w+)\s*\('
            arrow_pattern = r'const\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>'

            for match in re.finditer(class_pattern, content):
                signatures.append(f"class {match.group(1)}")

            for match in re.finditer(func_pattern, content):
                signatures.append(f"function {match.group(1)}()")

            for match in re.finditer(arrow_pattern, content):
                signatures.append(f"const {match.group(1)} = () =>")

        return "\n".join(signatures[:20])  # Limit signatures

    def _analyze_with_llm(
        self,
        graph: dict[str, DependencyNode],
        file_contents: dict[str, str],
    ) -> dict[str, Any]:
        """Analyze architecture using LLM."""
        if not self._client:
            logger.warning("No LLM client, using fallback analysis")
            return self._fallback_analysis(graph, file_contents)

        context = self._prepare_graph_context(graph, file_contents)

        system_prompt = """You are a Principal Software Architect analyzing a codebase's architecture.

Based on the dependency graph and code signatures provided, analyze:

1. **Architecture Type**: Identify the high-level architecture pattern:
   - Layered (Controllers/Services/Repositories)
   - Microservices (multiple independent services)
   - Hexagonal/Clean Architecture (ports and adapters, domain isolation)
   - Monolith (single tightly-coupled application)
   - Event-Driven (message queues, event sourcing)

2. **Design Patterns**: Identify design patterns from class structures:
   - Singleton, Factory, Builder, Observer, Strategy, Repository, etc.

3. **Data Flow Patterns**: How data moves through the system:
   - Layered, Event-Driven, Queue-Based, Streaming, etc.

4. **State Management**: Frontend state patterns if applicable:
   - Redux, Zustand, Context API, MobX, Pinia, Vuex, etc.

5. **Caching Strategies**: Identify caching layers:
   - Redis, Memcached, In-Memory, CDN, Browser storage

6. **Architectural Violations**: Any anti-patterns or violations:
   - Circular dependencies
   - Domain layer importing infrastructure
   - Tight coupling between modules
   - Mixed concerns

Return a JSON object with this exact schema:
{
    "architecture_type": "string",
    "design_patterns": [{"name": "string", "description": "string", "files": ["string"], "confidence": 0.0}],
    "data_flow_patterns": [{"name": "string", "description": "string", "files_involved": ["string"], "confidence": 0.0}],
    "state_patterns": [{"pattern": "string", "files": ["string"], "complexity": "simple|moderate|complex"}],
    "cache_patterns": [{"type": "string", "location": "server|client|edge", "files": ["string"]}],
    "architectural_violations": [{"rule": "string", "description": "string", "files_involved": ["string"], "severity": "low|medium|high"}]
}

Return ONLY the JSON object."""

        user_prompt = f"""Analyze this codebase architecture:

{context}

Return your analysis as a JSON object."""

        try:
            response = self._client.chat.completions.create(
                model=self._model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=2000,
            )

            content = response.choices[0].message.content
            if content:
                data = json.loads(content)
                return self._parse_llm_response(data)

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response: {e}")
        except Exception as e:
            logger.warning(f"LLM analysis failed: {e}")

        return self._fallback_analysis(graph, file_contents)

    def _parse_llm_response(self, data: dict) -> dict[str, Any]:
        """Parse and validate LLM response."""
        result: dict[str, Any] = {
            "architecture_type": data.get("architecture_type", "Unknown"),
            "design_patterns": [],
            "data_flow_patterns": [],
            "state_patterns": [],
            "cache_patterns": [],
            "architectural_violations": [],
        }

        # Parse design patterns
        for dp in data.get("design_patterns", []):
            result["design_patterns"].append(DesignPattern(
                name=dp.get("name", ""),
                description=dp.get("description", ""),
                files=dp.get("files", []),
                confidence=dp.get("confidence", 0.5),
            ))

        # Parse data flow patterns
        for dfp in data.get("data_flow_patterns", []):
            result["data_flow_patterns"].append(DataFlowPattern(
                name=dfp.get("name", ""),
                description=dfp.get("description", ""),
                files_involved=dfp.get("files_involved", []),
                confidence=dfp.get("confidence", 0.5),
            ))

        # Parse state patterns
        for sp in data.get("state_patterns", []):
            result["state_patterns"].append(StatePattern(
                pattern=sp.get("pattern", ""),
                files=sp.get("files", []),
                complexity=sp.get("complexity", "simple"),
            ))

        # Parse cache patterns
        for cp in data.get("cache_patterns", []):
            result["cache_patterns"].append(CachePattern(
                type=cp.get("type", ""),
                location=cp.get("location", "server"),
                files=cp.get("files", []),
            ))

        # Parse violations
        for v in data.get("architectural_violations", []):
            result["architectural_violations"].append(ArchitecturalViolation(
                rule=v.get("rule", ""),
                description=v.get("description", ""),
                files_involved=v.get("files_involved", []),
                severity=v.get("severity", "medium"),
            ))

        return result

    def _fallback_analysis(
        self,
        graph: dict[str, DependencyNode],
        file_contents: dict[str, str],
    ) -> dict[str, Any]:
        """Fallback analysis when LLM is unavailable."""
        all_content = " ".join(file_contents.values()).lower()
        all_paths = " ".join(file_contents.keys()).lower()

        # Guess architecture type
        arch_type = "Monolith"
        if "controller" in all_paths and "service" in all_paths and "repository" in all_paths:
            arch_type = "Layered"
        elif "domain" in all_paths and "infrastructure" in all_paths and "application" in all_paths:
            arch_type = "Hexagonal/Clean"
        elif "microservice" in all_paths or len([p for p in file_contents if "api" in p.lower()]) > 3:
            arch_type = "Microservices"

        # Detect state patterns
        state_patterns = []
        state_keywords = {
            "redux": ["redux", "createstore", "configurestores"],
            "zustand": ["zustand", "usestore"],
            "context": ["createcontext", "usecontext"],
        }
        for pattern, keywords in state_keywords.items():
            if any(k in all_content for k in keywords):
                state_patterns.append(StatePattern(pattern=pattern, files=[], complexity="simple"))

        # Detect cache patterns
        cache_patterns = []
        if "redis" in all_content:
            cache_patterns.append(CachePattern(type="redis", location="server", files=[]))
        if "localstorage" in all_content or "sessionstorage" in all_content:
            cache_patterns.append(CachePattern(type="browser", location="client", files=[]))

        return {
            "architecture_type": arch_type,
            "design_patterns": [],
            "data_flow_patterns": [],
            "state_patterns": state_patterns,
            "cache_patterns": cache_patterns,
            "architectural_violations": [],
        }

    def _generate_mermaid(self, graph: dict[str, DependencyNode]) -> str:
        """Generate Mermaid.js diagram from dependency graph."""
        if not graph:
            return ""

        lines = ["graph TD"]

        # Create node IDs (sanitize paths)
        node_ids = {}
        for i, path in enumerate(graph.keys()):
            # Create short readable ID
            basename = path.split("/")[-1].split("\\")[-1]
            basename = basename.replace(".", "_").replace("-", "_")
            node_ids[path] = f"N{i}_{basename[:20]}"

        # Add edges
        edges_added = set()
        for path, node in graph.items():
            from_id = node_ids[path]

            for imp in node.imports[:5]:  # Limit connections per node
                # Find matching graph path
                for target_path in graph:
                    if self._import_matches_path(imp, target_path):
                        to_id = node_ids[target_path]
                        edge_key = f"{from_id}->{to_id}"

                        if edge_key not in edges_added and from_id != to_id:
                            lines.append(f"    {from_id} --> {to_id}")
                            edges_added.add(edge_key)
                        break

        # Add node labels
        lines.append("")
        for path, node_id in node_ids.items():
            label = path.split("/")[-1].split("\\")[-1]
            lines.append(f"    {node_id}[{label}]")

        return "\n".join(lines) if len(lines) > 2 else ""

    def _find_entry_points(self, graph: dict[str, DependencyNode]) -> list[str]:
        """Find application entry points (not imported by others)."""
        entry_points = []
        for path, node in graph.items():
            if not node.imported_by:
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
                # Check if any graph path matches this import
                for target_path, target_node in graph.items():
                    if self._import_matches_path(imp, target_path):
                        # Check if target imports back to source
                        for target_imp in target_node.imports:
                            if self._import_matches_path(target_imp, path):
                                pair = tuple(sorted([path, target_path]))
                                if pair not in circular:
                                    circular.append(pair)
                        break

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
