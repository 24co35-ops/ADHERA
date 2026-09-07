-- Supabase Security Linter Remediations (2026-09-07)

-- 1. Fix mutable search_path on prevent_adherence_modification()
CREATE OR REPLACE FUNCTION public.prevent_adherence_modification()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = ''
AS $$
BEGIN
  IF tg_op = 'UPDATE' THEN
    RAISE EXCEPTION 'adherence records are immutable';
  END IF;
  RETURN old;
END;
$$;

-- 2. Revoke execute on SECURITY DEFINER function rls_auto_enable from public, anon, and authenticated
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_proc p
    JOIN pg_namespace n ON p.pronamespace = n.oid
    WHERE n.nspname = 'public' AND p.proname = 'rls_auto_enable'
  ) THEN
    REVOKE EXECUTE ON FUNCTION public.rls_auto_enable() FROM PUBLIC, anon, authenticated;
    GRANT EXECUTE ON FUNCTION public.rls_auto_enable() TO service_role, postgres;
  END IF;
END $$;

NOTIFY pgrst, 'reload schema';
