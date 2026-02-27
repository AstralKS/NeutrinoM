"""HDBSCAN clustering with rejection filters.

Pulls all document_chunks within a rolling 90-day window,
runs HDBSCAN, applies rejection filters, computes centroids.

Heavy dependencies (numpy, hdbscan/sklearn) are lazy-imported
to avoid slowing down cold starts for non-batch code paths.
"""

from __future__ import annotations

import logging
import math
from collections import Counter
from typing import Any

from trend_engine.config import TrendEngineSettings, get_settings

logger = logging.getLogger(__name__)


def cluster_embeddings(
    chunk_data: list[dict[str, Any]],
    settings: TrendEngineSettings | None = None,
) -> list[dict[str, Any]]:
    """Run HDBSCAN over chunk embeddings and return surviving clusters.

    Args:
        chunk_data: List of dicts with keys:
            chunk_id, document_id, embedding, source_name, published_at, source_weight, ...
        settings: Engine settings (for min_cluster_size, dominance threshold).

    Returns:
        List of cluster dicts, each containing:
            cluster_label (int), member_indices, centroid, member_chunk_ids,
            member_data (list of chunk dicts belonging to this cluster).
    """
    cfg = settings or get_settings()

    if len(chunk_data) < cfg.hdbscan_min_cluster_size:
        logger.warning(
            f"Too few chunks ({len(chunk_data)}) for clustering "
            f"(min_cluster_size={cfg.hdbscan_min_cluster_size})"
        )
        return []

    import numpy as np  # Lazy import — only needed in batch path

    # Parse embeddings into numpy array
    embeddings = []
    for cd in chunk_data:
        emb = cd.get("embedding")
        if isinstance(emb, str):
            # Parse string representation "[0.1, 0.2, ...]"
            emb = _parse_embedding_str(emb)
        if isinstance(emb, list):
            embeddings.append(emb)
        else:
            embeddings.append([0.0] * cfg.embedding_dim)

    X = np.array(embeddings, dtype=np.float32)

    # Run HDBSCAN — prefer sklearn (no C extension needed), fallback to standalone
    try:
        from sklearn.cluster import HDBSCAN as SklearnHDBSCAN
        clusterer = SklearnHDBSCAN(
            min_cluster_size=cfg.hdbscan_min_cluster_size,
            min_samples=cfg.hdbscan_min_samples,
            metric="euclidean",
            cluster_selection_method="eom",
        )
    except ImportError:
        import hdbscan
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=cfg.hdbscan_min_cluster_size,
            min_samples=cfg.hdbscan_min_samples,
            metric="euclidean",
            cluster_selection_method="eom",
        )
    labels = clusterer.fit_predict(X)

    # Group by cluster label (label -1 = noise)
    clusters_raw: dict[int, list[int]] = {}
    for idx, label in enumerate(labels):
        if label == -1:
            continue
        clusters_raw.setdefault(label, []).append(idx)

    logger.info(
        f"HDBSCAN found {len(clusters_raw)} raw clusters "
        f"from {len(chunk_data)} chunks "
        f"({sum(1 for l in labels if l == -1)} noise points)"
    )

    # Apply rejection filters
    surviving: list[dict[str, Any]] = []
    for cluster_label, indices in clusters_raw.items():
        # Filter 1: Cluster size below min_cluster_size
        if len(indices) < cfg.hdbscan_min_cluster_size:
            continue

        members = [chunk_data[i] for i in indices]

        # Filter 2: Single source contributes >70% of member documents
        source_counts = Counter(m.get("source_name", "") for m in members)
        total = len(members)
        max_source_frac = max(source_counts.values()) / total
        if max_source_frac > cfg.single_source_dominance_threshold:
            logger.debug(
                f"Cluster {cluster_label} rejected: single source "
                f"dominance {max_source_frac:.2%}"
            )
            continue

        # Compute centroid
        member_embeddings = X[indices]
        centroid = member_embeddings.mean(axis=0).tolist()

        surviving.append({
            "cluster_label": cluster_label,
            "member_indices": indices,
            "centroid": centroid,
            "member_chunk_ids": [m["chunk_id"] for m in members],
            "member_data": members,
            "cluster_size": len(members),
        })

    logger.info(
        f"{len(surviving)} clusters survived rejection filters "
        f"(out of {len(clusters_raw)} raw)"
    )
    return surviving


def _parse_embedding_str(s: str) -> list[float]:
    """Parse '[0.1, 0.2, ...]' string into list of floats."""
    s = s.strip().strip("[]")
    if not s:
        return []
    return [float(x) for x in s.split(",")]
