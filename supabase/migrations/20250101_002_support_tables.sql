-- 2. Transactional and Support Tables

-- adherence table (append-only)
create table public.adherence (
  id              uuid primary key default gen_random_uuid(),
  reminder_id     uuid not null references public.reminders(id),
  user_id         uuid not null references auth.users(id),
  scheduled_utc   timestamptz not null,
  status          text not null check (status in ('taken', 'missed', 'superseded')),
  outcome_utc     timestamptz not null default now(),
  supersedes_id   uuid references public.adherence(id),
  correction_note text,
  created_at      timestamptz not null default now()
);

-- feedback table (append-only)
create table public.feedback (
  id              uuid primary key default gen_random_uuid(),
  user_id         uuid not null references auth.users(id),
  medicine_id     uuid not null references public.medicines(id),
  description     text not null check (char_length(description) <= 2000),
  severity        smallint not null check (severity between 1 and 4),
  occurred_at     timestamptz not null,
  references_id   uuid references public.feedback(id),
  created_at      timestamptz not null default now()
);

-- emergency_contacts table
create table public.emergency_contacts (
  id           uuid primary key default gen_random_uuid(),
  user_id      uuid not null references auth.users(id),
  full_name    text not null,
  relationship text not null,
  email        text not null,
  verified     boolean not null default false,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now(),
  constraint one_contact_per_patient unique (user_id)
);

-- reports table (cache)
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

-- audit_log table
create table public.audit_log (
  id          uuid primary key default gen_random_uuid(),
  actor_id    uuid references auth.users(id),
  action_code text not null,
  target_id   uuid,
  reason      text,
  created_at  timestamptz not null default now()
);

-- disclaimer_acceptances table
create table public.disclaimer_acceptances (
  id               uuid primary key default gen_random_uuid(),
  user_id          uuid not null references auth.users(id),
  disclaimer_version text not null,
  accepted_at      timestamptz not null default now()
);
