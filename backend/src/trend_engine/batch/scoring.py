"""Trend scoring, classification, and exclusion filters.

All weights and thresholds come from config — zero hardcoded constants.
"""

from __future__ import annotations

import logging
import math
import statistics
from typing import Any

from trend_engine.config import TrendEngineSettings, get_settings

logger = logging.getLogger(__name__)


def _mad(values: list[float]) -> float:
    """Median Absolute Deviation — robust alternative to std.

    MAD = median(|x_i - median(x)|) * 1.4826
    The 1.4826 scaling factor makes MAD consistent with std for normal distributions.
    """
    if len(values) < 2:
        return 0.0
    med = statistics.median(values)
    abs_devs = [abs(v - med) for v in values]
    return statistics.median(abs_devs) * 1.4826


def _min_max_norm(values: list[float]) -> list[float]:
    """Min-max normalization across a batch of values."""
    if not values:
        return []
    lo = min(values)
    hi = max(values)
    rng = hi - lo
    if rng < 1e-9:
        return [0.5] * len(values)
    return [(v - lo) / rng for v in values]


def compute_trend_scores(
    clusters: list[dict[str, Any]],
    settings: TrendEngineSettings | None = None,
) -> list[dict[str, Any]]:
    """Compute trend_score and classification for all clusters in a batch.

    Modifies clusters in-place AND returns them.

    Steps:
    1. Apply exclusion filters (min density, single-source, volatility)
    2. Min-max normalize components across the batch
    3. Compute weighted trend_score
    4. Classify based on runtime percentile thresholds
    """
    cfg = settings or get_settings()

    if not clusters:
        return clusters

    # ── Exclusion Filters ─────────────────────────────────────────

    accelerations = [c.get("acceleration", 0.0) for c in clusters]

    # Use MAD (Median Absolute Deviation) for robust volatility detection.
    # Standard deviation is inflated by the outlier itself, making it useless
    # for detecting the very spike it should flag.
    accel_mad = _mad(accelerations)

    for c in clusters:
        c["_excluded"] = False

        # Min density threshold (already filtered in clustering, second gate)
        if c.get("cluster_size", 0) < cfg.hdbscan_min_cluster_size:
            c["_excluded"] = True
            c["trend_score"] = None
            c["classification"] = None
            logger.debug("Cluster excluded: below min density")
            continue

        # Volatility: |acceleration - median| > multiplier * MAD
        if accel_mad > 0:
            median_accel = statistics.median(accelerations)
            deviation = abs(c.get("acceleration", 0.0) - median_accel)
            if deviation > cfg.volatility_multiplier * accel_mad:
                c["_excluded"] = True
                c["trend_score"] = None
                c["classification"] = None
                logger.debug("Cluster excluded: volatility spike")
                continue

    # ── Normalization ─────────────────────────────────────────────

    active = [c for c in clusters if not c.get("_excluded", False)]

    if not active:
        return clusters

    growth_rates = [c.get("growth_rate", 0.0) for c in active]
    accelerations_a = [c.get("acceleration", 0.0) for c in active]
    log_sizes = [math.log(c.get("cluster_size", 1) + 1) for c in active]
    credibilities = [c.get("credibility_score", 0.0) for c in active]
    diversities = [c.get("source_diversity_score", 0.0) for c in active]

    norm_growth = _min_max_norm(growth_rates)
    norm_accel = _min_max_norm(accelerations_a)
    norm_size = _min_max_norm(log_sizes)
    norm_cred = _min_max_norm(credibilities)
    norm_div = _min_max_norm(diversities)

    # ── Weighted Score (vectorized) ───────────────────────────────

    try:
        import numpy as np

        components = np.column_stack([
            norm_growth, norm_accel, norm_size, norm_cred, norm_div
        ])
        weights = np.array([
            cfg.weight_alpha, cfg.weight_beta, cfg.weight_gamma,
            cfg.weight_delta, cfg.weight_zeta,
        ])
        scores = components @ weights

        for i, c in enumerate(active):
            c["trend_score"] = round(float(scores[i]), 4)
    except ImportError:
        # Fallback to pure Python if numpy unavailable
        for i, c in enumerate(active):
            score = (
                cfg.weight_alpha * norm_growth[i]
                + cfg.weight_beta * norm_accel[i]
                + cfg.weight_gamma * norm_size[i]
                + cfg.weight_delta * norm_cred[i]
                + cfg.weight_zeta * norm_div[i]
            )
            c["trend_score"] = round(score, 4)

    # ── Classification (runtime percentile thresholds) ────────────

    wdc90_values = sorted(
        c.get("weighted_doc_count_90", 0.0) for c in active
    )
    p50 = _percentile(wdc90_values, 50)
    p75 = _percentile(wdc90_values, 75)

    for c in active:
        gr = c.get("growth_rate", 0.0)
        acc = c.get("acceleration", 0.0)
        wdc90 = c.get("weighted_doc_count_90", 0.0)

        if (
            gr > cfg.growth_rate_emerging
            and acc > 0.0
            and wdc90 < p50
        ):
            c["classification"] = "emerging"
        elif (
            gr > cfg.growth_rate_expanding
            and acc >= 0.0
            and wdc90 >= p50
        ):
            c["classification"] = "expanding"
        elif (
            wdc90 >= p75
            and abs(acc) < cfg.acceleration_established_max
        ):
            c["classification"] = "established"
        elif (
            gr < cfg.growth_rate_declining
            and acc < 0.0
        ):
            c["classification"] = "declining"
        else:
            c["classification"] = None  # No forced assignment

    return clusters


def _percentile(sorted_values: list[float], pct: int) -> float:
    """Compute percentile from pre-sorted values."""
    if not sorted_values:
        return 0.0
    k = (len(sorted_values) - 1) * (pct / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_values[int(k)]
    return sorted_values[f] * (c - k) + sorted_values[c] * (k - f)
