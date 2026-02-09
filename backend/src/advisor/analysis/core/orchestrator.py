"""Analysis orchestrator - main coordinator for repository analysis.

Coordinates GitHub intake, deep AI review, and result aggregation.

NEW ARCHITECTURE:
1. Fetch repo files
2. Send to 3 parallel AIs for deep code review
3. Aggregate into evidence-based reports
"""

import logging
import time

from advisor.analysis.core.deep_review import DeepReviewOrchestrator
from advisor.database.models import (
    AnalysisRecord,
    ArchitecturePattern,
    BusinessModel,
    Feature,
    Integration,
    Recommendation,
    RiskItem,
    TechStackInfo,
)
from advisor.github.client import GitHubClient
from advisor.github.parser import RepositoryParser, RepositoryStructure
from advisor.github.strategic_fetcher import StrategicFetcher

logger = logging.getLogger(__name__)


class AnalysisOrchestrator:
    """Orchestrates the full repository analysis pipeline.

    Flow:
    1. Fetch repository files (up to 300 files)
    2. Run deep AI review (3 parallel AI calls)
    3. Generate evidence-based reports
    """

    def __init__(
        self,
        github_token: str | None = None,
    ) -> None:
        """Initialize orchestrator.

        Args:
            github_token: Optional GitHub token for private repos.
        """
        print("DEBUG: AnalysisOrchestrator.__init__ start", flush=True)
        self._github = GitHubClient(access_token=github_token)
        print("DEBUG: GitHubClient initialized", flush=True)
        self._strategic_fetcher = StrategicFetcher(self._github)
        print("DEBUG: StrategicFetcher initialized", flush=True)
        self._deep_reviewer = DeepReviewOrchestrator()
        print("DEBUG: DeepReviewOrchestrator initialized", flush=True)

    async def analyze(self, repo_url: str) -> AnalysisRecord:
        """Run full analysis on a repository.

        Args:
            repo_url: GitHub repository URL.

        Returns:
            Complete analysis record.
        """
        start_time = time.time()
        logger.info(f"Starting analysis of {repo_url}")

        # Parse repository URL
        owner, repo = GitHubClient.parse_repo_url(repo_url)
        repo_name = f"{owner}/{repo}"

        # Fetch repository data - get lots of files for deep review
        print(f"DEBUG: calling _fetch_repository for {owner}/{repo}")
        structure, file_contents = await self._fetch_repository(owner, repo)
        print(f"DEBUG: _fetch_repository returned {len(file_contents)} files")

        logger.info(f"Fetched {len(file_contents)} files for deep AI review")

        # Run deep AI review (3 parallel AI calls)
        print(f"DEBUG: calling deep_reviewer.review")
        deep_result = await self._deep_reviewer.review(repo_name, file_contents)
        print(f"DEBUG: deep_reviewer.review complete")

        logger.info(f"Deep review complete. Total tokens: {deep_result.total_tokens}")

        # Extract basic info for database (we focus on AI findings now)
        tech_stack = self._extract_tech_stack(file_contents)

        duration_ms = int((time.time() - start_time) * 1000)

        return AnalysisRecord(
            repo_url=repo_url,
            repo_name=repo_name,
            model_used=deep_result.model_used,
            tech_stack=tech_stack,
            architecture_patterns=[],  # Now in AI report
            risks_and_gaps=[],  # Now in AI report
            recommendations=[],  # Now in AI report
            features=[],  # Now in AI report
            business_model=None,  # Now in AI report
            integrations=[],  # Now in AI report
            technical_summary=deep_result.aggregated_technical,
            executive_summary=deep_result.aggregated_executive,
            analysis_duration_ms=duration_ms,
            file_count=structure.total_files,
            files_analyzed=len(file_contents),
            token_usage={"total": deep_result.total_tokens},
        )

    async def _fetch_repository(
        self,
        owner: str,
        repo: str,
    ) -> tuple[RepositoryStructure, dict[str, str]]:
        """Fetch repository structure and file contents.

        Fetches up to 300 files for comprehensive AI analysis.
        """
        # Get metadata to find default branch
        metadata = await self._github.get_repo_metadata(owner, repo)
        branch = metadata.get("default_branch", "main")

        # Get file tree
        file_tree = await self._github.get_file_tree(owner, repo, branch)

        # Parse structure for statistics
        tree_items = [{"path": f["path"], "type": f["type"]} for f in file_tree]
        structure = RepositoryParser.parse_file_tree(tree_items)

        # Fetch MORE files for deep AI review (300 instead of 150)
        file_contents = await self._strategic_fetcher.fetch_strategic_files(
            owner=owner,
            repo=repo,
            branch=branch,
            max_files=300,  # Increased for deep review
            batch_size=30,
        )

        logger.info(f"Fetched {len(file_contents)} files for analysis")
        return structure, file_contents

    def _extract_tech_stack(self, file_contents: dict[str, str]) -> TechStackInfo:
        """Extract basic tech stack from file names and content."""
        languages: set[str] = set()
        frameworks: set[str] = set()
        databases: set[str] = set()
        tools: set[str] = set()

        all_content = " ".join(file_contents.values()).lower()

        # Detect languages from file extensions
        for path in file_contents:
            if path.endswith(".py"):
                languages.add("Python")
            elif path.endswith((".ts", ".tsx")):
                languages.add("TypeScript")
            elif path.endswith((".js", ".jsx")):
                languages.add("JavaScript")
            elif path.endswith(".go"):
                languages.add("Go")
            elif path.endswith(".rs"):
                languages.add("Rust")
            elif path.endswith(".java"):
                languages.add("Java")

        # Detect frameworks
        framework_patterns = {
            "next": "Next.js", "react": "React", "vue": "Vue",
            "fastapi": "FastAPI", "django": "Django", "flask": "Flask",
            "express": "Express", "nestjs": "NestJS", "svelte": "Svelte",
        }
        for pattern, name in framework_patterns.items():
            if pattern in all_content:
                frameworks.add(name)

        # Detect databases
        db_patterns = {
            "postgres": "PostgreSQL", "mongodb": "MongoDB", "redis": "Redis",
            "supabase": "Supabase", "prisma": "Prisma", "mysql": "MySQL",
        }
        for pattern, name in db_patterns.items():
            if pattern in all_content:
                databases.add(name)

        # Detect tools
        tool_patterns = {
            "docker": "Docker", "kubernetes": "Kubernetes",
            "github actions": "GitHub Actions", "vercel": "Vercel",
            "terraform": "Terraform", "aws": "AWS",
        }
        for pattern, name in tool_patterns.items():
            if pattern in all_content:
                tools.add(name)

        return TechStackInfo(
            languages=list(languages),
            frameworks=list(frameworks),
            databases=list(databases),
            tools=list(tools),
            package_managers=[],
            versions={},
        )
