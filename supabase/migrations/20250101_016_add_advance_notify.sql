-- Migration to add optional 10-minute advance notification feature
ALTER TABLE public.reminders ADD COLUMN IF NOT EXISTS advance_notify boolean NOT NULL DEFAULT false;
ALTER TABLE public.reminders ADD COLUMN IF NOT EXISTS advance_notified_at timestamptz;

-- Enable pg_cron if not already enabled (requires superuser; run separately if this fails)
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Grant usage so the extension can fire
GRANT USAGE ON SCHEMA cron TO postgres;

-- Schedule pg_cron job to send advance notifications
SELECT cron.unschedule('dispatch-advance-reminders') WHERE EXISTS (
  SELECT 1 FROM cron.job WHERE jobname = 'dispatch-advance-reminders'
);

SELECT cron.schedule(
  'dispatch-advance-reminders',
  '* * * * *',
  $$
    -- Reset advance_notified_at after 12 hours so it can run again the next day
    UPDATE public.reminders
    SET advance_notified_at = NULL
    WHERE advance_notified_at IS NOT NULL
      AND advance_notified_at < now() - interval '12 hours';

    -- Find and dispatch due advance reminders
    WITH dispatched AS (
      SELECT r.id, r.user_id, u.email, m.name as medicine_name,
             m.dosage_amount || ' ' || m.dosage_unit as dosage, r.dose_label
      FROM public.reminders r
      JOIN public.medicines m ON r.medicine_id = m.id
      JOIN auth.users u ON r.user_id = u.id
      WHERE r.is_active = true
        AND r.advance_notify = true
        AND r.advance_notified_at IS NULL
        AND (r.dose_time_utc - interval '10 minutes') <= (now() at time zone 'utc')::time
        AND (r.dose_time_utc - interval '10 minutes') > (now() at time zone 'utc')::time - interval '30 minutes'
    )
    SELECT
      net.http_post(
        url := 'https://olsgvrmxqsftymsbeqve.supabase.co/functions/v1/dispatch-reminder',
        headers := '{"Content-Type": "application/json"}'::jsonb,
        body := jsonb_build_object(
          'reminder_id', id,
          'user_id', user_id,
          'user_email', email,
          'medicine_name', medicine_name,
          'dosage', dosage,
          'dose_label', dose_label,
          'scheduled_utc', (current_date + (now() at time zone 'utc')::time)::text,
          'is_advance', true
        ),
        timeout_ms := 5000
      )
    FROM dispatched;

    UPDATE public.reminders
    SET advance_notified_at = now()
    WHERE id IN (
      SELECT r.id
      FROM public.reminders r
      WHERE r.is_active = true
        AND r.advance_notify = true
        AND r.advance_notified_at IS NULL
        AND (r.dose_time_utc - interval '10 minutes') <= (now() at time zone 'utc')::time
        AND (r.dose_time_utc - interval '10 minutes') > (now() at time zone 'utc')::time - interval '30 minutes'
    );
  $$
);
