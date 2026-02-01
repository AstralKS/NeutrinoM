"""Database module for Supabase integration."""

from advisor.database.client import get_supabase_client
from advisor.database.models import AnalysisRecord, RepositoryMetadata
from advisor.database.repository import AnalysisRepository

__all__ = [
    "get_supabase_client",
    "AnalysisRecord",
    "RepositoryMetadata",
    "AnalysisRepository",
]
