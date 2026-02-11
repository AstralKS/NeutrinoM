"""Deep AI Review Orchestrator - Smart context-aware code analysis.

Architecture:
1. Fetch entire repo → optimize tokens
2. Partition into frontend, backend, infra buckets
3. Backend: send full logic + imports (priority)
4. Frontend/Infra: send function names + imports only (lightweight)
5. If frontend+infra < 60K tokens → single combined AI call
6. Aggregate findings into evidence-based reports with trend intelligence

Models support 128K context — we maximize usage to reduce AI calls.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from advisor.analysis.core.chunk_prompts import (
    build_backend_prompt,
    build_combined_frontend_infra_prompt,
    build_lightweight_prompt,
    extract_signatures,
)
from advisor.analysis.core.report_agent import ReportAgent
from advisor.analysis.core.token_optimizer import TokenOptimizer, CompressionStats
from advisor.llm.client import OpenRouterClient

logger = logging.getLogger(__name__)

# Token budget management
MAX_INPUT_TOKENS = 100_000
CHARS_PER_TOKEN = 4
COMBINED_THRESHOLD_CHARS = 60_000 * CHARS_PER_TOKEN  # 60K tokens

# File classification patterns
FRONTEND_PATTERNS = [
    "src/app", "src/pages", "src/components", "src/hooks", "src/lib",
    "app/", "pages/", "components/", "hooks/", "styles/", "public/",
    ".tsx", ".jsx", ".vue", ".svelte", "tailwind", "next.config",
    "vite.config", "nuxt.config", "package.json", "tsconfig",
]
BACKEND_PATTERNS = [
    "api/", "server/", "backend/", "src/advisor/", "routes/",
    "controllers/", "services/", "models/", "middleware/",
    "handlers/", "endpoints/", "main.py", "app.py", "server.",
    "requirements.txt", "pyproject.toml", "go.mod", "Cargo.toml",
]
INFRA_PATTERNS = [
    "docker", "kubernetes", "k8s", ".github/", "ci/", "cd/",
    "terraform", "pulumi", "ansible", "helm", "deploy",
    ".env", "config/", "scripts/", "makefile", "readme",
    "license", "changelog", ".yaml", ".yml", "nginx", "caddy",
]


@dataclass
class ChunkAnalysis:
    """Analysis result from one AI chunk."""
    chunk_name: str
    files_analyzed: list[str]
    token_count: int
    findings: str
    error: str | None = None
    started_at: str | None = None
    completed_at: str | None = None


@dataclass
class DeepReviewResult:
    """Complete deep review result."""
    total_files: int
    total_tokens: int
    compression_stats: CompressionStats | None
    frontend_analysis: ChunkAnalysis | None
    backend_analysis: ChunkAnalysis | None
    infra_analysis: ChunkAnalysis | None
    aggregated_technical: str
    aggregated_executive: str
    model_used: str
    trend_context: str = ""


class DeepReviewOrchestrator:
    """Orchestrates smart AI code review using full 128K context windows."""

    def __init__(self) -> None:
        self._llm = OpenRouterClient()
        self._optimizer = TokenOptimizer(
            max_file_chars=15000,
            max_total_chars=700000,
        )
        self._report_agent = ReportAgent(self._llm)
        self._trend_context: str = ""
        self._tech_tags: list[str] = []

    async def review(
        self, repo_name: str, file_contents: dict[str, str],
    ) -> DeepReviewResult:
        """Run deep AI review with smart chunking strategy."""
        logger.info(f"Starting deep review: {len(file_contents)} files")

        # Step 0: Optimize tokens
        optimized, stats = self._optimizer.optimize(file_contents)
        logger.info(
            f"Optimized: {stats.original_chars:,} -> {stats.compressed_chars:,} "
            f"chars ({stats.savings_percent:.1f}% saved)"
        )

        # Step 1: Partition files
        frontend, backend, infra = self._partition_files(optimized)
        logger.info(
            f"Partitioned: FE={len(frontend)} BE={len(backend)} Infra={len(infra)}"
        )

        # Step 2: Build prompts (backend=full, frontend/infra=signatures)
        backend_prompt = build_backend_prompt(backend, repo_name)
        fe_sigs = extract_signatures(frontend)
        infra_sigs = extract_signatures(infra)

        # Step 3: Smart call strategy
        fe_chars = sum(len(v) for v in fe_sigs.values())
        infra_chars = sum(len(v) for v in infra_sigs.values())
        combined_chars = fe_chars + infra_chars

        t_start = datetime.now(UTC).isoformat()

        if combined_chars < COMBINED_THRESHOLD_CHARS and (fe_sigs or infra_sigs):
            # COMBINED: 2 AI calls (backend + frontend/infra together)
            combined_prompt = build_combined_frontend_infra_prompt(
                fe_sigs, infra_sigs, repo_name,
            )
            all_files = list(fe_sigs) + list(infra_sigs)

            results = await asyncio.gather(
                self._analyze_chunk("backend", backend_prompt, list(backend)),
                self._analyze_chunk("frontend+infra", combined_prompt, all_files),
                return_exceptions=True,
            )
            t_end = datetime.now(UTC).isoformat()

            backend_result = self._safe_result(results[0], "backend", t_start, t_end)
            combined = self._safe_result(results[1], "frontend+infra", t_start, t_end)

            frontend_result = ChunkAnalysis(
                chunk_name="frontend", files_analyzed=list(fe_sigs),
                token_count=fe_chars // CHARS_PER_TOKEN,
                findings=combined.findings, started_at=t_start, completed_at=t_end,
            )
            infra_result = ChunkAnalysis(
                chunk_name="infrastructure", files_analyzed=list(infra_sigs),
                token_count=infra_chars // CHARS_PER_TOKEN,
                findings="(Combined with frontend call)", started_at=t_start,
                completed_at=t_end,
            )
        else:
            # SEPARATE: 3 AI calls
            results = await asyncio.gather(
                self._analyze_chunk("backend", backend_prompt, list(backend)),
                self._analyze_chunk(
                    "frontend",
                    build_lightweight_prompt("frontend", fe_sigs, repo_name),
                    list(fe_sigs),
                ),
                self._analyze_chunk(
                    "infrastructure",
                    build_lightweight_prompt("infrastructure", infra_sigs, repo_name),
                    list(infra_sigs),
                ),
                return_exceptions=True,
            )
            t_end = datetime.now(UTC).isoformat()

            backend_result = self._safe_result(results[0], "backend", t_start, t_end)
            frontend_result = self._safe_result(results[1], "frontend", t_start, t_end)
            infra_result = self._safe_result(results[2], "infra", t_start, t_end)

        # Step 4: Aggregate into final reports (parallel)
        trend_ctx = self._trend_context or ""
        technical, executive, model = await self._aggregate_reports(
            repo_name, frontend_result, backend_result, infra_result,
            trend_context=trend_ctx,
        )

        total_tokens = sum(r.token_count for r in [
            frontend_result, backend_result, infra_result,
        ])

        return DeepReviewResult(
            total_files=len(file_contents), total_tokens=total_tokens,
            compression_stats=stats, frontend_analysis=frontend_result,
            backend_analysis=backend_result, infra_analysis=infra_result,
            aggregated_technical=technical, aggregated_executive=executive,
            model_used=model, trend_context=trend_ctx,
        )

    # ── File Partitioning ──────────────────────────────────────────

    def _partition_files(
        self, file_contents: dict[str, str],
    ) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
        """Partition files into frontend, backend, and infra buckets."""
        frontend: dict[str, str] = {}
        backend: dict[str, str] = {}
        infra: dict[str, str] = {}
        fe_c = be_c = inf_c = 0
        max_chars = MAX_INPUT_TOKENS * CHARS_PER_TOKEN

        for path, content in file_contents.items():
            path_lower = path.lower()
            clen = len(content)

            if any(p in path_lower for p in FRONTEND_PATTERNS):
                if fe_c + clen < max_chars:
                    frontend[path] = content
                    fe_c += clen
            elif any(p in path_lower for p in BACKEND_PATTERNS):
                if be_c + clen < max_chars:
                    backend[path] = content
                    be_c += clen
            elif any(p in path_lower for p in INFRA_PATTERNS):
                if inf_c + clen < max_chars:
                    infra[path] = content
                    inf_c += clen
            else:
                sizes = [(fe_c, frontend, "fe"), (be_c, backend, "be"),
                         (inf_c, infra, "inf")]
                smallest = min(sizes, key=lambda x: x[0])
                if smallest[0] + clen < max_chars:
                    smallest[1][path] = content
                    if smallest[2] == "fe":
                        fe_c += clen
                    elif smallest[2] == "be":
                        be_c += clen
                    else:
                        inf_c += clen

        return frontend, backend, infra

    # ── AI Calls ───────────────────────────────────────────────────

    def _safe_result(
        self, result: Any, name: str, t_start: str, t_end: str,
    ) -> ChunkAnalysis:
        """Safely extract ChunkAnalysis from a gather result."""
        if isinstance(result, Exception):
            return ChunkAnalysis(
                chunk_name=name, files_analyzed=[], token_count=0,
                findings="", error=str(result),
                started_at=t_start, completed_at=t_end,
            )
        if isinstance(result, ChunkAnalysis):
            result.started_at = t_start
            result.completed_at = t_end
            return result
        return ChunkAnalysis(
            chunk_name=name, files_analyzed=[], token_count=0,
            findings="", error="Unknown result type",
            started_at=t_start, completed_at=t_end,
        )

    async def _analyze_chunk(
        self, chunk_name: str, prompt: str, files: list[str],
    ) -> ChunkAnalysis:
        """Send chunk to AI for analysis."""
        if not prompt or "No " in prompt[:50]:
            return ChunkAnalysis(
                chunk_name=chunk_name, files_analyzed=[], token_count=0,
                findings=f"No {chunk_name} files to analyze.",
            )

        token_est = len(prompt) // CHARS_PER_TOKEN
        logger.info(f"Analyzing {chunk_name}: ~{token_est:,} tokens, {len(files)} files")

        try:
            result = await self._llm.complete(
                prompt=prompt,
                system_prompt=(
                    "You are an expert code reviewer. Analyze thoroughly, "
                    "cite file/module references. Never suggest code fixes. "
                    "Be extremely detailed and comprehensive."
                ),
                temperature=0.2,
                max_tokens=16000,
            )
            return ChunkAnalysis(
                chunk_name=chunk_name, files_analyzed=files,
                token_count=token_est, findings=result["content"],
            )
        except Exception as e:
            logger.error(f"Error analyzing {chunk_name}: {e}")
            return ChunkAnalysis(
                chunk_name=chunk_name, files_analyzed=files,
                token_count=token_est, findings="", error=str(e),
            )

    # ── Report Aggregation (via Report Agent) ────────────────────────

    async def _aggregate_reports(
        self, repo_name: str,
        frontend: ChunkAnalysis, backend: ChunkAnalysis,
        infra: ChunkAnalysis, trend_context: str = "",
    ) -> tuple[str, str, str]:
        """Delegate report generation to the Report Agent.

        The agent queries RAG for historical context, enriches findings,
        and generates both reports in parallel.
        """
        return await self._report_agent.generate_reports(
            repo_name=repo_name,
            backend_findings=backend.findings or "",
            frontend_findings=frontend.findings or "",
            infra_findings=infra.findings or "",
            trend_context=trend_context,
            tech_tags=self._tech_tags,
        )
