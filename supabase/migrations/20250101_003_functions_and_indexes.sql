-- 3. Functions, Triggers, and Indexes

-- Auto-expire missed doses after 2 hours
create or replace function expire_missed_doses()
returns void language plpgsql as $$
begin
  insert into public.adherence (reminder_id, user_id, scheduled_utc, status, outcome_utc)
  select r.id, r.user_id, now() - interval '2 hours', 'missed', now()
  from public.reminders r
  where r.is_active = true
  and not exists (
    select 1 from public.adherence a 
    where a.reminder_id = r.id 
    and a.scheduled_utc >= now() - interval '2 hours'
  );
end;
$$;

-- Note: In a real Supabase project, you would enable pg_cron and run:
-- select cron.schedule('expire-missed-doses', '0 * * * *', 'select expire_missed_doses()');


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
