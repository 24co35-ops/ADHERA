-- Fix 9: Stale reports recalculation pg_cron job
-- Recalculates any report where is_stale=true so dashboards never show outdated data.

-- Helper function: recalculate a single report row from raw adherence data.
create or replace function public.recalculate_stale_report(p_report_id uuid)
returns void
language plpgsql
security definer
set search_path = ''
as $$
declare
  r public.reports%rowtype;
  v_total   integer;
  v_taken   integer;
  v_missed  integer;
  v_rate    numeric(5,1);
begin
  select * into r from public.reports where id = p_report_id;
  if not found then return; end if;

  select
    count(*) filter (where a.status in ('taken','missed','snoozed')),
    count(*) filter (where a.status = 'taken'),
    count(*) filter (where a.status = 'missed')
  into v_total, v_taken, v_missed
  from public.adherence a
  where a.user_id      = r.user_id
    and a.scheduled_utc::date between r.period_start and r.period_end;

  v_rate := case when v_total > 0 then round(v_taken::numeric / v_total * 100, 1) else 0 end;

  update public.reports
  set
    total_doses    = coalesce(v_total, 0),
    doses_taken    = coalesce(v_taken, 0),
    doses_missed   = coalesce(v_missed, 0),
    adherence_rate = v_rate,
    is_stale       = false,
    updated_at     = now()
  where id = p_report_id;
end;
$$;

-- Security hardening: revoke public/anon/authenticated execution of SECURITY DEFINER function
revoke execute on function public.recalculate_stale_report(uuid) from public, anon, authenticated;
grant execute on function public.recalculate_stale_report(uuid) to service_role, postgres;

-- Unschedule defensively so repeated migration runs do not error out (pg_cron has no IF EXISTS)
do $$
begin
  perform cron.unschedule('recalculate-stale-reports');
exception when others then
  null; -- job did not exist; safe to proceed
end;
$$;

-- pg_cron job: run every 15 minutes, process up to 50 stale reports at a time.
select cron.schedule(
  'recalculate-stale-reports',
  '*/15 * * * *',
  $$
  select public.recalculate_stale_report(id)
  from public.reports
  where is_stale = true
  order by updated_at asc
  limit 50;
  $$
);

notify pgrst, 'reload schema';
