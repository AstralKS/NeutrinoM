-- AI Development Advisor - Add version columns to trend_insights
-- Run this in your Supabase SQL Editor
-- Adds latest_version and version_info columns to existing trend_insights table

ALTER TABLE trend_insights
    ADD COLUMN IF NOT EXISTS latest_version TEXT DEFAULT '',
    ADD COLUMN IF NOT EXISTS version_info TEXT DEFAULT '';

COMMENT ON COLUMN trend_insights.latest_version IS 'Latest detected version for the technology (e.g. "3.12.1")';
COMMENT ON COLUMN trend_insights.version_info IS 'Brief notes about version changes and updates';
