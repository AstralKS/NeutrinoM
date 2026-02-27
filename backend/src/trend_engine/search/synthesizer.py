"""Synthesizer — LLM-powered report generation from ranked results.

Takes ranked & scored results and produces a TrendInsight with:
- Technical deep-dive (key_points, latest_version, risks, migration)
- Non-technical summary (momentum, direction, opportunities)
- Top source citations

Falls back to signal-based extraction if LLM fails.
"""

import logging

from trend_engine.models import (
    ExtractedSignal,
    RankedResult,
    SignalType,
    SourceType,
    TrendInsight,
    TrendSourceInfo,
)

logger = logging.getLogger(__name__)

_SYNTHESIS_PROMPT = """Analyze the following ranked search results about "{tag}" and produce a structured trend summary.

## Ranked Results (scored by freshness, authority, relevance)
{results_block}

## Extracted Signals
{signals_block}

Return a JSON object with these fields:
{{
    "key_points": ["10-15 concise, specific bullet points with deep metric/adoption evidence about current state and direction"],
    "momentum": "rising|stable|declining",
    "risks": ["max 7 key risks or concerns"],
    "opportunities": ["max 7 key opportunities"],
    "direction": "1-2 sentences on where {tag} is heading",
    "latest_version": "Latest stable version if found (e.g. '21.1.0'), or empty string",
    "version_info": "Brief note on recent version changes or upgrade path"
}}

Rules:
- Be specific: include version numbers, star counts, adoption metrics
- Cite evidence from the results, not speculation
- For latest_version: only include if you see a clear version number in the results
- Keep key_points actionable and evidence-based"""

_SOURCE_LABELS: dict[SourceType, str] = {
    SourceType.SERPER: "web",
    SourceType.GITHUB_SEARCH: "github",
    SourceType.GITHUB_RELEASES: "github",
    SourceType.HACKER_NEWS: "hn",
}


async def synthesize(
    tag: str,
    ranked_results: list[RankedResult],
    signals: list[ExtractedSignal],
    llm_client: object,
) -> TrendInsight:
    """Synthesize ranked results into a TrendInsight via LLM.

    Args:
        tag: Technology tag being analyzed.
        ranked_results: Scored and sorted results.
        signals: Extracted signals from content.
        llm_client: LLM client with .complete() method.

    Returns:
        TrendInsight with full analysis.
    """
    results_block = _format_results(ranked_results[:15])
    signals_block = _format_signals(signals[:20])

    prompt = _SYNTHESIS_PROMPT.format(
        tag=tag,
        results_block=results_block,
        signals_block=signals_block,
    )

    try:
        result = await llm_client.complete(
            prompt=prompt,
            temperature=0.3,
            max_tokens=4000,
            parse_json=True,
        )
        analysis = result["content"]
        sources = _extract_sources(ranked_results)

        return TrendInsight(
            tag=tag,
            key_points=analysis.get("key_points", [])[:15],
            momentum=analysis.get("momentum", "stable"),
            risks=analysis.get("risks", [])[:7],
            opportunities=analysis.get("opportunities", [])[:7],
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
    version = ""
    for sig in signals:
        if sig.signal_type == SignalType.VERSION and sig.version:
            version = sig.version
            break

    key_points = [f"Data collected from {len(ranked_results)} sources"]
    for sig in signals[:5]:
        if sig.content:
            key_points.append(sig.content[:100])

    return TrendInsight(
        tag=tag,
        key_points=key_points[:15],
        momentum="unknown",
        latest_version=version,
        sources=_extract_sources(ranked_results),
        sources_count=len(ranked_results),
    )


def _format_results(results: list[RankedResult]) -> str:
    if not results:
        return "No results found."
    lines: list[str] = []
    for i, r in enumerate(results, 1):
        lines.append(
            f"{i}. [{r.result.title}]({r.result.url}) "
            f"(composite={r.composite_score:.2f})\n"
            f"   {r.result.snippet[:150]}"
        )
    return "\n".join(lines)


def _format_signals(signals: list[ExtractedSignal]) -> str:
    if not signals:
        return "No specific signals extracted."
    lines: list[str] = []
    for sig in signals:
        ver_part = f" [v{sig.version}]" if sig.version else ""
        lines.append(f"- {sig.signal_type.value}{ver_part}: {sig.content[:100]}")
    return "\n".join(lines)


def _extract_sources(ranked_results: list[RankedResult]) -> list[TrendSourceInfo]:
    sources: list[TrendSourceInfo] = []
    seen: set[str] = set()

    for r in ranked_results[:9]:
        url = r.result.url
        if url in seen or not url:
            continue
        seen.add(url)
        sources.append(
            TrendSourceInfo(
                title=r.result.title[:80],
                url=url,
                source_type=_SOURCE_LABELS.get(r.result.source, "web"),
                date=r.result.published_at[:10],
                score=r.result.score,
            )
        )

    return sources[:9]
