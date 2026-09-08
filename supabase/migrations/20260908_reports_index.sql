-- Audit finding: reports.user_id has no index; add one to support
-- provider report lookups (GET /patients/{id}/report).
CREATE INDEX IF NOT EXISTS idx_reports_user_id ON public.reports(user_id);
NOTIFY pgrst, 'reload schema';
