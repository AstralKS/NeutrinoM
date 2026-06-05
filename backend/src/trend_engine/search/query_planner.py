"""Query planner — generates focused sub-queries per tech tag.

Turns a single tag like "Django" into targeted search queries:
- Release/version queries
- Performance/benchmark queries
- Roadmap/feature queries

Rule-based (no LLM) for speed, cost, and determinism.
Tuned for speed: 3 Serper + 1 GitHub + 1 HN = 5 queries/tag.
"""

import logging
from datetime import UTC, datetime

from trend_engine.models import SearchQuery, SearchQueryType

logger = logging.getLogger(__name__)


def _current_year() -> int:
    return datetime.now(UTC).year


# One high-signal query per type.
QUERY_TEMPLATES: dict[SearchQueryType, list[str]] = {
    SearchQueryType.RELEASE: [
        "{tag} latest stable release {year}",
    ],
    SearchQueryType.PERFORMANCE: [
        "{tag} performance benchmarks {year}",
    ],
    SearchQueryType.ROADMAP: [
        "{tag} roadmap upcoming features {year}",
    ],
}


def plan_queries(
    tag: str,
    *,
    max_queries: int = 3,
) -> list[SearchQuery]:
    """Generate focused sub-queries for a technology tag.

    Args:
        tag: Technology name (e.g., "react", "django").
        max_queries: Maximum number of queries to return.

    Returns:
        List of SearchQuery objects, typically 3 per tag.
    """
    tag = tag.lower().strip()
    year = _current_year()
    queries: list[SearchQuery] = []

    for query_type, templates in QUERY_TEMPLATES.items():
        for template in templates:
            query_text = template.format(tag=tag, year=year)
            queries.append(
                SearchQuery(
                    tag=tag,
                    query_type=query_type,
                    query_text=query_text,
                )
            )

    queries = queries[:max_queries]
    logger.info(f"QueryPlanner: {len(queries)} queries for '{tag}'")
    return queries


def plan_github_queries(tag: str) -> list[str]:
    """Generate GitHub-specific search terms for a tag."""
    return [f"{tag.lower().strip()} in:name,description,topics"]


def plan_hn_queries(tag: str) -> list[str]:
    """Generate HN search terms for a tag."""
    return [tag.lower().strip()]
