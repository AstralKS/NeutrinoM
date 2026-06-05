"""TrendContextBuilder — the only interface the AI agent imports.

Encapsulates the full retrieval sequence:
1. POST /query/similar with text query
2. Extract unique cluster_ids where classification is emerging or expanding
3. For each, GET /trends/{cluster_id}?view=technical and ?view=executive
4. Assemble structured TrendContext object

The downstream LLM receives this structured JSON — never raw vectors,
never unstructured text, never raw search results.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from trend_engine.models import RelatedTrend, TrendContext

logger = logging.getLogger(__name__)


class TrendContextBuilder:
    """Build structured trend context for downstream AI agents.

    This is the ONLY interface the agent orchestrator imports.
    """

    def __init__(
        self,
        api_base_url: str = "http://localhost:8001",
        api_key: str = "trend-engine-dev-key",
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base = api_base_url.rstrip("/")
        self._api_key = api_key
        self._external_client = http_client
        self._own_client: httpx.AsyncClient | None = None

    @property
    def _client(self) -> httpx.AsyncClient:
        if self._external_client:
            return self._external_client
        if self._own_client is None:
            self._own_client = httpx.AsyncClient(timeout=30.0)
        return self._own_client

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "X-API-Key": self._api_key,
            "Content-Type": "application/json",
        }

    async def build_context(
        self,
        query: str,
        top_k: int = 10,
        classifications: set[str] | None = None,
    ) -> TrendContext:
        """Execute the full retrieval sequence and return structured context.

        Args:
            query: Text query representing the topic of interest.
            top_k: Number of similar results to retrieve.
            classifications: Which classifications to included.
                Defaults to {"emerging", "expanding"}.

        Returns:
            TrendContext with all related trends assembled.
        """
        if classifications is None:
            classifications = {"emerging", "expanding"}

        # Step 1: POST /query/similar
        similar_results = await self._query_similar(query, top_k)

        # Step 2: Extract unique cluster_ids where classification matches
        target_cluster_ids: set[str] = set()
        for result in similar_results:
            cid = result.get("cluster_id")
            cls = result.get("cluster_classification")
            if cid and cls in classifications:
                target_cluster_ids.add(cid)

        # Step 3: For each cluster, get technical and executive views
        related_trends: list[RelatedTrend] = []

        for cluster_id in target_cluster_ids:
            technical = await self._get_trend_detail(cluster_id, "technical")
            executive = await self._get_trend_detail(cluster_id, "executive")

            if technical and executive:
                trend = self._merge_views(technical, executive)
                related_trends.append(trend)

        # Step 4: Assemble TrendContext
        return TrendContext(
            query=query,
            retrieved_at=datetime.now(timezone.utc),
            related_trends=related_trends,
        )

    async def _query_similar(
        self, text: str, top_k: int
    ) -> list[dict[str, Any]]:
        """POST /query/similar"""
        try:
            resp = await self._client.post(
                f"{self._base}/query/similar",
                headers=self._headers,
                json={"text": text, "top_k": top_k},
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.error(f"query/similar failed: {exc}")
            return []

    async def _get_trend_detail(
        self, cluster_id: str, view: str
    ) -> dict[str, Any] | None:
        """GET /trends/{cluster_id}?view=..."""
        try:
            resp = await self._client.get(
                f"{self._base}/trends/{cluster_id}",
                headers=self._headers,
                params={"view": view},
            )
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.error(f"trends/{cluster_id}?view={view} failed: {exc}")
            return None

    def _merge_views(
        self,
        technical: dict[str, Any],
        executive: dict[str, Any],
    ) -> RelatedTrend:
        """Merge technical and executive views into a RelatedTrend."""
        growth = technical.get("growth_metrics", {})

        return RelatedTrend(
            label=technical.get("label"),
            classification=technical.get("classification"),
            trend_score=executive.get("trend_score"),
            growth_rate=growth.get("growth_rate", 0.0),
            acceleration=growth.get("acceleration", 0.0),
            architecture_snapshot=technical.get("architecture_snapshot"),
            market_stats=executive.get("market_stats"),
            source_diversity=0.0,  # Not in detail view, set from trends list
            representative_snippets=executive.get("representative_snippets", []),
            top_sources=[
                doc.get("title", "")
                for doc in technical.get("top_documents", [])[:5]
            ],
        )

    async def close(self) -> None:
        """Close the internal HTTP client if we own it."""
        if self._own_client:
            await self._own_client.aclose()
            self._own_client = None
