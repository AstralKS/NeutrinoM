"""Repository pattern for analysis CRUD operations."""

from uuid import UUID

from supabase import Client

from advisor.database.models import AnalysisRecord

TABLE_NAME = "analysis_records"


class AnalysisRepository:
    """Repository for analysis record CRUD operations.

    Provides a clean interface for database operations,
    hiding Supabase-specific implementation details.
    """

    def __init__(self, client: Client) -> None:
        """Initialize repository with Supabase client.

        Args:
            client: Configured Supabase client instance.
        """
        self._client = client
        self._table = client.table(TABLE_NAME)

    async def create(self, record: AnalysisRecord) -> AnalysisRecord:
        """Create a new analysis record.

        Args:
            record: Analysis record to insert.

        Returns:
            Created record with generated ID.
        """
        data = record.to_db_dict()
        result = self._table.insert(data).execute()

        if result.data:
            return AnalysisRecord.from_db_row(result.data[0])
        raise ValueError("Failed to create analysis record")

    async def get_by_id(self, analysis_id: UUID) -> AnalysisRecord | None:
        """Get analysis record by ID.

        Args:
            analysis_id: UUID of the analysis record.

        Returns:
            Analysis record if found, None otherwise.
        """
        result = (
            self._table
            .select("*")
            .eq("id", str(analysis_id))
            .execute()
        )

        if result.data:
            return AnalysisRecord.from_db_row(result.data[0])
        return None

    async def get_by_repo_url(self, repo_url: str) -> list[AnalysisRecord]:
        """Get all analyses for a repository.

        Args:
            repo_url: GitHub repository URL.

        Returns:
            List of analysis records, newest first.
        """
        result = (
            self._table
            .select("*")
            .eq("repo_url", repo_url)
            .order("created_at", desc=True)
            .execute()
        )

        return [AnalysisRecord.from_db_row(row) for row in result.data]

    async def list_recent(self, limit: int = 20) -> list[AnalysisRecord]:
        """List recent analysis records.

        Args:
            limit: Maximum number of records to return.

        Returns:
            List of analysis records, newest first.
        """
        result = (
            self._table
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        return [AnalysisRecord.from_db_row(row) for row in result.data]

    async def delete(self, analysis_id: UUID) -> bool:
        """Delete an analysis record.

        Args:
            analysis_id: UUID of the record to delete.

        Returns:
            True if deleted, False if not found.
        """
        result = (
            self._table
            .delete()
            .eq("id", str(analysis_id))
            .execute()
        )

        return len(result.data) > 0
