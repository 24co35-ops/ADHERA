-- Fix 6: Auto-expiry race condition
-- Add unique constraint so concurrent pg_cron runs cannot insert duplicate missed rows.
-- ON CONFLICT DO NOTHING in the cron job then becomes the safe idempotency guard.

-- 1. Unique partial index: only one 'missed' record per (reminder_id, scheduled_utc).
--    Using a partial index (not a table constraint) so superseded/correction rows
--    for the same slot are still allowed (they have a different status).
create unique index if not exists adherence_unique_missed
  on public.adherence (reminder_id, scheduled_utc)
  where status = 'missed';

-- 2. Replace the existing pg_cron job with a version that uses ON CONFLICT DO NOTHING.
--    Unschedule defensively: pg_cron has no IF EXISTS, so catch the error when the
--    job was never registered (e.g. migration _013 was not applied in this project).
do $$
begin
  perform cron.unschedule('auto-expire-doses');
exception when others then
  null; -- job did not exist; safe to proceed
end;
$$;

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
  on conflict (reminder_id, scheduled_utc)
  where status = 'missed'
  do nothing;
  $$
);

notify pgrst, 'reload schema';
