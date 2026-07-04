-- =============================================================================
-- ADHERA: Pending Migration 018 — Must be run manually in Supabase SQL Editor
-- URL: https://supabase.com/dashboard/project/olsgvrmxqsftymsbeqve/sql/new
-- =============================================================================
-- This migration was NOT automatically applied to the live database.
-- The backend has been patched to work without these columns temporarily,
-- but to fully restore initiated_by filtering, run this SQL and then
-- re-enable the TODO comments in app/admin/router.py lines 534 and 568.
-- =============================================================================

-- Step 1: Add initiated_by column (idempotent)
ALTER TABLE public.assignments
  ADD COLUMN IF NOT EXISTS initiated_by text
  DEFAULT 'patient'
  CHECK (initiated_by IN ('patient', 'provider', 'admin'));

-- Step 2: Add assignment_id column (idempotent)
ALTER TABLE public.assignments
  ADD COLUMN IF NOT EXISTS assignment_id uuid DEFAULT gen_random_uuid();

-- Step 3: Fix status constraint to allow all valid statuses
ALTER TABLE public.assignments DROP CONSTRAINT IF EXISTS assignments_status_check;
ALTER TABLE public.assignments ADD CONSTRAINT assignments_status_check
  CHECK (status IN ('active', 'inactive', 'pending', 'declined', 'removed', 'cancelled'));

-- Step 4: Set default status to 'pending' for new assignments
ALTER TABLE public.assignments ALTER COLUMN status SET DEFAULT 'pending';

-- Step 5: Backfill initiated_by from assigned_by (admin-created rows have a UUID in assigned_by)
-- All existing rows with assigned_by IS NOT NULL were created by admin
UPDATE public.assignments
  SET initiated_by = 'admin'
  WHERE assigned_by IS NOT NULL;

-- Step 6: Reload PostgREST schema cache (CRITICAL — do this after any DDL)
NOTIFY pgrst, 'reload schema';

-- Step 7: Verify
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'assignments'
ORDER BY ordinal_position;
