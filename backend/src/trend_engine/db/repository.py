"""Repository — typed CRUD for documents, chunks, clusters, members."""

from __future__ import annotations

import logging
import math
from datetime import datetime
from typing import Any
from uuid import UUID

from trend_engine.db.client import SupabaseDB

logger = logging.getLogger(__name__)


class TrendRepository:
    """Data-access layer for all trend engine tables."""

    def __init__(self, db: SupabaseDB | None = None) -> None:
        self._db = db or SupabaseDB()

    # ── Documents ──────────────────────────────────────────────────

    async def insert_document(self, doc: dict[str, Any]) -> dict[str, Any] | None:
        """Insert a document. Returns None if duplicate (content_hash)."""
        rows = await self._db.insert(
            "documents", doc, on_conflict="content_hash"
        )
        if not rows:
            logger.debug(f"Duplicate document: {doc.get('content_hash', '')[:16]}")
            return None
        return rows[0]

    async def get_document(self, doc_id: str) -> dict[str, Any] | None:
        rows = await self._db.select(
            "documents", filters={"id": f"eq.{doc_id}"}, limit=1
        )
        return rows[0] if rows else None

    # ── Document Chunks ────────────────────────────────────────────

    async def insert_chunks(
        self, chunks: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Bulk insert chunks with embeddings."""
        if not chunks:
            return []
        # pgvector expects the embedding in [ ] list format
        for c in chunks:
            if isinstance(c.get("embedding"), list):
                c["embedding"] = str(c["embedding"])
        return await self._db.insert("document_chunks", chunks)

    async def get_chunks_for_document(
        self, document_id: str
    ) -> list[dict[str, Any]]:
        return await self._db.select(
            "document_chunks",
            filters={"document_id": f"eq.{document_id}"},
        )

    async def get_all_chunks_in_window(
        self, since: datetime
    ) -> list[dict[str, Any]]:
        """Fetch all chunks from documents published within the window."""
        iso = since.isoformat()
        # Join via document published_at — use RPC or construct query
        # We need chunks + document metadata for clustering
        sql = f"""
            SELECT
                dc.id AS chunk_id,
                dc.document_id,
                dc.chunk_text,
                dc.embedding,
                d.title,
                d.source_name,
                d.source_type,
                d.published_at,
                d.source_weight,
                d.content_hash
            FROM document_chunks dc
            JOIN documents d ON d.id = dc.document_id
            WHERE d.published_at >= '{iso}'
            ORDER BY d.published_at DESC
        """
        return await self._db.execute_sql(sql)

    # ── Topic Clusters ─────────────────────────────────────────────

    async def get_all_clusters(self) -> list[dict[str, Any]]:
        return await self._db.select("topic_clusters")

    async def get_cluster(self, cluster_id: str) -> dict[str, Any] | None:
        rows = await self._db.select(
            "topic_clusters", filters={"id": f"eq.{cluster_id}"}, limit=1
        )
        return rows[0] if rows else None

    async def get_clusters_by_filter(
        self,
        classification: str | None = None,
        min_trend_score: float | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        filters: dict[str, str] = {}
        if classification:
            filters["classification"] = f"eq.{classification}"
        if min_trend_score is not None:
            filters["trend_score"] = f"gte.{min_trend_score}"
        return await self._db.select(
            "topic_clusters",
            filters=filters,
            order="trend_score.desc.nullslast",
            limit=limit,
        )

    async def upsert_cluster(self, cluster: dict[str, Any]) -> dict[str, Any]:
        """Upsert a cluster (regenerated each batch run)."""
        if isinstance(cluster.get("centroid_embedding"), list):
            cluster["centroid_embedding"] = str(cluster["centroid_embedding"])
        rows = await self._db.insert(
            "topic_clusters", cluster, on_conflict="id", upsert=True
        )
        return rows[0] if rows else cluster

    async def delete_all_clusters(self) -> None:
        """Clear all clusters (full regeneration per batch run)."""
        # Delete members first (FK constraint), then clusters
        await self._db.execute_sql("DELETE FROM cluster_members")
        await self._db.execute_sql("DELETE FROM topic_clusters")

    # ── Cluster Members ────────────────────────────────────────────

    async def insert_members(
        self, members: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        if not members:
            return []
        return await self._db.insert("cluster_members", members)

    async def get_members_for_cluster(
        self, cluster_id: str
    ) -> list[dict[str, Any]]:
        return await self._db.select(
            "cluster_members",
            filters={"cluster_id": f"eq.{cluster_id}"},
        )

    async def get_member_chunks_for_cluster(
        self, cluster_id: str
    ) -> list[dict[str, Any]]:
        """Get full chunk + document data for a cluster's members."""
        sql = f"""
            SELECT
                dc.id AS chunk_id,
                dc.document_id,
                dc.chunk_text,
                d.title,
                d.source_name,
                d.source_type,
                d.published_at,
                d.source_weight
            FROM cluster_members cm
            JOIN document_chunks dc ON dc.id = cm.document_chunk_id
            JOIN documents d ON d.id = dc.document_id
            WHERE cm.cluster_id = '{cluster_id}'
            ORDER BY d.published_at DESC
        """
        return await self._db.execute_sql(sql)

    # ── Similarity Search (pgvector) ───────────────────────────────

    async def similarity_search(
        self, embedding: list[float], top_k: int = 10
    ) -> list[dict[str, Any]]:
        """Cosine similarity search against document_chunks."""
        vec_str = str(embedding)
        sql = f"""
            SELECT
                dc.id AS chunk_id,
                dc.document_id,
                dc.chunk_text,
                d.title,
                d.source_name,
                d.published_at,
                1 - (dc.embedding <=> '{vec_str}') AS similarity
            FROM document_chunks dc
            JOIN documents d ON d.id = dc.document_id
            ORDER BY dc.embedding <=> '{vec_str}'
            LIMIT {top_k}
        """
        return await self._db.execute_sql(sql)

    async def get_chunk_cluster_mapping(
        self, chunk_ids: list[str]
    ) -> dict[str, dict[str, Any]]:
        """For a list of chunk IDs, find their cluster assignments."""
        if not chunk_ids:
            return {}
        ids_str = ",".join(f"'{cid}'" for cid in chunk_ids)
        sql = f"""
            SELECT
                cm.document_chunk_id AS chunk_id,
                tc.id AS cluster_id,
                tc.label AS cluster_label,
                tc.trend_score AS cluster_trend_score,
                tc.classification AS cluster_classification
            FROM cluster_members cm
            JOIN topic_clusters tc ON tc.id = cm.cluster_id
            WHERE cm.document_chunk_id IN ({ids_str})
        """
        rows = await self._db.execute_sql(sql)
        result: dict[str, dict[str, Any]] = {}
        if isinstance(rows, list):
            for row in rows:
                result[row["chunk_id"]] = row
        return result
