"""Technology stack detection from repository files.

Analyzes package files, configs, and source code to identify
languages, frameworks, and tools used in the project.
"""

import json
import logging
from typing import Any

from advisor.database.models import TechStackInfo

logger = logging.getLogger(__name__)


# Language detection by file extension
EXTENSION_LANGUAGE_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".jsx": "JavaScript (React)",
    ".tsx": "TypeScript (React)",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".cs": "C#",
    ".cpp": "C++",
    ".c": "C",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".scala": "Scala",
    ".ex": "Elixir",
    ".clj": "Clojure",
    ".vue": "Vue",
    ".svelte": "Svelte",
}

# Framework detection patterns
FRAMEWORK_PATTERNS = {
    "package.json": {
        "react": "React",
        "next": "Next.js",
        "vue": "Vue.js",
        "nuxt": "Nuxt.js",
        "angular": "Angular",
        "svelte": "Svelte",
        "express": "Express.js",
        "fastify": "Fastify",
        "nestjs": "NestJS",
    },
    "requirements.txt": {
        "django": "Django",
        "flask": "Flask",
        "fastapi": "FastAPI",
        "tornado": "Tornado",
        "starlette": "Starlette",
    },
    "pyproject.toml": {
        "django": "Django",
        "flask": "Flask",
        "fastapi": "FastAPI",
    },
    "Cargo.toml": {
        "actix": "Actix",
        "rocket": "Rocket",
        "axum": "Axum",
    },
    "go.mod": {
        "gin": "Gin",
        "echo": "Echo",
        "fiber": "Fiber",
    },
}


class StackDetector:
    """Detects technology stack from repository files."""

    def detect(
        self,
        file_tree: list[dict[str, Any]],
        file_contents: dict[str, str],
    ) -> TechStackInfo:
        """Detect technology stack from files.

        Args:
            file_tree: List of files in repository.
            file_contents: Map of file path to content.

        Returns:
            Detected technology stack information.
        """
        languages = self._detect_languages(file_tree)
        frameworks = self._detect_frameworks(file_contents)
        databases = self._detect_databases(file_contents)
        tools = self._detect_tools(file_tree, file_contents)
        package_managers = self._detect_package_managers(file_tree)
        versions = self._extract_versions(file_contents)

        return TechStackInfo(
            languages=languages,
            frameworks=frameworks,
            databases=databases,
            tools=tools,
            package_managers=package_managers,
            versions=versions,
        )

    def _detect_languages(self, file_tree: list[dict[str, Any]]) -> list[str]:
        """Detect languages from file extensions."""
        languages = set()
        for item in file_tree:
            # Skip directories - check for tree type or if it's clearly a directory
            item_type = item.get("type", "blob")
            if item_type == "tree":
                continue
            path = item.get("path", "")
            for ext, lang in EXTENSION_LANGUAGE_MAP.items():
                if path.endswith(ext):
                    languages.add(lang)
                    break
        return sorted(languages)

    def _detect_frameworks(self, file_contents: dict[str, str]) -> list[str]:
        """Detect frameworks from package files."""
        frameworks = set()

        for filename, patterns in FRAMEWORK_PATTERNS.items():
            content = self._find_file_content(file_contents, filename)
            if content:
                content_lower = content.lower()
                for pattern, framework in patterns.items():
                    if pattern in content_lower:
                        frameworks.add(framework)

        return sorted(frameworks)

    def _detect_databases(self, file_contents: dict[str, str]) -> list[str]:
        """Detect database usage from dependencies and configs."""
        databases = set()
        db_patterns = {
            "postgresql": "PostgreSQL",
            "postgres": "PostgreSQL",
            "mysql": "MySQL",
            "mongodb": "MongoDB",
            "redis": "Redis",
            "sqlite": "SQLite",
            "dynamodb": "DynamoDB",
            "elasticsearch": "Elasticsearch",
            "supabase": "Supabase (PostgreSQL)",
        }

        all_content = " ".join(file_contents.values()).lower()
        for pattern, db in db_patterns.items():
            if pattern in all_content:
                databases.add(db)

        return sorted(databases)

    def _detect_tools(
        self,
        file_tree: list[dict[str, Any]],
        file_contents: dict[str, str],
    ) -> list[str]:
        """Detect build tools and CI/CD."""
        tools = set()

        # File-based detection
        file_tool_map = {
            "Dockerfile": "Docker",
            "docker-compose": "Docker Compose",
            ".github/workflows": "GitHub Actions",
            "Jenkinsfile": "Jenkins",
            ".gitlab-ci": "GitLab CI",
            "webpack": "Webpack",
            "vite.config": "Vite",
            "tsconfig": "TypeScript",
            "eslint": "ESLint",
            "prettier": "Prettier",
            "jest.config": "Jest",
            "pytest.ini": "pytest",
            "pyproject.toml": "Python (modern)",
        }

        for item in file_tree:
            path = item["path"].lower()
            for pattern, tool in file_tool_map.items():
                if pattern.lower() in path:
                    tools.add(tool)

        return sorted(tools)

    def _detect_package_managers(
        self,
        file_tree: list[dict[str, Any]],
    ) -> list[str]:
        """Detect package managers from lock files."""
        managers = set()
        manager_files = {
            "package-lock.json": "npm",
            "yarn.lock": "Yarn",
            "pnpm-lock.yaml": "pnpm",
            "poetry.lock": "Poetry",
            "Pipfile.lock": "Pipenv",
            "Cargo.lock": "Cargo",
            "go.sum": "Go Modules",
            "Gemfile.lock": "Bundler",
            "composer.lock": "Composer",
        }

        for item in file_tree:
            filename = item["path"].split("/")[-1]
            if filename in manager_files:
                managers.add(manager_files[filename])

        return sorted(managers)

    def _extract_versions(self, file_contents: dict[str, str]) -> dict[str, str]:
        """Extract version information from package files."""
        versions = {}

        # Try package.json
        pkg_json = self._find_file_content(file_contents, "package.json")
        if pkg_json:
            try:
                pkg = json.loads(pkg_json)
                if "version" in pkg:
                    versions["project"] = pkg["version"]
                # Check for specific tools
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                for key in ["react", "vue", "angular", "next", "typescript"]:
                    if key in deps:
                        versions[key] = deps[key].lstrip("^~")
            except json.JSONDecodeError:
                pass

        return versions

    def _find_file_content(
        self,
        file_contents: dict[str, str],
        filename: str,
    ) -> str | None:
        """Find file content by filename (case-insensitive)."""
        filename_lower = filename.lower()
        for path, content in file_contents.items():
            if path.lower().endswith(filename_lower):
                return content
        return None
