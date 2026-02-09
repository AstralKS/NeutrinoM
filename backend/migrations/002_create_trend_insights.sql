-- AI Development Advisor - Database Migration 002
-- CREATES THE TREND_INSIGHTS TABLE

-- Enable pgvector extension if not already enabled (for embeddings)
CREATE EXTENSION IF NOT EXISTS vector;

-- Drop existing if needed
DROP TABLE IF EXISTS trend_insights CASCADE;

-- Create table
CREATE TABLE trend_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tag TEXT NOT NULL,
    key_points JSONB NOT NULL DEFAULT '[]'::jsonb,
    momentum TEXT NOT NULL DEFAULT 'stable', -- rising, stable, declining
    risks JSONB NOT NULL DEFAULT '[]'::jsonb,
    opportunities JSONB NOT NULL DEFAULT '[]'::jsonb,
    direction TEXT DEFAULT '',
    
    -- Source tracking
    sources JSONB NOT NULL DEFAULT '[]'::jsonb,
    sources_count INTEGER DEFAULT 0,
    
    -- Metadata
    collected_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Embedding for RAG (semantic search)
    -- Using 1536 dimensions for OpenAI embeddings (text-embedding-3-small)
    embedding vector(1536)
);

-- Indexes
CREATE INDEX idx_trend_tag ON trend_insights(tag);
CREATE INDEX idx_trend_collected_at ON trend_insights(collected_at DESC);

-- Comments
COMMENT ON TABLE trend_insights IS 'Stores analyzed technology trends and market intelligence';
COMMENT ON COLUMN trend_insights.tag IS 'The technology tag (e.g., react, python, docker)';
COMMENT ON COLUMN trend_insights.momentum IS 'Current market momentum: rising, stable, or declining';
