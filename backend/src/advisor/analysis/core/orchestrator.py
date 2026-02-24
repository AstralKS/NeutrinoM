"""Analysis orchestrator - main coordinator for repository analysis.

Coordinates GitHub intake, deep AI review, trend enrichment, and result aggregation.

ARCHITECTURE:
1. Fetch repo files (with timestamps)
2. Extract tech stack for trend searches
3. Check RAG cache for existing trend data
4. Launch parallel web searches for uncached technologies
5. Send files + trend context to 3 parallel AIs for deep code review
6. Aggregate into evidence-based reports with trend intelligence
"""

import asyncio
import logging
import time

from advisor.analysis.core.deep_review import DeepReviewOrchestrator
from advisor.analysis.core.timeline import AnalysisTimeline
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

# Max age for cached trend data before re-fetching
TREND_CACHE_MAX_DAYS = 7


class AnalysisOrchestrator:
    """Orchestrates the full repository analysis pipeline.

    Flow:
    1. Fetch repository files (up to 300 files)
    2. Extract tech stack and enrich with trend data
    3. Run deep AI review (3 parallel AI calls + trend context)
    4. Generate evidence-based reports with timestamps
    """

    def __init__(
        self,
        github_token: str | None = None,
    ) -> None:
        """Initialize orchestrator.

        Args:
            github_token: Optional GitHub token for private repos.
        """
        self._github = GitHubClient(access_token=github_token)
        self._strategic_fetcher = StrategicFetcher(self._github)
        self._deep_reviewer = DeepReviewOrchestrator()
        self._timeline = AnalysisTimeline()

    async def analyze(self, repo_url: str) -> AnalysisRecord:
        """Run full analysis on a repository.

        Args:
            repo_url: GitHub repository URL.

        Returns:
            Complete analysis record with timeline and trend data.
        """
        start_time = time.time()
        self._timeline.start_phase("analysis_start")
        logger.info(f"Starting analysis of {repo_url}")

        # Parse repository URL
        owner, repo = GitHubClient.parse_repo_url(repo_url)
        repo_name = f"{owner}/{repo}"

        # Phase 1: Fetch repository data
        self._timeline.start_phase("github_fetch")
        try:
            structure, file_contents = await self._fetch_repository(owner, repo)
            self._timeline.complete_phase("github_fetch")
        except Exception as e:
            self._timeline.fail_phase("github_fetch", str(e))
            raise
        logger.info(f"Fetched {len(file_contents)} files for deep AI review")

        # Phase 2: Extract tech stack
        self._timeline.start_phase("tech_stack_extraction")
        tech_stack = self._extract_tech_stack(file_contents)
        self._timeline.complete_phase("tech_stack_extraction")

        # Phase 3: Enrich with trend data (parallel web searches + RAG cache)
        trend_context = ""
        self._timeline.start_phase("trend_search")
        try:
            trend_context = await self._enrich_with_trends(tech_stack)
            self._timeline.complete_phase("trend_search")
        except Exception as e:
            self._timeline.fail_phase("trend_search", str(e))
            logger.warning(f"Trend enrichment failed (non-fatal): {e}")

        # Phase 4: Run deep AI review (3 parallel AI calls + trend context)
        self._timeline.start_phase("deep_review")
        try:
            # Extract tags for RAG lookup
            tech_tags = self._get_tech_tags(tech_stack)
            self._deep_reviewer._tech_tags = tech_tags
            self._deep_reviewer._trend_context = trend_context
            
            deep_result = await self._deep_reviewer.review(repo_name, file_contents)
            self._timeline.complete_phase("deep_review")
        except Exception as e:
            self._timeline.fail_phase("deep_review", str(e))
            raise

        logger.info(f"Deep review complete. Total tokens: {deep_result.total_tokens}")

        # Complete timeline
        self._timeline.complete_phase("analysis_start")
        duration_ms = int((time.time() - start_time) * 1000)

        # Build trend_data dict for storage
        trend_data_dict = None
        if trend_context:
            trend_data_dict = {
                "context": trend_context[:5000],
                "tags_searched": self._get_tech_tags(tech_stack),
            }

        return AnalysisRecord(
            repo_url=repo_url,
            repo_name=repo_name,
            model_used=deep_result.model_used,
            tech_stack=tech_stack,
            architecture_patterns=[],
            risks_and_gaps=[],
            recommendations=[],
            features=[],
            business_model=None,
            integrations=[],
            technical_summary=deep_result.aggregated_technical,
            executive_summary=deep_result.aggregated_executive,
            executive_stats=deep_result.executive_stats,
            analysis_duration_ms=duration_ms,
            file_count=structure.total_files,
            files_analyzed=len(file_contents),
            token_usage={"total": deep_result.total_tokens},
            timeline=self._timeline.to_dict(),
            trend_data=trend_data_dict,
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

    def _get_tech_tags(self, tech_stack: TechStackInfo) -> list[str]:
        """Extract searchable tags from tech stack."""
        tags: list[str] = []
        tags.extend(t.lower() for t in tech_stack.languages)
        tags.extend(t.lower() for t in tech_stack.frameworks)
        tags.extend(t.lower() for t in tech_stack.databases)
        tags.extend(t.lower() for t in tech_stack.tools)
        return list(set(tags))  # Deduplicate

    async def _enrich_with_trends(
        self, tech_stack: TechStackInfo,
    ) -> str:
        """Fetch trend intelligence for detected technologies.

        Flow: RAG cache first (parallel) → miss → TrendMaster collects
        fresh data from Serper/GitHub/HN → LLM summarizes → stores in RAG.

        Returns:
            Formatted trend context string for report enrichment.
        """
        tags = self._get_tech_tags(tech_stack)
        if not tags:
            return ""

        # Optimization: Cap at top 5 tags to prevent timeout
        # Priority: Frameworks > Languages > Databases > Tools
        prioritized = []
        prioritized.extend([t for t in tech_stack.frameworks if t.lower() in tags])
        prioritized.extend([t for t in tech_stack.languages if t.lower() in tags])
        prioritized.extend([t for t in tech_stack.databases if t.lower() in tags])
        # Deduplicate while keeping order
        seen = set()
        final_tags = []
        for t in prioritized:
            if t.lower() not in seen:
                seen.add(t.lower())
                final_tags.append(t.lower())
        
        tags = final_tags[:5]


        logger.info(f"Searching trends for {len(tags)} technologies: {tags}")

        try:
            from advisor.trends.pipeline import TrendPipeline as TrendMaster
            from advisor.trends.rag_store import RAGStore as RAGManager

            rag = RAGManager()
            trend_master = TrendMaster()

            # Step 1: Parallel RAG cache check for all tags
            cache_results = await asyncio.gather(
                *[
                    rag.get_recent_for_tag(tag, days=TREND_CACHE_MAX_DAYS)
                    for tag in tags
                ],
                return_exceptions=True,
            )

            cached_insights: list[str] = []
            uncached_tags: list[str] = []

            for tag, result in zip(tags, cache_results):
                if isinstance(result, Exception):
                    logger.debug(f"RAG cache check failed for '{tag}': {result}")
                    uncached_tags.append(tag)
                    continue

                if result is not None:
                    # result is TrendInsight — use attribute access (not .get())
                    insight_text = self._format_insight(tag, result, "cached")
                    if insight_text:
                        cached_insights.append(insight_text)
                        logger.info(f"RAG cache hit for '{tag}'")
                        self._timeline.add_api_call(
                            "trend_search", f"rag_cache_hit:{tag}", 0,
                        )
                    else:
                        uncached_tags.append(tag)
                else:
                    uncached_tags.append(tag)

            # Step 2: Fresh search for uncached tags (parallel with semaphore)
            fresh_insights: list[str] = []
            if uncached_tags:
                logger.info(
                    f"Collecting fresh data for {len(uncached_tags)} tags: {uncached_tags}"
                )

                # Cap concurrency to 2 tags at a time to avoid rate limits
                sem = asyncio.Semaphore(2)

                async def _analyze_tag_safe(tag: str) -> str | None:
                    async with sem:
                        try:
                            t0 = time.time()
                            # Enforce strict 30s timeout per tag to ensure global responsiveness
                            result = await asyncio.wait_for(
                                trend_master.analyze_tag(tag),
                                timeout=30.0
                            )
                            ms = int((time.time() - t0) * 1000)
                            self._timeline.add_api_call(
                                "trend_search", f"fresh_collect:{tag}", ms,
                            )
                            if result:
                                return self._format_insight(tag, result, "fresh")
                        except asyncio.TimeoutError:
                            logger.warning(f"Trend search timed out for '{tag}'")
                        except Exception as e:
                            logger.warning(f"Trend search failed for '{tag}': {e}")
                    return None

                # Run with global timeout for the whole batch
                try:
                    results = await asyncio.wait_for(
                        asyncio.gather(*[_analyze_tag_safe(t) for t in uncached_tags]),
                        timeout=40.0  # Global timeout for all tags
                    )
                    fresh_insights = [r for r in results if r]
                except asyncio.TimeoutError:
                    logger.warning("Global trend search phase timed out")

            all_insights = cached_insights + fresh_insights
            if all_insights:
                return "\n\n".join(all_insights)
            return ""

        except ImportError:
            logger.warning("Trends module not available, skipping enrichment")
            return ""
        except Exception as e:
            logger.warning(f"Trend enrichment error (non-fatal): {e}")
            return ""

    def _format_insight(
        self, tag: str, insight: object, source_label: str,
    ) -> str:
        """Format a TrendInsight into a rich context string.

        Includes key_points, momentum, risks, opportunities, direction,
        and top sources with links for maximum report value.
        """
        points = getattr(insight, "key_points", [])
        if not points:
            return ""

        momentum = getattr(insight, "momentum", "")
        risks = getattr(insight, "risks", [])
        opps = getattr(insight, "opportunities", [])
        direction = getattr(insight, "direction", "")
        sources = getattr(insight, "sources", [])
        latest_version = getattr(insight, "latest_version", "")
        version_info = getattr(insight, "version_info", "")

        parts = [f"**{tag}** ({source_label}):"]
        parts.append(f"  Key Points: {'; '.join(points[:5])}")

        if latest_version:
            parts.append(f"  Latest Version: {latest_version}")
        if version_info:
            parts.append(f"  Version Info: {version_info}")
        if momentum:
            parts.append(f"  Momentum: {momentum}")
        if direction:
            parts.append(f"  Direction: {direction}")
        if risks:
            parts.append(f"  Risks: {'; '.join(risks[:3])}")
        if opps:
            parts.append(f"  Opportunities: {'; '.join(opps[:3])}")

        # Include top sources with links
        if sources:
            src_lines = []
            for s in sources[:3]:
                title = getattr(s, "title", "")
                url = getattr(s, "url", "")
                score = getattr(s, "score", 0)
                if title and url:
                    src_lines.append(f"    - [{title}]({url}) (score: {score})")
            if src_lines:
                parts.append("  Sources:\n" + "\n".join(src_lines))

        return "\n".join(parts)

    def _format_tech_stack(self, tech_stack: TechStackInfo) -> str:
        """Format tech stack as a readable string."""
        parts: list[str] = []
        if tech_stack.languages:
            parts.append(f"Languages: {', '.join(tech_stack.languages)}")
        if tech_stack.frameworks:
            parts.append(f"Frameworks: {', '.join(tech_stack.frameworks)}")
        if tech_stack.databases:
            parts.append(f"Databases: {', '.join(tech_stack.databases)}")
        if tech_stack.tools:
            parts.append(f"Tools: {', '.join(tech_stack.tools)}")
        return "\n".join(parts) if parts else "Not detected"
