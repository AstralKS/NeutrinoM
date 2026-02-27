-- Add missing columns to analysis_records table to match Python model
-- These columns are required for storing analysis metrics and trend data

ALTER TABLE public.analysis_records
ADD COLUMN IF NOT EXISTS timeline JSONB DEFAULT '{}'::jsonb,
ADD COLUMN IF NOT EXISTS trend_data JSONB DEFAULT '{}'::jsonb;

-- Verify user_id column exists (should be added by previous migration)
-- If not, uncomment the following line:
-- ALTER TABLE public.analysis_records ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);

-- Add index on user_id for faster history lookups (if not exists)
CREATE INDEX IF NOT EXISTS idx_analysis_records_user_id ON public.analysis_records(user_id);
