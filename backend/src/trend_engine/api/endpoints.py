"""API endpoints — all read-only against trend data.

POST /query/similar  — semantic similarity search
GET  /trends         — list trends with filters
GET  /trends/{id}    — detailed view (technical or executive)
GET  /health         — health check
"""

from __future__ import annotations

import logging
from typing import Any
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status

from trend_engine.api.auth import verify_api_key
from trend_engine.batch.enrichment import generate_business_signals
from trend_engine.config import get_settings
from trend_engine.db.repository import TrendRepository
from trend_engine.ingestion.embedder import Embedder
from trend_engine.models import (
    ExecutiveView,
    GrowthMetrics,
    MarketStats,
    BusinessSignals,
    SimilarQueryRequest,
    SimilarResult,
    SourceBreakdown,
    TechnicalView,
    TopDocument,
    TrendSummary,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Health Check ──────────────────────────────────────────────────


@router.get("/health")
async def health():
    return {"status": "healthy", "service": "trend-intelligence-engine", "version": "0.1.0"}


# ── POST /query/similar ──────────────────────────────────────────


@router.post(
    "/query/similar",
    response_model=list[SimilarResult],
    dependencies=[Depends(verify_api_key)],
)
async def query_similar(request: SimilarQueryRequest):
    """Semantic similarity search.

    Embedding happens at the API boundary — the caller never
    constructs or passes a vector.
    """
    embedder = Embedder()
    repo = TrendRepository()

    # Embed query text
    query_embedding = await embedder.embed_single(request.text)

    # pgvector similarity search
    results = await repo.similarity_search(query_embedding, top_k=request.top_k)

    if not results or not isinstance(results, list):
        return []

    # Enrich with cluster info
    chunk_ids = [r.get("chunk_id", "") for r in results if r.get("chunk_id")]
    cluster_map = await repo.get_chunk_cluster_mapping(chunk_ids)

    response: list[SimilarResult] = []
    for r in results:
        chunk_id = r.get("chunk_id", "")
        cluster_info = cluster_map.get(chunk_id, {})

        response.append(
            SimilarResult(
                chunk_id=chunk_id,
                chunk_text=r.get("chunk_text", ""),
                document_id=r.get("document_id", ""),
                source_name=r.get("source_name", ""),
                published_at=r.get("published_at", datetime.now(timezone.utc)),
                cluster_id=cluster_info.get("cluster_id"),
                cluster_label=cluster_info.get("cluster_label"),
                cluster_trend_score=cluster_info.get("cluster_trend_score"),
                cluster_classification=cluster_info.get("cluster_classification"),
            )
        )

    return response


# ── GET /trends ────────────────────────────────────────────────────


@router.get(
    "/trends",
    response_model=list[TrendSummary],
    dependencies=[Depends(verify_api_key)],
)
async def get_trends(
    classification: str | None = Query(None),
    min_trend_score: float | None = Query(None),
    limit: int = Query(default=20, ge=1, le=100),
):
    """List trends sorted by trend_score DESC."""
    repo = TrendRepository()

    clusters = await repo.get_clusters_by_filter(
        classification=classification,
        min_trend_score=min_trend_score,
        limit=limit,
    )

    response: list[TrendSummary] = []
    for c in clusters:
        # Get representative snippets (top 3 member chunks)
        members = await repo.get_member_chunks_for_cluster(c["id"])
        snippets = []
        if isinstance(members, list):
            snippets = [m.get("chunk_text", "")[:200] for m in members[:3]]

        response.append(
            TrendSummary(
                cluster_id=c["id"],
                label=c.get("label"),
                classification=c.get("classification"),
                trend_score=c.get("trend_score"),
                growth_rate=c.get("growth_rate", 0.0),
                acceleration=c.get("acceleration", 0.0),
                cluster_size=c.get("cluster_size", 0),
                credibility_score=c.get("credibility_score", 0.0),
                source_diversity_score=c.get("source_diversity_score", 0.0),
                representative_snippets=snippets,
                last_updated=c.get("last_updated", datetime.now(timezone.utc)),
            )
        )

    return response


# ── GET /trends/{cluster_id} ─────────────────────────────────────


@router.get(
    "/trends/{cluster_id}",
    dependencies=[Depends(verify_api_key)],
)
async def get_trend_detail(
    cluster_id: str,
    view: str = Query(default="technical", regex="^(technical|executive)$"),
):
    """Detailed trend view — technical or executive."""
    repo = TrendRepository()

    cluster = await repo.get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cluster {cluster_id} not found",
        )

    # Get member chunks with document data
    members = await repo.get_member_chunks_for_cluster(cluster_id)
    member_list = members if isinstance(members, list) else []

    if view == "technical":
        return _build_technical_view(cluster, member_list)
    else:
        return _build_executive_view(cluster, member_list)


def _build_technical_view(
    cluster: dict[str, Any],
    members: list[dict[str, Any]],
) -> TechnicalView:
    """Build technical view response."""
    # Source breakdown
    source_stats: dict[str, dict[str, Any]] = {}
    for m in members:
        src = m.get("source_name", "unknown")
        if src not in source_stats:
            source_stats[src] = {"count": 0, "weight_sum": 0.0}
        source_stats[src]["count"] += 1
        source_stats[src]["weight_sum"] += float(m.get("source_weight", 0.5))

    source_breakdown = [
        SourceBreakdown(
            source_name=src,
            doc_count=stats["count"],
            avg_source_weight=round(stats["weight_sum"] / max(stats["count"], 1), 2),
        )
        for src, stats in source_stats.items()
    ]

    # Top documents (deduplicated by title)
    seen_titles: set[str] = set()
    top_docs: list[TopDocument] = []
    for m in members[:20]:
        title = m.get("title", "")
        if title and title not in seen_titles:
            seen_titles.add(title)
            top_docs.append(
                TopDocument(
                    title=title,
                    url=None,  # URL not stored in chunks
                    published_at=m.get("published_at", datetime.now(timezone.utc)),
                )
            )
            if len(top_docs) >= 10:
                break

    return TechnicalView(
        cluster_id=cluster["id"],
        label=cluster.get("label"),
        classification=cluster.get("classification"),
        growth_metrics=GrowthMetrics(
            weighted_doc_count_7=cluster.get("weighted_doc_count_7", 0.0),
            weighted_doc_count_30=cluster.get("weighted_doc_count_30", 0.0),
            weighted_doc_count_90=cluster.get("weighted_doc_count_90", 0.0),
            growth_rate=cluster.get("growth_rate", 0.0),
            acceleration=cluster.get("acceleration", 0.0),
        ),
        architecture_snapshot=cluster.get("architecture_snapshot"),
        source_breakdown=source_breakdown,
        top_documents=top_docs,
    )


def _build_executive_view(
    cluster: dict[str, Any],
    members: list[dict[str, Any]],
) -> ExecutiveView:
    """Build executive view response."""
    # Market stats from cluster
    market_raw = cluster.get("market_stats")
    market_stats = None
    if market_raw and isinstance(market_raw, dict):
        market_stats = MarketStats(
            adoption_velocity=market_raw.get("adoption_velocity"),
            market_penetration=market_raw.get("market_penetration"),
            community_health_score=market_raw.get("community_health_score"),
            data_sources=market_raw.get("data_sources", []),
            scraped_at=market_raw.get("scraped_at"),
        )

    # Business signals
    biz = generate_business_signals(
        classification=cluster.get("classification"),
        growth_rate=cluster.get("growth_rate", 0.0),
        acceleration=cluster.get("acceleration", 0.0),
        credibility_score=cluster.get("credibility_score", 0.0),
    )

    # Representative snippets
    snippets = [m.get("chunk_text", "")[:200] for m in members[:2]]

    # Simplify architecture snapshot for executive view (remove dependency_graph)
    arch = cluster.get("architecture_snapshot")
    if arch and isinstance(arch, dict):
        arch = {
            "detected_layers": arch.get("detected_layers", []),
            "primary_patterns": arch.get("primary_patterns", []),
            "risk_zones": arch.get("risk_zones", []),
        }

    return ExecutiveView(
        cluster_id=cluster["id"],
        label=cluster.get("label"),
        classification=cluster.get("classification"),
        trend_score=cluster.get("trend_score"),
        architecture_snapshot=arch,
        market_stats=market_stats,
        business_signals=BusinessSignals(**biz),
        representative_snippets=snippets,
    )
