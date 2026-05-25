-- 1. Core Entity Tables

-- profiles table (extends auth.users)
create table public.profiles (
  id           uuid primary key references auth.users(id) on delete cascade,
  full_name    text not null,
  role         text not null check (role in ('patient', 'provider', 'admin')),
  date_of_birth date,
  contact_number text,
  timezone     text not null default 'UTC',
  is_active    boolean not null default true,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now()
);

-- medicines table
create table public.medicines (
  id               uuid primary key default gen_random_uuid(),
  user_id          uuid not null references auth.users(id),
  name             text not null,
  dosage_amount    numeric not null,
  dosage_unit      text not null check (dosage_unit in ('mg', 'ml', 'units')),
  route            text not null check (route in ('oral', 'topical', 'injection', 'inhaled', 'other')),
  frequency_type   text not null check (frequency_type in ('daily', 'weekday', 'alternate', 'prn')),
  recurrence_params jsonb,
  start_date       date not null,
  end_date         date,
  instructions     text,
  is_active        boolean not null default true,
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now()
);

-- reminders table
create table public.reminders (
  id               uuid primary key default gen_random_uuid(),
  medicine_id      uuid not null references public.medicines(id),
  user_id          uuid not null references auth.users(id),
  dose_label       text not null check (dose_label in ('morning', 'afternoon', 'evening', 'night')),
  dose_time_utc    time not null,
  timezone         text not null,
  recurrence_type  text not null,
  recurrence_params jsonb,
  is_active        boolean not null default true,
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now(),
  constraint unique_reminder_slot unique (
    medicine_id, dose_label, recurrence_type, recurrence_params, dose_time_utc
  )
);

-- assignments table
create table public.assignments (
  id           uuid primary key default gen_random_uuid(),
  patient_id   uuid not null references auth.users(id),
  provider_id  uuid not null references auth.users(id),
  status       text not null check (status in ('active', 'inactive')) default 'active',
  assigned_on  timestamptz not null default now(),
  note         text,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now(),
  constraint one_active_assignment unique nulls not distinct (patient_id, status)
    where (status = 'active')
);
