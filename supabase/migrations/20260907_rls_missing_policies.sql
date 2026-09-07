-- Fix rls_enabled_no_policy for audit_log, disclaimer_acceptances, reports, notification_retries, and system_events

-- 1. audit_log
ALTER TABLE public.audit_log ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can view own audit logs" ON public.audit_log;
CREATE POLICY "Users can view own audit logs"
  ON public.audit_log FOR SELECT
  USING (auth.uid() = actor_id);

-- 2. disclaimer_acceptances
ALTER TABLE public.disclaimer_acceptances ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users manage own disclaimer acceptances" ON public.disclaimer_acceptances;
CREATE POLICY "Users manage own disclaimer acceptances"
  ON public.disclaimer_acceptances FOR ALL
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- 3. reports
ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users view own reports" ON public.reports;
CREATE POLICY "Users view own reports"
  ON public.reports FOR SELECT
  USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Providers view assigned patient reports" ON public.reports;
CREATE POLICY "Providers view assigned patient reports"
  ON public.reports FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.assignments
      WHERE patient_id = reports.user_id
        AND provider_id = auth.uid()
        AND status = 'active'
    )
  );

-- 4. notification_retries
ALTER TABLE public.notification_retries ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users view own notification retries" ON public.notification_retries;
CREATE POLICY "Users view own notification retries"
  ON public.notification_retries FOR SELECT
  USING (auth.uid() = user_id);

-- 5. system_events
ALTER TABLE public.system_events ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Admins can view system events" ON public.system_events;
CREATE POLICY "Admins can view system events"
  ON public.system_events FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.profiles
      WHERE id = auth.uid() AND role = 'admin'
    )
  );

NOTIFY pgrst, 'reload schema';
