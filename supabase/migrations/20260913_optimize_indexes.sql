-- Performance optimization: add indexes on high-frequency query paths to prevent PostgREST 504 timeouts
CREATE INDEX IF NOT EXISTS idx_adherence_user_status_scheduled ON public.adherence(user_id, status, scheduled_utc DESC);
CREATE INDEX IF NOT EXISTS idx_adherence_scheduled_utc ON public.adherence(scheduled_utc DESC);
CREATE INDEX IF NOT EXISTS idx_assignments_provider_patient_status ON public.assignments(provider_id, patient_id, status);
CREATE INDEX IF NOT EXISTS idx_profiles_role_active ON public.profiles(role, is_active);

NOTIFY pgrst, 'reload schema';
