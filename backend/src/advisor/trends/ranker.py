"""Ranker — scores, deduplicates, and sorts search results.

Scoring dimensions:
- Freshness: Recent results score higher (30-day window)
- Authority: Official docs/repos > blogs > forums
- Relevance: Keyword match density to the tag

Final composite score is a weighted blend. Dedup by normalized URL.
"""

import logging
import re
from datetime import UTC, datetime
from urllib.parse import urlparse

from advisor.trends.models import (
    ExtractedSignal,
    RankedResult,
    SearchResult,
    SourceType,
)

logger = logging.getLogger(__name__)

# Weights for composite scoring
FRESHNESS_WEIGHT = 0.3
AUTHORITY_WEIGHT = 0.35
RELEVANCE_WEIGHT = 0.35

# Domains considered authoritative
AUTHORITY_DOMAINS = {
    "github.com": 0.9,
    "docs.python.org": 0.95,
    "react.dev": 0.95,
    "nextjs.org": 0.95,
    "vuejs.org": 0.95,
    "djangoproject.com": 0.95,
    "fastapi.tiangolo.com": 0.95,
    "kubernetes.io": 0.95,
    "docker.com": 0.9,
    "docs.docker.com": 0.95,
    "developer.mozilla.org": 0.9,
    "blog.rust-lang.org": 0.9,
    "go.dev": 0.95,
    "pypi.org": 0.85,
    "npmjs.com": 0.85,
    "medium.com": 0.5,
    "dev.to": 0.55,
    "stackoverflow.com": 0.7,
    "news.ycombinator.com": 0.65,
}


def rank_results(
    results: list[SearchResult],
    signals: list[ExtractedSignal],
    tag: str,
    *,
    top_n: int = 20,
) -> list[RankedResult]:
    """Score, deduplicate, and sort search results.

    Args:
        results: Raw search results from all sources.
        signals: Extracted signals mapped to results.
        tag: Technology tag for relevance scoring.
        top_n: Maximum results to return.

    Returns:
        Sorted list of RankedResult.
    """
    # Build signal lookup: url -> signals
    signal_map: dict[str, list[ExtractedSignal]] = {}
    for sig in signals:
        key = _normalize_url(sig.source_url)
        signal_map.setdefault(key, []).append(sig)

    # Deduplicate by normalized URL
    seen: dict[str, RankedResult] = {}
    for result in results:
        norm_url = _normalize_url(result.url)
        if norm_url in seen:
            # Keep the one with higher raw score
            existing = seen[norm_url]
            if result.score > existing.result.score:
                seen[norm_url] = _score_result(
                    result,
                    signal_map,
                    tag,
                )
            continue
        seen[norm_url] = _score_result(
            result,
            signal_map,
            tag,
        )

    # Sort by composite score
    ranked = sorted(
        seen.values(),
        key=lambda r: r.composite_score,
        reverse=True,
    )

    logger.info(
        f"Ranker: {len(results)} → {len(ranked)} "
        f"(deduped), returning top {min(top_n, len(ranked))}"
    )
    return ranked[:top_n]


def _score_result(
    result: SearchResult,
    signal_map: dict[str, list[ExtractedSignal]],
    tag: str,
) -> RankedResult:
    """Compute freshness, authority, and relevance scores."""
    norm_url = _normalize_url(result.url)
    matched_signals = signal_map.get(norm_url, [])

    freshness = _freshness_score(result.published_at)
    authority = _authority_score(result.url, result.source)
    relevance = _relevance_score(result, tag, matched_signals)

    composite = (
        freshness * FRESHNESS_WEIGHT
        + authority * AUTHORITY_WEIGHT
        + relevance * RELEVANCE_WEIGHT
    )

    return RankedResult(
        result=result,
        signals=matched_signals,
        freshness_score=round(freshness, 3),
        authority_score=round(authority, 3),
        relevance_score=round(relevance, 3),
        composite_score=round(composite, 3),
    )


def _freshness_score(published_at: str) -> float:
    """Score by recency. Recent = higher (0-1)."""
    if not published_at:
        return 0.3  # Unknown date gets moderate score

    try:
        # Handle ISO date strings (YYYY-MM-DD or full ISO)
        date_str = published_at[:10]
        pub_date = datetime.strptime(date_str, "%Y-%m-%d")
        pub_date = pub_date.replace(tzinfo=UTC)
        now = datetime.now(UTC)
        age_days = (now - pub_date).days

        if age_days <= 7:
            return 1.0
        if age_days <= 30:
            return 0.8
        if age_days <= 90:
            return 0.6
        if age_days <= 365:
            return 0.4
        return 0.2
    except (ValueError, TypeError):
        return 0.3


def _authority_score(url: str, source: SourceType) -> float:
    """Score by source authority."""
    # Source-type baseline
    source_baseline = {
        SourceType.GITHUB_RELEASES: 0.9,
        SourceType.GITHUB_SEARCH: 0.75,
        SourceType.SERPER: 0.5,
        SourceType.HACKER_NEWS: 0.6,
    }
    baseline = source_baseline.get(source, 0.5)

    # Domain-specific override
    try:
        domain = urlparse(url).netloc.lower()
        # Strip www.
        domain = re.sub(r"^www\.", "", domain)
        domain_score = AUTHORITY_DOMAINS.get(domain)
        if domain_score is not None:
            return max(baseline, domain_score)
    except Exception:
        pass

    return baseline


def _relevance_score(
    result: SearchResult,
    tag: str,
    signals: list[ExtractedSignal],
) -> float:
    """Score by relevance to the tag."""
    score = 0.0
    tag_lower = tag.lower()

    # Tag mention in title is strong signal
    if tag_lower in result.title.lower():
        score += 0.4

    # Tag mention in snippet
    if tag_lower in (result.snippet or "").lower():
        score += 0.2

    # Number of extracted signals
    if signals:
        score += min(len(signals) * 0.1, 0.3)

    # High raw score (stars, upvotes)
    if result.score > 100:
        score += 0.1

    return min(score, 1.0)


def _normalize_url(url: str) -> str:
    """Normalize URL for deduplication."""
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        # Strip query params, fragments, trailing slash
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        return normalized.rstrip("/").lower()
    except Exception:
        return url.lower()
