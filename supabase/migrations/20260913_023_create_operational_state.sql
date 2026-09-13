-- Migration: Create snooze_log table and operational_state view
CREATE TABLE IF NOT EXISTS public.snooze_log (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  reminder_id uuid NOT NULL REFERENCES public.reminders(id) ON DELETE CASCADE,
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  scheduled_utc timestamptz NOT NULL,
  snoozed_at timestamptz NOT NULL DEFAULT now(),
  resume_at timestamptz NOT NULL,
  snooze_count smallint NOT NULL DEFAULT 1,
  CONSTRAINT max_snoozes CHECK (snooze_count <= 3)
);

CREATE INDEX IF NOT EXISTS idx_snooze_log_user_reminder ON public.snooze_log(user_id, reminder_id, scheduled_utc);

ALTER TABLE public.snooze_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "patients_see_own_snooze_log"
  ON public.snooze_log FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "patients_insert_own_snooze_log"
  ON public.snooze_log FOR INSERT
  WITH CHECK (auth.uid() = user_id);

-- Operational state view projecting current reminder status, snooze count, and resume time
CREATE OR REPLACE VIEW public.operational_state AS
SELECT
  r.id AS reminder_id,
  r.user_id,
  COALESCE(a.scheduled_utc, sl.scheduled_utc, now()) AS scheduled_utc,
  CASE
    WHEN a.status = 'taken' THEN 'taken'
    WHEN a.status = 'missed' THEN 'missed'
    WHEN sl.id IS NOT NULL AND sl.resume_at > now() THEN 'snoozed'
    ELSE 'pending'
  END AS status,
  COALESCE(sl.snooze_count, 0) AS snooze_count,
  sl.resume_at AS snoozed_until
FROM public.reminders r
LEFT JOIN LATERAL (
  SELECT scheduled_utc, status
  FROM public.adherence
  WHERE reminder_id = r.id
  ORDER BY scheduled_utc DESC, outcome_utc DESC NULLS LAST
  LIMIT 1
) a ON true
LEFT JOIN LATERAL (
  SELECT id, scheduled_utc, snooze_count, resume_at
  FROM public.snooze_log
  WHERE reminder_id = r.id
  ORDER BY scheduled_utc DESC, snoozed_at DESC
  LIMIT 1
) sl ON true;

NOTIFY pgrst, 'reload schema';
