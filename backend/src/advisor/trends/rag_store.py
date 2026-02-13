"""RAG store — pgvector storage and retrieval for trend insights.

Handles:
- Storing TrendInsight objects in Supabase pgvector
- Retrieving cached insights by tag and time window
- Listing all stored tags
- Cleaning up old insights
"""

import hashlib
import logging
from datetime import UTC, datetime, timedelta

from supabase import Client

from advisor.database.client import get_supabase_client
from advisor.trends.models import TrendInsight

logger = logging.getLogger(__name__)

TABLE_NAME = "trend_insights"


class RAGStore:
    """Vector storage and retrieval for trend insights."""

    def __init__(self, client: Client | None = None) -> None:
        """Initialize with Supabase client.

        Args:
            client: Optional Supabase client. Uses default if None.
        """
        self._client = client or get_supabase_client()
        self._table = self._client.table(TABLE_NAME)

    async def store_insight(self, insight: TrendInsight) -> str:
        """Store a trend insight in the database.

        Args:
            insight: TrendInsight to store.

        Returns:
            ID of the stored insight.

        Raises:
            ValueError: If storage fails.
        """
        insight_id = _generate_id(
            insight.tag,
            insight.collected_at,
        )
        insight.id = insight_id

        data = insight.model_dump(mode="json")
        # Remove fields that may not exist in DB schema
        data.pop("embedding", None)

        try:
            result = self._table.upsert(data).execute()
            if result.data:
                logger.info(f"Stored insight for tag '{insight.tag}'")
                return insight_id
            raise ValueError("Upsert returned no data")
        except Exception as e:
            logger.error(f"Failed to store insight: {e}")
            raise

    async def get_recent_for_tag(
        self,
        tag: str,
        days: int = 7,
    ) -> TrendInsight | None:
        """Get most recent insight for a tag within time window.

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
                return TrendInsight.model_validate(
                    result.data[0],
                )
            return None
        except Exception as e:
            logger.error(f"Get recent for tag '{tag}' failed: {e}")
            return None

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

    async def get_last_collection_date(
        self,
        tag: str,
    ) -> datetime | None:
        """Get the date of the last collection for a tag.

        Args:
            tag: Tag to check.

        Returns:
            Datetime of last collection, or None.
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
                raw = result.data[0]["collected_at"]
                return datetime.fromisoformat(
                    raw.replace("Z", "+00:00"),
                )
            return None
        except Exception as e:
            logger.error(f"Get last collection date failed: {e}")
            return None

    async def list_all_tags(self) -> list[str]:
        """List all unique tags in the database.

        Returns:
            Sorted list of unique tags.
        """
        try:
            result = self._table.select("tag").execute()
            tags = {row["tag"] for row in result.data}
            return sorted(tags)
        except Exception as e:
            logger.error(f"List tags failed: {e}")
            return []

    async def delete_old_insights(
        self,
        days: int = 30,
    ) -> int:
        """Delete insights older than specified days.

        Args:
            days: Delete insights older than this.

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


def _generate_id(tag: str, timestamp: datetime) -> str:
    """Generate unique ID from tag and timestamp."""
    content = f"{tag.lower()}:{timestamp.isoformat()}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]
