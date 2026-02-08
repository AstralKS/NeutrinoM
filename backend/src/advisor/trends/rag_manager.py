"""RAG Manager for vector database operations.

Handles storage and retrieval of trend insights using Supabase pgvector.
Optimized for minimal storage and fast retrieval.
"""

import hashlib
import logging
from datetime import UTC, datetime, timedelta

from supabase import Client

from advisor.database.client import get_supabase_client
from advisor.trends.models import TrendInsight

logger = logging.getLogger(__name__)

TABLE_NAME = "trend_insights"


class RAGManager:
    """Manages vector storage and retrieval for trend insights."""

    def __init__(self, client: Client | None = None) -> None:
        """Initialize with Supabase client.

        Args:
            client: Optional Supabase client. If None, uses default.
        """
        self._client = client or get_supabase_client()
        self._table = self._client.table(TABLE_NAME)

    async def store_insight(self, insight: TrendInsight) -> str:
        """Store a trend insight in the database.

        Args:
            insight: TrendInsight to store.

        Returns:
            ID of the stored insight.
        """
        # Generate unique ID from tag and timestamp
        insight_id = self._generate_id(insight.tag, insight.collected_at)
        insight.id = insight_id

        data = insight.model_dump(mode="json")
        # Convert embedding to proper format for pgvector
        if insight.embedding:
            data["embedding"] = insight.embedding
        else:
            # Store without embedding if not available
            data.pop("embedding", None)

        try:
            result = self._table.upsert(data).execute()
            if result.data:
                logger.info(f"Stored insight for tag '{insight.tag}'")
                return insight_id
            raise ValueError("Failed to store insight")
        except Exception as e:
            logger.error(f"Failed to store insight: {e}")
            raise

    async def search_by_tag(
        self,
        tag: str,
        limit: int = 10,
    ) -> list[TrendInsight]:
        """Search for insights by exact tag match.

        Args:
            tag: Tag to search for.
            limit: Maximum results to return.

        Returns:
            List of matching TrendInsights.
        """
        try:
            result = (
                self._table.select("*")
                .eq("tag", tag.lower())
                .order("collected_at", desc=True)
                .limit(limit)
                .execute()
            )

            return [TrendInsight.model_validate(row) for row in result.data]
        except Exception as e:
            logger.error(f"Search by tag failed: {e}")
            return []

    async def get_recent_for_tag(
        self,
        tag: str,
        days: int = 7,
    ) -> TrendInsight | None:
        """Get the most recent insight for a tag within time window.

        Args:
            tag: Tag to search for.
            days: Number of days to look back.

        Returns:
            Most recent TrendInsight if found, None otherwise.
        """
        cutoff = datetime.now(UTC) - timedelta(days=days)

        try:
            result = (
                self._table.select("*")
                .eq("tag", tag.lower())
                .gte("collected_at", cutoff.isoformat())
                .order("collected_at", desc=True)
                .limit(1)
                .execute()
            )

            if result.data:
                return TrendInsight.model_validate(result.data[0])
            return None
        except Exception as e:
            logger.error(f"Get recent for tag failed: {e}")
            return None

    async def get_last_collection_date(self, tag: str) -> datetime | None:
        """Get the date of the last collection for a tag.

        Args:
            tag: Tag to check.

        Returns:
            Datetime of last collection, None if never collected.
        """
        try:
            result = (
                self._table.select("collected_at")
                .eq("tag", tag.lower())
                .order("collected_at", desc=True)
                .limit(1)
                .execute()
            )

            if result.data:
                return datetime.fromisoformat(
                    result.data[0]["collected_at"].replace("Z", "+00:00")
                )
            return None
        except Exception as e:
            logger.error(f"Get last collection date failed: {e}")
            return None

    async def list_all_tags(self) -> list[str]:
        """List all unique tags in the database.

        Returns:
            List of unique tags.
        """
        try:
            result = self._table.select("tag").execute()

            tags = {row["tag"] for row in result.data}
            return sorted(tags)
        except Exception as e:
            logger.error(f"List tags failed: {e}")
            return []

    async def delete_old_insights(self, days: int = 30) -> int:
        """Delete insights older than specified days.

        Args:
            days: Delete insights older than this many days.

        Returns:
            Number of deleted records.
        """
        cutoff = datetime.now(UTC) - timedelta(days=days)

        try:
            result = (
                self._table.delete().lt("collected_at", cutoff.isoformat()).execute()
            )

            count = len(result.data) if result.data else 0
            logger.info(f"Deleted {count} old insights")
            return count
        except Exception as e:
            logger.error(f"Delete old insights failed: {e}")
            return 0

    def _generate_id(self, tag: str, timestamp: datetime) -> str:
        """Generate unique ID from tag and timestamp."""
        content = f"{tag.lower()}:{timestamp.isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
