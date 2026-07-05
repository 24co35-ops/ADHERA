-- =============================================================================
-- ADHERA: Pending Migration 019 — Must be run manually in Supabase SQL Editor
-- URL: https://supabase.com/dashboard/project/olsgvrmxqsftymsbeqve/sql/new
-- =============================================================================
-- Root cause of Sentry error (PGRST205):
--   POST /v1/doses/{reminder_id}/taken triggers insights engine which inserts
--   into patient_flags. Table was never applied to the live DB (only in repo).
-- This script is IDEMPOTENT — safe to run multiple times.
-- =============================================================================

-- Step 1: Create table (idempotent via IF NOT EXISTS)
CREATE TABLE IF NOT EXISTS public.patient_flags (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  flag_type text NOT NULL CHECK (flag_type IN ('dose_drift', 'weekend_pattern', 'post_side_effect_drop', 'silent_inactivity')),
  severity smallint NOT NULL CHECK (severity BETWEEN 1 AND 4),
  details jsonb NOT NULL DEFAULT '{}'::jsonb,
  detected_at timestamptz NOT NULL DEFAULT now(),
  resolved_at timestamptz,
  related_medicine_id uuid REFERENCES public.medicines(id) ON DELETE SET NULL,
  related_feedback_id uuid REFERENCES public.feedback(id) ON DELETE SET NULL
);

-- Step 2: Index (idempotent)
CREATE INDEX IF NOT EXISTS idx_patient_flags_user_active
  ON public.patient_flags (user_id) WHERE resolved_at IS NULL;

-- Step 3: Enable RLS
ALTER TABLE public.patient_flags ENABLE ROW LEVEL SECURITY;

-- Step 4: RLS Policies (idempotent via DO block)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'patient_flags' AND policyname = 'patients_own_flags'
  ) THEN
    CREATE POLICY "patients_own_flags"
      ON public.patient_flags FOR SELECT
      USING (user_id = auth.uid());
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'patient_flags' AND policyname = 'providers_see_assigned_flags'
  ) THEN
    CREATE POLICY "providers_see_assigned_flags"
      ON public.patient_flags FOR SELECT
      USING (
        EXISTS (
          SELECT 1 FROM public.assignments
          WHERE patient_id = patient_flags.user_id
            AND provider_id = auth.uid()
            AND status = 'active'
        )
      );
  END IF;
END
$$;

-- Step 5: CRITICAL — Reload PostgREST schema cache
NOTIFY pgrst, 'reload schema';

-- Step 6: Verify
SELECT table_name, table_schema
FROM information_schema.tables
WHERE table_name = 'patient_flags' AND table_schema = 'public';
-- Expected: 1 row. If 0 rows, check permissions.
