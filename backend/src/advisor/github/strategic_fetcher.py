"""Strategic multi-pass file fetcher for deep repository analysis.

Fetches 100-150 strategic files in three passes:
1. Complete file tree structure analysis
2. Pattern-based prioritization (routes, models, configs, auth, services)
3. Parallel batch fetch with smart content sampling
"""

import asyncio
import logging
from typing import Any

from advisor.github.client import GitHubClient

logger = logging.getLogger(__name__)

# Strategic file patterns by category (ordered by importance)
ROUTE_PATTERNS = [
    "route", "router", "controller", "endpoint", "api",
    "views.py", "urls.py", "handlers", "rest",
]

MODEL_PATTERNS = [
    "model", "schema", "entity", "domain", "types.ts",
    "types.py", "interfaces", "dto",
]

CONFIG_PATTERNS = [
    "config", "settings", "env", ".toml", ".yaml", ".yml",
    "docker", "nginx", "webpack", "vite", "next.config",
]

AUTH_PATTERNS = [
    "auth", "login", "signup", "session", "jwt", "oauth",
    "passport", "permission", "guard", "middleware/auth",
]

SERVICE_PATTERNS = [
    "service", "usecase", "repository", "provider",
    "utils", "helpers", "lib/", "core/",
]

INTEGRATION_PATTERNS = [
    "stripe", "payment", "email", "sms", "twilio",
    "sendgrid", "aws", "s3", "firebase", "supabase",
]


class StrategicFetcher:
    """Multi-pass strategic file fetcher for deep analysis."""

    def __init__(self, github_client: GitHubClient) -> None:
        """Initialize with GitHub client."""
        self._github = github_client

    async def fetch_strategic_files(
        self,
        owner: str,
        repo: str,
        branch: str,
        max_files: int = 150,
        batch_size: int = 20,
    ) -> dict[str, str]:
        """Fetch strategic files using multi-pass approach.

        Args:
            owner: Repository owner.
            repo: Repository name.
            branch: Branch to fetch from.
            max_files: Maximum files to fetch.
            batch_size: Files per parallel batch.

        Returns:
            Dict mapping file paths to contents.
        """
        # Pass 1: Get complete file tree
        file_tree = await self._github.get_file_tree(owner, repo, branch)
        logger.info(f"Pass 1: Found {len(file_tree)} total items in tree")

        # Pass 2: Prioritize files by pattern
        prioritized = self._prioritize_files(file_tree)
        files_to_fetch = prioritized[:max_files]
        logger.info(f"Pass 2: Prioritized {len(files_to_fetch)} files for analysis")

        # Pass 3: Parallel batch fetch
        file_contents = await self._batch_fetch_contents(
            owner, repo, branch, files_to_fetch, batch_size
        )
        logger.info(f"Pass 3: Fetched {len(file_contents)} file contents")

        return file_contents

    def _prioritize_files(
        self,
        file_tree: list[dict[str, Any]],
    ) -> list[str]:
        """Prioritize files by strategic importance.

        Returns file paths ordered by importance score.
        """
        scored_files: list[tuple[str, int]] = []

        for item in file_tree:
            if item.get("type") != "blob":
                continue

            path = item["path"]
            score = self._calculate_priority_score(path)
            scored_files.append((path, score))

        # Sort by score (higher = more important)
        scored_files.sort(key=lambda x: x[1], reverse=True)

        return [path for path, _ in scored_files]

    def _calculate_priority_score(self, path: str) -> int:
        """Calculate priority score for a file path.

        Higher score = higher priority.
        """
        path_lower = path.lower()
        score = 0

        # Category scoring (higher = more strategic)
        if any(p in path_lower for p in ROUTE_PATTERNS):
            score += 100
        if any(p in path_lower for p in AUTH_PATTERNS):
            score += 90
        if any(p in path_lower for p in INTEGRATION_PATTERNS):
            score += 85
        if any(p in path_lower for p in MODEL_PATTERNS):
            score += 80
        if any(p in path_lower for p in SERVICE_PATTERNS):
            score += 70
        if any(p in path_lower for p in CONFIG_PATTERNS):
            score += 60

        # Boost for root-level important files
        if "/" not in path:
            if any(f in path_lower for f in [
                "package.json", "pyproject.toml", "requirements.txt",
                "readme", "dockerfile", "docker-compose",
            ]):
                score += 150

        # Reduce score for test files (still fetch but lower priority)
        if any(t in path_lower for t in ["test", "spec", "__tests__", "mock"]):
            score -= 30

        # Reduce score for vendor/node_modules
        if any(v in path_lower for v in ["node_modules", "vendor", "dist", "build"]):
            score -= 200

        # Boost for main entry points
        if any(e in path_lower for e in [
            "index.ts", "index.js", "main.py", "app.py",
            "server.ts", "server.js", "main.ts", "main.js",
        ]):
            score += 50

        return score

    async def _batch_fetch_contents(
        self,
        owner: str,
        repo: str,
        branch: str,
        file_paths: list[str],
        batch_size: int,
    ) -> dict[str, str]:
        """Fetch file contents in parallel batches."""
        contents: dict[str, str] = {}

        for i in range(0, len(file_paths), batch_size):
            batch = file_paths[i : i + batch_size]

            # Fetch batch in parallel
            tasks = [
                self._github.get_file_content(owner, repo, path, branch)
                for path in batch
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Collect successful results
            for path, result in zip(batch, results):
                if isinstance(result, str) and result:
                    contents[path] = result
                elif isinstance(result, Exception):
                    logger.debug(f"Failed to fetch {path}: {result}")

        return contents

    def get_file_categories(
        self,
        file_contents: dict[str, str],
    ) -> dict[str, list[str]]:
        """Categorize fetched files for analysis.

        Returns dict mapping category to list of file paths.
        """
        categories: dict[str, list[str]] = {
            "routes": [],
            "models": [],
            "configs": [],
            "auth": [],
            "services": [],
            "integrations": [],
            "other": [],
        }

        for path in file_contents:
            path_lower = path.lower()
            categorized = False

            if any(p in path_lower for p in ROUTE_PATTERNS):
                categories["routes"].append(path)
                categorized = True
            if any(p in path_lower for p in MODEL_PATTERNS):
                categories["models"].append(path)
                categorized = True
            if any(p in path_lower for p in CONFIG_PATTERNS):
                categories["configs"].append(path)
                categorized = True
            if any(p in path_lower for p in AUTH_PATTERNS):
                categories["auth"].append(path)
                categorized = True
            if any(p in path_lower for p in SERVICE_PATTERNS):
                categories["services"].append(path)
                categorized = True
            if any(p in path_lower for p in INTEGRATION_PATTERNS):
                categories["integrations"].append(path)
                categorized = True

            if not categorized:
                categories["other"].append(path)

        return categories
