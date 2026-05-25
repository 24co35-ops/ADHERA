-- 3. Functions, Triggers, and Indexes

-- Prevent adherence modification trigger
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

-- Indexes
create index idx_medicines_user_active    on public.medicines(user_id) where is_active = true;
create index idx_reminders_user_active    on public.reminders(user_id) where is_active = true;
create index idx_adherence_user           on public.adherence(user_id, scheduled_utc desc);
create index idx_adherence_reminder       on public.adherence(reminder_id, scheduled_utc desc);
create index idx_feedback_user            on public.feedback(user_id, created_at desc);
create index idx_assignments_patient      on public.assignments(patient_id, status);
create index idx_assignments_provider     on public.assignments(provider_id, status);
create index idx_audit_log_actor          on public.audit_log(actor_id, created_at desc);
