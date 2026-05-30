-- pg_cron extension required (auto-enabled on Supabase usually)
create extension if not exists pg_cron;

select cron.schedule(
  'auto-expire-doses',
  '* * * * *',
  $$
  insert into public.adherence (reminder_id, user_id, scheduled_utc, status)
  select
    os.reminder_id,
    os.user_id,
    os.scheduled_utc,
    'missed'
  from operational_state os
  where os.status in ('pending', 'snoozed')
    and os.scheduled_utc + interval '2 hours' < now()
    and not exists (
      select 1 from public.adherence a
      where a.reminder_id = os.reminder_id
        and a.scheduled_utc = os.scheduled_utc
    );
  $$
);
