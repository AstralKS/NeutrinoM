-- Migration: Add user_id column and Row Level Security to analysis_records
-- Run this in Supabase SQL Editor

-- 1. Add user_id column (nullable to preserve existing records)
ALTER TABLE analysis_records
ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL;

-- 2. Create index for fast user-specific queries
CREATE INDEX IF NOT EXISTS idx_analysis_records_user_id
ON analysis_records(user_id);

-- 3. Enable Row Level Security
ALTER TABLE analysis_records ENABLE ROW LEVEL SECURITY;

-- 4. Policy: Users can view their own records
CREATE POLICY "Users can view own records"
ON analysis_records
FOR SELECT
USING (auth.uid() = user_id);

-- 5. Policy: Users can insert records with their own user_id
CREATE POLICY "Users can insert own records"
ON analysis_records
FOR INSERT
WITH CHECK (auth.uid() = user_id OR user_id IS NULL);

-- 6. Policy: Allow anonymous inserts (for unauthenticated analyze requests)
CREATE POLICY "Allow anonymous inserts"
ON analysis_records
FOR INSERT
WITH CHECK (user_id IS NULL);

-- 7. Policy: Service role bypasses RLS (backend uses service_role_key)
-- Note: service_role key already bypasses RLS by default in Supabase.
-- The policies above apply only to anon/authenticated keys.

-- 8. Policy: Allow public SELECT for records without a user_id (backwards compat)
CREATE POLICY "Public can view anonymous records"
ON analysis_records
FOR SELECT
USING (user_id IS NULL);
