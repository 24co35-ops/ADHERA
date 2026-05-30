create table public.adherence (
  id              uuid primary key default gen_random_uuid(),
  reminder_id     uuid not null references public.reminders(id),
  user_id         uuid not null references auth.users(id),
  scheduled_utc   timestamptz not null,
  status          text not null check (status in ('taken', 'missed', 'superseded')),
  outcome_utc     timestamptz not null default now(),
  supersedes_id   uuid references public.adherence(id),  -- for admin corrections
  correction_note text,
  created_at      timestamptz not null default now()
  -- No updated_at: append-only table
);

-- Prevent application-level UPDATE/DELETE via RLS + trigger
create or replace function prevent_adherence_modification()
returns trigger language plpgsql as $$
begin
  if tg_op = 'UPDATE' then
    raise exception 'adherence records are immutable';
  end if;
  return old;
end;
$$;
create trigger adherence_immutable
  before update or delete on public.adherence
  for each row execute function prevent_adherence_modification();
