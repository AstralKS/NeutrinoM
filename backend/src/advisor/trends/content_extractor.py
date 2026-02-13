"""Content extractor — mines structured signals from raw search results.

Extracts:
- Version numbers (e.g., "v4.2.0", "21.1.0")
- Deprecation mentions
- Performance/benchmark data
- Migration steps
- Feature announcements

Each signal is tagged with source URL and confidence.
"""

import logging
import re

from advisor.trends.models import (
    ExtractedSignal,
    SearchResult,
    SignalType,
)

logger = logging.getLogger(__name__)

# Regex for version numbers: v4.2.0, 21.1.0, 3.12, etc.
VERSION_PATTERN = re.compile(
    r"\bv?(\d{1,4}\.\d{1,4}(?:\.\d{1,4})?(?:-[a-zA-Z0-9.]+)?)\b"
)

# Keywords that indicate specific signal types
DEPRECATION_KEYWORDS = [
    "deprecated",
    "deprecation",
    "end of life",
    "eol",
    "removed",
    "breaking change",
    "sunset",
]

MIGRATION_KEYWORDS = [
    "migration",
    "migrate",
    "upgrade guide",
    "upgrade path",
    "breaking change",
    "porting",
]

PERFORMANCE_KEYWORDS = [
    "benchmark",
    "performance",
    "faster",
    "speed",
    "throughput",
    "latency",
    "optimization",
]

FEATURE_KEYWORDS = [
    "new feature",
    "introducing",
    "announcing",
    "launched",
    "release",
    "now supports",
]


def extract_signals(
    results: list[SearchResult],
    tag: str,
) -> list[ExtractedSignal]:
    """Extract structured signals from search results.

    Args:
        results: Raw search results from all sources.
        tag: Technology tag for context.

    Returns:
        List of extracted signals, sorted by confidence.
    """
    signals: list[ExtractedSignal] = []

    for result in results:
        text = f"{result.title} {result.snippet}".lower()
        result_signals = _extract_from_text(
            text=text,
            source_url=result.url,
            source_title=result.title,
            tag=tag,
        )
        signals.extend(result_signals)

    # Sort by confidence descending
    signals.sort(key=lambda s: s.confidence, reverse=True)

    logger.info(f"ContentExtractor: Extracted {len(signals)} signals for '{tag}'")
    return signals


def _extract_from_text(
    text: str,
    source_url: str,
    source_title: str,
    tag: str,
) -> list[ExtractedSignal]:
    """Extract signals from a single text blob."""
    signals: list[ExtractedSignal] = []
    full_text = f"{source_title} {text}"
    text_lower = full_text.lower()

    # 1. Version extraction
    versions = _extract_versions(full_text, tag)
    for ver in versions:
        signals.append(
            ExtractedSignal(
                signal_type=SignalType.VERSION,
                content=f"{tag} version {ver}",
                version=ver,
                source_url=source_url,
                source_title=source_title,
                confidence=0.8,
            )
        )

    # 2. Deprecation signals
    if _has_keywords(text_lower, DEPRECATION_KEYWORDS):
        signals.append(
            ExtractedSignal(
                signal_type=SignalType.DEPRECATION,
                content=source_title[:120],
                source_url=source_url,
                source_title=source_title,
                confidence=0.7,
            )
        )

    # 3. Migration signals
    if _has_keywords(text_lower, MIGRATION_KEYWORDS):
        signals.append(
            ExtractedSignal(
                signal_type=SignalType.MIGRATION,
                content=source_title[:120],
                source_url=source_url,
                source_title=source_title,
                confidence=0.7,
            )
        )

    # 4. Performance signals
    if _has_keywords(text_lower, PERFORMANCE_KEYWORDS):
        signals.append(
            ExtractedSignal(
                signal_type=SignalType.PERFORMANCE,
                content=source_title[:120],
                source_url=source_url,
                source_title=source_title,
                confidence=0.6,
            )
        )

    # 5. Feature signals
    if _has_keywords(text_lower, FEATURE_KEYWORDS):
        signals.append(
            ExtractedSignal(
                signal_type=SignalType.FEATURE,
                content=source_title[:120],
                source_url=source_url,
                source_title=source_title,
                confidence=0.6,
            )
        )

    return signals


def _extract_versions(text: str, tag: str) -> list[str]:
    """Extract version numbers relevant to the tag."""
    matches = VERSION_PATTERN.findall(text)
    if not matches:
        return []

    # Filter: keep versions mentioned near the tag name
    tag_lower = tag.lower()
    relevant: list[str] = []
    for ver in matches:
        # Check if tag appears within ~50 chars of version
        ver_pos = text.lower().find(ver)
        if ver_pos == -1:
            continue
        context = text[max(0, ver_pos - 50) : ver_pos + 50].lower()
        if tag_lower in context or len(matches) <= 3:
            relevant.append(ver)

    return list(dict.fromkeys(relevant))[:5]  # Dedup, max 5


def _has_keywords(text: str, keywords: list[str]) -> bool:
    """Check if text contains any of the given keywords."""
    return any(kw in text for kw in keywords)
