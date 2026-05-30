create table public.disclaimer_acceptances (
  id               uuid primary key default gen_random_uuid(),
  user_id          uuid not null references auth.users(id),
  disclaimer_version text not null,
  accepted_at      timestamptz not null default now()
  -- Retained for account lifetime; non-deletable
);
