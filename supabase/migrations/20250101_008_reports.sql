create table public.reports (
  id           uuid primary key default gen_random_uuid(),
  user_id      uuid not null references auth.users(id),
  period_type  text not null check (period_type in ('daily', 'weekly', 'monthly')),
  period_start date not null,
  period_end   date not null,
  total_doses  integer not null,
  doses_taken  integer not null,
  doses_missed integer not null,
  adherence_rate numeric(5,1) not null,
  is_stale     boolean not null default false,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);
