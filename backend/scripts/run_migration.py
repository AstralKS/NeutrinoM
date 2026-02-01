"""Execute database migration via Supabase Management API."""

import httpx
from advisor.config import get_settings


def run_migration():
    """Execute the migration SQL against Supabase."""
    settings = get_settings()
    
    # Read migration SQL
    migration_sql = """
    -- Drop existing table (we're in dev, no data loss risk)
    DROP TABLE IF EXISTS analysis_records CASCADE;

    -- Create new table with enhanced fields
    CREATE TABLE analysis_records (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        repo_url TEXT NOT NULL,
        repo_name TEXT NOT NULL,
        analyzed_at TIMESTAMPTZ DEFAULT NOW(),
        model_used TEXT NOT NULL,
        
        -- Structured analysis output (JSONB for flexibility)
        tech_stack JSONB NOT NULL DEFAULT '{}'::jsonb,
        architecture_patterns JSONB NOT NULL DEFAULT '[]'::jsonb,
        risks_and_gaps JSONB NOT NULL DEFAULT '[]'::jsonb,
        recommendations JSONB NOT NULL DEFAULT '[]'::jsonb,
        
        -- NEW: Enhanced analysis fields
        features JSONB NOT NULL DEFAULT '[]'::jsonb,
        business_model JSONB DEFAULT NULL,
        integrations JSONB NOT NULL DEFAULT '[]'::jsonb,
        
        -- Dual outputs - derived from same analysis
        technical_summary TEXT NOT NULL DEFAULT '',
        executive_summary TEXT NOT NULL DEFAULT '',
        
        -- Metadata
        analysis_duration_ms INTEGER,
        file_count INTEGER,
        files_analyzed INTEGER,
        token_usage JSONB DEFAULT '{}'::jsonb,
        
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );

    -- Indexes for common queries
    CREATE INDEX idx_analysis_repo_url ON analysis_records(repo_url);
    CREATE INDEX idx_analysis_created_at ON analysis_records(created_at DESC);
    CREATE INDEX idx_analysis_repo_name ON analysis_records(repo_name);
    """
    
    # Use Supabase REST API to execute SQL via the /rest/v1/rpc endpoint
    # We need to create a function first, or use the SQL endpoint directly
    
    # Extract project ref from URL (format: https://xxx.supabase.co)
    project_ref = settings.supabase_url.split("//")[1].split(".")[0]
    
    print(f"Project: {project_ref}")
    print(f"Supabase URL: {settings.supabase_url}")
    print("\nExecuting migration via PostgREST...")
    
    # Try using the Supabase client directly with RPC
    from supabase import create_client
    
    client = create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
    )
    
    # Split into separate statements and execute
    statements = [s.strip() for s in migration_sql.split(";") if s.strip() and not s.strip().startswith("--")]
    
    print(f"\nFound {len(statements)} SQL statements to execute")
    print("\n" + "="*60)
    print("NOTE: Supabase Python client cannot execute raw DDL SQL.")
    print("You must run this in the Supabase SQL Editor:")
    print("="*60)
    print("\n1. Go to: https://supabase.com/dashboard/project/" + project_ref + "/sql")
    print("\n2. Paste and run this SQL:\n")
    print("-"*60)
    print(migration_sql)
    print("-"*60)
    

if __name__ == "__main__":
    run_migration()
