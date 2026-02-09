-- AI Development Advisor - Complete Database Schema
-- Run this entire script in your Supabase SQL Editor to set up the database

-- ==========================================
-- 1. EXTENSIONS
-- ==========================================
CREATE EXTENSION IF NOT EXISTS vector;

-- ==========================================
-- 2. ANALYSIS RECORDS TABLE
-- ==========================================
DROP TABLE IF EXISTS analysis_records CASCADE;

CREATE TABLE analysis_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_url TEXT NOT NULL,
    repo_name TEXT NOT NULL,
    analyzed_at TIMESTAMPTZ DEFAULT NOW(),
    model_used TEXT NOT NULL,
    
    -- Structured analysis output
    tech_stack JSONB NOT NULL DEFAULT '{}'::jsonb,
    architecture_patterns JSONB NOT NULL DEFAULT '[]'::jsonb,
    risks_and_gaps JSONB NOT NULL DEFAULT '[]'::jsonb,
    recommendations JSONB NOT NULL DEFAULT '[]'::jsonb,
    
    -- Enhanced analysis fields
    features JSONB NOT NULL DEFAULT '[]'::jsonb,
    business_model JSONB DEFAULT NULL,
    integrations JSONB NOT NULL DEFAULT '[]'::jsonb,
    
    -- Summaries
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

-- Indexes
CREATE INDEX idx_analysis_repo_url ON analysis_records(repo_url);
CREATE INDEX idx_analysis_created_at ON analysis_records(created_at DESC);
CREATE INDEX idx_analysis_repo_name ON analysis_records(repo_name);

-- ==========================================
-- 3. TREND INSIGHTS TABLE
-- ==========================================
DROP TABLE IF EXISTS trend_insights CASCADE;

CREATE TABLE trend_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tag TEXT NOT NULL,
    key_points JSONB NOT NULL DEFAULT '[]'::jsonb,
    momentum TEXT NOT NULL DEFAULT 'stable',
    risks JSONB NOT NULL DEFAULT '[]'::jsonb,
    opportunities JSONB NOT NULL DEFAULT '[]'::jsonb,
    direction TEXT DEFAULT '',
    
    -- Source tracking
    sources JSONB NOT NULL DEFAULT '[]'::jsonb,
    sources_count INTEGER DEFAULT 0,
    
    -- Metadata
    collected_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Embedding for RAG
    embedding vector(1536)
);

-- Indexes
CREATE INDEX idx_trend_tag ON trend_insights(tag);
CREATE INDEX idx_trend_collected_at ON trend_insights(collected_at DESC);

-- Instructions
-- After running this, your database will be ready for the application.
