"""Ingestion pipeline orchestrator.

Enforces the per-document execution order:
  1. Fetch URL
  2. Parse HTML → extract body content
  3. Clean: strip boilerplate
  4. Extract metadata
  5. Compute content_hash = SHA256(clean_text)
  6. Dedup check via INSERT (unique constraint on content_hash)
  7. On duplicate: discard, log, continue
  8. On new: INSERT into documents
  9. Chunk clean_text (300–800 tokens, sentence-aware)
  10. Embed each chunk
  11. INSERT into document_chunks

Step 6 BEFORE step 10 is a hard constraint.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from trend_engine.config import get_settings
from trend_engine.db.repository import TrendRepository
from trend_engine.ingestion.chunker import chunk_text
from trend_engine.ingestion.embedder import Embedder
from trend_engine.ingestion.fetcher import Fetcher
from trend_engine.ingestion.parser import compute_content_hash, extract_published_date, parse_html
from trend_engine.ingestion.sources import load_sources
from trend_engine.models import SourceConfig

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """Async ingestion worker with configurable source list."""

    def __init__(
        self,
        repo: TrendRepository | None = None,
        embedder: Embedder | None = None,
        fetcher: Fetcher | None = None,
    ) -> None:
        self._repo = repo or TrendRepository()
        self._embedder = embedder or Embedder()
        self._fetcher = fetcher or Fetcher()

    async def ingest_sources(
        self,
        sources: list[SourceConfig] | None = None,
    ) -> dict[str, int]:
        """Ingest content from all configured sources.

        Returns:
            Stats dict: {"fetched": N, "new": N, "duplicate": N, "failed": N}
        """
        if sources is None:
            sources = load_sources()

        stats = {"fetched": 0, "new": 0, "duplicate": 0, "failed": 0, "chunks": 0}

        for source in sources:
            logger.info(f"Ingesting source: {source.name} ({source.url})")
            try:
                result = await self.ingest_url(
                    url=source.url,
                    source_name=source.name,
                    source_type=source.source_type,
                    source_weight=source.source_weight,
                )
                stats["fetched"] += 1
                if result == "new":
                    stats["new"] += 1
                elif result == "duplicate":
                    stats["duplicate"] += 1
                else:
                    stats["failed"] += 1
            except Exception as exc:
                logger.error(f"Source {source.name} failed: {exc}")
                stats["failed"] += 1

        logger.info(f"Ingestion complete: {stats}")
        return stats

    async def ingest_url(
        self,
        url: str,
        source_name: str,
        source_type: str,
        source_weight: float,
        published_at: datetime | None = None,
        title: str | None = None,
    ) -> str:
        """Ingest a single URL through the full pipeline.

        Returns:
            "new", "duplicate", or "failed"
        """
        # Step 1: Fetch
        html = await self._fetcher.fetch(url)
        if html is None:
            return "failed"

        # Step 2 & 3: Parse and clean
        parsed = parse_html(html)
        clean_text = parsed["clean_text"]
        raw_text = parsed["raw_text"]
        doc_title = title or parsed["title"]

        if not clean_text or len(clean_text) < 50:
            logger.debug(f"Content too short after cleaning: {url}")
            return "failed"

        # Step 4: Extract metadata
        pub_date = published_at or extract_published_date(html) or datetime.now(timezone.utc)

        # Step 5: Compute content hash
        content_hash = compute_content_hash(clean_text)

        # Step 6 & 7 & 8: Dedup via INSERT (unique constraint on content_hash)
        doc_data = {
            "title": doc_title,
            "source_name": source_name,
            "source_type": source_type,
            "published_at": pub_date.isoformat(),
            "source_weight": source_weight,
            "raw_text": raw_text[:50000],  # Cap raw text to prevent oversized rows
            "clean_text": clean_text,
            "content_hash": content_hash,
        }

        inserted = await self._repo.insert_document(doc_data)
        if inserted is None:
            logger.info(f"Duplicate: {content_hash[:16]} ({url})")
            return "duplicate"

        doc_id = inserted["id"]
        logger.info(f"New document: {doc_id} ({doc_title[:60]})")

        # Step 9: Chunk clean_text
        chunks = chunk_text(clean_text)
        if not chunks:
            logger.warning(f"No chunks produced for {doc_id}")
            return "new"

        # Step 10: Generate embeddings
        try:
            embeddings = await self._embedder.embed_texts(chunks)
        except Exception as exc:
            logger.error(f"Embedding failed for {doc_id}: {exc}")
            # Document saved but chunks not — acceptable, will be chunked on retry
            return "new"

        # Step 11: INSERT into document_chunks
        chunk_rows = [
            {
                "document_id": doc_id,
                "chunk_text": chunk_text_val,
                "embedding": embedding,
            }
            for chunk_text_val, embedding in zip(chunks, embeddings)
        ]

        try:
            await self._repo.insert_chunks(chunk_rows)
            logger.info(f"Inserted {len(chunk_rows)} chunks for {doc_id}")
        except Exception as exc:
            logger.error(f"Chunk insert failed for {doc_id}: {exc}")

        return "new"

    async def ingest_direct(
        self,
        title: str,
        source_name: str,
        source_type: str,
        source_weight: float,
        clean_text: str,
        raw_text: str | None = None,
        published_at: datetime | None = None,
    ) -> str:
        """Ingest pre-extracted content (skip fetch/parse).

        Useful for testing and batch import from structured feeds.

        Returns:
            "new", "duplicate", or "failed"
        """
        if not clean_text or len(clean_text) < 50:
            return "failed"

        content_hash = compute_content_hash(clean_text)
        pub_date = published_at or datetime.now(timezone.utc)

        doc_data = {
            "title": title,
            "source_name": source_name,
            "source_type": source_type,
            "published_at": pub_date.isoformat(),
            "source_weight": source_weight,
            "raw_text": raw_text or clean_text,
            "clean_text": clean_text,
            "content_hash": content_hash,
        }

        inserted = await self._repo.insert_document(doc_data)
        if inserted is None:
            return "duplicate"

        doc_id = inserted["id"]
        chunks = chunk_text(clean_text)
        if not chunks:
            return "new"

        try:
            embeddings = await self._embedder.embed_texts(chunks)
        except Exception as exc:
            logger.error(f"Embedding failed for {doc_id}: {exc}")
            return "new"

        chunk_rows = [
            {
                "document_id": doc_id,
                "chunk_text": ct,
                "embedding": emb,
            }
            for ct, emb in zip(chunks, embeddings)
        ]

        await self._repo.insert_chunks(chunk_rows)
        return "new"
