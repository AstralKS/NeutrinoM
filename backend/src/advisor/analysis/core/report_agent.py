"""Report Agent - AI agent that intelligently builds analysis reports.

Acts as an agent that:
1. Queries RAG for historical analysis data on the repo's tech stack
2. Combines current findings with historical context
3. Decides what to emphasize based on trends and past analyses
4. Generates targeted technical + executive reports in parallel

This replaces dumb "dump everything into a prompt" with an agent
that has context awareness through RAG.
"""

import asyncio
import logging
from typing import Any

from advisor.llm.client import OpenRouterClient

logger = logging.getLogger(__name__)


class ReportAgent:
    """AI agent for intelligent report generation with RAG access."""

    def __init__(self, llm: OpenRouterClient | None = None) -> None:
        self._llm = llm or OpenRouterClient()
        self._rag = None  # Lazy-loaded

    def _get_rag(self):
        """Lazy-load RAG manager to avoid import errors if not configured."""
        if self._rag is None:
            try:
                from advisor.trends.rag_manager import RAGManager
                self._rag = RAGManager()
            except Exception as e:
                logger.warning(f"RAG not available: {e}")
        return self._rag

    async def generate_reports(
        self,
        repo_name: str,
        backend_findings: str,
        frontend_findings: str,
        infra_findings: str,
        trend_context: str = "",
        tech_tags: list[str] | None = None,
    ) -> tuple[str, str, str]:
        """Generate technical + executive reports using RAG context.

        Args:
            repo_name: Repository name.
            backend_findings: Raw backend analysis.
            frontend_findings: Raw frontend analysis.
            infra_findings: Raw infra analysis.
            trend_context: Trend intelligence string.
            tech_tags: Technology tags for RAG lookup.

        Returns:
            Tuple of (technical_report, executive_report, model_used).
        """
        # Step 1: Gather RAG context for historical insights
        rag_context = await self._fetch_rag_context(tech_tags or [])

        # Step 2: Build enriched findings
        enriched = self._build_enriched_findings(
            backend_findings, frontend_findings, infra_findings,
            trend_context, rag_context,
        )

        # Step 3: Generate both reports in parallel
        from advisor.llm.prompts import (
            AGGREGATED_EXECUTIVE_PROMPT,
            AGGREGATED_TECHNICAL_PROMPT,
        )

        tech_prompt = AGGREGATED_TECHNICAL_PROMPT.format(
            repo_name=repo_name, findings=enriched,
        )
        exec_prompt = AGGREGATED_EXECUTIVE_PROMPT.format(
            repo_name=repo_name, findings=enriched,
        )

        tech_result, exec_result = await asyncio.gather(
            self._llm.complete(
                prompt=tech_prompt,
                system_prompt=(
                    "Senior architect. Synthesize findings into a comprehensive "
                    "technical report. Reference files only — no code fixes. "
                    "Use historical RAG context to identify recurring patterns."
                ),
                temperature=0.2,
                max_tokens=16000,
            ),
            self._llm.complete(
                prompt=exec_prompt,
                system_prompt=(
                    "Technology strategist. Translate findings into business "
                    "insights: feature improvements, time/cost savings. No jargon. "
                    "Use historical context to show progress over time."
                ),
                temperature=0.2,
                max_tokens=16000,
            ),
        )

        return (
            tech_result["content"],
            exec_result["content"],
            tech_result["model"],
        )

    async def _fetch_rag_context(self, tags: list[str]) -> str:
        """Query RAG for historical insights on the tech stack.

        Queries all tags in parallel for maximum speed.
        Returns formatted context string with past analysis data.
        """
        rag = self._get_rag()
        if not rag or not tags:
            return ""

        async def _query_tag(tag: str) -> list[str]:
            """Query a single tag and format results."""
            results_text: list[str] = []
            try:
                results = await rag.search_by_tag(tag, limit=2)
                for r in results:
                    if hasattr(r, "key_points") and r.key_points:
                        points = "; ".join(r.key_points[:3])
                        collected = getattr(r, "collected_at", "unknown")
                        momentum = getattr(r, "momentum", "")
                        line = f"- **{tag}** ({collected}): {points}"
                        if momentum:
                            line += f" [momentum: {momentum}]"
                        results_text.append(line)
            except Exception as e:
                logger.debug(f"RAG lookup failed for '{tag}': {e}")
            return results_text

        # Parallel RAG lookups for all tags
        tag_results = await asyncio.gather(
            *[_query_tag(t) for t in tags[:8]]
        )
        insights = [line for result in tag_results for line in result]

        if insights:
            return (
                "## Historical RAG Context\n"
                "Past analyses and trend data for this tech stack:\n"
                + "\n".join(insights)
            )
        return ""

    def _build_enriched_findings(
        self,
        backend: str,
        frontend: str,
        infra: str,
        trends: str,
        rag_context: str,
    ) -> str:
        """Combine all sources into enriched findings for the LLM."""
        sections = [
            f"# BACKEND ANALYSIS (FULL CODE)\n{backend or 'No backend files.'}",
            f"# FRONTEND ANALYSIS (SIGNATURES)\n{frontend or 'No frontend files.'}",
            f"# INFRASTRUCTURE ANALYSIS (SIGNATURES)\n{infra or 'No infra files.'}",
        ]

        if trends:
            sections.append(f"# TECHNOLOGY TREND INTELLIGENCE\n{trends}")

        if rag_context:
            sections.append(f"# HISTORICAL CONTEXT (FROM RAG)\n{rag_context}")

        return "\n\n".join(sections)
