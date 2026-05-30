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

  -- Uniqueness: no duplicate slots
  constraint unique_reminder_slot unique (
    medicine_id, dose_label, recurrence_type, recurrence_params, dose_time_utc
  )
);
