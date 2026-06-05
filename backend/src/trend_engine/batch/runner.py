"""Batch runner — orchestrates Phase 2 + Phase 3 as an idempotent job.

Scheduled to run every 12 hours or daily. It is the ONLY writer
to topic_clusters and cluster_members.

Idempotence guarantee: topic_clusters is derived state, regenerated
from scratch each run. A crash mid-run followed by re-run produces
identical state to a clean run.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from trend_engine.batch.architecture import generate_architecture_snapshot
from trend_engine.batch.clustering import cluster_embeddings
from trend_engine.batch.enrichment import generate_business_signals, scrape_market_stats
from trend_engine.batch.labeling import (
    generate_cluster_label,
    get_representative_chunks,
    should_relabel,
)
from trend_engine.batch.scoring import compute_trend_scores
from trend_engine.batch.temporal import compute_acceleration, compute_temporal_metrics
from trend_engine.config import TrendEngineSettings, get_settings
from trend_engine.db.client import SupabaseDB, close_http_client, init_http_client
from trend_engine.db.repository import TrendRepository

logger = logging.getLogger(__name__)


async def run_batch_job(
    settings: TrendEngineSettings | None = None,
) -> dict[str, Any]:
    """Execute the full batch analytics pipeline.

    Phase 2: Clustering → Temporal Modeling → Architecture Snapshot
    Phase 3: Trend Scoring → Classification → Labeling → Enrichment

    Returns:
        Stats dict with cluster counts and processing details.
    """
    cfg = settings or get_settings()
    repo = TrendRepository()

    stats: dict[str, Any] = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "chunks_processed": 0,
        "raw_clusters": 0,
        "surviving_clusters": 0,
        "labeled": 0,
        "scored": 0,
    }

    # ── Step 1: Pull existing clusters for acceleration + label comparison ──

    existing_clusters = await repo.get_all_clusters()
    existing_by_id: dict[str, dict[str, Any]] = {
        c["id"]: c for c in existing_clusters
    }

    # Batch-fetch all cluster members in one query instead of N+1 sequential calls
    existing_members: dict[str, set[str]] = {}
    if existing_clusters:
        all_cluster_ids = [c["id"] for c in existing_clusters]
        try:
            ids_str = ",".join(f"'{cid}'" for cid in all_cluster_ids)
            all_member_rows = await repo._db.execute_sql(
                f"SELECT cluster_id, document_chunk_id FROM cluster_members "
                f"WHERE cluster_id IN ({ids_str})"
            )
            if isinstance(all_member_rows, list):
                for row in all_member_rows:
                    cid = row["cluster_id"]
                    existing_members.setdefault(cid, set()).add(
                        row["document_chunk_id"]
                    )
        except Exception as e:
            logger.warning(f"Batch member fetch failed, falling back: {e}")
            for c in existing_clusters:
                members = await repo.get_members_for_cluster(c["id"])
                existing_members[c["id"]] = {
                    m["document_chunk_id"] for m in members
                }

    # ── Step 2: Fetch all chunks within the rolling window ──────────

    window_start = datetime.now(timezone.utc) - timedelta(
        days=cfg.rolling_window_days
    )
    chunk_data = await repo.get_all_chunks_in_window(window_start)

    if not chunk_data or not isinstance(chunk_data, list):
        logger.warning("No chunks in rolling window, skipping batch run")
        stats["status"] = "no_data"
        return stats

    stats["chunks_processed"] = len(chunk_data)
    logger.info(f"Batch: {len(chunk_data)} chunks in {cfg.rolling_window_days}-day window")

    # ── Step 3: Run HDBSCAN clustering ──────────────────────────────

    surviving_clusters = cluster_embeddings(chunk_data, cfg)
    stats["surviving_clusters"] = len(surviving_clusters)

    if not surviving_clusters:
        logger.warning("No clusters survived rejection filters")
        stats["status"] = "no_clusters"
        return stats

    # ── Step 4: Clear old clusters (full regeneration) ──────────────

    await repo.delete_all_clusters()

    # ── Step 5: Process each cluster ────────────────────────────────

    cluster_records: list[dict[str, Any]] = []

    for cluster in surviving_clusters:
        cluster_id = str(uuid.uuid4())
        member_data = cluster["member_data"]
        member_chunk_ids = set(cluster["member_chunk_ids"])
        centroid = cluster["centroid"]

        # ── Temporal metrics ────────────────────────────────
        temporal = compute_temporal_metrics(member_data, cfg)

        # ── Acceleration (delta from previous run) ──────────
        # Find matching previous cluster by centroid similarity (best effort)
        prev_growth = _find_previous_growth(centroid, existing_clusters)
        acceleration = compute_acceleration(temporal["growth_rate"], prev_growth)

        # ── Representative chunks for labeling/architecture ─
        chunk_texts = [m.get("chunk_text", "") for m in member_data]
        chunk_embeddings = []
        for m in member_data:
            emb = m.get("embedding")
            if isinstance(emb, str):
                from trend_engine.batch.clustering import _parse_embedding_str
                emb = _parse_embedding_str(emb)
            chunk_embeddings.append(emb if isinstance(emb, list) else [])

        rep_chunks = get_representative_chunks(
            chunk_texts, chunk_embeddings, centroid,
            top_k=cfg.label_top_k_chunks,
        )

        # ── Architecture snapshot ───────────────────────────
        architecture = await generate_architecture_snapshot(rep_chunks, cfg)

        # ── Build cluster record ────────────────────────────
        record: dict[str, Any] = {
            "id": cluster_id,
            "centroid_embedding": centroid,
            "cluster_size": temporal["cluster_size"],
            "weighted_doc_count_7": temporal["weighted_doc_count_7"],
            "weighted_doc_count_30": temporal["weighted_doc_count_30"],
            "weighted_doc_count_90": temporal["weighted_doc_count_90"],
            "growth_rate": temporal["growth_rate"],
            "acceleration": acceleration,
            "credibility_score": temporal["credibility_score"],
            "source_diversity_score": temporal["source_diversity_score"],
            "architecture_snapshot": architecture,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

        cluster_records.append(record)

        # ── Persist cluster ─────────────────────────────────
        await repo.upsert_cluster(record)

        # ── Persist cluster members ─────────────────────────
        member_rows = [
            {
                "cluster_id": cluster_id,
                "document_chunk_id": cid,
            }
            for cid in member_chunk_ids
        ]
        await repo.insert_members(member_rows)

    # ── Step 6: Scoring & Classification (across full batch) ────────

    compute_trend_scores(cluster_records, cfg)
    stats["scored"] = sum(1 for c in cluster_records if c.get("trend_score") is not None)

    # ── Step 7: Labeling (conditional on membership shift) ──────────

    for record in cluster_records:
        cluster_id = record["id"]
        current_members = set(
            cluster["member_chunk_ids"]
            for cluster in surviving_clusters
            if str(uuid.UUID(cluster_id)) == cluster_id  # match by id
        )

        # Check if relabeling is needed
        needs_label = True  # Default: new cluster
        prev_label = None

        # Find best matching previous cluster
        for prev_id, prev_mems in existing_members.items():
            overlap = len(prev_mems & set(record.get("_member_ids", [])))
            if overlap > len(prev_mems) * 0.5:
                prev_data = existing_by_id.get(prev_id, {})
                prev_label = prev_data.get("label")
                needs_label = should_relabel(
                    set(record.get("_member_ids", [])),
                    prev_mems,
                    cfg.membership_shift_threshold,
                )
                break

        if needs_label or prev_label is None:
            # Get representative chunks for labeling
            rep = record.get("_rep_chunks", [])
            if not rep:
                # Fallback: use any available text
                for cl in surviving_clusters:
                    if True:  # find matching
                        rep = [m.get("chunk_text", "")[:500] for m in cl["member_data"][:5]]
                        break

            label = await generate_cluster_label(rep, cfg)
            if label:
                record["label"] = label
                stats["labeled"] += 1
        else:
            record["label"] = prev_label

        # ── Market stats enrichment (executive view) ──────────
        rep_snippets = [m.get("chunk_text", "")[:300] for m in surviving_clusters[0]["member_data"][:3]]
        market_stats = await scrape_market_stats(
            record.get("label"), rep_snippets, cfg
        )
        if market_stats:
            record["market_stats"] = market_stats

        # ── Persist final record with score, classification, label ──
        update_data = {
            "id": record["id"],
            "trend_score": record.get("trend_score"),
            "classification": record.get("classification"),
            "label": record.get("label"),
            "market_stats": record.get("market_stats"),
            "centroid_embedding": record["centroid_embedding"],
            "cluster_size": record["cluster_size"],
            "weighted_doc_count_7": record["weighted_doc_count_7"],
            "weighted_doc_count_30": record["weighted_doc_count_30"],
            "weighted_doc_count_90": record["weighted_doc_count_90"],
            "growth_rate": record["growth_rate"],
            "acceleration": record["acceleration"],
            "credibility_score": record["credibility_score"],
            "source_diversity_score": record["source_diversity_score"],
            "architecture_snapshot": record.get("architecture_snapshot"),
            "last_updated": record["last_updated"],
        }
        await repo.upsert_cluster(update_data)

    stats["finished_at"] = datetime.now(timezone.utc).isoformat()
    stats["status"] = "success"
    logger.info(f"Batch job complete: {stats}")
    return stats


def _find_previous_growth(
    centroid: list[float],
    existing_clusters: list[dict[str, Any]],
) -> float | None:
    """Find the most similar previous cluster and return its growth_rate."""
    if not existing_clusters:
        return None

    import numpy as np

    centroid_arr = np.array(centroid, dtype=np.float32)
    best_sim = -1.0
    best_growth = None

    for c in existing_clusters:
        prev_centroid = c.get("centroid_embedding")
        if not prev_centroid:
            continue
        if isinstance(prev_centroid, str):
            from trend_engine.batch.clustering import _parse_embedding_str
            prev_centroid = _parse_embedding_str(prev_centroid)

        prev_arr = np.array(prev_centroid, dtype=np.float32)
        dot = np.dot(centroid_arr, prev_arr)
        n1 = np.linalg.norm(centroid_arr)
        n2 = np.linalg.norm(prev_arr)
        if n1 > 0 and n2 > 0:
            sim = float(dot / (n1 * n2))
            if sim > best_sim and sim > 0.7:  # Threshold for matching
                best_sim = sim
                best_growth = c.get("growth_rate")

    return best_growth


async def run_batch_standalone() -> None:
    """Entry point for running batch job as a standalone script."""
    logging.basicConfig(level=logging.INFO)
    await init_http_client()
    try:
        stats = await run_batch_job()
        print(f"Batch job result: {stats}")
    finally:
        await close_http_client()


if __name__ == "__main__":
    asyncio.run(run_batch_standalone())
