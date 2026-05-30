create table public.medicines (
  id               uuid primary key default gen_random_uuid(),
  user_id          uuid not null references auth.users(id),
  name             text not null,
  dosage_amount    numeric not null,
  dosage_unit      text not null check (dosage_unit in ('mg', 'ml', 'units')),
  route            text not null check (route in ('oral', 'topical', 'injection', 'inhaled', 'other')),
  frequency_type   text not null check (frequency_type in ('daily', 'weekday', 'alternate', 'prn')),
  recurrence_params jsonb,        -- weekday bitmask or anchor_date for alternate-day
  start_date       date not null,
  end_date         date,
  instructions     text,
  is_active        boolean not null default true,
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now()
);
