create table public.audit_log (
  id          uuid primary key default gen_random_uuid(),
  actor_id    uuid references auth.users(id),
  action_code text not null,   -- e.g. 'LOGIN_FAILED', 'ASSIGNMENT_CHANGED'
  target_id   uuid,            -- affected user/record
  reason      text,            -- for authorised access events
  created_at  timestamptz not null default now()
  -- No PHI, no free-text medication data
);
