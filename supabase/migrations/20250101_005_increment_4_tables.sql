-- Increment 4: Notification Dispatch and Dose Tracking

-- Helper Functions
create or replace function public.update_updated_at_column()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create or replace function public.prevent_adherence_modification()
returns trigger language plpgsql as $$
begin
  raise exception 'adherence records are immutable';
  return old;
end;
$$;

-- doses table for operational state tracking
create table public.doses (
  id              uuid primary key default gen_random_uuid(),
  reminder_id     uuid not null references public.reminders(id),
  user_id         uuid not null references auth.users(id),
  scheduled_utc   timestamptz not null,
  status          text not null check (status in ('pending', 'taken', 'missed', 'snoozed')) default 'pending',
  snooze_count    integer not null default 0 check (snooze_count <= 3),
  last_notified_at timestamptz,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now(),
  constraint unique_dose_occurrence unique (reminder_id, scheduled_utc)
);

-- notification_retries table for persistent retry queue
create table public.notification_retries (
  id              uuid primary key default gen_random_uuid(),
  dose_id         uuid not null references public.doses(id) on delete cascade,
  retry_count     integer not null default 0,
  next_attempt_at timestamptz not null,
  last_error      text,
  is_resolved     boolean not null default false,
  created_at      timestamptz not null default now()
);

-- RLS for doses
alter table public.doses enable row level security;

create policy "patients_own_doses"
  on public.doses for all
  using (user_id = auth.uid());

create policy "providers_see_assigned_doses"
  on public.doses for select
  using (
    exists (
      select 1 from public.assignments
      where patient_id = doses.user_id
        and provider_id = auth.uid()
        and status = 'active'
    )
  );

-- RLS for notification_retries
alter table public.notification_retries enable row level security;

create policy "patients_own_retries"
  on public.notification_retries for select
  using (
    exists (
      select 1 from public.doses
      where id = notification_retries.dose_id
        and user_id = auth.uid()
    )
  );

-- Function to sync final outcomes to adherence table (ADH-FR-31)
create or replace function sync_dose_to_adherence()
returns trigger language plpgsql as $$
begin
  if (NEW.status in ('taken', 'missed')) then
    insert into public.adherence (reminder_id, user_id, scheduled_utc, status, outcome_utc)
    values (NEW.reminder_id, NEW.user_id, NEW.scheduled_utc, NEW.status, now());
  end if;
  return NEW;
end;
$$;

create trigger dose_final_outcome_sync
  after update of status on public.doses
  for each row
  when (NEW.status in ('taken', 'missed'))
  execute function sync_dose_to_adherence();

-- Update updated_at trigger for doses
create trigger set_doses_updated_at
  before update on public.doses
  for each row execute function update_updated_at_column();

-- Refined auto-expiry (ADH-FR-28)
create or replace function expire_missed_doses()
returns void language plpgsql as $$
begin
  -- Mark doses as missed if they are pending/snoozed and > 2 hours past scheduled time
  update public.doses
  set status = 'missed',
      updated_at = now()
  where status in ('pending', 'snoozed')
    and scheduled_utc <= now() - interval '2 hours';
end;
$$;

-- Function to generate upcoming doses from reminders (ADH-FR-22)
create or replace function generate_upcoming_doses()
returns void language plpgsql as $$
declare
  rem record;
  scheduled_at timestamptz;
begin
  for rem in 
    select r.* 
    from public.reminders r
    where r.is_active = true
  loop
    -- Simple logic: calculate when the next dose should be based on dose_time_utc
    -- In a real app, this would account for recurrence_type and recurrence_params.
    -- For v1.0, we assume daily for simplicity or check recurrence.
    
    scheduled_at := (current_date || ' ' || rem.dose_time_utc)::timestamptz;
    
    -- If it's within the next 5 minutes and doesn't exist yet
    if (scheduled_at between now() - interval '1 minute' and now() + interval '5 minutes') then
      insert into public.doses (reminder_id, user_id, scheduled_utc, status)
      values (rem.id, rem.user_id, scheduled_at, 'pending')
      on conflict (reminder_id, scheduled_utc) do nothing;
    end if;
  end loop;
end;
$$;
