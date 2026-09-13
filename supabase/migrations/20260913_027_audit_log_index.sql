-- Fix 10: Audit log index on action_code
-- Queries like "show all LOGIN_FAILED events" full-scan the table without this index.
create index if not exists idx_audit_log_action_code
  on public.audit_log (action_code, created_at desc);

notify pgrst, 'reload schema';
