"""Temporal modeling — recency weights, growth, acceleration, credibility, diversity.

All formulas match the spec exactly. All parameters come from config.
"""

from __future__ import annotations

import math
import logging
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from trend_engine.config import TrendEngineSettings, get_settings

logger = logging.getLogger(__name__)


def compute_temporal_metrics(
    member_data: list[dict[str, Any]],
    settings: TrendEngineSettings | None = None,
) -> dict[str, float]:
    """Compute all temporal metrics for a single cluster.

    Args:
        member_data: List of chunk dicts, each must have:
            published_at (str or datetime), source_name, source_weight

    Returns:
        Dict with keys: weighted_doc_count_7, weighted_doc_count_30,
        weighted_doc_count_90, growth_rate, credibility_score,
        source_diversity_score, cluster_size
    """
    cfg = settings or get_settings()
    now = datetime.now(timezone.utc)
    decay_lambda = cfg.decay_lambda

    # Deduplicate by document_id to avoid counting chunks from same doc
    seen_docs: dict[str, dict[str, Any]] = {}
    for m in member_data:
        doc_id = m.get("document_id", "")
        if doc_id not in seen_docs:
            seen_docs[doc_id] = m

    docs = list(seen_docs.values())

    # Compute recency-weighted counts per window
    w7 = 0.0
    w30 = 0.0
    w90 = 0.0

    for doc in docs:
        pub = _parse_datetime(doc.get("published_at"))
        age_days = max(0.0, (now - pub).total_seconds() / 86400.0)
        w = math.exp(-decay_lambda * age_days)

        if age_days <= 7:
            w7 += w
        if age_days <= 30:
            w30 += w
        if age_days <= 90:
            w90 += w

    # Growth rate
    baseline = w30 / 4.0  # weekly proxy from 30-day window
    growth_rate = (w7 - baseline) / (baseline + 1e-6)

    # Credibility score = mean(source_weight) across member documents
    weights = [float(doc.get("source_weight", 0.5)) for doc in docs]
    credibility_score = sum(weights) / max(len(weights), 1)

    # Source diversity = unique_source_count / log(cluster_size + 1)
    unique_sources = len(set(doc.get("source_name", "") for doc in docs))
    cluster_size = len(member_data)  # chunk count, not doc count
    source_diversity = unique_sources / math.log(cluster_size + 1)

    return {
        "weighted_doc_count_7": round(w7, 4),
        "weighted_doc_count_30": round(w30, 4),
        "weighted_doc_count_90": round(w90, 4),
        "growth_rate": round(growth_rate, 6),
        "credibility_score": round(credibility_score, 4),
        "source_diversity_score": round(source_diversity, 4),
        "cluster_size": cluster_size,
    }


def compute_acceleration(
    current_growth: float,
    previous_growth: float | None,
) -> float:
    """Compute acceleration = delta of growth_rate vs previous run.

    If no previous run exists, returns 0.0.
    """
    if previous_growth is None:
        return 0.0
    return round(current_growth - previous_growth, 6)


def _parse_datetime(val: Any) -> datetime:
    """Parse various datetime formats into timezone-aware datetime."""
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=timezone.utc)
        return val
    if isinstance(val, str):
        val = val.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(val)
        except ValueError:
            pass
    return datetime.now(timezone.utc)
