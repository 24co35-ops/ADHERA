-- 022_directory_indexes.sql: Indexes supporting Platform Identity Directory queries
CREATE INDEX IF NOT EXISTS idx_assignments_patient_id ON public.assignments(patient_id);
CREATE INDEX IF NOT EXISTS idx_adherence_user_id ON public.adherence(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_actor_id ON public.audit_log(actor_id);

NOTIFY pgrst, 'reload schema';
