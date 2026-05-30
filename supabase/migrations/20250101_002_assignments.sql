create table public.assignments (
  id           uuid primary key default gen_random_uuid(),
  patient_id   uuid not null references auth.users(id),
  provider_id  uuid not null references auth.users(id),
  status       text not null check (status in ('active', 'inactive')) default 'active',
  assigned_on  timestamptz not null default now(),
  note         text,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now(),

  -- Enforce: patient has at most one active assignment
  constraint one_active_assignment unique nulls not distinct (patient_id, status)
    where (status = 'active')
);
