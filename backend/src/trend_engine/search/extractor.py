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

from trend_engine.models import ExtractedSignal, SearchResult, SignalType

logger = logging.getLogger(__name__)

VERSION_PATTERN = re.compile(
    r"\bv?(\d{1,4}\.\d{1,4}(?:\.\d{1,4})?(?:-[a-zA-Z0-9.]+)?)\b"
)

_KEYWORD_MAP: dict[SignalType, tuple[list[str], float]] = {
    SignalType.DEPRECATION: (
        ["deprecated", "deprecation", "end of life", "eol", "removed",
         "breaking change", "sunset"],
        0.7,
    ),
    SignalType.MIGRATION: (
        ["migration", "migrate", "upgrade guide", "upgrade path",
         "breaking change", "porting"],
        0.7,
    ),
    SignalType.PERFORMANCE: (
        ["benchmark", "performance", "faster", "speed", "throughput",
         "latency", "optimization"],
        0.6,
    ),
    SignalType.FEATURE: (
        ["new feature", "introducing", "announcing", "launched",
         "release", "now supports"],
        0.6,
    ),
}


def extract_signals(
    results: list[SearchResult],
    tag: str,
) -> list[ExtractedSignal]:
    """Extract structured signals from search results.

    Args:
        results: Raw search results from all sources.
        tag: Technology tag for context.

    Returns:
        List of extracted signals, sorted by confidence descending.
    """
    signals: list[ExtractedSignal] = []

    for result in results:
        text = f"{result.title} {result.snippet}".lower()
        signals.extend(
            _extract_from_text(text, result.url, result.title, tag)
        )

    signals.sort(key=lambda s: s.confidence, reverse=True)
    logger.info(f"Extractor: {len(signals)} signals for '{tag}'")
    return signals


def _extract_from_text(
    text: str,
    source_url: str,
    source_title: str,
    tag: str,
) -> list[ExtractedSignal]:
    signals: list[ExtractedSignal] = []
    full_text = f"{source_title} {text}"
    text_lower = full_text.lower()

    # Version extraction
    for ver in _extract_versions(full_text, tag):
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

    # Keyword-based signal extraction
    for signal_type, (keywords, confidence) in _KEYWORD_MAP.items():
        if any(kw in text_lower for kw in keywords):
            signals.append(
                ExtractedSignal(
                    signal_type=signal_type,
                    content=source_title[:120],
                    source_url=source_url,
                    source_title=source_title,
                    confidence=confidence,
                )
            )

    return signals


def _extract_versions(text: str, tag: str) -> list[str]:
    """Extract version numbers relevant to the tag."""
    matches = VERSION_PATTERN.findall(text)
    if not matches:
        return []

    tag_lower = tag.lower()
    relevant: list[str] = []
    text_lower = text.lower()

    for ver in matches:
        ver_pos = text_lower.find(ver)
        if ver_pos == -1:
            continue
        context = text_lower[max(0, ver_pos - 50): ver_pos + 50]
        if tag_lower in context or len(matches) <= 3:
            relevant.append(ver)

    # Deduplicate, cap at 5
    return list(dict.fromkeys(relevant))[:5]
