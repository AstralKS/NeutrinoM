"""Supabase client configuration and connection management."""

from functools import lru_cache

from supabase import Client, create_client

from advisor.config import get_settings


@lru_cache
def get_supabase_client() -> Client:
    """Get cached Supabase client instance.

    The client is created once and reused for all database operations.
    Connection errors will raise immediately for fail-fast behavior.

    Returns:
        Configured Supabase client.

    Raises:
        Exception: If connection to Supabase fails.
    """
    settings = get_settings()
    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
    )
