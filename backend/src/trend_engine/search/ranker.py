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

from trend_engine.models import (
    ExtractedSignal,
    RankedResult,
    SearchResult,
    SourceType,
)

logger = logging.getLogger(__name__)

# Weights for composite scoring
FRESHNESS_WEIGHT = 0.30
AUTHORITY_WEIGHT = 0.35
RELEVANCE_WEIGHT = 0.35

# Domains considered authoritative
AUTHORITY_DOMAINS: dict[str, float] = {
    "github.com": 0.90,
    "docs.python.org": 0.95,
    "react.dev": 0.95,
    "nextjs.org": 0.95,
    "vuejs.org": 0.95,
    "djangoproject.com": 0.95,
    "fastapi.tiangolo.com": 0.95,
    "kubernetes.io": 0.95,
    "docker.com": 0.90,
    "docs.docker.com": 0.95,
    "developer.mozilla.org": 0.90,
    "blog.rust-lang.org": 0.90,
    "go.dev": 0.95,
    "pypi.org": 0.85,
    "npmjs.com": 0.85,
    "medium.com": 0.50,
    "dev.to": 0.55,
    "stackoverflow.com": 0.70,
    "news.ycombinator.com": 0.65,
}

_SOURCE_BASELINES: dict[SourceType, float] = {
    SourceType.GITHUB_RELEASES: 0.90,
    SourceType.GITHUB_SEARCH: 0.75,
    SourceType.SERPER: 0.50,
    SourceType.HACKER_NEWS: 0.60,
}

_WWW_RE = re.compile(r"^www\.")


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
    # Build signal lookup: normalized_url -> signals
    signal_map: dict[str, list[ExtractedSignal]] = {}
    for sig in signals:
        key = _normalize_url(sig.source_url)
        signal_map.setdefault(key, []).append(sig)

    # Deduplicate by normalized URL, keeping higher-scored version
    seen: dict[str, RankedResult] = {}
    for result in results:
        norm = _normalize_url(result.url)
        scored = _score_result(result, signal_map, tag)
        existing = seen.get(norm)
        if existing is None or result.score > existing.result.score:
            seen[norm] = scored

    ranked = sorted(seen.values(), key=lambda r: r.composite_score, reverse=True)
    logger.info(
        f"Ranker: {len(results)} → {len(ranked)} (deduped), "
        f"returning top {min(top_n, len(ranked))}"
    )
    return ranked[:top_n]


def _score_result(
    result: SearchResult,
    signal_map: dict[str, list[ExtractedSignal]],
    tag: str,
) -> RankedResult:
    norm = _normalize_url(result.url)
    matched = signal_map.get(norm, [])

    freshness = _freshness_score(result.published_at)
    authority = _authority_score(result.url, result.source)
    relevance = _relevance_score(result, tag, matched)

    composite = (
        freshness * FRESHNESS_WEIGHT
        + authority * AUTHORITY_WEIGHT
        + relevance * RELEVANCE_WEIGHT
    )

    return RankedResult(
        result=result,
        signals=matched,
        freshness_score=round(freshness, 3),
        authority_score=round(authority, 3),
        relevance_score=round(relevance, 3),
        composite_score=round(composite, 3),
    )


def _freshness_score(published_at: str) -> float:
    if not published_at:
        return 0.3
    try:
        pub_date = datetime.strptime(published_at[:10], "%Y-%m-%d").replace(tzinfo=UTC)
        age_days = (datetime.now(UTC) - pub_date).days
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
    baseline = _SOURCE_BASELINES.get(source, 0.5)
    try:
        domain = _WWW_RE.sub("", urlparse(url).netloc.lower())
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
    score = 0.0
    tag_lower = tag.lower()

    if tag_lower in result.title.lower():
        score += 0.4
    if tag_lower in (result.snippet or "").lower():
        score += 0.2
    if signals:
        score += min(len(signals) * 0.1, 0.3)
    if result.score > 100:
        score += 0.1

    return min(score, 1.0)


def _normalize_url(url: str) -> str:
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/").lower()
    except Exception:
        return url.lower()
