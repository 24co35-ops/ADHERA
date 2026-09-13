-- Trim audit_log rows older than 90 days to recover DB space
-- Run this manually, then set up pg_cron to repeat monthly
DELETE FROM public.audit_log
WHERE created_at < now() - interval '90 days';

-- Schedule monthly pruning via pg_cron (if not already scheduled)
SELECT cron.unschedule('prune-audit-log') WHERE EXISTS (
  SELECT 1 FROM cron.job WHERE jobname = 'prune-audit-log'
);

SELECT cron.schedule(
  'prune-audit-log',
  '0 3 1 * *',  -- 3am on 1st of every month
  $$
  DELETE FROM public.audit_log WHERE created_at < now() - interval '90 days';
  $$
);

NOTIFY pgrst, 'reload schema';
