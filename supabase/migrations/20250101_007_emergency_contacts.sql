create table public.emergency_contacts (
  id           uuid primary key default gen_random_uuid(),
  user_id      uuid not null references auth.users(id),
  full_name    text not null,
  relationship text not null,
  email        text not null,
  verified     boolean not null default false,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now(),

  -- One contact per patient regardless of verification state
  constraint one_contact_per_patient unique (user_id)
);
