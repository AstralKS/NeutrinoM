"""Synthesizer — LLM-powered dual-report generation from ranked results.

Takes ranked & scored results and produces a TrendInsight with:
- Technical deep-dive (key_points, latest_version, risks, migration)
- Non-technical summary (momentum, direction, opportunities)
- Top source citations

Falls back to signal-based extraction if LLM fails.
"""

import logging

from advisor.llm.client import OpenRouterClient
from advisor.trends.models import (
    ExtractedSignal,
    RankedResult,
    SignalType,
    TrendInsight,
    TrendSourceInfo,
)

logger = logging.getLogger(__name__)

SYNTHESIS_PROMPT = """Analyze the following ranked search results about "{tag}" and produce a structured trend summary.

## Ranked Results (scored by freshness, authority, relevance)
{results_block}

## Extracted Signals
{signals_block}

Return a JSON object with these fields:
{{
    "key_points": ["5-7 concise, specific bullet points about current state and direction"],
    "momentum": "rising|stable|declining",
    "risks": ["max 3 key risks or concerns"],
    "opportunities": ["max 3 key opportunities"],
    "direction": "1-2 sentences on where {tag} is heading",
    "latest_version": "Latest stable version if found (e.g. '21.1.0'), or empty string",
    "version_info": "Brief note on recent version changes or upgrade path"
}}

Rules:
- Be specific: include version numbers, star counts, adoption metrics
- Cite evidence from the results, not speculation
- For latest_version: only include if you see a clear version number in the results
- Keep key_points actionable and evidence-based"""


async def synthesize(
    tag: str,
    ranked_results: list[RankedResult],
    signals: list[ExtractedSignal],
    llm_client: OpenRouterClient,
) -> TrendInsight:
    """Synthesize ranked results into a TrendInsight via LLM.

    Args:
        tag: Technology tag being analyzed.
        ranked_results: Scored and sorted results.
        signals: Extracted signals from content.
        llm_client: OpenRouter LLM client.

    Returns:
        TrendInsight with full analysis.
    """
    # Build the LLM prompt inputs
    results_block = _format_results(ranked_results[:15])
    signals_block = _format_signals(signals[:20])

    prompt = SYNTHESIS_PROMPT.format(
        tag=tag,
        results_block=results_block,
        signals_block=signals_block,
    )

    try:
        result = await llm_client.complete(
            prompt=prompt,
            temperature=0.3,
            max_tokens=1024,
            parse_json=True,
        )
        analysis = result["content"]
        sources = _extract_sources(ranked_results)

        return TrendInsight(
            tag=tag,
            key_points=analysis.get("key_points", [])[:7],
            momentum=analysis.get("momentum", "stable"),
            risks=analysis.get("risks", [])[:3],
            opportunities=analysis.get("opportunities", [])[:3],
            direction=analysis.get("direction", ""),
            latest_version=analysis.get("latest_version", ""),
            version_info=analysis.get("version_info", ""),
            sources=sources,
            sources_count=len(ranked_results),
        )

    except Exception as e:
        logger.error(f"LLM synthesis failed for '{tag}': {e}")
        return _fallback_insight(tag, ranked_results, signals)


def _fallback_insight(
    tag: str,
    ranked_results: list[RankedResult],
    signals: list[ExtractedSignal],
) -> TrendInsight:
    """Build a basic insight from signals when LLM fails."""
    # Extract version from signals
    version = ""
    for sig in signals:
        if sig.signal_type == SignalType.VERSION and sig.version:
            version = sig.version
            break

    key_points = [f"Data collected from {len(ranked_results)} sources"]
    for sig in signals[:5]:
        if sig.content:
            key_points.append(sig.content[:100])

    sources = _extract_sources(ranked_results)

    return TrendInsight(
        tag=tag,
        key_points=key_points[:7],
        momentum="unknown",
        latest_version=version,
        sources=sources,
        sources_count=len(ranked_results),
    )


def _format_results(results: list[RankedResult]) -> str:
    """Format ranked results for the LLM prompt."""
    lines: list[str] = []
    for i, r in enumerate(results, 1):
        score_info = f"composite={r.composite_score:.2f}"
        lines.append(
            f"{i}. [{r.result.title}]({r.result.url}) "
            f"({score_info})\n"
            f"   {r.result.snippet[:150]}"
        )
    return "\n".join(lines) if lines else "No results found."


def _format_signals(signals: list[ExtractedSignal]) -> str:
    """Format extracted signals for the LLM prompt."""
    if not signals:
        return "No specific signals extracted."

    lines: list[str] = []
    for sig in signals:
        ver_part = f" [v{sig.version}]" if sig.version else ""
        lines.append(f"- {sig.signal_type.value}{ver_part}: {sig.content[:100]}")
    return "\n".join(lines)


def _extract_sources(
    ranked_results: list[RankedResult],
) -> list[TrendSourceInfo]:
    """Extract top source citations from ranked results."""
    sources: list[TrendSourceInfo] = []
    seen: set[str] = set()

    for r in ranked_results[:9]:
        url = r.result.url
        if url in seen or not url:
            continue
        seen.add(url)

        source_type = _source_to_label(r.result.source)
        sources.append(
            TrendSourceInfo(
                title=r.result.title[:80],
                url=url,
                source_type=source_type,
                date=r.result.published_at[:10],
                score=r.result.score,
            )
        )

    return sources[:9]


def _source_to_label(source) -> str:
    """Map SourceType to display label."""
    from advisor.trends.models import SourceType

    mapping = {
        SourceType.SERPER: "web",
        SourceType.GITHUB_SEARCH: "github",
        SourceType.GITHUB_RELEASES: "github",
        SourceType.HACKER_NEWS: "hn",
    }
    return mapping.get(source, "web")
