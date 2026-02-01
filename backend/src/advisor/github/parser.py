"""Repository structure parsing and analysis.

Classifies files, identifies key configuration files, and builds
a structured view of the repository for analysis.
"""

from pathlib import PurePath
from typing import Any

from pydantic import BaseModel

# Priority files for analysis (ordered by importance)
PRIORITY_FILES = [
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "setup.py",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "composer.json",
    "Gemfile",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    ".github/workflows",
    "README.md",
    "README.rst",
]

# File extensions to analyze (source code)
CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs",
    ".rb", ".php", ".cs", ".cpp", ".c", ".h", ".swift", ".kt",
    ".scala", ".ex", ".exs", ".clj", ".vue", ".svelte",
}

# Configuration file patterns
CONFIG_PATTERNS = {
    ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
    ".env.example", ".env.sample",
}


class FileInfo(BaseModel):
    """Information about a file in the repository."""

    path: str
    type: str  # code, config, doc, other
    extension: str
    size: int = 0
    priority: int = 100  # Lower = higher priority


class RepositoryStructure(BaseModel):
    """Parsed repository structure."""

    total_files: int = 0
    code_files: list[FileInfo] = []
    config_files: list[FileInfo] = []
    doc_files: list[FileInfo] = []
    priority_files: list[FileInfo] = []
    directory_tree: str = ""


class RepositoryParser:
    """Parser for repository structure analysis."""

    @staticmethod
    def parse_file_tree(tree: list[dict[str, Any]]) -> RepositoryStructure:
        """Parse raw file tree into structured format.

        Args:
            tree: Raw file tree from GitHub API.

        Returns:
            Structured repository information.
        """
        structure = RepositoryStructure()
        code_files = []
        config_files = []
        doc_files = []
        priority_files = []

        for item in tree:
            if item["type"] != "blob":  # Skip directories
                continue

            path = item["path"]
            ext = PurePath(path).suffix.lower()
            filename = PurePath(path).name

            file_info = FileInfo(
                path=path,
                type="other",
                extension=ext,
                size=item.get("size", 0),
            )

            # Check if priority file
            priority = RepositoryParser._get_priority(path)
            if priority < 100:
                file_info.priority = priority
                file_info.type = "priority"
                priority_files.append(file_info)

            # Classify by type
            if ext in CODE_EXTENSIONS:
                file_info.type = "code"
                code_files.append(file_info)
            elif ext in CONFIG_PATTERNS or filename.startswith("."):
                file_info.type = "config"
                config_files.append(file_info)
            elif ext in {".md", ".rst", ".txt"} or filename == "LICENSE":
                file_info.type = "doc"
                doc_files.append(file_info)

        # Sort by priority
        priority_files.sort(key=lambda f: f.priority)
        code_files.sort(key=lambda f: f.size, reverse=True)

        structure.total_files = len(tree)
        structure.code_files = code_files[:50]  # Limit to top 50
        structure.config_files = config_files
        structure.doc_files = doc_files
        structure.priority_files = priority_files
        structure.directory_tree = RepositoryParser._build_tree_string(tree)

        return structure

    @staticmethod
    def _get_priority(path: str) -> int:
        """Get priority score for a file path (lower = higher priority)."""
        for i, pattern in enumerate(PRIORITY_FILES):
            if pattern in path:
                return i
        return 100

    @staticmethod
    def _build_tree_string(tree: list[dict[str, Any]], max_depth: int = 3) -> str:
        """Build directory tree string for display."""
        lines = []
        dirs_seen = set()

        for item in sorted(tree, key=lambda x: x["path"]):
            path = item["path"]
            parts = path.split("/")

            # Limit depth
            if len(parts) > max_depth + 1:
                continue

            # Add directory entries
            for i in range(len(parts) - 1):
                dir_path = "/".join(parts[: i + 1])
                if dir_path not in dirs_seen:
                    dirs_seen.add(dir_path)
                    indent = "  " * i
                    lines.append(f"{indent}📁 {parts[i]}/")

            # Add file entry
            if item["type"] == "blob":
                indent = "  " * (len(parts) - 1)
                lines.append(f"{indent}📄 {parts[-1]}")

        return "\n".join(lines[:100])  # Limit lines

    @staticmethod
    def get_files_to_analyze(
        structure: RepositoryStructure,
        max_files: int = 20,
    ) -> list[str]:
        """Get list of files to analyze (prioritized).

        Args:
            structure: Parsed repository structure.
            max_files: Maximum number of files to return.

        Returns:
            List of file paths to fetch and analyze.
        """
        files = []

        # Always include priority files
        for f in structure.priority_files:
            if f.path not in files:
                files.append(f.path)

        # Add representative code files
        for f in structure.code_files:
            if len(files) >= max_files:
                break
            if f.path not in files:
                files.append(f.path)

        return files[:max_files]
