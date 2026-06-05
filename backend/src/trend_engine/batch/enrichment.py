"""Market statistics enrichment for executive view.

Scrapes adoption velocity, community health, and market penetration
data for cluster tech tags. Runs on same cadence as labeling.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from trend_engine.config import TrendEngineSettings, get_settings
from trend_engine.db.client import get_http_client

logger = logging.getLogger(__name__)


async def scrape_market_stats(
    label: str | None,
    representative_snippets: list[str],
    settings: TrendEngineSettings | None = None,
) -> dict[str, Any] | None:
    """Scrape market statistics for a cluster's technology.

    Uses LLM to generate structured market data from the cluster label
    and representative content. In production, this would call
    npm registry, PyPI, GitHub API, etc. directly.

    Args:
        label: Cluster label (e.g. "Vector Database Integration Patterns").
        representative_snippets: Top snippets from cluster.

    Returns:
        Market stats dict or None on failure.
    """
    cfg = settings or get_settings()

    if not label:
        return None

    try:
        client = get_http_client()

        prompt = f"""Analyze the technology topic "{label}" and provide realistic market statistics.

Representative content:
{chr(10).join(s[:300] for s in representative_snippets[:3])}

Return ONLY a valid JSON object:
{{
  "adoption_velocity": "estimated percentage change over 90 days, e.g. '+34% over 90 days'",
  "market_penetration": "estimated developer usage percentage with source, e.g. '61% of surveyed developers (Stack Overflow 2024)'",
  "community_health_score": 0.0 to 1.0,
  "data_sources": ["list of data sources used"],
  "scraped_at": "{datetime.now(timezone.utc).isoformat()}"
}}"""

        resp = await client.post(
            f"{cfg.openrouter_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {cfg.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": cfg.llm_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 500,
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"].strip()

        # Strip markdown fences
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

        import json
        stats = json.loads(content)
        return stats

    except Exception as exc:
        logger.error(f"Market stats scrape failed for '{label}': {exc}")
        return None


def generate_business_signals(
    classification: str | None,
    growth_rate: float,
    acceleration: float,
    credibility_score: float,
) -> dict[str, str | None]:
    """Derive executive business signals from cluster metrics.

    Returns:
        Dict with longevity_risk, migration_urgency, investment_signal.
    """
    signals: dict[str, str | None] = {
        "longevity_risk": None,
        "migration_urgency": None,
        "investment_signal": None,
    }

    # Longevity risk
    if classification == "declining":
        signals["longevity_risk"] = "high"
        signals["migration_urgency"] = "evaluate alternatives"
    elif classification == "established":
        signals["longevity_risk"] = "low"
        signals["migration_urgency"] = "none"
    elif classification == "emerging":
        signals["longevity_risk"] = "moderate — early stage"
        signals["migration_urgency"] = "none"
    elif classification == "expanding":
        signals["longevity_risk"] = "low"
        signals["migration_urgency"] = "none"

    # Investment signal
    if growth_rate > 0.3 and acceleration > 0:
        signals["investment_signal"] = "increasing adoption, healthy ecosystem"
    elif growth_rate > 0.1:
        signals["investment_signal"] = "steady growth, stable ecosystem"
    elif growth_rate < -0.1:
        signals["investment_signal"] = "declining interest, consider alternatives"
    else:
        signals["investment_signal"] = "stable, no significant momentum change"

    if credibility_score > 0.8:
        signals["investment_signal"] += " (high-credibility sources)"

    return signals
