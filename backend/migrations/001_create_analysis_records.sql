-- AI Development Advisor - Database Migration V2
-- DROPS THE EXISTING TABLE AND RECREATES WITH NEW FIELDS
-- Run this in your Supabase SQL Editor

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

-- Comments
COMMENT ON TABLE analysis_records IS 'Stores repository analysis results from the AI Development Advisor V2';
COMMENT ON COLUMN analysis_records.features IS 'User-facing features detected from API endpoints';
COMMENT ON COLUMN analysis_records.business_model IS 'Auth, payments, monetization, growth mechanisms';
COMMENT ON COLUMN analysis_records.integrations IS 'Cloud services, SaaS tools with cost tiers';
COMMENT ON COLUMN analysis_records.files_analyzed IS 'Number of files strategically fetched (up to 150)';
