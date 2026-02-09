"""Graph engine for dependency analysis - pure math, no LLM."""

import ast
import re
from collections import defaultdict

from .models import DependencyNode


class GraphEngine:
    """Pure graph analysis operations - deterministic, no AI needed."""

    def build_graph(self, file_contents: dict[str, str], extractor) -> dict[str, DependencyNode]:
        """Build dependency graph from file contents."""
        graph: dict[str, DependencyNode] = {}
        for path, content in file_contents.items():
            imports = extractor.extract_imports(content, path)
            graph[path] = DependencyNode(path=path, imports=imports)

        # Populate imported_by (reverse edges)
        for path, node in graph.items():
            for imp in node.imports:
                for target_path in graph:
                    if self._import_matches_path(imp, target_path):
                        graph[target_path].imported_by.append(path)
        return graph

    def _import_matches_path(self, import_name: str, file_path: str) -> bool:
        """Check if an import name could refer to a file path."""
        import_parts = import_name.replace(".", "/").lower()
        path_lower = file_path.lower().replace("\\", "/")
        return import_parts in path_lower or path_lower.endswith(f"{import_parts}.py")

    def find_entry_points(self, graph: dict[str, DependencyNode]) -> list[str]:
        """Find application entry points (not imported by others)."""
        return [p for p, n in graph.items() if not n.imported_by and n.imports]

    def find_shared_utilities(self, graph: dict[str, DependencyNode]) -> list[str]:
        """Find utility modules imported by many files."""
        threshold = max(3, len(graph) // 4)
        return [p for p, n in graph.items() if len(n.imported_by) >= threshold]

    def find_circular_deps(self, graph: dict[str, DependencyNode]) -> list[tuple[str, str]]:
        """Find circular dependencies."""
        circular: list[tuple[str, str]] = []
        visited: set[str] = set()

        def dfs(node: str, path: list[str]) -> None:
            if node in path:
                idx = path.index(node)
                for i in range(idx, len(path) - 1):
                    pair = (path[i], path[i + 1])
                    if pair not in circular:
                        circular.append(pair)
                return
            if node in visited or node not in graph:
                return
            visited.add(node)
            for imp in graph[node].imports:
                for target in graph:
                    if self._import_matches_path(imp, target):
                        dfs(target, path + [node])

        for start in graph:
            dfs(start, [])
        return circular

    def calculate_coupling(self, graph: dict[str, DependencyNode]) -> float:
        """Calculate overall coupling score (0-1)."""
        if len(graph) < 2:
            return 0.0
        total_edges = sum(len(n.imports) for n in graph.values())
        max_edges = len(graph) * (len(graph) - 1)
        return round(total_edges / max_edges, 2) if max_edges else 0.0

    def generate_mermaid(self, graph: dict[str, DependencyNode]) -> str:
        """Generate Mermaid.js diagram from dependency graph."""
        lines = ["graph TD"]
        node_ids: dict[str, str] = {}

        for i, path in enumerate(graph.keys()):
            name = path.split("/")[-1].split("\\")[-1].replace(".", "_")
            node_ids[path] = f"N{i}_{name}"

        for path, node in graph.items():
            src = node_ids[path]
            for imp in node.imports:
                for target, tid in node_ids.items():
                    if self._import_matches_path(imp, target):
                        lines.append(f"    {src} --> {tid}")

        lines.append("")
        for path, nid in node_ids.items():
            label = path.split("/")[-1].split("\\")[-1]
            lines.append(f"    {nid}[{label}]")

        return "\n".join(lines)
